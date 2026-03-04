"""Nodes."""

from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from llama_index.core.schema import NodeWithScore
from typing import Dict, Any, List

from llms.agent.graph.state import BasicState, SafeguardResult, RagState
from llms.agent.llm import LLM
from llms.agent.rag.vector_store import VectorStore


def safeguard_request(state: BasicState) -> Dict[str, Any]:
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


def safeguard_request_reject(state: BasicState) -> Dict[str, Any]:
    response: str = (
        """I can help with financial topics only. Can you rephrase your question to be finance-related?"""
    )
    return {
        "answer": response,
        "messages": AIMessage(content=response, additional_kwargs={"public": True}),
    }


def get_public_history(state: BasicState) -> List[BaseMessage]:
    """Get public history."""
    return list(
        filter(lambda x: x.additional_kwargs.get("public", False), state["messages"])
    )


def generate_response(state: BasicState) -> Dict[str, Any]:
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


def make_node_retrieve(
    vector_store: VectorStore,
    top_k_each: int,
    top_k_final: int,
    alpha: float,
    metadata_filters: List = [],
):
    """Retrieve node factory."""

    def retrieve(state: RagState) -> Dict[str, Any]:
        """Retrieve."""
        nodes: List[NodeWithScore] = vector_store.run_hybrid_search(
            query=state["user_query"],
            top_k_each=top_k_each,
            top_k_final=top_k_final,
            alpha=alpha,
            metadata_filters=metadata_filters,
        )
        return {
            "retrieved_nodes": nodes,
        }

    return retrieve


def generate_response_with_retrieval(state: RagState) -> Dict[str, Any]:
    """Generate response with retrieval."""
    system_prompt = """Your name is Richard. You are a financial assistant.
    Use the provided context to reply to the user query.
    If the context is insufficient, say so.
    Cite sources like [1], [2], ..."""
    context_prompt = """Context from the knowledge base:
    {context}
    """
    prompt_template = ChatPromptTemplate(
        [
            ("system", system_prompt),
            MessagesPlaceholder("history"),
            ("system", context_prompt),  # best for grounding.
            ("human", "{query}"),
        ]
    )
    chain = prompt_template | LLM
    context: str = VectorStore.format_nodes_for_prompt(nodes=state["retrieved_nodes"])
    public_history: List[BaseMessage] = get_public_history(state=state)
    history: List[BaseMessage] = public_history[:-1]
    query: HumanMessage = public_history[-1]
    response: AIMessage = chain.invoke(
        {"history": history, "context": context, "query": query}
    )
    response.additional_kwargs = {**response.additional_kwargs, **{"public": True}}
    return {"answer": response.content, "messages": response}
