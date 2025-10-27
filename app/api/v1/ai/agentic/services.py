from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage
from app.api.v1.utils.config import Config
from app.api.v1.utils.postgres_sql_manager import PostgresDBManager
from app.api.v1.utils.config import Config
import json

def sql_analyst(user_question: str):
    """
    Description:
        Converts a natural language question into an optimized PostgreSQL SELECT query.

    Purpose:
        This tool uses an LLM to translate user intent into SQL for a predefined Postgres schema.
        It helps users query structured data without needing SQL knowledge.

    Input:
        user_question (str): The user's plain-English query about sales data.
            Example: "Show me total revenue by region for September."

    Output:
        dict: A JSON object with three keys:
            - "sql" (str): The generated SQL SELECT statement.
            - "explanation" (str): A human-readable explanation of the query logic.
            - "params" (dict): Parameter placeholders (e.g., {"p1": "2025-09-01"}).

    Notes:
        - Only SELECT queries are allowed (read-only).
        - It respects schema constraints and column definitions.
        - Automatically applies a LIMIT clause to prevent large queries.
    """

    prompt = """
    You are a SQL assistant. Context:
    - DB: Postgres. Read-only access.
    - Allowed statements: SELECT only. Max rows: {max_rows}.
    - Schema (schema -> table -> columns):
        Schema: bronze
        Table: sales_data
            - date (DATE): Transaction date of the sale
            - store_id (INTEGER): Unique store identifier
            - store_region (VARCHAR(50)): Region where the store is located (e.g., North, South)
            - sku_id (INTEGER): Unique product SKU identifier
            - category (VARCHAR(50)): Product category (e.g., Beverages, Snacks)
            - units_sold (INTEGER): Number of units sold on that date
            - revenue (NUMERIC): Total sales amount generated
            - promo_flag (BOOLEAN): Whether the sale occurred under a promotion
            - promo_type (VARCHAR(50), nullable): Type of promotion (e.g., Discount, BOGO)
            - price (NUMERIC): Unit price of the product during the sale
            - inventory_level (INTEGER): Closing inventory level at the end of the day
            - store_size (VARCHAR(20)): Store size category (e.g., Small, Medium, Large)
            - holiday_flag (BOOLEAN): Indicates if the date was a holiday (1 = Yes, 0 = No)

    User question:
    "{user_question}"

    Constraints:
    - Use only existing columns above.
    - Use parameter placeholders like :p1 for external filters.
    - Add LIMIT {max_rows} if necessary.
    - Return JSON with keys: {{"sql": "<SELECT ...>", "explanation": "...", "params": {{"p1":"value", ...}}}}

    Produce the simplest, efficient SQL that answers the question."""

    # Initialize the Azure OpenAI chat model
    chat_model = init_chat_model(
        model= conf.ai_deployment_name,
        model_provider="azure_openai"
    )


    # Get the response
    response = chat_model.invoke(prompt.format(max_rows= 100, user_question= user_question))

    query_details = json.loads(response.content)

    return query_details