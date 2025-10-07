# backend/backup_manager.py
"""
Backup manager: handles snapshots, versioning, encryption, storage,
pruning old versions, and integration with DR helpers.

Exposed functions used by other modules:
- handle_file_event(user_email, file_path, event_type)
- create_snapshot(target_path, user_email, reason=None)
- perform_manual_backup(user_id, file_path)  # lower-level API
"""

import os
import tempfile
import shutil
import hashlib
import traceback
from datetime import datetime

from config import settings
from backend import db
from backend.encryption import encrypt_file
from backend import storage_client
from backend import alerts

# Default retention - uses settings or fallback to 3
MAX_VERSIONS = getattr(settings, "MAX_VERSIONS_PER_FILE", 3)


# -------------------------
# Utilities
# -------------------------
def _sha256_of_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_basename(path: str) -> str:
    return os.path.basename(path)


# -------------------------
# Core backup flow
# -------------------------
def perform_manual_backup(user_id: int, file_path: str) -> db.FileEntry:
    """
    Encrypts file_path, uploads to primary storage (via storage_client),
    creates DB FileEntry, enqueues replication, prunes old versions,
    logs and notifies the user.

    Returns the created FileEntry.
    """
    user = db.get_user(user_id)
    if not user:
        raise ValueError("User not found")

    if not os.path.exists(file_path):
        msg = f"Backup failed: source not found: {file_path}"
        db.add_log(user_id, "backup_failed", msg)
        raise FileNotFoundError(msg)

    fname = _safe_basename(file_path)
    # determine next version
    latest = db.get_latest_version(user_id, fname)
    version = latest + 1

    # create temp encrypted file
    tmpdir = tempfile.mkdtemp(prefix="fyp_enc_")
    try:
        enc_path = os.path.join(tmpdir, f"{fname}.enc")
        encrypt_file(file_path, enc_path)  # from backend.encryption
        checksum = _sha256_of_file(enc_path)

        # attempt upload to primary storage (storage_client should implement upload_file)
        try:
            storage_path = storage_client.upload_file(user_id, fname, version, enc_path)
        except Exception as e:
            # on upload failure: enqueue unsynced file for crash-recovery and raise/log
            db.add_log(user_id, "upload_failed", f"{fname} v{version} upload failed: {e}")
            db.add_unsynced_file(user_id, file_path, fname)
            # record DR event
            db.record_dr_event(user_id, "upload_failed", f"{fname} v{version} upload failed: {traceback.format_exc()}")
            raise

        # create DB file entry
        fe = db.add_file_entry(user_id, fname, version, storage_path, checksum)

        # create or update snapshot grouping: for single-file snapshot this creates a snapshot and links it
        snap = db.create_snapshot(user_id, name=f"{fname}-v{version}", description=f"Auto snapshot for {fname}:v{version}")
        db.add_snapshot_entry(snap.id, fe.id)

        # enqueue replication to secondary store (e.g., Ubuntu VM)
        db.enqueue_replication(fe.id, storage_path)

        # prune old versions beyond MAX_VERSIONS
        removed = db.prune_old_versions(user_id, fname, keep=MAX_VERSIONS)
        # removed is list of tuples (entry_id, storage_path) — caller should delete blobs if desired.
        # For now, storage_client may implement delete_blob(storage_path) - try to delete
        for entry_id, spath in removed:
            try:
                storage_client.delete_blob(spath)
            except Exception:
                # log and continue
                db.add_log(user_id, "prune_warning", f"Failed to delete blob {spath} during prune")

        # logging & alert
        db.add_log(user_id, "backup", f"{fname} v{version} backed up -> {storage_path}")
        try:
            alerts.send_alert(user.telegram_chat_id, f"Backup complete: {fname} (v{version})")
        except Exception:
            # don't fail backup if notification fails
            db.add_log(user_id, "alert_failed", f"Telegram alert failed for {fname} v{version}")

        # return the created FileEntry
        return fe

    finally:
        # cleanup temp dir
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass


