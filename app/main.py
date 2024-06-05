from fastapi import FastAPI, APIRouter, Depends
from app.endpoints import ground_data, auth
from app.utils import get_current_user

description = """
3S API for our service
"""

app = FastAPI(
    title="GRND133",
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
    },
)

root_router = APIRouter()


@root_router.get("/")
async def root():
    return {"status": "OK"}


app.include_router(ground_data.router, prefix="/api/v1", tags=["ground_data"], dependencies=[Depends(get_current_user)])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(root_router, tags=["root"])
