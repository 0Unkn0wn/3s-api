import os
from typing import List, Any, Dict
from typing import Union, Generator
from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import MetaData, create_engine, inspect, select, Column, Integer, String, Float, Date, Boolean
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.testing.schema import Table

from app.schemas.response_models import TableStructureResponse

load_dotenv()

DB_URL = os.environ.get('DB_URL')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_URL}/db-3s")

metadata = MetaData()
metadata.reflect(bind=engine)

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
                return {"message": f"No tables for schema '{schema_name}'."}
            return {"schema_name": schema_name, "tables": jsonable_encoder(schema['tables'])}
    return {"message": f"Schema '{schema_name}' not found."}


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
def map_column_type(col_type: str):
    if col_type.startswith("Integer"):
        return Integer
    elif col_type.startswith("String"):
        if "(" in col_type and ")" in col_type:
            length = int(col_type.split("(")[1].split(")")[0])
            return String(length)
        else:
            return String
    elif col_type.startswith("Float"):
        return Float
    elif col_type.startswith("Date"):
        return Date
    elif col_type.startswith("Boolean"):
        return Boolean
    else:
        raise ValueError(f"Unsupported column type: {col_type}")


def create_table_for_schema(
    db: Session,
    schema_name: str,
    table_name: str,
    columns: Dict[str, Any],
    primary_key: str = None
):
    # Define the table with the specified columns
    table_columns = []
    for col_name, col_type in columns.items():
        if col_name == primary_key:
            table_columns.append(Column(col_name, map_column_type(col_type), primary_key=True))
        else:
            table_columns.append(Column(col_name, map_column_type(col_type)))

    table = Table(
        table_name,
        metadata,
        *table_columns,
        schema=schema_name
    )

    try:
        # Create the table in the database
        table.create(bind=db.get_bind(), checkfirst=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating table: {e}")


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


def delete_table(db: Session, schema_name: str, table_name: str):
    try:
        table = Table(table_name, metadata, autoload_with=db.bind, schema=schema_name)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found in schema '{schema_name}'. Error: {e}")

    try:
        table.drop(db.bind)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting table '{table_name}' in schema '{schema_name}': {e}")

    return {"message": f"Table '{table_name}' deleted successfully"}
