"""Chainlit chat application - independent service that calls FastAPI backend."""

import os
import chainlit as cl
import httpx

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "300"))  # 5 min default


@cl.on_chat_start
async def start():
    """Initialize the chat session."""
    thread_id = cl.context.session.thread_id
    cl.user_session.set("thread_id", thread_id)

    await cl.Message(
        content="Hello! I'm your financial analysis assistant. Ask me questions about SEC 10-Q filings."
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """Process user messages by calling the FastAPI /invoke endpoint."""
    user_message = message.content
    thread_id = cl.user_session.get("thread_id")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/invoke",
                json={
                    "message": user_message,
                    "thread_id": thread_id,
                    "metadata": {},
                },
                timeout=API_TIMEOUT,
            )
            response.raise_for_status()
            result = response.json()

        await cl.Message(content=result["answer"]).send()

    except httpx.HTTPStatusError as e:
        error_detail = e.response.text if e.response else "Unknown error"
        await cl.Message(
            content=f"Error from backend: {e.response.status_code} - {error_detail}"
        ).send()
    except httpx.RequestError:
        await cl.Message(
            content=f"Could not connect to backend service at {API_BASE_URL}. Please ensure the API is running."
        ).send()
    except Exception as e:
        await cl.Message(content=f"An unexpected error occurred: {str(e)}").send()
