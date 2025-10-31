from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from app.api.v1.utils.langchain_utils import contextualise_chain
from app.api.v1.utils.langgraph_agent import agent
from app.api.v1.utils.azure_sql_manager import AzureSQLManager
from app.api.v1.ai.agentic.models import AgenticChatRequest, ChatResponse
from app.api.v1.utils.config import Config
from app.api.v1.utils.utils import history_to_lc_messages, append_message
import logging

agentic_router = APIRouter(prefix= "/agentic")
logging.basicConfig(filename='app.log', level=logging.INFO)


@agentic_router.post("/chat")
def chat(query_input: AgenticChatRequest):
    """
    Main chat endpoint using the LangGraph agent with routing, RAG, Analyst, and web search capabilities.
    """

    logging.info(f"Session ID: {query_input.session_id}, User Query: {query_input.question}")

    try:
        # Store the conversation
        azure_db = AzureSQLManager(Config())

        # Convert chat history to LangChain messages
        chat_history = azure_db.get_chat_history(query_input.session_id)
        messages = history_to_lc_messages(chat_history)

        # Add current user message
        # 2. Generate a stand-alone question
        standalone_q = contextualise_chain.invoke({
            "chat_history": messages,
            "input": query_input.question,
        })

        messages = append_message(messages, HumanMessage(content=standalone_q))

        # Invoke the LangGraph
        result = agent.invoke(
            {"messages": messages, "session_id": query_input.session_id}
        )

        # Get the last AI message
        last_message = next((m for m in reversed(result["messages"])
                           if isinstance(m, AIMessage)), None)

        if last_message:
            answer = last_message.content
        else:
            answer = "I apologize, but I couldn't generate a response at this time."

        params = (query_input.session_id, query_input.user_id, query_input.question, answer, query_input.user_id)
        azure_db.insert_chat_history(params)
        logging.info(f"Session ID: {query_input.session_id}, AI Response: {answer}")

        return ChatResponse(answer=answer, session_id=query_input.session_id)

    except Exception as e:
        logging.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@agentic_router.get("/get-chat-history")
def get_chat_history(session_id: str):
    azure_sql_manager = AzureSQLManager(Config())
    chat_history = azure_sql_manager.get_chat_history([session_id])
    messages = [{"human": hum, "ai": ai} for hum, ai in chat_history]
    response = {"session_id": session_id, "messages": messages}
    return response

@agentic_router.delete("/delete-chat-history")
def delete_chat_history(session_id: str):
    azure_sql_manager = AzureSQLManager(Config())
    status = azure_sql_manager.delete_chat_history([session_id])
    return status


@agentic_router.get("/all-session-ids")
def get_all_session_ids(user_id: str):
    azure_sql_manager = AzureSQLManager(Config())
    chat_history = azure_sql_manager.get_first_record_per_group([user_id])
    response = [{"session_id": sid, "user_question": q} for sid, q in chat_history]
    return response





    