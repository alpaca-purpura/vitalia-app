"""Password hashing, encryption, and key derivation utilities."""

import base64
import hashlib

from cryptography.fernet import Fernet
from passlib.context import CryptContext

from luana_core_platform.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def generate_key() -> bytes:
    """Generate a random key for encryption."""
    return Fernet.generate_key()


def encrypt_string(text: str, key: str) -> str:
    """Encrypt a string using Fernet (symmetric encryption)."""
    f = Fernet(key.encode())
    return f.encrypt(text.encode()).decode()


def decrypt_string(token: str, key: str) -> str:
    """Decrypt a string using Fernet."""
    f = Fernet(key.encode())
    return f.decrypt(token.encode()).decode()


def get_encryption_key() -> str:
    """Derive a URL-safe base64 32-byte key from ``API_SECRET_KEY``.

    Fail-loud if unset: under the multibrand contract ``API_SECRET_KEY``
    defaults to empty, so a brand that actually uses engine encryption
    (Telegram link tokens, credential storage) MUST configure it — a silent
    empty-string key would be a deterministic, known weak key.
    """
    secret = get_settings().API_SECRET_KEY
    if not secret:
        msg = (
            "API_SECRET_KEY is not configured — required for encryption/key "
            "derivation. Set it in the environment of any deployment that uses "
            "engine encryption (Telegram link tokens, credential storage)."
        )
        raise RuntimeError(msg)
    digest = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode()
