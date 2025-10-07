# backend/storage_client.py
"""
Storage client (local-first) with replication support.

Responsibilities:
- upload_file(user_id, filename, version, local_encrypted_path) -> storage_path
- download_file(storage_path, local_target_path)
- fetch_blob(storage_path) -> bytes
- delete_blob(storage_path)
- start_replication_worker() -> background thread that replicates queued blobs to a secondary store

Design goals:
- Local-first (fast, easy testing). Primary storage path is LOCAL_STORAGE_PATH (config).
- Replication to secondary store (SECONDARY_STORAGE_PATH local folder OR SFTP replica) is handled asynchronously.
- Robust logging and DR event recording through backend.db.
- Pluggable: later replace local storage operations with SMB/Paramiko calls.
"""

import os
import shutil
import threading
import time
import logging
from pathlib import Path
from typing import Optional

from config import settings
from backend import db

logger = logging.getLogger("storage_client")
logger.setLevel(logging.INFO)

# Settings and defaults
PRIMARY_STORAGE = getattr(settings, "LOCAL_STORAGE_PATH", "./nas_storage")
SECONDARY_STORAGE = getattr(settings, "SECONDARY_STORAGE_PATH", None)  # optional local path for replica
# Optional SFTP backup config for secondary (dict in settings or None):
# SECONDARY_SFTP = {"host": "...", "port": 22, "username": "...", "password": "...", "remote_base": "/backups"}
SECONDARY_SFTP = getattr(settings, "SECONDARY_SFTP", None)

# Ensure primary storage exists
os.makedirs(PRIMARY_STORAGE, exist_ok=True)


# -----------------------------
# Basic local storage operations
# -----------------------------
def _user_dir(user_id: int) -> str:
    d = os.path.join(PRIMARY_STORAGE, f"user_{user_id}")
    os.makedirs(d, exist_ok=True)
    return d


def _storage_filename(filename: str, version: int) -> str:
    # sanitize filename slightly
    safe = filename.replace(os.sep, "_")
    return f"{safe}.v{version}.enc"


def upload_file(user_id: int, filename: str, version: int, local_encrypted_path: str) -> str:
    """
    Uploads the encrypted file (local_encrypted_path) to PRIMARY_STORAGE and returns storage_path.
    For local-first mode this simply copies file into PRIMARY_STORAGE/user_{id}/.
    """
    user_dir = _user_dir(user_id)
    dest_name = _storage_filename(filename, version)
    dest_path = os.path.join(user_dir, dest_name)

    try:
        shutil.copy2(local_encrypted_path, dest_path)
        db.add_log(user_id, "upload_success", f"Uploaded {filename} v{version} -> {dest_path}")
        # enqueue replication to secondary store
        db.enqueue_replication_file = None  # noop placeholder (db handles enqueue)
        # Insert replication queue entry
        db.enqueue_replication = getattr(db, "enqueue_replication", None)
        if callable(db.enqueue_replication):
            try:
                # We need to get file_entry_id but backup_manager calls this before FileEntry exists.
                # So backup_manager enqueues replication after DB entry creation. Here we only return storage path.
                pass
            except Exception:
                pass
        return dest_path
    except Exception as e:
        db.add_log(user_id, "upload_exception", f"Failed to copy to primary storage: {e}")
        db.record_dr_event(user_id, "upload_failed_local", f"{filename} v{version} upload failed: {e}")
        raise


def download_file(storage_path: str, local_target_path: str) -> None:
    """
    Download a blob from storage_path into local_target_path.
    For local-first mode, storage_path is a local path; just copy.
    """
    try:
        if not os.path.exists(storage_path):
            raise FileNotFoundError(f"Storage path not found: {storage_path}")
        os.makedirs(os.path.dirname(local_target_path) or ".", exist_ok=True)
        shutil.copy2(storage_path, local_target_path)
    except Exception as e:
        logger.exception("download_file failed")
        raise


def fetch_blob(storage_path: str) -> bytes:
    """
    Return bytes of the blob at storage_path.
    """
    if not os.path.exists(storage_path):
        raise FileNotFoundError(f"Storage path not found: {storage_path}")
    with open(storage_path, "rb") as f:
        return f.read()


def delete_blob(storage_path: str) -> bool:
    """
    Delete blob from primary storage. Returns True if removed or did not exist.
    """
    try:
        if os.path.exists(storage_path):
            os.remove(storage_path)
            return True
        return True
    except Exception as e:
        logger.exception("delete_blob failed")
        return False


# -----------------------------
# Replication: local or SFTP
# -----------------------------
def _replicate_to_local_secondary(storage_path: str) -> bool:
    """
    Copy a primary storage file to SECONDARY_STORAGE local path.
    Returns True on success.
    """
    if not SECONDARY_STORAGE:
        return False

    try:
        # path under secondary: SECONDARY_STORAGE/user_{id}/<basename>
        # Attempt to derive user_id from path: primary stores under .../user_<id>/file
        p = Path(storage_path)
        parts = p.parts
        # naive find 'user_<id>' segment
        user_seg = next((s for s in parts if s.startswith("user_")), None)
        if user_seg:
            user_dir = os.path.join(SECONDARY_STORAGE, user_seg)
        else:
            user_dir = SECONDARY_STORAGE
        os.makedirs(user_dir, exist_ok=True)
        dest = os.path.join(user_dir, p.name)
        shutil.copy2(storage_path, dest)
        return True
    except Exception as e:
        logger.exception("Local secondary replication failed")
        return False


