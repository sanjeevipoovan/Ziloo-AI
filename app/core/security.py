"""
Security primitives: password hashing, JWT issuance/verification, and API
key generation/hashing.

Passwords use Argon2id (via argon2-cffi) because they are low-entropy,
human-chosen secrets that need a slow, memory-hard hash.

API keys are the opposite: high-entropy, machine-generated random tokens.
Hashing them with Argon2 would be pure overhead (and would make every
request artificially slow), so they're hashed with SHA-256 instead - fast,
deterministic, and more than sufficient given the key's own entropy comes
from `secrets.token_urlsafe`, not from the hash.
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import get_settings

settings = get_settings()
_password_hasher = PasswordHasher()

API_KEY_PREFIX_LENGTH = 8
API_KEY_DISPLAY_PREFIX = "myai_"


# --------------------------------------------------------------------------
# Passwords
# --------------------------------------------------------------------------
def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _password_hasher.verify(hashed, password)
    except VerifyMismatchError:
        return False
    except Exception:
        # Malformed/legacy hash, corrupted value, etc. - never raise out of
        # an auth check, just treat it as a failed verification.
        return False


# --------------------------------------------------------------------------
# JWTs (human users)
# --------------------------------------------------------------------------
def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_minutes or settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": subject, "iat": now, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    # Raises jwt.PyJWTError (expired, bad signature, malformed, ...) - callers
    # are expected to translate that into an AuthenticationError.
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


# --------------------------------------------------------------------------
# API keys (external applications)
# --------------------------------------------------------------------------
def generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key.

    Returns (full_key, prefix, key_hash). `full_key` is shown to the caller
    exactly once, at creation time, and is never stored or logged. Only
    `prefix` (for display, e.g. "myai_ab12cd34...") and `key_hash` are
    persisted.
    """
    raw = secrets.token_urlsafe(32)
    prefix = raw[:API_KEY_PREFIX_LENGTH]
    full_key = f"{API_KEY_DISPLAY_PREFIX}{raw}"
    return full_key, prefix, hash_api_key(full_key)


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def verify_api_key(api_key: str, key_hash: str) -> bool:
    return hmac.compare_digest(hash_api_key(api_key), key_hash)
