import pyodbc
from app.api.v1.utils.config import Config


class AzureSQLManager:
    def __init__(self, config: Config):
        """Initialize connection parameters."""
        self.conf = config
        self.connection = None

    # ---------- Connect ----------
    def connect(self):
        """Establish connection to Azure SQL."""
        try:
            conn_str = (
                f"DRIVER={self.conf.driver};"
                f"SERVER={self.conf.server};"
                f"DATABASE={self.conf.database};"
                f"UID={self.conf.username};"
                f"PWD={self.conf.password};"
                f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
            )
            print(conn_str)
            self.connection = pyodbc.connect(conn_str)
        except Exception as e:
            raise Exception(f"Connection failed: {e}")

    # ---------- Disconnect ----------
    def disconnect(self):
        """Close the connection."""
        if self.connection:
            self.connection.close()
            print("Disconnected from Azure SQL.")

    # ---------- Read ----------
    def read_data(self, query, params=None):
        """Execute SELECT query and return results."""
        if not self.connection:
            self.connect()
        cursor = self.connection.cursor()
        cursor.execute(query, params or [])
        rows = cursor.fetchall()
        cursor.close()
        return rows

    # ---------- Internal Execute ----------
    def _execute_query(self, query, params):
        """Internal method for INSERT/UPDATE/DELETE."""
        if not self.connection:
            self.connect()
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        cursor.close()

    def insert_file_metadata(self, params):
        status = False
        try:
            if not self.connection:
                self.connect()
            query= """
                    INSERT INTO dbo.file_metadata(session_id, user_id, file_name, created_by)
                    VALUES (?, ?, ?, ?)
                """
            
            self._execute_query(query, params)
            status = True
            return status
        except Exception as e:
            print("Insert file metadata failed", str(e))
            return status

