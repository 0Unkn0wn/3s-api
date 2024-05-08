from pydantic import BaseModel, HttpUrl

from typing import Sequence, Optional


class SoilDataBase(BaseModel):
    id: int
    name: str
    location: str
    soil_depth: Optional[int] = None
    filetype: str


class SoilDataCreate(SoilDataBase):
    submitter_id: int
    name: str
    location: str
    soil_depth: int
    filetype: str


class UpdateSoilData(SoilDataBase):
    name: Optional[str] = None
    location: Optional[str] = None
    soil_depth: Optional[int] = None
    filetype: Optional[str] = None


class SoilDataSearchResults(SoilDataBase):
    results: Sequence[SoilDataBase]


# Properties shared by models stored in DB
class SoilDataInDBBase(SoilDataBase):
    id: int
    submitter_id: int

    class Config:
        orm_mode = True


# Properties to return to client
class SoilData(SoilDataInDBBase):
    pass


# Properties stored in DB
class SoilDataInDB(SoilDataInDBBase):
    pass
