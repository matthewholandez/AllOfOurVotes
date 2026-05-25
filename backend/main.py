"""FastAPI entry point.

On startup, the lifespan handler ensures the schema exists and seeds the
database from `out/*.csv` if it's empty. The CSVs are produced by
`scripts/seed-db-from-undl.py` — the lifespan re-runs that script if `out/`
is missing.

Run: `uv run uvicorn main:app --reload`
"""

import os
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path

import asyncpg
from fastapi import FastAPI
from routers import countries, resolutions

BACKEND_DIR = Path(__file__).parent
SCHEMA_FILE = BACKEND_DIR / "schema.sql"
OUT_DIR = BACKEND_DIR / "out"
INGEST_SCRIPT = BACKEND_DIR / "scripts" / "seed-db-from-undl.py"

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/allofourvotes"
)

# (table, csv filename). Order matters for FKs.
SEED_TABLES = [
    ("countries",           "countries.csv"),
    ("country_names",       "country_names.csv"),
    ("subjects",            "subjects.csv"),
    ("resolutions",         "resolutions.csv"),
    ("votes",               "votes.csv"),
    ("resolution_subjects", "resolution_subjects.csv"),
]


async def ensure_schema(conn) -> None:
    await conn.execute(SCHEMA_FILE.read_text())


async def is_seeded(conn) -> bool:
    return (await conn.fetchval("SELECT EXISTS (SELECT 1 FROM countries)")) is True


def ensure_csvs() -> None:
    missing = [
        OUT_DIR / fname for _, fname in SEED_TABLES if not (OUT_DIR / fname).exists()
    ]
    if not missing:
        return
    print(f"out/ missing {len(missing)} files; running ingest script…")
    subprocess.run(
        ["python", str(INGEST_SCRIPT)], cwd=BACKEND_DIR, check=True
    )


async def seed(conn) -> None:
    ensure_csvs()
    for table, fname in SEED_TABLES:
        path = OUT_DIR / fname
        with path.open("rb") as f:
            await conn.copy_to_table(
                table, source=f, format="csv", header=True, null=""
            )
        count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
        print(f"  seeded {table}: {count} rows")
    # subjects.id is SERIAL; bump the sequence past the values we just inserted.
    await conn.execute(
        "SELECT setval(pg_get_serial_sequence('subjects', 'id'), "
        "(SELECT COALESCE(MAX(id), 1) FROM subjects))"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    async with pool.acquire() as conn:
        await ensure_schema(conn)
        if await is_seeded(conn):
            print("DB already seeded; skipping bulk load.")
        else:
            print("DB empty; seeding from out/…")
            async with conn.transaction():
                await seed(conn)
            print("Seed complete.")
    app.state.db = pool
    try:
        yield
    finally:
        await pool.close()


app = FastAPI(title="AllOfOurVotes API", lifespan=lifespan)
app.include_router(countries.router)
app.include_router(resolutions.router)


@app.get("/health")
async def health():
    async with app.state.db.acquire() as conn:
        ok = await conn.fetchval("SELECT 1")
    return {"status": "ok" if ok == 1 else "degraded"}
