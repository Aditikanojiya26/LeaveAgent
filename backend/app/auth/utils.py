from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
import os
import hashlib

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def normalize_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def hash_password(password: str) -> str:
    return pwd_context.hash(normalize_password(password))


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(normalize_password(password), hashed)


def create_token(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=60)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)