"""Basic agent."""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from typing import List
import os

from llms.agent.graph.state import BasicState, RagState
from llms.agent.graph.nodes import (
    safeguard_request,
    safeguard_request_reject,
    generate_response,
    make_node_retrieve,
    generate_response_with_retrieval,
)
from llms.agent.graph.edges import safeguard_request_router
from llms.agent.rag.vector_store import VectorStore
from llms.commons.logger import logger


CHECKPOINTER = InMemorySaver()


def build_basic_graph(is_use_short_term_memory: bool = True, **kwargs):
    """Build basic graph."""
    workflow = StateGraph(BasicState)
    workflow.add_node("safeguard_request", safeguard_request)
    workflow.add_node("safeguard_request_reject", safeguard_request_reject)
    workflow.add_node("generate_response", generate_response)
    workflow.add_conditional_edges(
        "safeguard_request",
        safeguard_request_router,
        {
            True: "generate_response",
            False: "safeguard_request_reject",
        },
    )
    workflow.add_edge("safeguard_request_reject", END)
    workflow.add_edge("generate_response", END)
    workflow.set_entry_point("safeguard_request")

    # short term memory
    checkpointer = CHECKPOINTER if is_use_short_term_memory else None

    return workflow.compile(checkpointer=checkpointer)


def build_rag_graph(
    collection_name: str,
    top_k_each: int,
    top_k_final: int,
    alpha: float,
    embeddings_model_name: str = "BAAI/bge-small-en-v1.5",
    is_hybrid_search: bool = True,
    metadata_filters: List = [],
    is_use_short_term_memory: bool = True,
    **kwargs,
):
    """Build rag graph."""
    workflow = StateGraph(RagState)

    logger.info(f"Instantiating embeddings model {embeddings_model_name}")
    embeddings_model = HuggingFaceEmbedding(model_name=embeddings_model_name)

    vector_db_url: str = os.getenv("VECTOR_DB_URL")

    if vector_db_url is None:
        raise Exception("No VECTOR_DB_URL")

    logger.info(
        f"Instantiating vector store with url={vector_db_url} collection={collection_name}"
    )
    vector_store = VectorStore(
        url=vector_db_url,
        collection_name=collection_name,
        embeddings_model=embeddings_model,
        is_recreate_collection=False,
        is_hybrid=is_hybrid_search,
    )

    workflow.add_node("safeguard_request", safeguard_request)
    workflow.add_node("safeguard_request_reject", safeguard_request_reject)
    workflow.add_node(
        "retrieve",
        make_node_retrieve(
            vector_store=vector_store,
            metadata_filters=metadata_filters,
            top_k_each=top_k_each,
            top_k_final=top_k_final,
            alpha=alpha,
        ),
    )
    workflow.add_node("generate_response", generate_response_with_retrieval)

    workflow.add_conditional_edges(
        "safeguard_request",
        safeguard_request_router,
        {
            True: "retrieve",
            False: "safeguard_request_reject",
        },
    )

    workflow.add_edge("retrieve", "generate_response")
    workflow.add_edge("safeguard_request_reject", END)
    workflow.add_edge("generate_response", END)

    workflow.set_entry_point("safeguard_request")

    # short term memory
    checkpointer = CHECKPOINTER if is_use_short_term_memory else None

    return workflow.compile(checkpointer=checkpointer)
