"""FastAPI entry point.

Seeding is a one-shot offline job (`scripts/seed-db-from-undl.py` + psql
`\\copy`); the runtime app assumes the schema and data are already in place.

Run: `uv run uvicorn main:app --reload`
"""

import os
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routers import countries, resolutions

# Data is updated only via offline re-seeds, so we can cache aggressively at
# Vercel's CDN. s-maxage is the CDN TTL; stale-while-revalidate lets the CDN
# serve a stale response while it refreshes in the background.
CACHE_CONTROL = "public, s-maxage=86400, stale-while-revalidate=604800"
NO_CACHE_PATHS = {"/health"}

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/allofourvotes"
)

# Comma-separated list of allowed frontend origins.
CORS_ORIGINS = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # statement_cache_size=0 is required when DATABASE_URL points at
    # Supabase's transaction pooler (port 6543, PgBouncer txn mode).
    pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=0,
        max_size=5,
        statement_cache_size=0,
    )
    app.state.db = pool
    try:
        yield
    finally:
        await pool.close()


app = FastAPI(title="AllOfOurVotes API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if (
        request.method == "GET"
        and response.status_code == 200
        and request.url.path not in NO_CACHE_PATHS
        and "cache-control" not in response.headers
    ):
        response.headers["Cache-Control"] = CACHE_CONTROL
        # Ensure the CDN keys cached entries by Origin so CORS responses
        # remain correct across allowed frontends.
        existing_vary = response.headers.get("Vary")
        response.headers["Vary"] = (
            f"{existing_vary}, Origin" if existing_vary else "Origin"
        )
    return response


app.include_router(countries.router)
app.include_router(resolutions.router)


@app.get("/health")
async def health():
    async with app.state.db.acquire() as conn:
        ok = await conn.fetchval("SELECT 1")
    return {"status": "ok" if ok == 1 else "degraded"}
