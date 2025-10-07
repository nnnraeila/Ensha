# backend/db.py
"""
Rewritten DB layer with Disaster Recovery (DR) structures.

Features added / changed:
- Snapshot table (represents a logical snapshot event / snapshot set)
- SnapshotEntry table (file entries belonging to a snapshot)
- DREvent table (records detected DR events: ransomware, corruption, device crash, failover)
- ReplicationQueue table (tracks blobs that must be replicated to secondary/Ubuntu)
- UnsyncedFile table (files changed locally but not yet uploaded - used for crash recovery)
- Helpers for DR reporting, replication bookkeeping, ransomware marking, integrity checks

Usage:
- Call init_db() at startup to create tables.
- Use get_session() context manager for DB operations.
"""

from typing import Optional, List, Tuple
import contextlib
from datetime import datetime, timedelta
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Text,
    Boolean,
    func,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from config.settings import DB_URL, DB_NAME

# Engine / session setup
_engine_kwargs = {"future": True}
connect_args = {}
if DB_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    _engine = create_engine(DB_URL, connect_args=connect_args, **_engine_kwargs)
else:
    _engine = create_engine(DB_URL, pool_pre_ping=True, **_engine_kwargs)

SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


# --------------------
# Models
# --------------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    telegram_chat_id = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    file_entries = relationship("FileEntry", back_populates="user", cascade="all, delete-orphan")
    otps = relationship("OTP", back_populates="user", cascade="all, delete-orphan")
    logs = relationship("LogEntry", back_populates="user", cascade="all, delete-orphan")
    snapshots = relationship("Snapshot", back_populates="user", cascade="all, delete-orphan")


class FileEntry(Base):
    """
    Individual file/version record. Represents one backed-up file version.
    """
    __tablename__ = "files"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(1024), nullable=False)  # base filename
    version = Column(Integer, nullable=False)
    storage_path = Column(String(2048), nullable=False)
    checksum = Column(String(128), nullable=True)
    deleted = Column(Boolean, default=False, nullable=False)
    suspected_ransomware = Column(Boolean, default=False, nullable=False)
    corrupted = Column(Boolean, default=False, nullable=False)
    backup_time = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="file_entries")

    __table_args__ = (
        UniqueConstraint("user_id", "filename", "version", name="uq_user_filename_version"),
        Index("ix_user_filename", "user_id", "filename"),
    )


class Snapshot(Base):
    """
    Logical snapshot: a point-in-time capture (e.g., folder snapshot or periodic snapshot).
    Snapshots group multiple SnapshotEntry rows.
    """
    __tablename__ = "snapshots"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=True)  # optional friendly name
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    description = Column(Text, nullable=True)
    # relationship
    entries = relationship("SnapshotEntry", back_populates="snapshot", cascade="all, delete-orphan")
    user = relationship("User", back_populates="snapshots")


class SnapshotEntry(Base):
    """
    Links a snapshot to concrete FileEntry versions (so you can restore a snapshot as a set).
    """
    __tablename__ = "snapshot_entries"
    id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, ForeignKey("snapshots.id"), nullable=False, index=True)
    file_entry_id = Column(Integer, ForeignKey("files.id"), nullable=False, index=True)
    snapshot = relationship("Snapshot", back_populates="entries")
    # Not defining backref to FileEntry to keep FileEntry independent


class OTP(Base):
    __tablename__ = "otps"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    code = Column(String(64), nullable=False, index=True)
    expiry = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="otps")


class LogEntry(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(200), nullable=False)
    details = Column(Text, nullable=True)
    log_time = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="logs")


class DREvent(Base):
    """
    Disaster Recovery events: e.g., ransomware_detected, auto_restore_performed, crash_recovery, replication_failover.
    """
    __tablename__ = "drevents"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    event_type = Column(String(100), nullable=False)  # e.g., 'ransomware', 'corruption', 'crash_recovery', 'nas_failover'
    details = Column(Text, nullable=True)
    handled = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReplicationQueue(Base):
    """
    Tracks storage blobs that must be replicated to a secondary store (e.g., Ubuntu VM).
    Contains storage_path and replication status.
    """
    __tablename__ = "replication_queue"
    id = Column(Integer, primary_key=True)
    file_entry_id = Column(Integer, ForeignKey("files.id"), nullable=False, index=True)
    storage_path = Column(String(2048), nullable=False)
    attempted = Column(Integer, default=0, nullable=False)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    replicated = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UnsyncedFile(Base):
    """
    Files that were changed locally but not yet successfully uploaded to primary storage.
    Used to resume uploads after crash.
    """
    __tablename__ = "unsynced_files"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    local_path = Column(String(2048), nullable=False)
    filename = Column(String(1024), nullable=False)
    queued_at = Column(DateTime(timezone=True), server_default=func.now())
    attempts = Column(Integer, default=0, nullable=False)


# --------------------
# DB utilities
# --------------------
def init_db() -> None:
    """
    Create tables. Call this at app startup.
    """
    Base.metadata.create_all(bind=_engine)