# -------------------------
# High-level APIs used by monitor / UI
# -------------------------
def create_snapshot(target_path: str, user_email: str, reason: str = None):
    """
    High-level function called by monitor when a snapshot is desired for a path.
    - If target_path is a file: perform backup of that file.
    - If target_path is a directory: iterate files and backup (recursive).
    - user_email: resolved to user_id via DB.
    - reason: optional reason for logging.
    """
    user = db.get_user_by_email(user_email)
    if not user:
        # If no user found by email, try treating user_email as numeric id string
        try:
            uid = int(user_email)
            user = db.get_user(uid)
        except Exception:
            raise ValueError("User not found for snapshot")

    user_id = user.id
    db.add_log(user_id, "snapshot_start", f"Snapshot requested for {target_path}. Reason: {reason}")

    if os.path.isdir(target_path):
        # Walk directory and backup files
        for root, _, files in os.walk(target_path):
            for f in files:
                full = os.path.join(root, f)
                try:
                    perform_manual_backup(user_id, full)
                except Exception as ex:
                    db.add_log(user_id, "snapshot_file_failed", f"{full}: {ex}")
    else:
        # single file
        try:
            fe = perform_manual_backup(user_id, target_path)
        except Exception as ex:
            db.add_log(user_id, "snapshot_file_failed", f"{target_path}: {ex}")
            return

    db.add_log(user_id, "snapshot_complete", f"Snapshot completed for {target_path}. Reason: {reason}")


def handle_file_event(user_email: str, file_path: str, event_type: str):
    """
    Called by file_monitor when a file is created/modified.
    event_type: "created" | "modified" | "deleted"
    Behavior:
      - For created/modified: schedule/perform snapshot according to writer rules handled elsewhere.
      - For deleted: record log and create a snapshot of last known version (DB may already have entries).
    """
    # Resolve user id
    user = db.get_user_by_email(user_email)
    if not user:
        # try parse numeric
        try:
            uid = int(user_email)
            user = db.get_user(uid)
        except Exception:
            db.add_log(None, "handle_event_error", f"user not found for event on {file_path}")
            return

    user_id = user.id

    try:
        if event_type in ("created", "modified"):
            # For now: perform immediate backup. The writer-thread may also call create_snapshot on intervals.
            try:
                perform_manual_backup(user_id, file_path)
            except Exception as e:
                db.add_log(user_id, "backup_error", f"Backup failed for {file_path}: {e}")
                # if upload failed, unsynced entry is already queued in perform_manual_backup
        elif event_type == "deleted":
            db.add_log(user_id, "file_deleted_event", f"{file_path}")
            alerts.send_alert(user.telegram_chat_id, f"File deleted: {file_path}")
            # Optionally, trigger DR workflow: attempt auto-restore of last version
            entries = db.get_file_entries(user_id, os.path.basename(file_path))
            if entries:
                last = entries[0]
                db.record_dr_event(user_id, "auto_restore_attempt", f"Auto-restore last version of {file_path}")
                # Attempt to fetch and restore in background via restore_manager (not imported here to avoid circular)
    except Exception as e:
        db.add_log(user_id, "handle_event_exception", f"{file_path} event {event_type}: {traceback.format_exc()}")


# -------------------------
# Convenience: manual trigger for bulk snapshot (e.g., user asks "Snapshot folder now")
# -------------------------
def snapshot_folder_now(user_id: int, folder_path: str, description: str = None):
    """
    Exposed API for UI to snapshot a folder immediately.
    """
    if not os.path.isdir(folder_path):
        raise ValueError("Folder not found")

    snap = db.create_snapshot(user_id, description=description or f"Manual snapshot of {folder_path}")
    # iterate and backup each file, adding snapshot entries
    for root, _, files in os.walk(folder_path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                fe = perform_manual_backup(user_id, fp)
                db.add_snapshot_entry(snap.id, fe.id)
            except Exception as e:
                db.add_log(user_id, "snapshot_folder_file_failed", f"{fp}: {e}")
    db.add_log(user_id, "snapshot_folder_complete", f"{folder_path} snapshot complete")
