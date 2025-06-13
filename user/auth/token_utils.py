from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, status
import logging
from typing import Literal
import uuid

logger = logging.getLogger(__name__)

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ACCESS_TOKEN_EXPIRE_DAYS = 7

def generate_401_exception(detail: str):
    """Generate a 401 HTTPException with the given detail."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"}
    )

def create_token(data: dict, expires_delta: timedelta, token_type: Literal["access", "refresh"]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({
        "exp": expire,
        "token_type": token_type,
        "jti": str(uuid.uuid4())
    })
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_access_token(data: dict) -> str:
    return create_token(data, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), "access")

def create_refresh_token(data: dict) -> str:
    return create_token(data, timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS), "refresh")

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        logger.warning("Token expired")
        raise generate_401_exception(detail="Token has expired")
    except JWTError as e:
        logger.warning(f"Token invalid: {str(e)}")
        raise generate_401_exception(detail="Invalid token")
    
def verify_access_token(token: str):
    logger.info(f"Access token verification attempt")
    if not token or token.lower() == "undefined":
        logger.warning("Access token verification failed: Invalid or missing token")
        raise generate_401_exception("Invalid or missing access token")

    payload = decode_token(token)
    user_id: int = payload.get("sub")
    token_type: str = payload.get("token_type")

    if user_id is None:
        logger.warning("Access token verification failed: User ID not found in token")
        raise generate_401_exception("User ID not found in token")
    elif token_type != "access":
        logger.warning("Access token verification failed: Invalid token type")
        raise generate_401_exception("Invalid token type")

    return int(user_id)
