# This file handles all the security logic:
# 1. Hashing passwords before saving to DB
# 2. Verifying passwords on login
# 3. Creating JWT tokens after successful login
# 4. Decoding JWT tokens to identify who is making a request

from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")                          # Used to sign tokens 
ALGORITHM = os.getenv("ALGORITHM")                            # HS256 = HMAC with SHA-256
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))  # Token lifetime

# CryptContext handles bcrypt hashing — bcrypt is slow by design, making brute force hard
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Takes a plain password, returns a bcrypt hash to store in DB
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Compares plain password to stored hash — returns True if they match
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Creates a JWT token with user email + expiry time embedded inside
# The frontend sends this token with every request to prove who they are
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Decodes a JWT token and extracts the email
# Returns None if the token is invalid or expired
def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return email
    except JWTError:
        return None
    
    