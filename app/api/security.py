import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from dotenv import load_dotenv

# .env ফাইল লোড করা
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt directly, safely handling length limits."""
    if isinstance(password, str):
        password_bytes = password.encode('utf-8')
    else:
        password_bytes = password

    # Bcrypt 72-byte truncation safety check
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    # Generate salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against the hashed version."""
    if isinstance(plain_password, str):
        password_bytes = plain_password.encode('utf-8')
    else:
        password_bytes = plain_password

    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generate a JWT access token for authenticated users."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
