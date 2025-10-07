# backend/auth.py
import sqlite3
import hashlib
import os
import secrets
from config.settings import DB_URL


# ---------------------------
# Helper functions
# ---------------------------

def hash_password(password: str, salt: bytes = None) -> (str, str):
    """
    Hash a password with SHA-256 + salt.
    Returns (hashed_password, salt).
    """
    if salt is None:
        salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return pwd_hash.hex(), salt.hex()


def verify_password(stored_hash: str, stored_salt: str, password: str) -> bool:
    """
    Verify entered password matches stored hash.
    """
    pwd_hash, _ = hash_password(password, bytes.fromhex(stored_salt))
    return pwd_hash == stored_hash


# ---------------------------
# User Management
# ---------------------------

def register_user(email: str, password: str) -> bool:
    """
    Register a new user. Returns True if successful, False if email exists.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE email=?", (email,))
    if cursor.fetchone():
        conn.close()
        return False  # user already exists

    hashed_pwd, salt = hash_password(password)
    cursor.execute(
        "INSERT INTO users (email, password, salt) VALUES (?, ?, ?)",
        (email, hashed_pwd, salt),
    )
    conn.commit()
    conn.close()
    return True


def login_user(email: str, password: str) -> bool:
    """
    Authenticate a user. Returns True if valid.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT password, salt FROM users WHERE email=?", (email,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return False

    stored_hash, stored_salt = result
    return verify_password(stored_hash, stored_salt, password)


def generate_session_token() -> str:
    """
    Generate secure session token.
    """
    return secrets.token_hex(32)


def set_session(email: str, token: str) -> None:
    """
    Save session token to database.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET session_token=? WHERE email=?", (token, email))
    conn.commit()
    conn.close()


def clear_session(email: str) -> None:
    """
    Clear user session (logout).
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET session_token=NULL WHERE email=?", (email,))
    conn.commit()
    conn.close()
