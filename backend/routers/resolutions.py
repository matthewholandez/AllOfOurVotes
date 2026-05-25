from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

router = APIRouter(tags=["resolutions"])


class ResolutionSummary(BaseModel):
    undl_id: int
    resolution_code: str | None
    vote_date: date
    body: str
    title: str | None
    total_yes: int | None
    total_no: int | None
    total_abstentions: int | None
    total_non_voting: int | None
    total_ms: int | None


class ResolutionPage(BaseModel):
    total: int
    items: list[ResolutionSummary]


class SubjectRef(BaseModel):
    id: int
    name: str


class VoteRecord(BaseModel):
    ms_code: str
    country_name: str | None
    vote: str
    permanent_member: bool | None
    vote_note: str | None


class ResolutionDetail(BaseModel):
    undl_id: int
    resolution_code: str | None
    vote_date: date
    body: str
    session: int | None
    title: str | None
    agenda: str | None
    drafts: list[str]
    committee_report: str | None
    meeting: str | None
    modality: str | None
    vote_note: str | None
    total_yes: int | None
    total_no: int | None
    total_abstentions: int | None
    total_non_voting: int | None
    total_ms: int | None
    undl_link: str | None
    subjects: list[SubjectRef]
    votes: list[VoteRecord]


class SubjectSummary(BaseModel):
    id: int
    name: str


@router.get("/resolutions", response_model=ResolutionPage)
async def list_resolutions(
    request: Request,
    body: Annotated[str | None, Query(pattern="^(GA|SC)$")] = None,
    from_date: date | None = None,
    to_date: date | None = None,
    subject_id: int | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    conditions: list[str] = []
    params: list = []

    def add(clause: str, value) -> None:
        params.append(value)
        conditions.append(clause.replace("?", f"${len(params)}"))

    if body:
        add("r.body = ?", body)
    if from_date:
        add("r.vote_date >= ?", from_date)
    if to_date:
        add("r.vote_date <= ?", to_date)
    if subject_id is not None:
        add(
            "EXISTS (SELECT 1 FROM resolution_subjects rs WHERE rs.undl_id = r.undl_id AND rs.subject_id = ?)",
            subject_id,
        )

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    base_sql = f"FROM resolutions r {where}"

    async with request.app.state.db.acquire() as conn:
        total = await conn.fetchval(f"SELECT COUNT(*) {base_sql}", *params)
        n = len(params)
        rows = await conn.fetch(
            f"""
            SELECT undl_id, resolution_code, vote_date, body, title,
                   total_yes, total_no, total_abstentions, total_non_voting, total_ms
            {base_sql}
            ORDER BY vote_date DESC
            LIMIT ${n + 1} OFFSET ${n + 2}
            """,
            *params + [limit, offset],
        )
    return {"total": total, "items": [dict(r) for r in rows]}


@router.get("/resolutions/{undl_id}", response_model=ResolutionDetail)
async def get_resolution(undl_id: int, request: Request):
    async with request.app.state.db.acquire() as conn:
        res = await conn.fetchrow(
            "SELECT * FROM resolutions WHERE undl_id = $1", undl_id
        )
        if res is None:
            raise HTTPException(status_code=404, detail="Resolution not found")

        subjects = await conn.fetch(
            """
            SELECT s.id, s.name
            FROM subjects s
            JOIN resolution_subjects rs ON rs.subject_id = s.id
            WHERE rs.undl_id = $1
            ORDER BY s.name
            """,
            undl_id,
        )
        votes = await conn.fetch(
            """
            SELECT v.ms_code, cn.name AS country_name, v.vote, v.permanent_member, v.vote_note
            FROM votes v
            LEFT JOIN LATERAL (
                SELECT name FROM country_names cn
                WHERE cn.ms_code = v.ms_code
                  AND $2::date >= cn.valid_from
                  AND ($2::date < cn.valid_to OR cn.valid_to IS NULL)
                ORDER BY cn.valid_from DESC
                LIMIT 1
            ) cn ON true
            WHERE v.undl_id = $1
            ORDER BY v.ms_code
            """,
            undl_id,
            res["vote_date"],
        )

    return {
        **dict(res),
        "drafts": res["drafts"] or [],
        "subjects": [dict(s) for s in subjects],
        "votes": [dict(v) for v in votes],
    }


@router.get("/subjects", response_model=list[SubjectSummary])
async def list_subjects(request: Request):
    async with request.app.state.db.acquire() as conn:
        rows = await conn.fetch("SELECT id, name FROM subjects ORDER BY name")
    return [dict(r) for r in rows]
