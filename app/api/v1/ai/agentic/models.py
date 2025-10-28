from pydantic import BaseModel

class AgenticChatRequest(BaseModel):
    session_id: str
    user_id: str
    question: str

class ChatResponse(BaseModel):
    answer: str
    session_id: str