import os
from typing import List, Any, Dict
from typing import Union, Generator
from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import MetaData, create_engine, inspect, select, Column, Integer, String, Float, Date, Boolean, update
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.testing.schema import Table
import sqlalchemy as sa

from app.schemas.response_models import TableStructureResponse

load_dotenv()

DB_URL = os.environ.get('DB_URL')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_URL}/db-3s")

metadata = MetaData()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_public_schemas(db: Session) -> List[str]:
    try:
        ground_data_schema_table = Table('ground_data_schema_dictionary', metadata, autoload_with=engine,
                                         schema='public')
        query = select(ground_data_schema_table.c.schema_name)
        result = db.execute(query)
        public_schemas = [row['schema_name'] for row in result.mappings().all()]  # Access by column name
        return public_schemas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching public schemas: {e}")


def get_schemas_and_tables(schema_list: List[str]) -> List[Dict[str, Any]]:
    inspector = inspect(engine)
    return [
        {
            'schema': schema,
            'tables': inspector.get_table_names(schema=schema)
        }
        for schema in schema_list
    ]


def validate_schema_access(schema_name: str, schema_list: List[str]):
    inspector = inspect(engine)
    if schema_name not in inspector.get_schema_names():
        raise HTTPException(status_code=404, detail=f"Schema '{schema_name}' not found.")
    if schema_name not in schema_list:
        raise HTTPException(status_code=403, detail=f"Access to schema '{schema_name}' is forbidden.")


def get_tables_for_schema(schema_name: str, schemas_and_tables: List[Dict[str, Any]]) -> dict[Any, Any] | list[Any]:
    for schema in schemas_and_tables:
        if schema['schema'] == schema_name:
            if not schema['tables']:
                raise HTTPException(status_code=200, detail=f"No tables for schema '{schema_name}'.")
            return {"schema_name": schema_name, "tables": jsonable_encoder(schema['tables'])}
    raise HTTPException(status_code=404, detail=f"Schema '{schema_name}' not found.")


def get_primary_key_column(table: Table) -> str:
    try:
        for column in table.columns:
            if column.primary_key:
                return column.name
        return ""
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching primary key column for table '{table.name}': {e}")


def get_first_column_name(table: Table) -> str:
    try:
        for column in table.columns:
            return column.name
        return ""
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching first column name for table '{table.name}': {e}")


def get_data_for_table(
        db: Session,
        schema_name: str,
        table_name: str,
        primary_key_value: Any = None,
        limit: int = None
) -> Dict[str, Any]:
    try:
        table = Table(table_name, metadata, autoload_with=engine, schema=schema_name)
        primary_key_column = get_primary_key_column(table)
        filter_column = primary_key_column or get_first_column_name(table)
        if not filter_column:
            raise HTTPException(status_code=500,
                                detail=f"No primary key or suitable column found for table '{table_name}' "
                                       f"in schema '{schema_name}'.")

        query = select(table)
        if limit is not None:
            query = query.limit(limit)
        if primary_key_value:
            query = query.where(getattr(table.c, filter_column) == primary_key_value)
        result = db.execute(query)
        rows = result.fetchall()
        columns = result.keys()
        if rows:
            data_dicts = [dict(zip(columns, row)) for row in rows]
            return {"table_name": table_name, "data": jsonable_encoder(data_dicts)}
        else:
            return {"table_name": table_name, "data": []}
    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error fetching data from table '{table_name}' in schema '{schema_name}': {e}")


def add_data_to_table(
        db: Session,
        schema_name: str,
        table_name: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
):
    try:
        table = Table(table_name, metadata, autoload_with=engine, schema=schema_name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found in schema '{schema_name}'."
                                                    f"Error: {e}")
    if isinstance(data, dict):
        data = [data]
    for item in data:
        for key in item.keys():
            if key not in table.columns.keys():
                raise HTTPException(status_code=400, detail=f"Column '{key}' not found in table '{table_name}'.")
    try:
        db.execute(table.insert(), data)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error inserting data into table {table}: {e}")
    return {"message": "Data added successfully"}


# Helper function to map string types to SQLAlchemy types
def map_column_type(column_type: str, length: int = None):
    try:
        if length:
            return getattr(sa, column_type)(int(length))
        return getattr(sa, column_type)()
    except AttributeError:
        raise HTTPException(status_code=400, detail=f"Unsupported column type '{column_type}'.")


def create_table_for_schema(
    db: Session,
    schema_name: str,
    table_name: str,
    columns: Dict[str, Any],
    primary_key: str = None
):
    # Define the table with the specified columns
    table_columns = []
    for col_name, col_props in columns.items():
        if isinstance(col_props, list) and len(col_props) == 2:
            col_type, col_length = col_props
            col_type = map_column_type(col_type, col_length)
        else:
            col_type = map_column_type(col_props)
        if col_name == primary_key:
            table_columns.append(Column(col_name, col_type, primary_key=True))
        else:
            table_columns.append(Column(col_name, col_type))

    table = Table(
        table_name,
        metadata,
        *table_columns,
        schema=schema_name,
        extend_existing=True
    )

    inspector = inspect(db.get_bind())
    if not inspector.has_table(table_name, schema=schema_name):
        try:
            # Create the table in the database
            table.create(bind=db.get_bind(), checkfirst=True)
            db.commit()
            return {"message": f"Table '{table_name}' created successfully in schema '{schema_name}'."}
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating table: {e}")
    else:
        return {"message": f"Table '{table_name}' already exists in schema '{schema_name}'."}


def get_table_structure(schema_name: str, table_name: str) -> TableStructureResponse:
    inspector = inspect(engine)
    columns_info = {}
    primary_key = None

    try:
        columns = inspector.get_columns(table_name, schema=schema_name)
        primary_keys = inspector.get_pk_constraint(table_name, schema=schema_name)['constrained_columns']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching table structure: {e}")

    for column in columns:
        col_type = str(column['type'])
        columns_info[column['name']] = col_type
        if column['name'] in primary_keys:
            primary_key = column['name']

    return TableStructureResponse(table_name=table_name, columns=columns_info, primary_key=primary_key)


def update_row(
    db: Session,
    schema_name: str,
    table_name: str,
    row_id: Any,
    update_data: Dict[str, Any]
):
    try:
        table = Table(table_name, metadata, autoload_with=db.bind, schema=schema_name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found in schema '{schema_name}'. "
                                                    f"Error: {e}")

    primary_key_column = get_primary_key_column(table)
    filter_column = primary_key_column or get_first_column_name(table)
    if not filter_column:
        raise HTTPException(status_code=500,
                            detail=f"No primary key or suitable column found "
                                   f"for table '{table_name}' in schema '{schema_name}'.")

    try:
        stmt = (
            update(table)
            .where(getattr(table.c, filter_column) == row_id)
            .values(update_data)
        )
        db.execute(stmt)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating row in table '{table_name}': {e}")

    return {"message": f"Row with ID '{row_id}' updated successfully in table '{table_name}'."}


def delete_table(db: Session, schema_name: str, table_name: str):
    try:
        table = Table(table_name, metadata, autoload_with=db.bind, schema=schema_name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found"
                                                    f"in schema '{schema_name}'. Error: {e}")

    try:
        table.drop(db.bind)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting table '{table_name}'"
                                                    f"in schema '{schema_name}': {e}")

    return {"message": f"Table '{table_name}' deleted successfully"}