@contextlib.contextmanager
def get_session() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# --------------------
# High-level helpers (DR-focused)
# --------------------
def create_user(email: str, password_hash: str, telegram_chat_id: Optional[str] = None) -> User:
    with get_session() as session:
        exists = session.query(User).filter_by(email=email).first()
        if exists:
            raise ValueError("User already exists")
        user = User(email=email, password_hash=password_hash, telegram_chat_id=telegram_chat_id)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def get_user_by_email(email: str) -> Optional[User]:
    with get_session() as session:
        return session.query(User).filter_by(email=email).first()


def get_user(user_id: int) -> Optional[User]:
    with get_session() as session:
        return session.get(User, user_id)


def set_user_telegram_chat_id(user_id: int, chat_id: str) -> bool:
    with get_session() as session:
        u = session.get(User, user_id)
        if not u:
            return False
        u.telegram_chat_id = chat_id
        session.commit()
        return True


def add_log(user_id: Optional[int], action: str, details: Optional[str] = None) -> LogEntry:
    with get_session() as session:
        entry = LogEntry(user_id=user_id, action=action, details=details)
        session.add(entry)
        session.commit()
        session.refresh(entry)
        return entry


# File entry helpers
def add_file_entry(user_id: int, filename: str, version: int, storage_path: str, checksum: Optional[str] = None) -> FileEntry:
    with get_session() as session:
        fe = FileEntry(
            user_id=user_id,
            filename=filename,
            version=version,
            storage_path=storage_path,
            checksum=checksum,
            deleted=False,
            suspected_ransomware=False,
            corrupted=False,
        )
        session.add(fe)
        session.commit()
        session.refresh(fe)
        return fe


def get_file_entries(user_id: int, filename: Optional[str] = None) -> List[FileEntry]:
    with get_session() as session:
        q = session.query(FileEntry).filter_by(user_id=user_id, deleted=False)
        if filename:
            q = q.filter_by(filename=filename)
        return q.order_by(FileEntry.filename, FileEntry.version.desc()).all()


def get_file_entry(user_id: int, filename: str, version: int) -> Optional[FileEntry]:
    with get_session() as session:
        return session.query(FileEntry).filter_by(user_id=user_id, filename=filename, version=version, deleted=False).first()


def get_latest_version(user_id: int, filename: str) -> int:
    with get_session() as session:
        entry = session.query(FileEntry).filter_by(user_id=user_id, filename=filename, deleted=False).order_by(FileEntry.version.desc()).first()
        return entry.version if entry else 0


def mark_file_corrupted(file_entry_id: int) -> bool:
    with get_session() as session:
        fe = session.get(FileEntry, file_entry_id)
        if not fe:
            return False
        fe.corrupted = True
        session.commit()
        return True


def mark_file_suspected_ransom(file_entry_id: int) -> bool:
    with get_session() as session:
        fe = session.get(FileEntry, file_entry_id)
        if not fe:
            return False
        fe.suspected_ransomware = True
        session.commit()
        return True


def delete_file_entry(entry_id: int) -> bool:
    with get_session() as session:
        fe = session.get(FileEntry, entry_id)
        if not fe:
            return False
        fe.deleted = True
        session.commit()
        return True


def prune_old_versions(user_id: int, filename: str, keep: int = 3) -> List[Tuple[int, str]]:
    with get_session() as session:
        entries = session.query(FileEntry).filter_by(user_id=user_id, filename=filename, deleted=False).order_by(FileEntry.version.desc()).all()
        if len(entries) <= keep:
            return []
        to_remove = entries[keep:]
        removed = []
        for e in to_remove:
            removed.append((e.id, e.storage_path))
            session.delete(e)
        session.commit()
        return removed


# Snapshot helpers
def create_snapshot(user_id: int, name: Optional[str] = None, description: Optional[str] = None) -> Snapshot:
    with get_session() as session:
        s = Snapshot(user_id=user_id, name=name, description=description)
        session.add(s)
        session.commit()
        session.refresh(s)
        return s


def add_snapshot_entry(snapshot_id: int, file_entry_id: int) -> SnapshotEntry:
    with get_session() as session:
        se = SnapshotEntry(snapshot_id=snapshot_id, file_entry_id=file_entry_id)
        session.add(se)
        session.commit()
        session.refresh(se)
        return se


def get_snapshots(user_id: int, limit: int = 50) -> List[Snapshot]:
    with get_session() as session:
        return session.query(Snapshot).filter_by(user_id=user_id).order_by(Snapshot.created_at.desc()).limit(limit).all()


def get_snapshot_entries(snapshot_id: int) -> List[SnapshotEntry]:
    with get_session() as session:
        return session.query(SnapshotEntry).filter_by(snapshot_id=snapshot_id).all()


# Unsynced file helpers (for crash recovery)
def add_unsynced_file(user_id: int, local_path: str, filename: str) -> UnsyncedFile:
    with get_session() as session:
        u = UnsyncedFile(user_id=user_id, local_path=local_path, filename=filename)
        session.add(u)
        session.commit()
        session.refresh(u)
        return u


