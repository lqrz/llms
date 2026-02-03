"""Basic agent."""

from typing import TypedDict, Annotated, List
from dotenv import load_dotenv
import os
from langgraph.graph import add_messages, StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI


checkpointer = InMemorySaver()

load_dotenv()

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
LLM_MODEL = "gpt-5-nano"
TEMPERATURE = 0.1


LLM = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model=LLM_MODEL,
    temperature=TEMPERATURE,
)


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
    response = LLM.invoke(messages)
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
