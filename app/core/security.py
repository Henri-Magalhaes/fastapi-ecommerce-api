import jwt

from fastapi.security import OAuth2PasswordBearer

from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher

from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

ph = PasswordHasher()

def hash_password(senha: str) -> str:
    return ph.hash(senha)

def verify_hash_password(senha: str, hash_senha: str) -> bool:
    try:
        return ph.verify(hash_senha, senha)
    except Exception:
        return False

def create_token(user_id: int, type: str, role: str, time: timedelta) -> str:
    payload = {
        "sub": str(user_id),
        "type": type,
        "role": role,
        "exp": datetime.now(timezone.utc) + time
    }

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

def create_access_token(user_id: int, user_role: str) -> str:
    return create_token(user_id, "access", user_role, timedelta(minutes=settings.access_token_time))
