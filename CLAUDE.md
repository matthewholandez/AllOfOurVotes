# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Monorepo layout

- **`backend/`** — Python 3.12, managed by `uv`. Per the root README this is meant to host a FastAPI + PostgreSQL service, but at the moment the only working code is an offline ingest pipeline that turns UN Digital Library CSV exports into Postgres-loadable files. `backend/main.py` is a placeholder. See `backend/CLAUDE.md` for ingest internals.
- **`frontend/`** — Svelte/SvelteKit data-visualization site (the public surface at allofourvotes.org).

The two halves are decoupled: the backend currently produces files on disk, and the eventual API + the frontend consume them independently. There is no shared schema package or generated client yet.

## Project intent

AllOfOurVotes.org surfaces how UN member states vote on resolutions. Source-of-truth is the UN Digital Library — the project does not re-derive vote data, only ingests, normalizes, and presents it. Two design consequences worth carrying into any new work:

- **Historical fidelity matters.** Country names, ISO codes, and political entities change over time (USSR/Russia, Zaire/DRC, Upper Volta/Burkina Faso, the UAR period). Don't flatten history — names are time-ranged at the data layer (`country_names`), not stored on `countries`.
- **The data layer keeps raw values; presentation lives in the frontend.** Vote codes stay as single letters (`Y`/`N`/`A`/`X`), country names stay in their source casing, and translations are not the backend's job.
