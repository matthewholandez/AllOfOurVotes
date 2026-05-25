from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

router = APIRouter(prefix="/countries", tags=["countries"])


class CountrySummary(BaseModel):
    ms_code: str
    name: str | None
    m49_code: int | None


class NamePeriod(BaseModel):
    name: str
    valid_from: date
    valid_to: date | None


class CountryDetail(BaseModel):
    ms_code: str
    name: str | None
    m49_code: int | None
    name_history: list[NamePeriod]


class VoteItem(BaseModel):
    undl_id: int
    resolution_code: str | None
    vote_date: date
    body: str
    title: str | None
    vote: str
    permanent_member: bool | None


class VotePage(BaseModel):
    total: int
    items: list[VoteItem]


@router.get("", response_model=list[CountrySummary])
async def list_countries(request: Request):
    async with request.app.state.db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT c.ms_code, cn.name, cn.m49_code
            FROM countries c
            LEFT JOIN country_names cn
                ON cn.ms_code = c.ms_code AND cn.valid_to IS NULL
            ORDER BY cn.name NULLS LAST
            """
        )
    return [dict(r) for r in rows]


@router.get("/{ms_code}", response_model=CountryDetail)
async def get_country(ms_code: str, request: Request):
    ms_code = ms_code.upper()
    async with request.app.state.db.acquire() as conn:
        current = await conn.fetchrow(
            """
            SELECT cn.name, cn.m49_code
            FROM countries c
            LEFT JOIN country_names cn
                ON cn.ms_code = c.ms_code AND cn.valid_to IS NULL
            WHERE c.ms_code = $1
            """,
            ms_code,
        )
        if current is None:
            raise HTTPException(status_code=404, detail="Country not found")
        history = await conn.fetch(
            """
            SELECT name, valid_from, valid_to
            FROM country_names
            WHERE ms_code = $1
            ORDER BY valid_from
            """,
            ms_code,
        )
    return {
        "ms_code": ms_code,
        "name": current["name"],
        "m49_code": current["m49_code"],
        "name_history": [dict(r) for r in history],
    }


@router.get("/{ms_code}/votes", response_model=VotePage)
async def get_country_votes(
    ms_code: str,
    request: Request,
    body: Annotated[str | None, Query(pattern="^(GA|SC)$")] = None,
    vote: Annotated[str | None, Query(pattern="^[YNAX]$")] = None,
    from_date: date | None = None,
    to_date: date | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    ms_code = ms_code.upper()

    conditions = ["v.ms_code = $1"]
    params: list = [ms_code]

    def add(clause: str, value) -> None:
        params.append(value)
        conditions.append(clause.replace("?", f"${len(params)}"))

    if body:
        add("r.body = ?", body)
    if vote:
        add("v.vote = ?", vote)
    if from_date:
        add("r.vote_date >= ?", from_date)
    if to_date:
        add("r.vote_date <= ?", to_date)

    where = " AND ".join(conditions)
    base_sql = f"""
        FROM votes v
        JOIN resolutions r ON r.undl_id = v.undl_id
        WHERE {where}
    """

    async with request.app.state.db.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT EXISTS (SELECT 1 FROM countries WHERE ms_code = $1)", ms_code
        )
        if not exists:
            raise HTTPException(status_code=404, detail="Country not found")

        total = await conn.fetchval(f"SELECT COUNT(*) {base_sql}", *params)
        params_page = params + [limit, offset]
        n = len(params)
        rows = await conn.fetch(
            f"""
            SELECT v.undl_id, r.resolution_code, r.vote_date, r.body, r.title,
                   v.vote, v.permanent_member
            {base_sql}
            ORDER BY r.vote_date DESC
            LIMIT ${n + 1} OFFSET ${n + 2}
            """,
            *params_page,
        )
    return {"total": total, "items": [dict(r) for r in rows]}
