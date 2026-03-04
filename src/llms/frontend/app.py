"""Chainlit chat application - independent service that calls FastAPI backend."""

import os
import chainlit as cl
from chainlit.input_widget import Select, Slider
import httpx
import logging
from typing import Dict, Any

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:9000")
API_TIMEOUT = float(os.getenv("API_TIMEOUT", "300"))  # 5 min default


# @cl.set_starters
# async def set_starters():
#     return [
#         cl.Starter(
#             label="🔍 Analyze 10-Q Filings",
#             message="What are the key insights from the latest SEC 10-Q filings available?",
#         ),
#         cl.Starter(
#             label="⚖️ Compare Performance",
#             message="Compare the revenue and operating margins of major tech companies from their recent reports.",
#         ),
#         cl.Starter(
#             label="🛠️ Data Management",
#             message="/settings",
#         ),
#     ]


@cl.on_chat_start
async def start():
    """Initialize the chat session."""
    thread_id = cl.context.session.thread_id
    cl.user_session.set("thread_id", thread_id)

    # 2. Define Chat Settings (Real Settings Sidebar)
    settings = await cl.ChatSettings(
        [
            Select(
                id="WORKFLOW_TYPE",
                label="Workflow",
                values=["basic", "rag"],
                initial_index=0,
            ),
            Select(
                id="COLLECTION_NAME",
                label="Vector db collection",
                values=["data"],
                initial_index=0,
            ),
            Select(
                id="ALPHA",
                label="Alpha",
                values=["0.0", "0.5", "1.0"],
                initial_index=1,
                description="0.0 = Keyword (BM25), 1.0 = Semantic, 0.5 = Hybrid",
            ),
            Slider(
                id="TOP_K_EACH",
                label="Top k initial",
                initial=20,
                min=5,
                max=50,
                step=5,
                description="Number of documents to initially retrieved",
            ),
            Slider(
                id="TOP_K_FINAL",
                label="Top k final",
                initial=5,
                min=1,
                max=10,
                step=1,
                description="Number of documents to finally retrieved",
            ),
        ]
    ).send()
    cl.user_session.set("settings", settings)

    await cl.Message(content="### 📈 I'm your financial analyst").send()


# @cl.on_chat_start
# async def start():
#     """Initialize the chat session."""
#     thread_id = cl.context.session.thread_id
#     cl.user_session.set("thread_id", thread_id)

#     await cl.Message(
#         content="Hello! I'm your financial analysis assistant. Ask me questions about SEC 10-Q filings."
#     ).send()


@cl.on_message
async def main(message: cl.Message):
    """Process user messages by calling the FastAPI /invoke endpoint."""
    user_message = message.content
    thread_id = cl.user_session.get("thread_id")
    settings: Dict[str, Any] = cl.user_session.get("settings", dict())
    workflow_kwargs: Dict[str, Any] = {
        "collection_name": settings["COLLECTION_NAME"],
        "alpha": settings["ALPHA"],
        "top_k_each": settings["TOP_K_EACH"],
        "top_k_final": settings["TOP_K_FINAL"],
    }
    url: str = f"{API_BASE_URL}/agent/invoke"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={
                    "message": user_message,
                    "thread_id": thread_id,
                    "workflow_type": settings["WORKFLOW_TYPE"],
                    "workflow_kwargs": workflow_kwargs,
                    "metadata": {},
                },
                timeout=API_TIMEOUT,
            )
            response.raise_for_status()
            result = response.json()

        await cl.Message(content=result["answer"]).send()

    except httpx.HTTPStatusError as e:
        logging.error(e)
        error_detail = e.response.text if e.response else "Unknown error"
        await cl.Message(
            content=f"Error from backend: {e.response.status_code} - {error_detail}"
        ).send()
    except httpx.RequestError as e:
        logging.error(e)
        await cl.Message(
            content=f"Could not connect to backend service at {url}. Error: {e}."
        ).send()
    except Exception as e:
        logging.error(e)
        await cl.Message(content=f"An unexpected error occurred: {str(e)}").send()
