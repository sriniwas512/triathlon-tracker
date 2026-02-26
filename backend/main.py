"""
Triathlon Competition Tracker — FastAPI Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import PLAYER1_NAME, PLAYER2_NAME, FRONTEND_URL
from backend.services.block_service import seed_blocks, seed_players
from backend.routers import auth, players, activities, scores


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: seed blocks and players."""
    seed_blocks()
    seed_players([PLAYER1_NAME, PLAYER2_NAME])
    yield


app = FastAPI(
    title="Triathlon Competition Tracker",
    description="March 2026 Triathlon Challenge Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(players.router)
app.include_router(activities.router)
app.include_router(scores.router)


@app.get("/")
async def root():
    return {"message": "Triathlon Competition Tracker API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
