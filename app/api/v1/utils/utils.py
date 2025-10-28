from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from typing import List, Dict, Optional, Tuple

def history_to_lc_messages(history: List[Tuple]) -> List[BaseMessage]:
    """Convert chat history from DB to LangChain message objects."""
    messages = []
    for message in history:
        messages.append(HumanMessage(content= message[0]))
        messages.append(AIMessage(content= message[0]))
    return messages

def append_message(history: List[BaseMessage], message: BaseMessage) -> List[BaseMessage]:
    """Return a new list with the message appended."""
    return history + [message] 