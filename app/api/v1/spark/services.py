from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, rand, floor, when, expr, udf
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType, DateType, BooleanType
import random
import numpy as np

class PostgresSparkHelper:
    def __init__(self, app_name: str, jdbc_url: str, user: str, password: str, driver: str = "org.postgresql.Driver"):
        """
        Constructor to initialize the helper class with PostgreSQL JDBC connection details.
        
        :param app_name: Name of the Spark application.
        :param jdbc_url: JDBC URL for the PostgreSQL database.
        :param user: Database username.
        :param password: Database password.
        :param driver: JDBC driver class (default: 'org.postgresql.Driver').
        """
        self.app_name = app_name
        self.jdbc_url = jdbc_url
        self.user = user
        self.password = password
        self.driver = driver
        
        # Create a Spark session
        self.spark = SparkSession.builder \
            .master("local")\
            .config("spark.sql.execution.pyspark.udf.faulthandler.enabled", "true") \
            .config("spark.python.worker.faulthandler.enabled", "true") \
            .config("spark.jars", r"C:\Users\dinesh_vel\Desktop\learning\llm_capstone\package\postgresql-42.7.8.jar") \
            .appName(self.app_name) \
            .getOrCreate()

    def read_table(self, schema_name: str, table_name: str):
        """
        Reads a PostgreSQL table into a Spark DataFrame.

        :param table_name: Name of the table to read.
        :return: Spark DataFrame containing the table data.
        """
        df = self.spark.read.format("jdbc") \
            .option("url", self.jdbc_url) \
            .option("dbtable", f"{schema_name}.{table_name}") \
            .option("user", self.user) \
            .option("password", self.password) \
            .option("driver", self.driver) \
            .load()
        
        return df
    
    def write_table(self, df, schema_name: str, table_name: str, write_mode: str = "append"):
        """
        Writes a Spark DataFrame to a PostgreSQL table.

        :param df: Spark DataFrame to be written.
        :param table_name: Target table name in PostgreSQL.
        :param write_mode: Write mode (default: 'append'). Can be 'overwrite', 'append', etc.
        """
        df.write.format("jdbc") \
            .option("url", self.jdbc_url) \
            .option("dbtable", f"{schema_name}.{table_name}") \
            .option("user", self.user) \
            .option("password", self.password) \
            .option("driver", self.driver)\
            .mode(write_mode) \
            .save()
    
    def stop_spark(self):
        """
        Stop the Spark session.
        """
        self.spark.stop()

    def generate_pyspark_data(self, num_rows):
        # Generate Data in PySpark
        df = self.spark.range(0, num_rows).withColumn("id", col("id"))

        # Generate random columns
        df = df.withColumn("date", expr("DATE_ADD('2022-01-01', CAST(rand()*365 AS INT))"))\
            .withColumn("store_id", floor(rand() * 10 + 1))\
            .withColumn("store_region", when((rand() < 0.33), "North").when(rand() < 0.66, "South").otherwise("East"))\
            .withColumn("sku_id", floor(rand() * 50 + 101))\
            .withColumn("category", when((rand() < 0.2), "Beverages").when(rand() < 0.4, "Snacks")
                .when(rand() < 0.6, "Dairy").when(rand() < 0.8, "Household").otherwise("Personal Care"))\
            .withColumn("base_price", floor(rand() * 8 + 2))\
            .withColumn("promo_flag", when(rand() < 0.2, 1).otherwise(0))\
            .withColumn("promo_type", when(col("promo_flag") == 1, when((rand() < 0.33), "Discount").
                when(rand() < 0.66, "BuyOneGetOne").otherwise("FlashSale")).otherwise(None))\
            .withColumn("price", col("base_price") * when(col("promo_flag") == 1, 0.8).otherwise(1.0))\
            .withColumn("units_sold", when(col("promo_flag") == 1, floor(rand() * 20 + 20)).otherwise(floor(rand() * 10 + 10)))\
            .withColumn("revenue", col("units_sold") * col("price"))\
            .withColumn("inventory_level", floor(rand() * 900 + 100))\
            .withColumn("store_size", when((rand() < 0.33), "Small").when(rand() < 0.66, "Medium").otherwise("Large"))\
            .withColumn("holiday_flag", when(expr("WEEKDAY(date) IN (5, 6)"), 1).otherwise(0))
        
        df = df.select(
            col("date").cast(DateType()).alias("date"),
            col("store_id").cast(IntegerType()).alias("store_id"),
            col("store_region").cast(StringType()).alias("store_region"),
            col("sku_id").cast(IntegerType()).alias("sku_id"),
            col("category").cast(StringType()).alias("category"),
            col("units_sold").cast(IntegerType()).alias("units_sold"),
            col("revenue").cast(FloatType()).alias("revenue"),
            col("promo_flag").cast(BooleanType()).alias("promo_flag"),
            col("promo_type").cast(StringType()).alias("promo_type"),
            col("price").cast(FloatType()).alias("price"),
            col("inventory_level").cast(IntegerType()).alias("inventory_level"),
            col("store_size").cast(StringType()).alias("store_size"),
            col("holiday_flag").cast(BooleanType()).alias("holiday_flag")
        )
        
        return df
