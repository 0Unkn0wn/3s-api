import os
from typing import List, Any, Dict
from typing import Union, Generator
from dotenv import load_dotenv
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import MetaData, create_engine, inspect, select, Column, Integer, String, Float, Date, Boolean
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.testing.schema import Table

load_dotenv()

DB_URL = os.environ.get('DB_URL')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')

engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_URL}/db-3s")

metadata = MetaData()
metadata.reflect(bind=engine)

SessionLocal = sessionmaker(bind=engine)


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
        trans = db.begin()
        try:
            db.execute(table.insert(), data)
            trans.commit()
        except Exception as e:
            trans.rollback()
            raise HTTPException(status_code=500, detail=f"Error inserting data: {e}")
        return {"message": "Data added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding data to table '{table_name}': {e}")


# Helper function to map string types to SQLAlchemy types
def map_column_type(col_type: str):
    if col_type.startswith("Integer"):
        return Integer
    elif col_type.startswith("String"):
        length = int(col_type.split("(")[1].split(")")[0])
        return String(length)
    elif col_type.startswith("Float"):
        return Float
    elif col_type.startswith("Date"):
        return Date
    elif col_type.startswith("Boolean"):
        return Boolean
    else:
        raise ValueError(f"Unsupported column type: {col_type}")


def create_table_for_schema(table_name: str, columns: Dict[str, Any], schema_name: str, db: Session):
    # Define the table with the specified columns
    table_columns = [Column(col_name, map_column_type(col_type)) for col_name, col_type in columns.items()]

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
