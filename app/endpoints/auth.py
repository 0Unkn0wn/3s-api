from fastapi import HTTPException, APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, Table, DDL
from sqlalchemy.orm import Session

from app.schemas.user import UserOut, UserAuth, SystemUser, TokenSchema
from starlette import status
from app.security import get_hashed_password, verify_password, create_access_token

from app.db import get_db, metadata, engine
from app.utils import get_current_user
router = APIRouter()


@router.post('/signup', summary="Create new user", response_model=UserOut)
def create_user(data: UserAuth, db: Session = Depends(get_db)):
    table_user = Table('user', metadata, autoload_with=engine, schema='account')
    existing_user_query = select(table_user).where(table_user.c.email == data.email)
    existing_user = db.execute(existing_user_query).fetchone()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Determine privilege based on email domain
    email_domain = data.email.split('@')[1]

    if email_domain == 'student.saxion.nl':
        privilege = "Student/Researcher"
    elif email_domain == 'student.utwente.nl':
        privilege = "Student/Researcher"
    elif email_domain == 'saxion.nl':
        privilege = "Student/Researcher"
    else:
        privilege = "Free"

    # Prepare user data
    user_data = {
        'email': data.email,
        'privilege': privilege,
        'password': get_hashed_password(data.password),
        'first_name': data.first_name,
        'last_name': data.last_name,
        'phone_number': data.phone_number
    }

    # Insert new user into the database
    try:
        db.execute(table_user.insert().values(**user_data))
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inserting data: {e}")

    try:
        # Retrieve the new user to get the user_id
        new_user_query = select(table_user).where(table_user.c.email == data.email)
        new_user = db.execute(new_user_query).fetchone()

        # Create a schema for the new user
        schema_name = f"user_own_data_[{new_user.user_id}]"
        create_schema_ddl = DDL(f"CREATE SCHEMA {schema_name}")
        db.execute(create_schema_ddl)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating user schema: {e}")

    return UserOut(
        user_id=new_user.user_id,
        email=new_user.email,
        privilege=new_user.privilege,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        phone_number=new_user.phone_number
    )


@router.post('/login', summary="Create access and refresh tokens for user", response_model=TokenSchema)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    table = Table('user', metadata, autoload_with=engine, schema='account')
    user_query = select(table).where(table.c.email == form_data.username)
    user = db.execute(user_query).fetchone()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    hashed_pass = user.password
    if not verify_password(form_data.password, hashed_pass):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password"
        )

    access_token = create_access_token(subject=user.email)
    return {
        "access_token": access_token,
    }


@router.get('/me', summary='Get details of currently logged in user', response_model=UserOut)
async def get_me(user: SystemUser = Depends(get_current_user)):
    return user
