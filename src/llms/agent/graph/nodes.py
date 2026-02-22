"""Nodes."""

from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    AIMessagePromptTemplate,
)
from langchain_core.messages import AIMessage
from llama_index.core.schema import NodeWithScore
from typing import List

from llms.agent.graph.state import BasicState, SafeguardResult
from llms.agent.llm import LLM
from llms.agent.rag.vector_store import VectorStore


def safeguard_request(state: BasicState):
    """Apply safeguards."""
    prompt = """You are a financial assistant.
    You only reply to financial related questions. Nothing else.
    Your taks is to evaluate if the user request in backticks corresponds to a financial related matter.
    If the user request is about a financial topic set is_on_topic=True, otherwise set is_on_topic=False.
    Explain your decision. Reason must be under 20 words.
    Return ONLY the structured output.
    Request: ```{user_query}```"""
    prompt_template = ChatPromptTemplate([("system", prompt)])
    chain = prompt_template | LLM.with_structured_output(schema=SafeguardResult)
    response: SafeguardResult = chain.invoke({"user_query": state["user_query"]})
    return {
        "safeguard_result": response,
        "messages": AIMessage(
            content=f"Safeguard: {response}", additional_kwargs={"public": False}
        ),
    }


def safeguard_request_reject(state: BasicState):
    response: str = (
        """I can help with financial topics only. Can you rephrase your question to be finance-related?"""
    )
    return {
        "answer": response,
        "messages": AIMessage(content=response, additional_kwargs={"public": True}),
    }


def get_public_history(state: BasicState):
    """Get public history."""
    return list(
        filter(lambda x: x.additional_kwargs.get("public", False), state["messages"])
    )


def generate_response(state: BasicState):
    """Generate response."""
    prompt = """Your name is Richard. You are a financial assistant.
    Whatever is asked to you, you only reply in short sentences; 2 sentences tops."""
    prompt_template = ChatPromptTemplate(
        [
            ("system", prompt),
            MessagesPlaceholder("history"),
        ]
    )
    chain = prompt_template | LLM
    response: AIMessage = chain.invoke({"history": get_public_history(state=state)})
    response.additional_kwargs = {**response.additional_kwargs, **{"public": True}}
    return {"answer": response.content, "messages": response}


def retrieve(state: BasicState):
    """Retrieve."""
    nodes:List[NodeWithScore] = retriever.run_hybrid_search(
        query=state["user_query"],
        top_k_each: int,
        top_k_final: int,
        alpha: float,
        metadata_filters: List[MetadataFilters],
    )  # TODO: pass retriever & run search
    return {
        "retrieved_nodes": nodes,
    }


def generate_response_with_retrieval(state: BasicState):
    """Generate response with retrieval."""
    prompt = """Your name is Richard. You are a financial assistant.
    Use the provided context.
    If the context is insufficient, say so.
    Cite sources like [1], [2]."""
    prompt_template = ChatPromptTemplate(
        [
            ("system", prompt),
            MessagesPlaceholder("history"),
            AIMessagePromptTemplate("context"),  # TODO: should this be an AI msg?
        ]
    )
    chain = prompt_template | LLM
    context: str = VectorStore.format_nodes_for_prompt(nodes=state["retrieved_nodes"])
    response: AIMessage = chain.invoke(
        {
            "history": get_public_history(state=state),
            "context": context,
        }
    )
    response.additional_kwargs = {**response.additional_kwargs, **{"public": True}}
    return {"answer": response.content, "messages": response}
