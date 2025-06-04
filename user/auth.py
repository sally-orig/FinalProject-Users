from datetime import datetime, timedelta, UTC
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import HTTPException, status, APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .models import Credential
from .schemas import UserOut
from .db import get_db

token_router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(plain_password):
    return pwd_context.hash(plain_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

credentials_exception = {
    "status_code": status.HTTP_401_UNAUTHORIZED,
    "detail": "Could not validate credentials",
    "headers": {"WWW-Authenticate": "Bearer"},
}

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(**credentials_exception)
        return user_id
    except JWTError:
        return HTTPException(**credentials_exception)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    access_token = create_access_token(data={"sub": user["id"]})
    return access_token