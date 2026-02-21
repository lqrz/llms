"""Main."""

import asyncio
from collections import defaultdict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from llms.agent.basic_agent import build_basic_graph
from llms.commons.logger import logger
from llms.backend.routes.agent import router as agent_router
from llms.backend.routes.server import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        # app.state.graph = build_graph()
        logger.info("Building basic graph inside lifespan.")
        app.state.graph = build_basic_graph()
        app.state.thread_locks = defaultdict(asyncio.Lock)
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

# include routes
app.include_router(agent_router)
app.include_router(health_router)


@app.get("/")
def root():
    return {"Hello": "World"}
