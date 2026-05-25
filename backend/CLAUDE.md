# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Monorepo context and project intent live in the root `CLAUDE.md`; this file covers the ingest pipeline only.

## Commands

Python 3.12+, dependencies managed by `uv` (see `uv.lock`).

```bash
uv sync                                       # install deps into .venv
uv run python scripts/seed-db-from-undl.py    # regenerate out/ CSVs
uv run uvicorn main:app --reload              # run FastAPI app (auto-seeds DB on first start)
```

The ingest script must be invoked from `backend/` — paths are resolved against `Path.cwd()`. `uvicorn` should also be run from `backend/` (the lifespan resolves `out/` and `scripts/` relative to `main.py`'s parent).

`DATABASE_URL` env var configures the DB connection (default: `postgresql://postgres:postgres@localhost:5432/allofourvotes`).

## App lifespan / seeding

`main.py` defines a FastAPI app whose lifespan handler:

1. Creates an asyncpg pool and applies `schema.sql` (uses `CREATE … IF NOT EXISTS` so re-runs are safe).
2. Checks if `countries` has any rows. If yes, skips seeding entirely.
3. If empty: re-runs the ingest script when `out/*.csv` is missing, then `COPY`s each CSV in FK-safe order inside a single transaction, and bumps the `subjects.id` sequence past the surrogate ids we just loaded.

The schema lives in `schema.sql` (source of truth for DDL). The script docstring duplicates it for context but `schema.sql` is what runs. Keep them in sync if you change tables.

## Ingest architecture

`scripts/seed-db-from-undl.py` is the entire pipeline. It reads three CSVs from `data/undl/` and writes six Postgres-ready CSVs to `out/`. Critical invariants:

- **No DB or network I/O.** Outputs are files only; loading is a separate `psql \copy` step (load order documented in the script). Don't add a DB driver dependency here.
- **Idempotent.** Each output is sorted by primary key and re-running must produce byte-identical files. Any new field must preserve this — if you introduce dict iteration that affects output ordering, sort it.
- **Skipped rows are logged, never silently dropped.** All validation failures go to `out/skipped.log` as `<source_file>:<line>:<reason>`.

### Historical country names (non-obvious)

The UN vote CSVs tag every vote with the *modern* ISO code (e.g. all USSR votes 1945–1991 are tagged `SUN`, all Upper Volta votes 1960–1984 are tagged `BFA`). Country names are time-ranged in `country_names`, NOT stored on `countries` (which is just a `ms_code` FK anchor). To resolve a name at vote time:

```sql
SELECT name FROM country_names
WHERE ms_code = $1
  AND $2::date BETWEEN valid_from AND COALESCE(valid_to, 'infinity');
```

The auth file (`member_states_auths_*.csv`) is the source of historical ranges. `parse_auths()` does union-find on the `Earlier or Later Name` chain so historical-only ISO codes (e.g. `HVO` Upper Volta) get reattributed to the modern code in vote data (`BFA`). When a chain has multiple modern codes (e.g. UAR overlaps both EGY and SYR), the algorithm bails out and leaves the historical row under its own code — this produces a known ~250-vote coverage gap (EGY during the 1958–1971 UAR period plus admission-boundary edge cases). It's logged, not fatal.

Two ISO codes (`GER`, `SCG`) appear in vote data but not the auth file. They're hard-coded in `FALLBACK_NAME_SEGMENTS` at the top of the script.

### Other transformations worth knowing

- `drafts` field is pipe-delimited in source, emitted as a Postgres array literal `{a,b,c}`.
- `subjects` are deduped globally into a surrogate-key table; `resolution_subjects` is the junction.
- SC `permanent_member` is forced to `True` for the P5 (`USA, CHN, RUS, FRA, GBR`) regardless of source value — this lets `vote='N' AND permanent_member=true` serve as the veto predicate.
- GA totals come as floats (`159.0`), SC as ints — both go through `to_int_or_none` which handles both.
- Empty cells become SQL `NULL` (empty CSV field), never `0` or `""`.

## Data layout

- `data/undl/` — source CSVs (GA votes, SC votes, member-state authorities). Inputs only, never written.
- `out/` — generated; safe to delete and regenerate.
