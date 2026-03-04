"""Agent routes."""

from fastapi import APIRouter
from fastapi import HTTPException, Request
from typing import Any, Dict
import os

from llms.agent.graph.utils import graph_invoke
from llms.backend.schemas.invoke_request import InvokeRequest
from llms.backend.schemas.invoke_response import InvokeResponse
from llms.agent.graph.graph_factory import GraphFactory
from llms.commons.logger import logger

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/invoke")
async def invoke(req: InvokeRequest, request: Request) -> InvokeResponse:
    """Invoke."""
    message: str = req.message
    metadata: Dict[str, Any] = req.metadata
    thread_id: str = req.thread_id
    workflow_type: str = req.workflow_type
    workflow_kwargs: Dict[str, Any] = dict(req.workflow_kwargs)

    logger.info(
        f"Received request with workflow_type={workflow_type} workflow_kwargs={workflow_kwargs} message={message} thread_id={thread_id} metadata={metadata}"
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
        _ = logger.info("Calling graph factory")
        graph = GraphFactory.instantiate_graph(
            workflow_type=workflow_type, **workflow_kwargs
        )

        _ = logger.info("Invoking graph")
        answer, _, previous_state, new_state = await graph_invoke(
            graph=graph,
            message=message,
            thread_id=thread_id,
            metadata=metadata,
        )

        logger.info(f"--------- Previous state: {previous_state}")
        logger.info(f"--------- New state: {new_state}")

        _ = logger.info("Building response")
        response = InvokeResponse(thread_id=thread_id, answer=answer, raw={})

        return response
