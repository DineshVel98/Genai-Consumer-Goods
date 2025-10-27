import psycopg2
import logging

class PostgreSQLDatabase:
    def __init__(self, db_name, user, password, host='localhost', port=5432):
        """
        Initializes the PostgreSQLDatabase instance with connection details.
        """
        self.db_name = db_name
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.connection = None

        #Configure logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def connect(self):
        """
        Connects to the PostgreSQL database using the provided credentials.
        """

        try:
            self.connection = psycopg2.connect(
                dbname = self.db_name,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )

            self.logger.info(f"Connected to the database {self.db_name} successfully.")
        except Exception as e:
            self.logger.error(f"Error connecting to database: {e}")
            self.connection = None

    def execute_ddl_script(self, script):
        """
        Executes a SQL script for creating or modifying database objects.
        This method is meant for DDL statements only (like CREATE, ALTER, DROP).

        Parameters:
        - script (str): The SQL script to be executed.

        Returns:
        - success (bool): True if the script executed successfully, False otherwise.
        """

        if not self.connection:
            self.logger.warning("Database connection is not established. Call the `connect()` method first.")
            return False
        
        # Execute the provided script

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(script)
                self.connection.commit()
                self.logger.info("DDL script executed successfully.")
                return True
        except Exception as e:
            self.logger.error(f"Error executing DDl script: {e}")
            self.connection.rollback()
            return False
    
    def close_connection(self):
        """
        Closes the database connection.
        """

        if self.connection:
            self.connection.close()
            self.logger.info("Database connection closed.")
        else:
            self.logger.warning("Database connection is already closed.")