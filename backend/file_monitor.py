# backend/file_monitor.py
import os
import time
import hashlib
import threading
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from backend.backup_manager import create_snapshot
from backend.alerts import send_alert


# ---------------------------
# Helpers
# ---------------------------

def file_hash(path: str) -> str:
    """Return SHA256 hash of a file (or None if unreadable)."""
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None


def is_file_open(path: str) -> bool:
    """Check if a file is open by any process (Windows only)."""
    for proc in psutil.process_iter(["pid", "open_files"]):
        try:
            files = proc.info["open_files"]
            if files:
                for f in files:
                    if f.path == path:
                        return True
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    return False


# ---------------------------
# File Open Snapshot Thread
# ---------------------------

def snapshot_while_open(file_path: str, user_email: str):
    """
    Take snapshot every 5 minutes while file is open,
    then one final snapshot when closed.
    """
    print(f"[Monitor] Tracking file for writer-like behavior: {file_path}")
    already_backed = False

    while is_file_open(file_path):
        if not already_backed:
            create_snapshot(file_path, user_email, reason="File opened")
            already_backed = True

        time.sleep(300)  # wait 5 minutes
        if is_file_open(file_path):
            create_snapshot(file_path, user_email, reason="5-min writer snapshot")

    # file closed → final snapshot
    create_snapshot(file_path, user_email, reason="File closed")


# ---------------------------
# Ransomware & Corruption Detection
# ---------------------------

class RansomwareHandler(FileSystemEventHandler):
    """
    Detect suspicious changes like rapid encryption, extension changes,
    or mass modifications (potential ransomware).
    """

    def __init__(self, user_email: str):
        self.user_email = user_email
        self.change_count = 0
        self.last_reset = time.time()

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = event.src_path
        self.change_count += 1

        # Reset counter every minute
        if time.time() - self.last_reset > 60:
            self.change_count = 0
            self.last_reset = time.time()

        # Check suspicious behavior
        if file_path.endswith((".locked", ".enc", ".encrypted")):
            send_alert(
                self.user_email,
                f"⚠️ Ransomware Alert: File extension changed -> {file_path}",
            )
            create_snapshot(file_path, self.user_email, reason="Ransomware detected")

        elif self.change_count > 50:
            send_alert(
                self.user_email,
                "⚠️ Ransomware Alert: Too many files modified in 1 minute.",
            )

    def on_deleted(self, event):
        if event.is_directory:
            return
        file_path = event.src_path
        send_alert(self.user_email, f"⚠️ File deleted: {file_path}")
        create_snapshot(file_path, self.user_email, reason="File deleted")


# ---------------------------
# Monitor Manager
# ---------------------------

class FileMonitor:
    def __init__(self, paths_to_watch: list, user_email: str):
        self.paths_to_watch = paths_to_watch
        self.user_email = user_email
        self.observer = Observer()

    def start(self):
        """Start monitoring files & folders."""
        event_handler = RansomwareHandler(self.user_email)
        for path in self.paths_to_watch:
            if os.path.exists(path):
                self.observer.schedule(event_handler, path, recursive=True)

                # Launch background thread for writer-style monitoring
                thread = threading.Thread(
                    target=snapshot_while_open, args=(path, self.user_email), daemon=True
                )
                thread.start()

        self.observer.start()
        print("[Monitor] File monitoring started.")

    def stop(self):
        """Stop monitoring."""
        self.observer.stop()
        self.observer.join()
        print("[Monitor] File monitoring stopped.")
