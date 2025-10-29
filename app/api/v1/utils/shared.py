from app.api.v1.utils.llm_manager import LLMManager
from app.api.v1.utils.config import Config
from typing import TypedDict, List, Literal, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage


# ── Pydantic schemas ─────────────────────────────────────────────────
class RouteDecisionModel(BaseModel):
    route: Literal["rag", "answer", "analyst" ,"end"]
    reply: str | None = Field(None, description="Filled only when route == 'end'")

class RagJudgeModel(BaseModel):
    sufficient: bool

from typing import Dict, Any
from pydantic import BaseModel, Field

class AnalystModel(BaseModel):
    sql: str
    explanation: str
    params: Dict[str, Any] | None


# ── Shared state type ────────────────────────────────────────────────
class AgentState(TypedDict, total=False):
    messages: List[BaseMessage]
    route:    Literal["rag", "answer", "analyst", "end"]
    rag:      str
    web:      str
    analyst:  str
    session_id: str

# ── LLM instances with structured output where needed ───────────────
router_llm = LLMManager(Config(), temperature=0)\
                .connect()\
                .with_structured_output(RouteDecisionModel)

judge_llm  = LLMManager(Config(), temperature=0)\
                .connect()\
                .with_structured_output(RagJudgeModel)

answer_llm = LLMManager(Config(), temperature=0.7)\
                .connect()

analyst_llm = LLMManager(Config(), temperature=0)\
                .connect()\
                .with_structured_output(AnalystModel, method="function_calling")

