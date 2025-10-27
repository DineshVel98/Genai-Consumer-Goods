from fastapi import APIRouter
from app.api.v1.spark.services import PostgresSparkHelper
from db.connect import PostgreSQLDatabase
from dotenv import load_dotenv
import os
import json

spark_router = APIRouter(prefix= "/spark")

@spark_router.post("/create-bronze-tables")
async def create_bronze_table():
    # load config to enviroment variables.
    load_dotenv()

    # Assign env variables to variable.
    db_name = os.getenv("POSTGRE_DATABASE")
    user = os.getenv("POSTGRE_USERNAME")
    password = os.getenv("POSTGRE_PASSWORD")
    host = os.getenv("POSTGRE_HOST_NAME")
    port = os.getenv("POSTGRE_PORT")

    # Database connection creation.
    db = PostgreSQLDatabase(
        db_name= db_name,
        user= user,
        password= password,
        host= host,
        port= port
    )

    db.connect()
    create_table_script = """
            CREATE SCHEMA IF NOT EXISTS bronze;
            CREATE TABLE IF NOT EXISTS bronze.sales_data (
                date DATE NOT NULL,                              -- Sale date
                store_id INTEGER NOT NULL,                      -- Store ID
                store_region VARCHAR(50) NOT NULL,             -- Store region
                sku_id INTEGER NOT NULL,                        -- SKU (product) ID
                category VARCHAR(50) NOT NULL,                 -- Product category
                units_sold INTEGER NOT NULL,                    -- Number of units sold
                revenue NUMERIC(10, 2) NOT NULL,                -- Revenue generated
                promo_flag BOOLEAN NOT NULL,                    -- Promotion flag (true if promo is active)
                promo_type VARCHAR(50),                         -- Type of promotion (can be NULL)
                price NUMERIC(10, 2) NOT NULL,                  -- Product price
                inventory_level INTEGER NOT NULL,               -- Inventory level
                store_size VARCHAR(20) NOT NULL,               -- Size of the store (Small, Medium, Large)
                holiday_flag BOOLEAN NOT NULL                  -- Weekend/holiday flag (true for Sat/Sun)
            );
    """
    tbl_status = db.execute_ddl_script(create_table_script)
    # Close the database connection
    db.close_connection()

    if tbl_status:
        db.logger.info("Table 'test_table' created successfully.")
        return {"message": "Tables are successfully created"}
    else:
        db.logger.error("Failed to create db and bronze table.")
        return {"message": "Tables creation failed"}


@spark_router.post("/ingest-bronze-tables")
async def ingest_bronze_table():
    try:
        # load config to enviroment variables.
        load_dotenv()

        db_name = os.getenv("POSTGRE_DATABASE")
        host = os.getenv("POSTGRE_HOST_NAME")
        port = os.getenv("POSTGRE_PORT")
        user = os.getenv("POSTGRE_USERNAME")
        password = os.getenv("POSTGRE_PASSWORD")
        jdbc_url = os.getenv("JDBC_URL")
        schema_name = os.getenv("BRONZE_SCHEMA")
        tbl_name = os.getenv("BRZ_SALES_TABLE_NAME")

        # Database connection creation.
        db = PostgreSQLDatabase(
            db_name= db_name,
            user= user,
            password= password,
            host= host,
            port= port
        )

        db.connect()
        truncate_statment = f"""TRUNCATE TABLE {schema_name}.{tbl_name}"""
        tbl_status = db.execute_ddl_script(truncate_statment)
        # Close the database connection
        db.close_connection()

        spark = PostgresSparkHelper(app_name= "BronzeLayerIngestion",
                                jdbc_url= jdbc_url, 
                                user= user, password= password)
        
        df = spark.generate_pyspark_data(num_rows= 5000)
        record_count = df.count()
        spark.write_table(df, schema_name= schema_name, table_name= tbl_name)

        spark.stop_spark()
        return {"message": f"{record_count} records loaded successfully"}
    except Exception as e:
        print(e)
        return {"message": f"Data ingestion failed"}