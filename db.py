from typing import Type

import sqlalchemy as sa
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import MetaData, create_engine, inspect, select, insert, update
from sqlalchemy.dialects.postgresql import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.automap import automap_base
from fastapi.encoders import jsonable_encoder
from sqlalchemy.testing.schema import Table
from typing import List, Type, Any, Dict

# engine = create_engine("postgresql://postgres:1qa2ws@127.0.0.1/imbor_database")
#
# session = Session(engine)
#
# metadata = MetaData()
# metadata.reflect(engine)
#
# Base = automap_base(metadata=metadata)
# Base.prepare(autoload_with=engine, schema="dbo")
#
# test = Base.classes.imborkern_attributen
#
# table_names = metadata.tables.keys()
# table_names = list(map(lambda x: x.split(".")[1], table_names))
#
# insp = sa.inspect(engine)
# schema_list = insp.get_schema_names()
#
# def make_catel(table_name, table_names):
#     print(table_name)
#     for table in table_names:
#         if table == table_name:
#             table = table.split('.')[-1]
#             return getattr(Base.classes, table)


# def get_data_by_id(id):
#     pk_name = inspect(test).mapper.primary_key[0].name
#     pk_column = getattr(test, pk_name)
#     return jsonable_encoder(session.query(test).where(pk_column == id).all())

# def get_data_by_id(id, table_name):
#     t = make_catel(table_name, table_names)
#     print(t)
#     try:
#         pk_name = inspect(t).mapper.primary_key[0].name
#     except Exception as e:
#         return jsonable_encoder("")
#     pk_column = getattr(t, pk_name)
#     return jsonable_encoder(session.query(t).where(pk_column == id).all())


# if __name__ == "__main__":
engine = create_engine("postgresql://postgres:1qa2ws@127.0.0.1/imbor_database")

# Reflect all tables from the database
metadata = MetaData()
metadata.reflect(bind=engine)

inspector = sa.inspect(engine)

# Get all schemas
schemas = inspector.get_schema_names()

session = Session(engine)

Base = automap_base(metadata=metadata)

# Get all tables for each schema
schemas_and_tables = [
    {
        'schema': schema,
        'tables': inspector.get_table_names(schema=schema)
    }
    for schema in schemas
]


def get_all_schemas():
    return [schema['schema'] for schema in schemas_and_tables]


def get_tables_for_schema(schema_name):
    for schema in schemas_and_tables:
        if schema['schema'] == schema_name:
            return schema['tables']
    return []


# def get_data_for_table(schema_name, table_name):
#     try:
#         Base.prepare(autoload_with=engine, schema=schema_name)
#         # Get the class corresponding to the table
#         table_class = getattr(Base.classes, table_name, None)
#         if table_class:
#             # Construct a query to fetch all data from the table
#             query = session.query(table_class)
#
#             # Print the generated SQL query
#             print("Generated SQL Query:", query)
#
#             # Fetch all data from the table
#             data = query.all()
#
#             if data:
#                 data_dicts = [row.__dict__ for row in data]
#                 print(data_dicts)
#                 return jsonable_encoder(data_dicts)
#             else:
#                 print(f"No data found in table '{table_name}' in schema '{schema_name}'.")
#                 return []
#         else:
#             print(f"Table '{table_name}' not found in schema '{schema_name}'.")
#             return []
#     except Exception as e:
#         print(f"Error fetching data from table '{table_name}' in schema '{schema_name}': {e}")
#         return []


def get_data_for_table(schema_name, table_name):
    try:
        # Reflect the table directly from the database
        table = Table(table_name, metadata, autoload_with=engine, schema=schema_name)
        # Establish a connection
        with engine.connect() as connection:
            # Construct a select query to fetch all data from the table
            query = table.select()

            # Execute the query and fetch all rows
            result = connection.execute(query)
            rows = result.fetchall()
            columns = result.keys()

        if rows:
            # Convert each row to a dictionary
            data_dicts = [dict(zip(columns, row)) for row in rows]
            return jsonable_encoder(data_dicts)
        else:
            print(f"No data found in table '{table_name}' in schema '{schema_name}'.")
            return []
    except Exception as e:
        print(f"Error fetching data from table '{table_name}' in schema '{schema_name}': {e}")
        return []


def get_primary_key_column(table):
    try:
        for column in table.columns:
            if column.primary_key:
                return column.name
        print(f"No primary key found for table '{table.name}'.")
        return None
    except Exception as e:
        print(f"Error fetching primary key column for table '{table.name}': {e}")
        return None


def get_first_column_name(table):
    try:
        for column in table.columns:
            return column.name
        print(f"No suitable column found for table '{table.name}'.")
        return None
    except Exception as e:
        print(f"Error fetching first column name for table '{table.name}': {e}")
        return None


def get_row_by_primary_key(schema_name, table_name, primary_key_value):
    try:
        table = Table(table_name, metadata, autoload_with=engine, schema=schema_name)

        # Get the primary key column name
        primary_key_column = get_primary_key_column(table)

        if not primary_key_column:
            primary_key_column = get_first_column_name(table)
            if not primary_key_column:
                return []
        print(primary_key_column)
        # Create a session
        with engine.connect() as connection:
            # Construct a select query to fetch the row by primary key
            query = select(table).where(getattr(table.c, primary_key_column) == primary_key_value)

            # Execute the query and fetch the row
            result = connection.execute(query)
            rows = result.fetchall()

        if rows:
            # Convert the rows to dictionaries
            rows_dicts = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(table.columns):
                    row_dict[col.name] = row[i]  # Access column value by index
                rows_dicts.append(row_dict)
            return jsonable_encoder(rows_dicts)
        else:
            print(f"No row found with primary key '{primary_key_value}' in table '{table_name}'.")
            return []
    except Exception as e:
        print(f"Error fetching row with primary key '{primary_key_value}' from table '{table_name}': {e}")
        return []


def upload_data(data):
    try:
        for item in schemas_and_tables:
            item_str = str(item)  # Convert to string
            schema_name, table_name = item_str.split('.')
            table = Table(table_name, metadata, autoload_with=engine, schema=schema_name)

            # Create a list of dictionaries containing data for this table
            table_data = [row for row in data if row['table'] == table_name]

            if table_data:
                with engine.connect() as connection:
                    # Begin a transaction
                    with connection.begin():
                        # Insert data into the table
                        connection.execute(insert(table), table_data)

                print(f"Data uploaded successfully to '{schema_name}.{table_name}'.")
            else:
                print(f"No data provided for '{schema_name}.{table_name}'.")
    except Exception as e:
        print(f"Error uploading data: {e}")

