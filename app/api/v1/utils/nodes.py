from typing import Literal
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.api.v1.utils.shared import AgentState, router_llm, judge_llm, analyst_llm, answer_llm, RouteDecisionModel, RagJudgeModel
from app.api.v1.utils.tools import web_search_tool, sql_analyst_tool, rag_search_tool
from app.api.v1.utils.vector_db_manager import VectorDBManager
from app.api.v1.utils.config import Config


# Node 1: decision/router
def router_node(state: AgentState) -> AgentState:
    # Use full message history with a system prompt
    system_prompt = (
        "You are a smart routing controller that decides which node should handle a user's query.\n"
        "Classify each query into one of the following categories and return both the 'route' and an optional 'reply' when required.\n\n"
        "Routing rules:\n"
        "- Use 'end' if the message is:\n"
        "  • A greeting, farewell, or small talk (e.g., 'hi', 'hello', 'how are you', 'thanks').\n"
        "  • A repeated question already answered in the recent chat history. Include a short friendly reply.\n\n"
        "- Use 'analyst' if the question relates to:\n"
        "  • Sales data, sales metrics, revenue, stores, products, customers, or any business data analysis.\n"
        "  • Mentions words like 'sales_data', 'revenue', 'profit', 'region performance', 'trend analysis', or 'KPIs'.\n"
        "  • Analytical or explanatory requests (e.g., 'explain', 'analyze', 'summarize', 'compare', 'show insights').\n\n"
        "- Use 'rag' if the query needs factual or domain-specific information that is not directly about sales data\n"
        "  and not already answered — meaning a knowledge base lookup or document search is needed.\n\n"
        "- Use 'answer' if you can confidently respond directly using general knowledge, reasoning, or context,\n"
        "  without needing external data or retrieval.\n\n"
    )



    messages = [SystemMessage(content= system_prompt)] + state["messages"]
    result: RouteDecisionModel = router_llm.invoke(messages)

    out = {"messages": state["messages"], "route": result.route}

    if result.route == "end":
        out["messages"] = state["messages"] + [AIMessage(content=result.reply or "Hello!")]

    return out

# Node 2: RAG lookup
def rag_node(state: AgentState) -> AgentState:
    query = next((m.content for m in reversed(state["messages"])
                    if isinstance(m, HumanMessage)), "")

    chunks = rag_search_tool.invoke({"user_query": query, "session_id": state["session_id"]})

    # Use structured output to judge if RAG results are sufficient
    judge_messages = [
        ("system", (
            "You are a judge evaluating if the retrieved information is sufficient "
            "to answer the user's question. Consider both relevance and completeness."
        )),
        ("user", f"Question: {query}\n\nRetrieved info: {chunks}\n\nIs this sufficient to answer the question?")
    ]

    verdict: RagJudgeModel = judge_llm.invoke(judge_messages)

    return {
        **state,
        "rag": chunks,
        "route": "answer" if verdict.sufficient else "web"
    }

# Node 3: Web search
def web_node(state: AgentState) -> AgentState:
    query = next((m.content for m in reversed(state["messages"])
                  if isinstance(m, HumanMessage)), "")
    snippets = web_search_tool.invoke({"query": query})
    return {**state, "web": snippets, "route": "answer"}


# Node 4: Sql analyst node
def analyst_node(state: AgentState) -> AgentState:
    query = next((m.content for m in reversed(state["messages"])
                  if isinstance(m, HumanMessage)), "")

    output = sql_analyst_tool.invoke({"user_question": query})
    return {**state, "analyst": output, "route": "answer"}


# Node 5: Final answer
def answer_node(state: AgentState) -> AgentState:
    user_q = next((m.content for m in reversed(state["messages"])
                   if isinstance(m, HumanMessage)), "")
    
    ctx_parts = []

    if state.get("rag"):
        ctx_parts.append("Knowledge Base Information:\n" + state["rag"])
    if state.get("web"):
        ctx_parts.append("Web Search Results:\n" + state["web"])

    context = "\n\n".join(ctx_parts) if ctx_parts else "No external context available."

    if state.get("analyst"):
        context = "Analyst Results:\n" + str(state["analyst"])

    prompt = f"""Please answer the user's question using the provided context.

                Question: {user_q}

                Context:
                {context}

                Provide a helpful, accurate, and concise response based on the available information."""
    
    messages = state["messages"] + [HumanMessage(content=prompt)]
    ans = answer_llm.invoke(messages).content

    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=ans)]
    }
    

    


