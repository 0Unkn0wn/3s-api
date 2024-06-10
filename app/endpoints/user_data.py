from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db, validate_schema_access
from app.schemas.user import SystemUser
from app.utils import get_current_user

router = APIRouter()


@router.post("/create_table/")
def create_table(
    table_name: str,
    columns: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user)
):
    schema_name = f"user_own_data_{current_user.user_id}"
    validate_schema_access(schema_name, [schema_name])
    create_table(table_name, columns, schema_name, db)
    return {"message": f"Table {table_name} created successfully in schema {schema_name}"}
