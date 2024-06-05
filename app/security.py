from passlib.context import CryptContext
import os
from datetime import datetime, timedelta
from typing import Union, Any
from jose import jwt
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day
ALGORITHM = "HS256"
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')  # should be kept secret
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_hashed_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password, hashed_pass)


def create_access_token(subject: Union[str, Any], lifetime: int = None) -> str:
    if lifetime is not None:
        lifetime = datetime.utcnow() + lifetime
    else:
        lifetime = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {}
    payload["exp"] = lifetime
    payload["iat"] = datetime.utcnow()
    payload["sub"] = str(subject)
    encoded_jwt = jwt.encode(payload, JWT_SECRET_KEY, ALGORITHM)
    return encoded_jwt
