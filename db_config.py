import os
from sqlalchemy import create_engine

def get_db_engine():
    db_type = os.getenv("DB_TYPE", "sqlserver").lower()

    if db_type == "sqlserver":
        server = os.getenv("SQLSERVER_HOST")
        db = os.getenv("SQLSERVER_DB")
        user = os.getenv("SQLSERVER_USER")
        password = os.getenv("SQLSERVER_PASSWORD")
        driver = os.getenv("SQLSERVER_DRIVER", "ODBC Driver 18 for SQL Server")

        connection_string = f"mssql+pyodbc://{user}:{password}@{server}/{db}?driver={driver}"
    
    elif db_type == "postgresql":
        host = os.getenv("PG_HOST")
        db = os.getenv("PG_DB")
        user = os.getenv("PG_USER")
        password = os.getenv("PG_PASSWORD")
        port = os.getenv("PG_PORT", "5432")

        connection_string = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"
    
    else:
        raise ValueError("Tipo de base de datos no soportado. Usa 'sqlserver' o 'postgresql'.")

    return create_engine(connection_string)
