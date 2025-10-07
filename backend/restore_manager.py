# backend/restore_manager.py
"""
Restore manager for FYP backup system.

Responsibilities:
- Start a restore request (generate OTP, save to DB, notify user via Telegram)
- Perform a single-file restore after OTP validation
- Perform a snapshot restore (restore set of files)
- Defensive logging, DR event creation, and fallback handling for storage client API variations

Assumptions:
- DB helpers from backend.db are available:
    - create_otp_record(user_id, code, expiry)
    - get_valid_otp(user_id, code)
    - mark_otp_used(otp_id)
    - add_log(...)
    - get_file_entry(...)
    - get_snapshot_entries(snapshot_id) and get_file_entry(...)
    - get_user(user_id)
- Encryption helper: backend.encryption.decrypt_file(input_path, output_path)
- Storage client exposes one of:
    - download_file(storage_path, local_target_path)
    - fetch_blob(storage_path) -> bytes
    - get_blob(storage_path) -> bytes
  This module attempts to use whichever exists.
"""

import os
import tempfile
import traceback
import random
from datetime import datetime, timedelta

from config import settings
from backend import db
from backend import alerts
from backend import encryption
from backend import storage_client

# OTP defaults (fallbacks if settings missing)
OTP_LENGTH = getattr(settings, "OTP_LENGTH", 6)
OTP_EXPIRY_SECONDS = getattr(settings, "OTP_EXPIRY_SECONDS", 300)


# -------------------------
# Internal utilities
# -------------------------
def _make_otp_code(length: int = OTP_LENGTH) -> str:
    """Create a numeric OTP code of given length."""
    return ''.join(str(random.randint(0, 9)) for _ in range(length))


def _storage_download_to_temp(storage_path: str) -> str:
    """
    Download a storage blob into a temp file and return its path.
    Tries different storage_client APIs for compatibility.
    """
    # Prefer a direct download API that writes to a path
    tmpdir = tempfile.mkdtemp(prefix="fyp_restore_")
    local_path = os.path.join(tmpdir, os.path.basename(storage_path).replace(os.sep, "_") + ".enc")

    # Try preferred function names in storage_client
    for fn_name in ("download_file", "get_file", "fetch_blob_to_file", "save_to_local"):
        fn = getattr(storage_client, fn_name, None)
        if callable(fn):
            # Functions that write to a path should accept (storage_path, local_path) or (user_id, filename, version, local_path)
            try:
                # Try both signatures: (storage_path, local_path) first
                try:
                    fn(storage_path, local_path)
                except TypeError:
                    # fallback: try with only local_path (some clients may require different args)
                    fn(local_path)
                return local_path
            except Exception:
                # if it failed, continue to try other functions
                continue

    # Try fetch_blob / get_blob which return bytes
    for fn_name in ("fetch_blob", "get_blob", "download_blob"):
        fn = getattr(storage_client, fn_name, None)
        if callable(fn):
            try:
                blob = fn(storage_path)
                if blob is None:
                    raise RuntimeError("Storage client returned no data")
                # write bytes to file
                with open(local_path, "wb") as f:
                    if isinstance(blob, bytes):
                        f.write(blob)
                    else:
                        # If it's a file-like object
                        try:
                            f.write(blob.read())
                        except Exception:
                            raise
                return local_path
            except Exception:
                continue

    # As last resort, raise helpful error
    raise RuntimeError("No compatible storage_client download API found (tried download_file/fetch_blob/get_blob).")


