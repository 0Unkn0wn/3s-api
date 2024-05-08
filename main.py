from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import FastAPI, Query, HTTPException, status, Depends, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated, Optional
from schemas import Token, TokenData, User, UserInDB, SoilData, UpdateSoilData, SoilDataSearchResults, SoilDataCreate

SECRET_KEY = "aa080c24c3ce107d80742324ef2720363585c7d0ff72b433b686db50d7ee7d24"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

fake_users_db = {
    "johndoe": {
        "username": "3s",
        "full_name": "John Doe",
        "email": "3s@gmail.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

description = """
3S API for our service
"""

app = FastAPI(
    title="GroundedAPP",
    description=description,
    summary="empty",
    version="0.0.1",
    terms_of_service="http://empty.com",
    contact={
        "name": "3S",
        "url": "http://empty.com",
        "email": "empty@gmail.com",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    }, )

api_router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
        current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@api_router.post("/token")
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@api_router.get("/users/me/", response_model=User)
async def read_users_me(
        current_user: Annotated[User, Depends(get_current_active_user)],
):
    return current_user


@api_router.get("/")
async def root():
    return {"Place": "Root"}


@api_router.get("/about")
async def info():
    return {"Place": "About Page"}


SOIL_DATABASE = [
    {
        "id": 1,
        "name": "testing",
        "location": "Deventer",
        "soil_depth": "5",
        "filetype": "pdf"
    }
]


@api_router.get("/get-data/{item_id}", status_code=200, response_model=SoilData)
def get_data(
        item_id: int,
) -> dict:
    result = [data for data in SOIL_DATABASE if data["id"] == item_id]
    if not result:
        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
    return result[0]


@api_router.get("/search/", status_code=200, response_model=SoilDataSearchResults)
def search_recipes(
    *,
    keyword: Optional[str] = Query(None, min_length=3),
    max_results: Optional[int] = 10
) -> dict:

    if not keyword:
        return {"results": SoilData[:max_results]}

    results = filter(lambda data: keyword.lower() in data["name"].lower(), SOIL_DATABASE)
    return {"results": list(results)[:max_results]}


@api_router.post("/create-data/", status_code=201, response_model=SoilData)
def upload_data(
    *,
    input_data: SoilDataCreate,
) -> dict:
    new_entry_id = len(SOIL_DATABASE) + 1
    soil_entry = SoilData(
        id=new_entry_id,
        name=input_data.name,
        location=input_data.location,
        soil_depth=input_data.soil_depth,
        filetype=input_data.filetype,
    )
    SOIL_DATABASE.append(soil_entry.dict())

    return soil_entry


@api_router.put("/update-data/{item_id}")
async def upload_data(item_id: int, item: UpdateSoilData, current_user: Annotated[User, Depends(get_current_active_user)]):
    if item_id not in SOIL_DATABASE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if item.name is not None:
        SOIL_DATABASE[item_id].name = item.name

    if item.location is not None:
        SOIL_DATABASE[item_id].location = item.location

    if item.soil_depth is not None:
        SOIL_DATABASE[item_id].soil_depth = item.soil_depth

    if item.filetype is not None:
        SOIL_DATABASE[item_id].filetype = item.filetype
    return [{"data": SOIL_DATABASE[item_id], "owner": current_user.username}]


@api_router.delete("/delete-item")
async def delete_item(current_user: Annotated[User, Depends(get_current_active_user)], item_id: int = Query(..., discription="field is required")):
    if item_id not in SOIL_DATABASE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    del SOIL_DATABASE[item_id]
    return [{"deleted data": SOIL_DATABASE[item_id], "owner": current_user.username}]

app.include_router(api_router)
