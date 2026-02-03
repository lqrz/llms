"""Nodes."""

from langchain_core.messages import SystemMessage, HumanMessage

from src.agent.state import BasicState
from src.agent.llm import LLM


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
