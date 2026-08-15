from app.core.security import (
    create_access_token, decode_access_token, generate_api_key,
    hash_password, verify_api_key, verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("wrong password", hashed)


def test_password_hash_is_not_plaintext():
    hashed = hash_password("secret123")
    assert hashed != "secret123"


def test_jwt_roundtrip():
    token = create_access_token(subject="user-123")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


def test_api_key_generation_and_verification():
    full_key, prefix, key_hash = generate_api_key()
    assert full_key.startswith(f"myai_{prefix}")
    assert verify_api_key(full_key, key_hash)
    assert not verify_api_key("myai_wrongkeyvalue", key_hash)


def test_api_key_hash_never_reveals_plaintext():
    full_key, _prefix, key_hash = generate_api_key()
    assert key_hash != full_key
    assert len(key_hash) == 64  # sha256 hex digest
