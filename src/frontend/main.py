"""Main."""

from fastapi import FastAPI
from chainlit.utils import mount_chainlit

app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "frontend"}


# Mount Chainlit UI + websocket under /
mount_chainlit(app=app, target="src/frontend/app.py", path="/")
