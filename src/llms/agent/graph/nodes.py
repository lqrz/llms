"""Nodes."""

from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from llama_index.core.schema import NodeWithScore
from llama_index.core.vector_stores import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
    FilterCondition,
)
from typing import Dict, Any, List

from llms.agent.graph.state import BasicState, SafeguardResult, RagState, RetrievalPlan
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


def make_node_plan_retrieval(llm):
    """Make retrieval plan node."""

    def plan_retrieval(state: RagState):
        """Retrieval plan."""
        prompt = """You are a retrieval planning assistant for SEC filing RAG.

        Extract a retrieval plan from the user's question.

        Rules:
        - Only fill fields when supported by the query.
        - Keep query concise and retrieval-oriented.
        - Use content_type="table_row" for precise numeric / line-item / financial value questions.
        - Use content_type="table_full" when the user asks to show or inspect an entire table/statement.
        - Use content_type="text" for narrative, explanation, discussion, risks, qualitative sections.
        - Use mode="filtered" when the query clearly specifies company / ticker / filing period / section.
        - Otherwise use mode="broad".
        - Do not invent section headers.
        - If the query names a section explicitly, place it in header_1 or header_2 as appropriate.
        - Years should be 4-digit strings like "2022".
        - Quarters should be strings like "Q1", "Q2", "Q3", "Q4".
        """

        prompt_template = ChatPromptTemplate([("system", prompt), ("human", "{query}")])

        query: str = state["user_query"]
        chain = prompt_template | llm
        plan: RetrievalPlan = chain.invoke({"query": query})

        return {"retrieval_plan": plan}

    return plan_retrieval


def build_filters_from_plan(plan: RetrievalPlan) -> MetadataFilters | None:
    """Build metadata filters from retrieval plan."""
    filters: list[MetadataFilter] = []

    if plan.ticker:
        filters.append(
            MetadataFilter(
                key="ticker",
                operator=FilterOperator.EQ,
                value=plan.ticker,
            )
        )

    if plan.company:
        filters.append(
            MetadataFilter(
                key="company",
                operator=FilterOperator.EQ,
                value=plan.company,
            )
        )

    if plan.year:
        filters.append(
            MetadataFilter(
                key="year",
                operator=FilterOperator.EQ,
                value=plan.year,
            )
        )

    if plan.quarter:
        filters.append(
            MetadataFilter(
                key="quarter",
                operator=FilterOperator.EQ,
                value=plan.quarter,
            )
        )

    if plan.content_type:
        filters.append(
            MetadataFilter(
                key="content_type",
                operator=FilterOperator.EQ,
                value=plan.content_type,
            )
        )

    if plan.header_1:
        filters.append(
            MetadataFilter(
                key="header_1",
                operator=FilterOperator.EQ,
                value=plan.header_1,
            )
        )

    if plan.header_2:
        filters.append(
            MetadataFilter(
                key="header_2",
                operator=FilterOperator.EQ,
                value=plan.header_2,
            )
        )

    if not filters:
        return None

    return MetadataFilters(
        filters=filters,
        condition=FilterCondition.AND,
    )


def build_filters_from_plan_node(state: RagState):
    """Build filters from retrieval plan."""
    plan: RetrievalPlan = state["retrieval_plan"]
    metadata_filters: MetadataFilters = build_filters_from_plan(plan=plan)

    return {"metadata_filters": metadata_filters}


def make_node_retrieve(
    vector_store: VectorStore,
    top_k_each: int,
    top_k_final: int,
    alpha: float,
):
    """Retrieve node factory."""

    def retrieve(state: RagState) -> Dict[str, Any]:
        """Retrieve."""
        metadata_filters = state["metadata_filters"]
        nodes: List[NodeWithScore] = vector_store.run_hybrid_search(
            query=state["user_query"],
            top_k_each=top_k_each,
            top_k_final=top_k_final,
            alpha=alpha,
            metadata_filters=metadata_filters,
        )
        return {"retrieved_nodes": nodes}

    return retrieve


def generate_response_with_retrieval(state: RagState) -> Dict[str, Any]:
    """Generate response with retrieval."""
    system_prompt = """Your name is Richard. You are a financial assistant.

    Use only the provided context to answer the user's query.
    If the context is insufficient to answer confidently, say so clearly.

    Requirements:
    1. Cite supporting sources inline using numeric citations like [1], [2], [3].
    2. Every factual claim derived from the context should be supported by one or more citations.
    3. At the end of the response, add a section titled 'Sources'.
    4. In the 'Sources' section, list every citation used in the answer.
    5. For each citation, include:
    - the citation number
    - a short human-readable description of the source
    - any useful metadata available from the context, such as document name, company, year, quarter, page number, or section
    6. Do not invent source details. Only use metadata that is actually present in the provided context.
    7. If multiple chunks come from the same underlying document, you may still list them separately if they support different claims, or merge them if the citation refers to the same source location.

    Output format:
    - First provide the answer with inline citations.
    - Then provide:

    Sources:
    [1] <short description of source 1>
    [2] <short description of source 2>
    ...

    Example:
    Amazon reported revenue growth in the quarter [1].

    Sources:
    [1] Amazon 2022 Q3 filing, page 12, section 'Net Sales'
    """
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
