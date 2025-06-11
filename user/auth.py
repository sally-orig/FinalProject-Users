from datetime import datetime, timedelta, UTC
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import HTTPException, status, APIRouter, Depends, Header, Body
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .models import Credential
from .schemas import UserOut, ActionLogEnum, ActionLogActionsEnum
from .db import get_db
from .logger import logger, log_action

token_router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ACCESS_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(plain_password):
    return pwd_context.hash(plain_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "token_type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "token_type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def generate_401_exception(detail: str):
    """Generate a 401 HTTPException with the given detail."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"}
    )
    
def authenticate_user(db: Session, username: str, plain_password: str) -> UserOut | None:
    """Authenticate a user by username and password.
    Args:  
        db (Session): The database session.
        username (str): The username of the user.
        plain_password (str): The plain text password to verify.
    Returns:
        UserOut | None: A UserOut schema representing the user if authentication is successful, or None if not.
    """
    credentials = db.query(Credential).filter(Credential.username == username).first()
    if not credentials or not verify_password(plain_password, credentials.hashed_password):
        return None
    return UserOut.model_validate(credentials.user).model_dump()
    
@token_router.post("/token", status_code=status.HTTP_200_OK, summary="Generate access token", description="Generate an access token for the user.")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login: username={form_data.username}")
        log_action(db, username=form_data.username, action=ActionLogEnum.login, status=ActionLogActionsEnum.failed)
        raise generate_401_exception(detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": str(user["id"])})
    refresh_token = create_refresh_token(data={"sub": str(user["id"])})
    logger.info(f"Token issued: user_id={str(user['id'])}")
    log_action(db, user_id=user["id"], action=ActionLogEnum.login, status=ActionLogActionsEnum.success)
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}

def verify_access_token(token: str):
    logger.info(f"Access token verification attempt")
    if not token or token.lower() == "undefined":
        logger.warning(f"Access token verification failed: Invalid or missing token")
        raise generate_401_exception(detail="Invalid or missing access token")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        token_type: str = payload.get("token_type")
        if user_id is None:
            logger.warning(f"Access token verification failed: User ID not found in token")
            raise generate_401_exception(detail="User ID not found in token")
        elif token_type != "access":
            logger.warning(f"Access token verification failed: Invalid token type {token_type}")
            raise generate_401_exception(detail="Invalid token type")
        return int(user_id)
    except ExpiredSignatureError:
        logger.warning(f"Access token verification failed: token has expired")
        raise generate_401_exception(detail="Token has expired")
    except JWTError as e:
        logger.warning(f"Token verification failed: {str(e)}")
        raise generate_401_exception(detail=str(e))
    
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserOut | None:
    user_id = verify_access_token(token)
    user = db.query(Credential).filter(Credential.user_id == user_id).first()
    if not user:
        logger.warning(f"Token verification failed: User not found for user_id={user_id}")
        log_action(db, user_id=user["id"], action=ActionLogEnum.verify_token, status=ActionLogActionsEnum.failed)
        raise generate_401_exception(detail="User not found")
    logger.warning(f"Token verification success for user_id={user_id}")
    log_action(db, user_id=user.id, action=ActionLogEnum.verify_token, status=ActionLogActionsEnum.success)
    return user

@token_router.post("/token/refresh", status_code=status.HTTP_200_OK, summary="Refresh access token", description="Refresh the provided access token and return a new one.")
async def refresh_access_token(refresh_token: str = Body(embed=True)):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("token_type") != "refresh":
            logger.warning(f"Refresh token verification failed: Invalid token type")
            raise generate_401_exception(detail="Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            logger.warning(f"Refresh token verification failed: User not found for user_id={user_id}")
            raise generate_401_exception(detail="User not found in refresh token")
        
        new_access_token = create_access_token({"sub": user_id})
        new_refresh_token = create_refresh_token({"sub": user_id})

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except ExpiredSignatureError:
        logger.warning(f"Refresh token verification failed: Refresh token has expired")
        raise generate_401_exception(detail="Refresh token has expired")
    except JWTError:
        logger.warning(f"Refresh token verification failed: Invalid refresh token")
        raise generate_401_exception(detail="Invalid refresh token")
