from pydantic import BaseModel

class AskQuestionRequest(BaseModel):
    session_id: str
    user_id: str
    user_question: str