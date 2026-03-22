from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.engine import init_db, async_session
from app.api.router import api_router
from app.scenarios.loader import load_scenarios


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Auto-load scenarios from JSON files
    async with async_session() as db:
        loaded = await load_scenarios(db)
        if loaded:
            print(f"Loaded {loaded} scenarios into database")
    yield


app = FastAPI(
    title="When Agents Disagree",
    description="Multi-Agent Conflict Resolution Research Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "when-agents-disagree"}
