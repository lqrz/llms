"""Nodes."""

from langchain_core.messages import SystemMessage, HumanMessage

from src.agent.state import BasicState
from src.agent.llm import LLM


def safeguard_request(state: BasicState):
    """Apply safeguards."""
    prompt = f"""You are a financial assistant.
    You only reply to financial related questions. Nothing else.
    Your taks is to evaluate if the user request in backticks corresponds to a financial related matter.
    Format your response as a True or False value. Do not respond with more than one label.
    Request: ```{state["messages"][-1].content}```"""

    messages = [
        SystemMessage(content=prompt),
    ]
    response = LLM.invoke(messages)
    return {"is_safe_request": response}


def generate_response(state: BasicState):
    """Generate response."""
    prompt = """Your name is Richard. You are a financial assistant.
    Whatever is asked to you, you only reply in short sentences; 2 sentences tops."""
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"Query: {state["messages"]}"),
    ]
    response = LLM.invoke(messages)
    return {"messages": response}
