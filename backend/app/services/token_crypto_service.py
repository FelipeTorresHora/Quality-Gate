from cryptography.fernet import Fernet

from app.core.config import get_settings
from app.core.errors import AppError


def generate_key() -> str:
    return Fernet.generate_key().decode("ascii")


def _fernet() -> Fernet:
    key = get_settings().token_encryption_key
    if not key:
        raise AppError(
            503,
            "token_encryption_key_missing",
            "TOKEN_ENCRYPTION_KEY is required.",
        )
    return Fernet(key.encode("ascii"))


def encrypt_token(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("ascii")


def decrypt_token(value: str) -> str:
    return _fernet().decrypt(value.encode("ascii")).decode("utf-8")
