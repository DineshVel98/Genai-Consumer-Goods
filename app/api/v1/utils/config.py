from dotenv import load_dotenv
import os

class Config:
    def __init__(self):
        load_dotenv()

        # large language model configuration.
        self.ai_api_key = os.getenv("OPENAI_API_KEY")
        self.ai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.ai_deployment_name = os.getenv("OPENAI_DEPLOYMENT_NAME")
        self.ai_api_version = os.getenv("OPENAI_API_VERSION")

        # Embedding model configuration.
        self.embedding_deployment_name = os.getenv("AZURE_EMBEDDING_DEPLOYMENT_NAME")
        self.embedding_api_version = os.getenv("AZURE_EMBEDDING_API_VERSION")

        # Ai search configuration.
        self.ai_search_endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT")
        self.ai_search_key = os.getenv("AZURE_AI_SEARCH_KEY")
        self.ai_consumer_sales_index_name = os.getenv("AZURE_INDEX_NAME")

        # Azure Sql Configuration.
        self.driver = os.getenv("AZURE_SQL_DRIVER")
        self.server = os.getenv("AZURE_SQL_SERVER")
        self.database = os.getenv("AZURE_SQL_DATABASE")
        self.username = os.getenv("AZURE_SQL_USERNAME")
        self.password = os.getenv("AZURE_SQL_PASSWORD")

        # Postgres Configuration.
        self.postgres_host = os.getenv("POSTGRE_HOST_NAME")
        self.postgres_database = os.getenv("POSTGRE_DATABASE")
        self.postgres_username = os.getenv("POSTGRE_USERNAME")
        self.postgres_password = os.getenv("POSTGRE_PASSWORD")
        self.postgres_port = os.getenv("POSTGRE_PORT")

        # Tavily configuration
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")