"""Basic agent."""

from typing import TypedDict, Annotated, List
from dotenv import load_dotenv
from langgraph.graph import add_messages, StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import SystemMessage, HumanMessage

from src.models.factory import ModelFactory
from src.models.providers.provider import Provider

provider: Provider = ModelFactory.get_llm()
checkpointer = InMemorySaver()

load_dotenv()


class BasicState(TypedDict):
    """BasicState."""

    messages: Annotated[List, add_messages]


def generate_response(state: BasicState):
    """Generate response."""
    prompt = """Your name is Richard. You are a financial assistant.
    Whatever is asked to you, you only reply in short sentences; 2 sentences tops."""
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=f"Query: {state["messages"]}"),
    ]
    response = provider.llm.invoke(messages)
    return {"messages": response}


def build_basic_graph():
    """Build basic graph."""
    workflow = StateGraph(BasicState)
    workflow.add_node("generate_response", generate_response)
    workflow.add_edge("generate_response", END)
    workflow.set_entry_point("generate_response")

    # with short term memory
    return workflow.compile(checkpointer=checkpointer)

    # without short term memory
    # return workflow.compile()
