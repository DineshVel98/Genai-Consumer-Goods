from fastapi import APIRouter
from app.api.v1.ai.agentic.services import sql_analyst

agentic_router = APIRouter(prefix= "/agentic-chatbot")


@agentic_router.post("/ask-question")
async def ask_question(user_question: str):
    return sql_analyst(user_question)
    