def pop_unsynced_files(limit: int = 100) -> List[UnsyncedFile]:
    """
    Retrieve unsynced files for processing (uploads) and remove them from queue.
    Caller should attempt upload and re-create entry on failure if needed.
    """
    with get_session() as session:
        rows = session.query(UnsyncedFile).order_by(UnsyncedFile.queued_at.asc()).limit(limit).all()
        results = []
        for r in rows:
            results.append(r)
            session.delete(r)
        session.commit()
        return results


# Replication queue helpers
def enqueue_replication(file_entry_id: int, storage_path: str) -> ReplicationQueue:
    with get_session() as session:
        rq = ReplicationQueue(file_entry_id=file_entry_id, storage_path=storage_path)
        session.add(rq)
        session.commit()
        session.refresh(rq)
        return rq


def pop_replication_candidates(limit: int = 50) -> List[ReplicationQueue]:
    with get_session() as session:
        rows = session.query(ReplicationQueue).filter_by(replicated=False).order_by(ReplicationQueue.created_at.asc()).limit(limit).all()
        return rows


def mark_replicated(replication_id: int) -> bool:
    with get_session() as session:
        r = session.get(ReplicationQueue, replication_id)
        if not r:
            return False
        r.replicated = True
        r.last_attempt_at = datetime.utcnow()
        session.commit()
        return True


def record_replication_attempt(replication_id: int) -> None:
    with get_session() as session:
        r = session.get(ReplicationQueue, replication_id)
        if not r:
            return
        r.attempted += 1
        r.last_attempt_at = datetime.utcnow()
        session.commit()


# DR Event helpers
def record_dr_event(user_id: Optional[int], event_type: str, details: Optional[str] = None) -> DREvent:
    with get_session() as session:
        e = DREvent(user_id=user_id, event_type=event_type, details=details, handled=False)
        session.add(e)
        session.commit()
        session.refresh(e)
        return e


def mark_dr_event_handled(event_id: int) -> bool:
    with get_session() as session:
        e = session.get(DREvent, event_id)
        if not e:
            return False
        e.handled = True
        session.commit()
        return True


# OTP helpers (used by otp.py)
def create_otp_record(user_id: int, code: str, expiry: datetime) -> OTP:
    with get_session() as session:
        otp = OTP(user_id=user_id, code=code, expiry=expiry, used=False)
        session.add(otp)
        session.commit()
        session.refresh(otp)
        return otp


def get_valid_otp(user_id: int, code: str) -> Optional[OTP]:
    with get_session() as session:
        now = datetime.utcnow()
        otp = session.query(OTP).filter_by(user_id=user_id, code=code, used=False).first()
        if not otp:
            return None
        if otp.expiry < now:
            return None
        return otp


def mark_otp_used(otp_id: int) -> bool:
    with get_session() as session:
        otp = session.get(OTP, otp_id)
        if not otp:
            return False
        otp.used = True
        session.commit()
        return True


# Reporting helpers (DR report)
def generate_dr_summary(user_id: Optional[int] = None) -> dict:
    """
    Return a summary dictionary for DR reporting. Useful to show in audit page or export as report.
    """
    with get_session() as session:
        res = {}
        # recent backups count (last 24 hours)
        since = datetime.utcnow() - timedelta(days=1)
        q = session.query(FileEntry)
        if user_id:
            q = q.filter_by(user_id=user_id)
        recent_count = q.filter(FileEntry.backup_time >= since).count()
        res["backups_last_24h"] = recent_count

        # total snapshots
        q2 = session.query(Snapshot)
        if user_id:
            q2 = q2.filter_by(user_id=user_id)
        res["snapshots_total"] = q2.count()

        # DR events last 24h
        q3 = session.query(DREvent)
        if user_id:
            q3 = q3.filter_by(user_id=user_id)
        res["drevents_last_24h"] = q3.filter(DREvent.created_at >= since).count()

        # unsynced files
        q4 = session.query(UnsyncedFile)
        if user_id:
            q4 = q4.filter_by(user_id=user_id)
        res["unsynced_files"] = q4.count()

        # replication pending
        q5 = session.query(ReplicationQueue).filter_by(replicated=False)
        if user_id:
            # join FileEntry to filter by user
            q5 = q5.join(FileEntry, ReplicationQueue.file_entry_id == FileEntry.id).filter(FileEntry.user_id == user_id)
        res["replication_pending"] = q5.count()

        return res


def get_recent_dr_events(user_id: Optional[int] = None, limit: int = 100) -> List[DREvent]:
    with get_session() as session:
        q = session.query(DREvent)
        if user_id:
            q = q.filter_by(user_id=user_id)
        return q.order_by(DREvent.created_at.desc()).limit(limit).all()


# Misc helpers
def get_logs(user_id: Optional[int] = None, limit: int = 500) -> List[LogEntry]:
    with get_session() as session:
        q = session.query(LogEntry)
        if user_id:
            q = q.filter_by(user_id=user_id)
        return q.order_by(LogEntry.log_time.desc()).limit(limit).all()
