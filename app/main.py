from fastapi import FastAPI, APIRouter, Depends
from app.endpoints import ground_data, auth, user_data
from app.utils import get_current_user

description = """
This FastAPI application offers a structured approach to handle public and private data schemas stored in a PostgreSQL database. 
Key functionalities include data retrieval, insertion, and schema management. 
The API ensures secure access with JWT-based authentication, and leverages Azure services for deployment, including automated CI/CD with GitHub Actions for consistent updates and reliability.
"""

app = FastAPI(
    title="GRND133",
    description=description,
    version="1.0",
    contact={
        "name": "3S Grounded 133",
        "url": "https://kind-glacier-0aee57503.5.azurestaticapps.net/",
        "email": "514541@student.saxion.nl",
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


app.include_router(ground_data.router, prefix="/api/v1", tags=["ground_data"])
app.include_router(user_data.router, prefix="/api/v1/user-data", tags=["user-data"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(root_router, tags=["root"])