# -------------------------
# Public API
# -------------------------
def start_restore_request(user_id: int, filename: str, version: int = None) -> dict:
    """
    Generate OTP for a user to authorize restoration of `filename`.
    If version is None, the latest version will be restored when performed.
    Returns: dict {ok: bool, message: str}
    """
    user = db.get_user(user_id)
    if not user:
        return {"ok": False, "message": "User not found"}

    code = _make_otp_code()
    expiry = datetime.utcnow() + timedelta(seconds=OTP_EXPIRY_SECONDS)
    otp = db.create_otp_record(user_id, code, expiry)

    # Notify user via Telegram (prefer sending to their stored chat id)
    chat_id = user.telegram_chat_id
    msg = f"Your OTP for restoring '{filename}' is: {code}\nThis code expires in {OTP_EXPIRY_SECONDS // 60} minutes."
    sent = alerts.send_alert(chat_id, msg)
    db.add_log(user_id, "otp_sent", f"OTP id={otp.id} for {filename}, sent={sent}")

    # record DR event for auditing
    db.record_dr_event(user_id, "otp_issued", f"OTP {otp.id} issued for {filename}, expires {expiry.isoformat()}")

    if not sent:
        return {"ok": False, "message": "Failed to send OTP via Telegram; check configuration."}
    return {"ok": True, "message": "OTP sent via Telegram. Check your messages."}


def perform_restore(user_id: int, filename: str, version: int, target_path: str, otp_code: str) -> dict:
    """
    Validate OTP and perform file restore.
    - filename: base filename (as stored in DB)
    - version: integer version to restore (if None, restore latest)
    - target_path: local filesystem path where decrypted file will be written
    - otp_code: code provided by user
    Returns: dict {ok: bool, message: str}
    """
    try:
        # Validate user
        user = db.get_user(user_id)
        if not user:
            return {"ok": False, "message": "User not found"}

        # Validate OTP
        otp_rec = db.get_valid_otp(user_id, otp_code)
        if not otp_rec:
            db.add_log(user_id, "restore_failed_otp", f"OTP invalid for {filename}")
            return {"ok": False, "message": "OTP invalid or expired"}

        # Mark OTP used (one-time)
        db.mark_otp_used(otp_rec.id)

        # Determine which file entry to restore
        if version is None:
            # latest version
            entries = db.get_file_entries(user_id, filename)
            if not entries:
                return {"ok": False, "message": "No backups found for this file"}
            entry = entries[0]  # newest (db returns sorted desc)
        else:
            entry = db.get_file_entry(user_id, filename, version)
            if not entry:
                return {"ok": False, "message": f"Requested version {version} not found"}

        storage_path = entry.storage_path
        db.add_log(user_id, "restore_start", f"Restore {filename} v{entry.version} to {target_path}")

        # Download encrypted blob into temp file
        try:
            enc_local = _storage_download_to_temp(storage_path)
        except Exception as e:
            db.add_log(user_id, "restore_download_failed", f"{storage_path}: {e}")
            db.record_dr_event(user_id, "restore_failed", f"Download failed for {storage_path}: {traceback.format_exc()}")
            return {"ok": False, "message": "Failed to download backup from storage"}

        # Decrypt into target path (do not overwrite unless user explicitly chooses UI action)
        try:
            # ensure target folder exists
            os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)
            encryption.decrypt_file(enc_local, target_path)
        except Exception as e:
            db.add_log(user_id, "restore_decrypt_failed", f"{filename} v{entry.version}: {e}")
            db.record_dr_event(user_id, "restore_failed", f"Decryption failed for {filename} v{entry.version}: {traceback.format_exc()}")
            return {"ok": False, "message": "Failed to decrypt backup (possible corruption or wrong key)"}
        finally:
            # cleanup encrypted temp files
            try:
                # remove temp dir that enc_local resides in
                tdir = os.path.dirname(enc_local)
                if os.path.exists(tdir):
                    # remove file(s) safely
                    for f in os.listdir(tdir):
                        try:
                            os.remove(os.path.join(tdir, f))
                        except Exception:
                            pass
                    try:
                        os.rmdir(tdir)
                    except Exception:
                        pass
            except Exception:
                pass

        # Success!
        db.add_log(user_id, "restore_success", f"{filename} v{entry.version} restored to {target_path}")
        db.record_dr_event(user_id, "restore_performed", f"{filename} v{entry.version} restored to {target_path}")
        # Notify user
        try:
            alerts.send_alert(user.telegram_chat_id, f"Restore completed: {filename} (v{entry.version}) to {target_path}")
        except Exception:
            db.add_log(user_id, "alert_failed", f"Failed to send restore completion alert for {filename}")

        return {"ok": True, "message": "Restore completed successfully"}

    except Exception as ex:
        # Unexpected error
        db.add_log(user_id, "restore_unexpected_error", f"{filename}: {traceback.format_exc()}")
        db.record_dr_event(user_id, "restore_failed_unexpected", f"{filename}: {traceback.format_exc()}")
        return {"ok": False, "message": "Unexpected error during restore"}


