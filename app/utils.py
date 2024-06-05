from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import Table, select
from sqlalchemy.orm import Session

from db import get_db, metadata, engine
from security import ALGORITHM, JWT_SECRET_KEY

from jose import jwt
from pydantic import ValidationError
from schemas.user import TokenPayload, SystemUser

reuseable_oauth = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(reuseable_oauth), db: Session = Depends(get_db)) -> SystemUser:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)

        if datetime.fromtimestamp(token_data.exp) < datetime.now():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    table = Table('user', metadata, autoload_with=engine, schema='account')
    user_query = select(table).where(table.c.email == token_data.sub)
    user = db.execute(user_query).fetchone()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find user",
        )

    return SystemUser(
        user_id=user.user_id,
        email=user.email,
        privilege=user.privilege,
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=user.phone_number,
        password=user.password
    )
