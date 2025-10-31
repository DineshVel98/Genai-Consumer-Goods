from langchain.chat_models import init_chat_model
from langchain.schema import SystemMessage, HumanMessage
from app.api.v1.utils.postgres_sql_manager import PostgresDBManager
from app.api.v1.utils.vector_db_manager import VectorDBManager
from app.api.v1.utils.config import Config
from app.api.v1.utils.shared import analyst_llm
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
import json


@tool
def sql_analyst_tool(user_question: str):
    """
    Description:
        Converts a natural language question into an optimized PostgreSQL SELECT query.

    Purpose:
        This tool uses an LLM to translate user intent into SQL for a predefined Postgres schema.
        It helps users query structured data without needing SQL knowledge.
    """

    BASE_PROMPT = """
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
    - Use **PostgreSQL parameter placeholders** in the form `%s`, etc.
    - Ensure syntactically correct, efficient, and readable SQL.
    - Add LIMIT {max_rows} if necessary.
    - Return JSON with keys: {{"sql": "<SELECT ...>", "explanation": "...", "params": ["value1", "value2", ...]}}

    Produce the simplest, efficient SQL that answers the question."""

    db_manager = PostgresDBManager(Config())
    max_retries = 5
    last_error = None
    query_details = None
    sql = None
    explanation = None
    params = None

    for attempt in range(1, max_retries + 1):
        try:
            # Build prompt (if retry, include error context)
            if last_error:
                prompt = (
                    BASE_PROMPT
                    + f"\nThe previous SQL failed with error:\n{last_error}\n"
                      "Please fix the SQL and regenerate a valid one."
                )
            else:
                prompt = BASE_PROMPT

            # Get LLM response
            response = analyst_llm.invoke(prompt.format(max_rows=100, user_question=user_question))
            # Parse LLM response safely
            try:
                sql = response.sql
                explanation = response.explanation
                params = response.params
            except Exception:
                raise ValueError(f"Invalid LLM output format: {response}")

            # Try executing query
            output = db_manager._execute_query(sql, params)
            return output

        except Exception as e:
            last_error = str(e) or traceback.format_exc()
            print(f"[Attempt {attempt}] Query failed: {last_error}")

            # Retry with error feedback
            if attempt == max_retries:
                return "Failed"

@tool
def rag_search_tool(user_question: str, session_id: str):
    """Top-3 chunks from Knowledge Base (empty string if none)"""
    try:
        vector_db = VectorDBManager(Config())

        similar_docs = vector_db.vector_store.similarity_search(
            query = user_question,
            k=5,
            filters=f"session_id eq '{session_id}'"
        )

        return "\n\n".join([doc.page_content for doc in similar_docs])
    except Exception as e:
        return f"RAG_SEARCH_TOOL Error::{e}"
    

# Initialize Tavily search
tavily = TavilySearch(max_results=3, topic="general")

@tool
def web_search_tool(query: str) -> str:
    """Up-to-date web info via Tavily"""
    try:
        result = tavily.invoke({"query": query})

        # Extract and format the results from Tavily response
        if isinstance(result, dict) and 'results' in result:
            formatted_results = []
            for item in result['results']:
                title = item.get('title', 'No title')
                content = item.get('content', 'No content')
                url = item.get('url', '')
                formatted_results.append(f"Title: {title}\nContent: {content}\nURL: {url}")

            return "\n\n".join(formatted_results) if formatted_results else "No results found"
        else:
            return str(result)
    except Exception as e:
        return f"WEB_SEARCH_TOOL::{e}"
