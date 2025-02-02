from datetime import datetime
import time
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.config import settings
security = HTTPBearer()

def decode_access_token(
    token: str,
    algorithm: str = settings.auth_jwt.algorithm,
    secret: str = settings.auth_jwt.secret_key,
) -> str:
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        user_id: str = payload.get("sub")
        exp = payload.get("exp")
        if exp < time.mktime(datetime.now().timetuple()):
            raise ValueError("Token has expired")
        if user_id is None:
            raise ValueError("User ID not found in token")
        return user_id
    except jwt.PyJWTError:
        raise ValueError("Token is invalid or has expired")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    try:
        # Извлекаем токен из заголовка "Bearer"
        token = credentials.credentials
        user_id = decode_access_token(token)
        return user_id
    except ValueError as e:
        # Обрабатываем различные ошибки декодирования
        error_message = str(e)
        if "expired" in error_message:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
