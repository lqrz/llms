"""Nodes."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage

from src.agent.state import BasicState, SafeguardResult
from src.agent.llm import LLM


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
