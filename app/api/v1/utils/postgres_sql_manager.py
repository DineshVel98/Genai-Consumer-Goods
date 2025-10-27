import psycopg2
from psycopg2 import sql
from app.api.v1.utils.config import Config


class PostgresDBManager:
    def __init__(self, config: Config):
        """Initialize connection parameters."""
        self.conf = config
        self.connection = None

    # ---------- Connect ----------
    def connect(self):
        """Establish connection to PostgreSQL."""
        try:
            self.connection = psycopg2.connect(
                host=self.conf.postgres_host,          # or use 'hostname'
                database=self.conf.postgres_database,
                user=self.conf.postgres_username,
                password=self.conf.postgres_password,
                port=self.conf.postgres_port  # default port 5432
            )
            print("Connected to PostgreSQL.")
        except Exception as e:
            raise Exception(f"Connection failed: {e}")

    # ---------- Disconnect ----------
    def disconnect(self):
        """Close the connection."""
        if self.connection:
            self.connection.close()
            print("Disconnected from PostgreSQL.")

    # ---------- Read ----------
    def read_data(self, query, params=None):
        """Execute SELECT query and return results."""
        if not self.connection:
            self.connect()
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or [])
            rows = cursor.fetchall()
            return rows
        finally:
            cursor.close()

    # ---------- Internal Execute ----------
    def _execute_query(self, query, params=None):
        """
        Execute any SQL query (SELECT, INSERT, UPDATE, DELETE).
        Returns fetched rows if it's a SELECT query; otherwise commits changes.
        """
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params or [])

            # If query starts with SELECT, fetch results
            if cursor.description is not None:  
                rows = cursor.fetchall()
                return rows
            else:
                self.connection.commit()
                return None
        except Exception as e:
            self.connection.rollback()
            raise Exception(f"Query execution failed: {e}")
        finally:
            cursor.close()