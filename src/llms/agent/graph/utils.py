"""Graph."""

from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage
from typing import Dict, Any


async def graph_invoke(
    graph: StateGraph,
    message: str,
    thread_id: str,
    metadata: Dict[str, Any],
):
    config = {
        "configurable": {
            "thread_id": thread_id,
            **metadata,
        },
    }

    state = {
        "user_query": message,
        "messages": [HumanMessage(content=message, additional_kwargs={"public": True})],
    }

    # previous_state = {}
    previous_state = graph.get_state(config=config)

    result = await graph.ainvoke(state, config=config)

    # new_state = {}
    new_state = graph.get_state(config=config)

    answer = result["answer"]

    return answer, result, previous_state, new_state
