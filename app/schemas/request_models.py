from typing import Any, Dict

from pydantic import BaseModel


class TableCreateRequest(BaseModel):
    table_name: str
    columns: Dict[str, Any]
    primary_key: str = None


class RowUpdateRequest(BaseModel):
    row_id: Any
    update_data: Dict[str, Any]
