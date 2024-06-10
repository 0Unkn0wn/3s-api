from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db, validate_schema_access, create_table_for_schema, get_schemas_and_tables, \
    get_tables_for_schema
from app.schemas.response_models import TablesResponse
from app.schemas.user import SystemUser
from app.schemas.request_models import TableCreateRequest
from app.utils import get_current_user

router = APIRouter()


@router.get("/tables", response_model=TablesResponse)
def read_tables_for_schema(current_user: SystemUser = Depends(get_current_user)):
    schema_name = f"user_own_data_{current_user.user_id}"
    schemas_and_tables = get_schemas_and_tables([schema_name])
    tables = get_tables_for_schema(schema_name, schemas_and_tables)
    if "message" in tables:
        raise HTTPException(status_code=404, detail=tables["message"])
    return tables


@router.post("/create_table/")
def create_table(
    request: TableCreateRequest,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    schema_name = f"user_own_data_{current_user.user_id}"
    validate_schema_access(schema_name, [schema_name])
    create_table_for_schema(db, schema_name, request.table_name, request.columns, request.primary_key)
    return {"message": f"Table {request.table_name} created successfully in schema {schema_name}"}
