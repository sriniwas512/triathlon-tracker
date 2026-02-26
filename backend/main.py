"""
Triathlon Competition Tracker — FastAPI Application
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import FRONTEND_URL, BACKEND_URL
from services.block_service import seed_blocks, seed_players
from routers import auth, players, activities, scores
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: seed blocks and players + logging configuration."""
    print("--- Startup Configuration ---")
    print(f"FRONTEND_URL: {FRONTEND_URL}")
    print(f"BACKEND_URL: {BACKEND_URL}")
    print(f"API_BASE_URL (env): {os.getenv('API_BASE_URL')}")
    print("-----------------------------")
    
    seed_blocks()
    seed_players()
    yield


app = FastAPI(
    title="Triathlon Competition Tracker",
    description="March 2026 Triathlon Challenge Backend",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
# Only use the configured FRONTEND_URL (which defaults to localhost for dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
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
