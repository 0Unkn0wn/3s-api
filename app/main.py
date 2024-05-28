from fastapi import FastAPI, APIRouter
from app.endpoints import ground_data, auth

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
    }, )

api_router = APIRouter()


@api_router.get("/")
async def root():
    return {"status": "OK"}


app.include_router(api_router)
api_router.include_router(ground_data.router, prefix="/ground_data", tags=["ground_data"])
