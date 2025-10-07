# backend/encryption.py
import os
from cryptography.fernet import Fernet

# ---------------------------
# Key Management
# ---------------------------

KEY_FILE = "config/encryption.key"


def generate_key() -> bytes:
    """
    Generate a new AES key and save it to KEY_FILE if not exists.
    """
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    else:
        with open(KEY_FILE, "rb") as f:
            key = f.read()
    return key


def load_key() -> bytes:
    """
    Load AES encryption key.
    """
    if not os.path.exists(KEY_FILE):
        return generate_key()
    with open(KEY_FILE, "rb") as f:
        return f.read()


# ---------------------------
# File Encryption / Decryption
# ---------------------------

def encrypt_file(input_path: str, output_path: str) -> None:
    """
    Encrypt a file using AES and save encrypted version.
    """
    key = load_key()
    fernet = Fernet(key)

    with open(input_path, "rb") as f:
        data = f.read()

    encrypted = fernet.encrypt(data)

    with open(output_path, "wb") as f:
        f.write(encrypted)


def decrypt_file(input_path: str, output_path: str) -> None:
    """
    Decrypt a file using AES and restore original.
    """
    key = load_key()
    fernet = Fernet(key)

    with open(input_path, "rb") as f:
        data = f.read()

    decrypted = fernet.decrypt(data)

    with open(output_path, "wb") as f:
        f.write(decrypted)
