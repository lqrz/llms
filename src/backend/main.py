"""Main."""

import asyncio
from collections import defaultdict
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.agent.graph import graph_invoke
from src.agent.basic_agent import build_basic_graph
from src.backend.schemas.invoke_request import InvokeRequest
from src.backend.schemas.invoke_response import InvokeResponse
from src.commons.logger import logger

thread_locks = defaultdict(asyncio.Lock)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # app.state.graph = build_graph()
        logger.info("Building basic graph inside lifespan.")
        app.state.graph = build_basic_graph()
        yield
    except Exception as e:
        logger.error(f"Could not build graph: {e}")
    finally:
        app.state.graph = None


app = FastAPI(title="Financial agentic RAG backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in prod
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"Hello": "World"}


@app.post("/invoke")
async def invoke(req: InvokeRequest, request: Request) -> InvokeResponse:
    """Invoke."""
    message: str = req.message
    metadata: Dict[str, Any] = req.metadata
    thread_id: str = req.thread_id

    logger.info(
        f"Received request with message={message} thread_id={thread_id} metadata={metadata}"
    )

    if thread_id is None or not isinstance(thread_id, str):
        raise HTTPException(status_code=400, detail="Thread id must be of type str.")

    lock = thread_locks[thread_id]

    if lock.locked():
        _ = logger.error(
            f"Received multiple requests for the same thread_id={thread_id}"
        )
        raise HTTPException(status_code=400, detail="Thread is busy.")

    async with lock:
        _ = logger.info("Invoking graph")
        answer, raw_result, previous_state, new_state = await graph_invoke(
            graph=request.app.state.graph,
            message=message,
            thread_id=thread_id,
            metadata=metadata,
        )

        logger.info(f"--------- Previous state: {previous_state}")
        logger.info(f"--------- New state: {new_state}")

        _ = logger.info("Building response")
        response = InvokeResponse(thread_id=thread_id, answer=answer, raw={})

        return response
