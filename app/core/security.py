"""Хеширование паролей (Argon2) и выпуск/проверка JWT-токенов."""

from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import config

_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return _password_hash.verify(password, hashed)


def create_access_token(user_id: int, role: str) -> str:
    """JWT с id пользователя (sub), ролью и временем жизни (exp)."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=config["jwt_expire_minutes"]),
    }
    return jwt.encode(payload, config["jwt_secret"], algorithm=config["jwt_algorithm"])


def decode_access_token(token: str) -> dict:
    """Проверяет подпись и срок действия. При ошибке бросает jwt.InvalidTokenError."""
    return jwt.decode(token, config["jwt_secret"], algorithms=[config["jwt_algorithm"]])
