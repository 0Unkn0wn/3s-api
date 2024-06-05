from fastapi import Query, HTTPException, APIRouter, Body, Depends
from typing import Optional, Any, List, Dict, Union

from sqlalchemy.orm import Session

from app.db import get_db, get_all_schemas, get_tables_for_schema, get_data_for_table, add_data_to_table

from app.schemas.response_models import SchemaResponse, TablesResponse, TableDataResponse, AddDataResponse
router = APIRouter()


@router.get("/schemas", response_model=SchemaResponse)
def read_schemas():
    schemas = get_all_schemas()
    if "message" in schemas:
        raise HTTPException(status_code=404, detail=schemas["message"])
    return schemas



@router.get("/schemas/{schema_name}/tables", response_model=TablesResponse)
def read_tables_for_schema(schema_name: str):
    tables = get_tables_for_schema(schema_name)
    if "message" in tables:
        raise HTTPException(status_code=404, detail=tables["message"])
    return tables


@router.get("/schemas/{schema_name}/tables/{table_name}/data", response_model=TableDataResponse)
def read_data_for_table(
    schema_name: str,
    table_name: str,
    primary_key_value: Any = None,
    limit: int = Query(None, description="Limit the number of rows returned"),
    db_: Session = Depends(get_db),
) -> Any:
    return get_data_for_table(db_, schema_name, table_name, primary_key_value, limit)


@router.post("/schemas/{schema_name}/tables/{table_name}/data", response_model=AddDataResponse)
def add_data(
    schema_name: str,
    table_name: str,
    data: Union[Dict[str, Any], List[Dict[str, Any]]],
    db_: Session = Depends(get_db),
):
    return add_data_to_table(db_, schema_name, table_name, data)