from passlib.context import CryptContext
from fastapi import status, APIRouter, Depends, Body, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from ..models import Credential, RefreshToken
from ..schemas import UserOut, ActionLogEnum, ActionLogActionsEnum
from ..db import get_db
from ..logger import logger, log_action
from .token_utils import create_access_token, create_refresh_token, decode_token, generate_401_exception, generate_400_exception, verify_access_token

token_router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
ACCESS_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(plain_password):
    """Hash a plain password using bcrypt."""
    return pwd_context.hash(plain_password)
    
def authenticate_user(db: Session, username: str, plain_password: str) -> UserOut | None:
    """Authenticate a user by username and password."""
    credentials = db.query(Credential).filter(Credential.username == username).first()
    if not credentials or not verify_password(plain_password, credentials.hashed_password):
        return None
    return UserOut.model_validate(credentials.user).model_dump()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> UserOut | None:
    """Get the current user based on the provided access token."""
    user_id = verify_access_token(token)
    user = db.query(Credential).filter(Credential.user_id == user_id).first()
    if not user:
        logger.warning(f"Token verification failed: User not found for user_id={user_id}")
        log_action(db, user_id=user_id, action=ActionLogEnum.verify_token, status=ActionLogActionsEnum.failed)
        raise generate_401_exception(detail="User not found")
    logger.warning(f"Token verification success for user_id={user_id}")
    log_action(db, user_id=user.id, action=ActionLogEnum.verify_token, status=ActionLogActionsEnum.success)
    return user

def save_refresh_token(db: Session, refresh_token: str):
    """Save the refresh token to the database."""
    payload = decode_token(refresh_token)
    expiry = datetime.fromtimestamp(payload.get("exp"), timezone.utc) if payload.get("exp") else None
    if not expiry or not payload.get("sub") or not payload.get("jti"):
        logger.error("Invalid refresh token payload")
        raise generate_401_exception(detail="Invalid refresh token payload")
    
    db_token = RefreshToken(
        jti=payload.get("jti"),
        user_id=payload.get("sub"),
        expires_at=expiry
    )
    try:
        db.add(db_token)
        db.commit()
    except Exception:
        db.rollback()
        raise

def revoke_refresh_token(jti: str, db: Session) -> None:
    """Revoke a refresh token."""
    if not jti:
        logger.warning(f"Refresh token verification failed: JTI not found in token")
        raise generate_400_exception("JTI not found in token")
    db_token = db.query(RefreshToken).filter(RefreshToken.jti == jti).first()
    if not db_token or db_token.revoked or db_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        logger.warning(f"Refresh token verification failed: Token invalid/expired")
        raise generate_400_exception("Refresh token is invalid or expired")
    
    db_token.revoked = True
    db_token.revoked_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to revoke refresh token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke refresh token"
        )

    db.refresh(db_token)

def verify_refresh_token(refresh_token: str, db: Session) -> str:
    """Verify the provided refresh token and return the associated user."""
    if not refresh_token or refresh_token.lower() == "undefined":
        logger.warning("Refresh token verification failed: Invalid or missing token")
        raise generate_400_exception("Invalid or missing refresh token")

    payload = decode_token(refresh_token)
    user_id = payload.get("sub")
    if payload.get("token_type") != "refresh":
        logger.warning(f"Refresh token verification failed: Invalid token type")
        raise generate_400_exception(detail="Invalid token type")
    if not user_id:
        logger.warning(f"Refresh token verification failed: User not found for user_id={user_id}")
        raise generate_400_exception(detail="User not found in refresh token")

    revoke_refresh_token(payload.get("jti"), db)

    return user_id
    
@token_router.post("/token", status_code=status.HTTP_200_OK, summary="Generate access token", description="Generate an access token for the user.")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login: username={form_data.username}")
        log_action(db, username=form_data.username, action=ActionLogEnum.login, status=ActionLogActionsEnum.failed)
        raise generate_401_exception(detail="Incorrect username or password")
    user_id = user.id if isinstance(user, UserOut) else user["id"]
    access_token = create_access_token(data={"sub": str(user_id)})
    refresh_token = create_refresh_token(data={"sub": str(user_id)})
    save_refresh_token(db, refresh_token)

    logger.info(f"Token issued: user_id={str(user['id'])}")
    log_action(db, user_id=user["id"], action=ActionLogEnum.login, status=ActionLogActionsEnum.success)
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "refresh_token": refresh_token
    }

@token_router.post("/token/refresh", status_code=status.HTTP_200_OK, summary="Refresh access token", description="Refresh the provided access token and return a new one.")
async def refresh_access_token(refresh_token: str = Body(embed=True), db: Session = Depends(get_db), current_user: UserOut = Depends(get_current_user)):
    logger.info(f"Refresh token verification attempt")
    user_id = verify_refresh_token(refresh_token, db)
    
    new_access_token = create_access_token({"sub": user_id})
    new_refresh_token = create_refresh_token({"sub": user_id})

    save_refresh_token(db, new_refresh_token)

    logger.info(f"Token issued: user_id={user_id}")
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