def restore_snapshot(user_id: int, snapshot_id: int, target_folder: str, otp_code: str = None) -> dict:
    """
    Restore all files referenced by a snapshot into a target folder.
    If OTP is required, caller must validate OTP prior to calling (or call start_restore_request and then pass OTP here).
    This function will iterate snapshot entries and restore each file.
    Returns summary dict with success/failure counts and details.
    """
    try:
        # Basic validations
        user = db.get_user(user_id)
        if not user:
            return {"ok": False, "message": "User not found"}

        # Optionally require OTP for snapshot restore (enforce depending on policy)
        if getattr(settings, "REQUIRE_OTP_FOR_SNAPSHOT_RESTORE", True):
            if not otp_code:
                return {"ok": False, "message": "OTP required for snapshot restore"}
            otp_rec = db.get_valid_otp(user_id, otp_code)
            if not otp_rec:
                return {"ok": False, "message": "OTP invalid or expired"}
            db.mark_otp_used(otp_rec.id)

        # Get snapshot entries
        entries = db.get_snapshot_entries(snapshot_id)
        if not entries:
            return {"ok": False, "message": "Snapshot not found or has no entries"}

        successes = []
        failures = []

        for se in entries:
            # se.file_entry_id is stored; fetch file entry details
            fe = db.get_file_entry(None, None, None)  # placeholder - we will fetch via session manually below
            # But since helper doesn't support getting by id, we'll use session directly
            with db.get_session() as session:
                fe = session.get(db.FileEntry, se.file_entry_id)

            if not fe:
                failures.append({"entry_id": se.file_entry_id, "reason": "File entry missing"})
                continue

            # compute local target path per filename
            tgt = os.path.join(target_folder, fe.filename)
            try:
                # reuse perform_restore flow but bypass OTP (we already validated)
                # download encrypted blob
                enc_local = _storage_download_to_temp(fe.storage_path)
                # decrypt into target
                os.makedirs(os.path.dirname(tgt) or ".", exist_ok=True)
                encryption.decrypt_file(enc_local, tgt)
                # cleanup temp
                try:
                    tdir = os.path.dirname(enc_local)
                    for f in os.listdir(tdir):
                        try:
                            os.remove(os.path.join(tdir, f))
                        except Exception:
                            pass
                    try:
                        os.rmdir(tdir)
                    except Exception:
                        pass
                except Exception:
                    pass

                db.add_log(user_id, "snapshot_restore_file", f"Restored {fe.filename} (v{fe.version}) to {tgt}")
                successes.append({"filename": fe.filename, "version": fe.version, "target": tgt})
            except Exception as e:
                db.add_log(user_id, "snapshot_restore_failed", f"{fe.filename} v{fe.version}: {traceback.format_exc()}")
                failures.append({"filename": fe.filename, "version": fe.version, "reason": str(e)})

        # summary logging & notification
        db.record_dr_event(user_id, "snapshot_restore", f"Snapshot {snapshot_id} restored: success={len(successes)} fail={len(failures)}")
        try:
            alerts.send_alert(user.telegram_chat_id, f"Snapshot restore completed: {len(successes)} files restored, {len(failures)} failures")
        except Exception:
            pass

        return {"ok": True, "restored": successes, "failed": failures}

    except Exception as ex:
        db.add_log(user_id, "snapshot_restore_unexpected", traceback.format_exc())
        db.record_dr_event(user_id, "snapshot_restore_failed_unexpected", traceback.format_exc())
        return {"ok": False, "message": "Unexpected error during snapshot restore"}