def _replicate_to_sftp(storage_path: str) -> bool:
    """
    Attempt to replicate file to SFTP secondary. SECONDARY_SFTP must be configured in settings.
    Tries paramiko if installed. Returns True on success.
    """
    if not SECONDARY_SFTP:
        return False

    try:
        import paramiko  # optional dependency
    except ImportError:
        logger.warning("paramiko not installed; SFTP replication unavailable")
        return False

    cfg = SECONDARY_SFTP
    host = cfg.get("host")
    port = cfg.get("port", 22)
    username = cfg.get("username")
    password = cfg.get("password")
    remote_base = cfg.get("remote_base", ".")

    try:
        transport = paramiko.Transport((host, port))
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        # determine remote path. Use same basename
        basename = os.path.basename(storage_path)
        remote_dir = remote_base.rstrip("/")
        try:
            sftp.chdir(remote_dir)
        except IOError:
            # try to mkdir recursively (simple)
            try:
                sftp.mkdir(remote_dir)
            except Exception:
                pass

        remote_path = remote_dir + "/" + basename
        sftp.put(storage_path, remote_path)
        sftp.close()
        transport.close()
        return True
    except Exception:
        logger.exception("SFTP replication failed")
        return False


def _replicate_blob(storage_path: str) -> bool:
    """
    Try replicating to secondary with retry order:
      1) local secondary folder (if configured)
      2) SFTP secondary (if configured and paramiko present)
    """
    # Try local secondary first
    if SECONDARY_STORAGE:
        ok = _replicate_to_local_secondary(storage_path)
        if ok:
            return True

    # Try SFTP if configured
    if SECONDARY_SFTP:
        ok = _replicate_to_sftp(storage_path)
        if ok:
            return True

    return False


# -----------------------------
# Replication worker
# -----------------------------
_REPL_WORKER = None
_REPL_STOP = threading.Event()


def _replication_worker_loop(interval_seconds: int = 10):
    """
    Worker loop: polls replication queue, tries to replicate each entry.
    Uses db.pop_replication_candidates() to fetch candidates.
    """
    logger.info("Replication worker started")
    while not _REPL_STOP.is_set():
        try:
            # Fetch candidates
            candidates = db.pop_replication_candidates(limit=20)
            if not candidates:
                # nothing to do
                time.sleep(interval_seconds)
                continue

            for r in candidates:
                # r is a ReplicationQueue ORM object with id, storage_path, attempted, file_entry_id
                rid = r.id
                spath = r.storage_path
                try:
                    db.record_replication_attempt(rid)
                    ok = _replicate_blob(spath)
                    if ok:
                        db.mark_replicated(rid)
                        db.add_log(None, "replication_success", f"Replicated {spath} (replication_id={rid})")
                    else:
                        # not replicated: increment attempts (done), leave for next loop (or reinsert)
                        db.add_log(None, "replication_failed", f"Failed replicate {spath} (replication_id={rid})")
                except Exception as e:
                    logger.exception("Error processing replication candidate")
                    db.add_log(None, "replication_exception", f"{spath}: {e}")
            # short sleep before next loop
            time.sleep(1)
        except Exception:
            logger.exception("Replication worker loop error")
            time.sleep(interval_seconds)
    logger.info("Replication worker stopping")


def start_replication_worker(interval_seconds: int = 10):
    """
    Start replication worker in background if not already running.
    """
    global _REPL_WORKER, _REPL_STOP
    if _REPL_WORKER and _REPL_WORKER.is_alive():
        logger.info("Replication worker already running")
        return
    _REPL_STOP.clear()
    _REPL_WORKER = threading.Thread(target=_replication_worker_loop, args=(interval_seconds,), daemon=True)
    _REPL_WORKER.start()


def stop_replication_worker():
    global _REPL_STOP
    _REPL_STOP.set()


# -----------------------------
# Initialization helper
# -----------------------------
def init_storage():
    """
    Ensure primary and secondary storage directories exist (local-only).
    Call at app startup.
    """
    os.makedirs(PRIMARY_STORAGE, exist_ok=True)
    if SECONDARY_STORAGE:
        os.makedirs(SECONDARY_STORAGE, exist_ok=True)


# -----------------------------
# Convenience: test function
# -----------------------------
def health_check() -> dict:
    """
    Return a small status dict for debugging / UI.
    """
    return {
        "primary_exists": os.path.exists(PRIMARY_STORAGE),
        "primary_path": os.path.abspath(PRIMARY_STORAGE),
        "secondary_exists": bool(SECONDARY_STORAGE and os.path.exists(SECONDARY_STORAGE)),
        "secondary_configured": bool(SECONDARY_STORAGE or SECONDARY_SFTP),
        "secondary_path": os.path.abspath(SECONDARY_STORAGE) if SECONDARY_STORAGE else None,
    }
