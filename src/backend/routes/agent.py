"""Agent routes."""

from fastapi import APIRouter
from fastapi import HTTPException, Request
from typing import Any, Dict

from agent.graph.utils import graph_invoke
from src.backend.schemas.invoke_request import InvokeRequest
from src.backend.schemas.invoke_response import InvokeResponse
from src.commons.logger import logger

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/invoke")
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

    lock = request.app.state.thread_locks[thread_id]

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
