from typing import List, Dict, Any
from pydantic import BaseModel


class SchemaResponse(BaseModel):
    schemas: List[str]


class TablesResponse(BaseModel):
    schema_name: str
    tables: List[str]


class TableDataResponse(BaseModel):
    table_name: str
    data: List[Dict[str, Any]]


class AddDataResponse(BaseModel):
    message: str


class UpdateDataResponse(BaseModel):
    message: str


class RemoveDataResponse(BaseModel):
    message: str


class TableStructureResponse(BaseModel):
    table_name: str
    columns: Dict[str, str]
    primary_key: str = None
