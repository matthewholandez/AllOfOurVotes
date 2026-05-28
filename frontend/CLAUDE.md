# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- `npm run dev` — start Vite dev server (also runnable from the repo root via `mprocs`, which boots backend + frontend together).
- `npm run build` — production build (SvelteKit + `adapter-auto`; Vercel is the deploy target).
- `npm run preview` — preview the production build locally.

There is no test runner, linter, or formatter configured in this package.

Node version is pinned to `20.x` (`package.json` engines).

## Architecture

SvelteKit (Svelte 5, using `$props`/runes) site that visualizes UN voting data. It is a pure presentation layer — it owns no data, only fetches from the backend API.

### Backend connection

All API calls go through the relative path `/api`, routed differently per environment:

- **Dev**: `vite.config.js` proxies `/api/*` → `http://localhost:8000` (the FastAPI backend; `mprocs.yaml` at the repo root starts both together).
- **Prod**: `vercel.json` rewrites `/api/:path*` → `https://allofourvotes.vercel.app/:path*`.

Because the path is always relative, the same `api()` helper works for SSR loaders and browser fetches. `src/lib/api.js` is the only place that should talk to the backend; route `+page.js` loaders call it with SvelteKit's injected `fetch` so SSR-side requests are deduped/serialized correctly.

### Route shape

Routes follow the data model exposed by the backend:

- `/countries`, `/countries/[ms_code]` — keyed by UN member-state code.
- `/resolutions`, `/resolutions/[undl_id]` — keyed by UN Digital Library ID.
- `/subjects`, `/subjects/[id]`.
- `/methodology`, `/privacy` — static content.

Each list/detail page has a `+page.js` loader that calls `api(...)` and a `+page.svelte` that renders the result. Shared layout (`Nav`, `Footer`) and global styles (`src/app.css`) live in `+layout.svelte`.

### Presentation conventions (carry from root CLAUDE.md)

The backend keeps raw values; the frontend handles all presentation:

- Vote codes from the API are single letters `Y`/`N`/`A`/`X` — use `VOTE_LABEL` in `src/lib/api.js` to humanize.
- Tallies use the `Y–N–A` format (`tallyText`); outcomes (`Adopted`/`Rejected`/`Tied`) are derived client-side via `outcomeLabel`.
- Dates from the API are ISO strings; format with `fmtDate`/`fmtYear` (UTC-safe, avoid `new Date(iso)` directly to dodge timezone shifts).
- Country names are time-ranged at the data layer — don't assume a country has one canonical name; render whatever the API returns for the relevant period.

### JS, not TS

`jsconfig.json` extends SvelteKit's generated tsconfig with `allowJs` + `checkJs: false`. Source is plain JS with JSDoc type annotations (see `src/lib/api.js`). Keep that style — don't introduce `.ts` files without reason.
