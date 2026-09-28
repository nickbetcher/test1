from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app import api, web
from app.config import get_settings
from app.db import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Fine for a small service. A larger one would run Alembic migrations as a
    # separate deploy step instead of creating tables on startup.
    Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="Application Registry",
    version="0.1.0",
    description="Internal registry of applications. Humans use the web UI; "
    "agents and automation use the REST API documented here.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.include_router(api.router)
app.include_router(web.router)


@app.get("/healthz", tags=["ops"])
def healthz():
    """Liveness probe: the process is up."""
    return {"status": "ok"}


@app.get("/readyz", tags=["ops"])
def readyz():
    """Readiness probe: the database is reachable."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ready", "environment": get_settings().environment}
