from fastapi import Query, HTTPException, APIRouter
from typing import Optional, Any
import app.db as db

router = APIRouter()


@router.get("/data/schemas", status_code=200)
async def get_schema_list() -> Any:
    result = db.get_all_schemas()
    if not result:
        raise HTTPException(status_code=404, detail=f"Schema list empty no schemas in this database")
    return result


@router.get("/data/schemas/{schema_name}/tables", status_code=200)
async def get_table_list(
        schema_name: str,
) -> Any:
    result = db.get_tables_for_schema(schema_name)
    if not result:
        raise HTTPException(status_code=404, detail=f"Table list empty no tables in this schema {schema_name}")
    return result


@router.get("/data/schemas/{schema_name}/tables/{table_name}", status_code=200)
async def get_all_data(
        schema_name: str,
        table_name: str,
        limit: Optional[int] = Query(None, gt=0, le=100),
) -> Any:
    result = db.get_data_for_table(schema_name, table_name)
    if not result:
        raise HTTPException(status_code=404, detail=f"Table empty no data in this table {table_name}")
    if limit:
        result = result[:limit]
    return result


@router.get("/data/schemas/{schema_name}/tables/{table_name}/items/{item_id}", status_code=200)
async def get_single_item(
        *,
        schema_name: str,
        table_name: str,
        item_id: int,
) -> Any:
    result = db.get_row_by_primary_key(schema_name, table_name, item_id)
    if not result:
        if not str(result):
            raise HTTPException(status_code=404, detail=f"Tabel {table_name} not found")
        raise HTTPException(status_code=404, detail=f"Item with ID {item_id} not found")
    return result
