from typing import Dict, Any, Union, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db, create_table_for_schema, get_schemas_and_tables, \
    get_tables_for_schema, get_data_for_table, get_table_structure, add_data_to_table, delete_table, update_row
from app.schemas.response_models import TablesResponse, TableDataResponse, TableStructureResponse, AddDataResponse, \
    RemoveDataResponse, UpdateDataResponse
from app.schemas.user import SystemUser
from app.schemas.request_models import TableCreateRequest, RowUpdateRequest
from app.utils import get_current_user

router = APIRouter()


@router.post("/create_table/")
def create_table(
    request: TableCreateRequest,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    schema_name = f"user_own_data_{current_user.user_id}"
    create_table_for_schema(db, schema_name, request.table_name, request.columns, request.primary_key)
    return {"message": f"Table {request.table_name} created successfully in schema {schema_name}"}


@router.get("/tables", response_model=TablesResponse)
def read_tables_for_schema(current_user: SystemUser = Depends(get_current_user)):
    schema_name = f"user_own_data_{current_user.user_id}"
    schemas_and_tables = get_schemas_and_tables([schema_name])
    tables = get_tables_for_schema(schema_name, schemas_and_tables)
    if "message" in tables:
        raise HTTPException(status_code=404, detail=tables["message"])
    return tables


@router.get("/tables/{table_name}", response_model=TableDataResponse)
def get_table_data(
    table_name: str,
    primary_key_value: Any = None,
    limit: int = Query(None, description="Limit the number of rows returned"),
    current_user: SystemUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    schema_name = f"user_own_data_{current_user.user_id}"
    return get_data_for_table(db, schema_name, table_name, primary_key_value, limit)


@router.get("/table_structure/{table_name}", response_model=TableStructureResponse)
def get_table_structure_endpoint(
        table_name: str,
        current_user: SystemUser = Depends(get_current_user)
):
    schema_name = f"user_own_data_{current_user.user_id}"
    return get_table_structure(schema_name, table_name)


@router.post("/tables/{table_name}/data", response_model=AddDataResponse)
def add_table_data(
    table_name: str,
    data: Union[Dict[str, Any], List[Dict[str, Any]]],
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    schema_name = f"user_own_data_{current_user.user_id}"
    return add_data_to_table(db, schema_name, table_name, data)


@router.patch("/tables/{table_name}/rows", response_model=UpdateDataResponse)
def update_row_endpoint(
    table_name: str,
    request: RowUpdateRequest,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    schema_name = f"user_own_data_{current_user.user_id}"
    return update_row(db, schema_name, table_name, request.row_id, request.update_data)


@router.delete("/tables/{table_name}", response_model=RemoveDataResponse)
def delete_table_endpoint(
        table_name: str,
        db: Session = Depends(get_db),
        current_user: SystemUser = Depends(get_current_user)
):
    schema_name = f"user_own_data_{current_user.user_id}"
    return delete_table(db, schema_name, table_name)
