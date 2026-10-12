import hashlib
import secrets


def hash_password(password: str) -> str:
    """Băm mật khẩu bằng thuật toán chuẩn PBKDF2-HMAC-SHA256 với salt ngẫu nhiên."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100_000,
    )
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiểm tra mật khẩu khớp với giá trị băm lưu trong cơ sở dữ liệu."""
    try:
        salt, key_hex = hashed_password.split("$", 1)
        expected_key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=100_000,
        )
        return secrets.compare_digest(expected_key.hex(), key_hex)
    except (ValueError, AttributeError):
        return False
