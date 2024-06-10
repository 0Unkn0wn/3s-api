from fastapi import Query, HTTPException, APIRouter, Depends
from typing import Any, List, Dict, Union

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.db import get_db, get_schemas_and_tables, get_tables_for_schema, get_data_for_table, \
    get_public_schemas

from app.schemas.response_models import SchemaResponse, TablesResponse, TableDataResponse
router = APIRouter()


@router.get("/schemas", response_model=SchemaResponse)
def read_public_schemas(db: Session = Depends(get_db)):
    public_schemas = get_public_schemas(db)
    if not public_schemas:
        raise HTTPException(status_code=404, detail="No public schemas found.")
    return {"schemas": jsonable_encoder(public_schemas)}


@router.get("/schemas/{schema_name}/tables", response_model=TablesResponse)
def read_tables_for_schema(schema_name: str, db: Session = Depends(get_db)):
    public_schemas = get_public_schemas(db)
    if schema_name not in public_schemas:
        raise HTTPException(status_code=403, detail=f"Access to schema '{schema_name}' is forbidden.")
    schemas_and_tables = get_schemas_and_tables(public_schemas)
    tables = get_tables_for_schema(schema_name, schemas_and_tables)
    if "message" in tables:
        raise HTTPException(status_code=404, detail=tables["message"])
    return tables


@router.get("/schemas/{schema_name}/tables/{table_name}/data", response_model=TableDataResponse)
def get_table_data(
    schema_name: str,
    table_name: str,
    primary_key_value: Any = None,
    limit: int = Query(None, description="Limit the number of rows returned"),
    db: Session = Depends(get_db),
):
    public_schemas = get_public_schemas(db)
    if schema_name not in public_schemas:
        raise HTTPException(status_code=403, detail=f"Access to schema '{schema_name}' is forbidden.")
    return get_data_for_table(db, schema_name, table_name, primary_key_value, limit)
