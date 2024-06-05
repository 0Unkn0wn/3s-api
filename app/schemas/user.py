from typing import Optional

from pydantic import BaseModel, Field

class TokenSchema(BaseModel):
    access_token: str

class TokenPayload(BaseModel):
    sub: str = None
    exp: int = None

class UserAuth(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=5, max_length=24, description="User password")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    phone_number: Optional[str] = Field(None, description="Phone number")
class UserOut(BaseModel):
    user_id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    privilege: str = Field(..., description="User privilege")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    phone_number: Optional[str] = Field(None, description="Phone number")

    class Config:
        orm_mode = True


class SystemUser(UserOut):
    password: str