"""Ingest UN Digital Library GA + SC voting CSVs into Postgres-ready files.

Outputs six CSVs to out/ ready for `psql \\copy`. Does not connect to Postgres.
Idempotent: same inputs produce byte-identical outputs.

Subjects are hierarchical. In the source `subjects` cell, `|` separates distinct
top-level topical references and `--` separates parent → subtopic levels within
a reference. We model this as a DAG: `subjects` holds globally-unique names,
and `subject_parents(child_id, parent_id)` is a many-to-many junction (REPORTS,
UN, RECOMMENDATIONS etc. legitimately appear under many parents). Each
|-separated reference links its leaf segment to the resolution in
`resolution_subjects`; ancestor queries use a recursive CTE.

Schema (countries holds only the FK anchor; country_names is the source of truth
for any human-readable name, time-ranged so historical votes resolve correctly):

    CREATE EXTENSION IF NOT EXISTS btree_gist;

    CREATE TABLE countries (
        ms_code CHAR(3) PRIMARY KEY
    );

    CREATE TABLE country_names (
        ms_code    CHAR(3) NOT NULL REFERENCES countries(ms_code),
        name       TEXT    NOT NULL,
        valid_from DATE    NOT NULL,
        valid_to   DATE,                  -- NULL = still current
        m49_code   INTEGER,
        PRIMARY KEY (ms_code, valid_from),
        EXCLUDE USING gist (
            ms_code WITH =,
            daterange(valid_from, COALESCE(valid_to, DATE 'infinity'), '[]') WITH &&
        )
    );

    -- Resolve a country's name at a given vote_date:
    --   SELECT name FROM country_names
    --   WHERE ms_code = $1
    --     AND $2::date BETWEEN valid_from AND COALESCE(valid_to, 'infinity');

Known coverage gap: votes recorded in the source CSVs under EGY for the
1958–1971 UAR period (and the small handful of admission-boundary cases like
ARE @ 1971-10-07, COM @ Nov 1975, DMA @ Nov–Dec 1978) won't resolve to a name,
because the UAR auth entry overlaps both EGY and SYR's name-chains and we
can't safely attribute it to one. Logged but not blocking.
"""

import csv
import datetime as dt
from pathlib import Path

UN_DL_DIR = Path.cwd() / "data" / "undl"
GA_FILE = UN_DL_DIR / "2026_02_06_ga_voting.csv"
SC_FILE = UN_DL_DIR / "2026_02_06_sc_voting.csv"
AUTHS_FILE = UN_DL_DIR / "member_states_auths_2026-04-30.csv"
OUT_DIR = Path.cwd() / "out"

VALID_VOTES = {"Y", "N", "A", "X"}
P5 = {"USA", "CHN", "RUS", "FRA", "GBR"}
MIN_DATE = dt.date(1946, 1, 1)
MAX_DATE = dt.date.today()

# Codes that appear in vote data but not in the UN auth file. Sourced from
# UN press releases (FRG seat was coded GER 1973–1990; SCG was the Serbia and
# Montenegro state union 2003-02-04 to 2006-06-05).
FALLBACK_NAME_SEGMENTS = [
    ("GER", "Germany, Federal Republic of", dt.date(1973, 9, 18), dt.date(1990, 10, 2), 278),
    ("SCG", "Serbia and Montenegro", dt.date(2003, 2, 4), dt.date(2006, 6, 5), 891),
]


def clean(s):
    if s is None:
        return None
    s = s.strip()
    return s if s else None


def to_int_or_none(s):
    s = clean(s)
    if s is None:
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def parse_date(s):
    s = clean(s)
    if s is None:
        return None
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        return None


def parse_drafts(s):
    s = clean(s)
    if s is None:
        return []
    return [d.strip() for d in s.split("|") if d.strip()]


def drafts_to_pg_array(drafts):
    if not drafts:
        return "{}"
    escaped = []
    for d in drafts:
        if any(c in d for c in [',', '{', '}', '"', '\\', ' ']):
            escaped.append('"' + d.replace('\\', '\\\\').replace('"', '\\"') + '"')
        else:
            escaped.append(d)
    return "{" + ",".join(escaped) + "}"


def parse_subjects(s):
    """Return a list of subject paths, each a tuple of hierarchy segments.

    Source format inside one comma-separated grouping: `|` separates distinct
    top-level topical references; `--` separates parent → subtopic levels
    within a reference. So `AFRICA--REGIONAL SECURITY|TERRORISM` yields two
    paths: ('AFRICA', 'REGIONAL SECURITY') and ('TERRORISM',).
    """
    s = clean(s)
    if s is None:
        return []
    paths = []
    for piece in s.split(","):
        for ref in piece.split("|"):
            segments = tuple(seg.strip() for seg in ref.split("--"))
            segments = tuple(seg for seg in segments if seg)
            if segments:
                paths.append(segments)
    return paths


def parse_bool(s):
    s = clean(s)
    if s is None:
        return None
    if s == "True":
        return True
    if s == "False":
        return False
    return None


def parse_auths(vote_codes):
    """Yield (ms_code, name, valid_from, valid_to, m49) segments.

    A row may carry comma-separated Start/End dates for discontinuous validity
    (Egypt 1945–1958 then 1971–present, etc.). Zip into one segment per range.

    UN vote data tags every vote with the *modern* ISO code (e.g. all Upper Volta
    votes 1960–1984 are tagged BFA, all USSR votes 1945–1991 are tagged RUS). The
    auth file, by contrast, gives the pre-rename entity its own historical ISO
    (HVO for Upper Volta, SUN for USSR). To make vote-date lookups resolvable, we
    merge auth rows by their name-chain: if HVO's name chain leads to BFA and BFA
    is in vote data while HVO is not, HVO's segments are reattributed to BFA.
    """
    raw_rows = []
    with open(AUTHS_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ms_code = clean(row.get("ISO Code"))
            name = clean(row.get("Member State"))
            start_raw = clean(row.get("Start date"))
            if not ms_code or not name or not start_raw:
                continue
            starts = [s.strip() for s in start_raw.split(",") if s.strip()]
            end_raw = clean(row.get("End date")) or ""
            ends = [e.strip() for e in end_raw.split(",") if e.strip()]
            m49 = to_int_or_none(row.get("M49 Code"))
            ref_name = clean(row.get("Earlier or Later Name"))
            row_segments = []
            for i, s in enumerate(starts):
                try:
                    vf = dt.date.fromisoformat(s)
                except ValueError:
                    print(f"WARN: auth row {ms_code} unparseable start '{s}' — skipped")
                    continue
                vt = None
                if i < len(ends):
                    try:
                        vt = dt.date.fromisoformat(ends[i])
                    except ValueError:
                        print(f"WARN: auth row {ms_code} unparseable end '{ends[i]}' — skipped")
                        continue
                row_segments.append((vf, vt))
            raw_rows.append({
                "ms_code": ms_code,
                "name": name,
                "m49": m49,
                "ref_name": ref_name,
                "segments": row_segments,
            })

    # Union-find on name chains so all rows in one political-entity lineage share
    # the same component.
    by_name: dict[str, int] = {}
    parent = list(range(len(raw_rows)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i, r in enumerate(raw_rows):
        by_name.setdefault(r["name"], i)
    for i, r in enumerate(raw_rows):
        if r["ref_name"] and r["ref_name"] in by_name:
            union(i, by_name[r["ref_name"]])

    components: dict[int, list[int]] = {}
    for i in range(len(raw_rows)):
        components.setdefault(find(i), []).append(i)

    segments = []
    for comp_indices in components.values():
        comp_rows = [raw_rows[i] for i in comp_indices]
        codes_in_comp = {r["ms_code"] for r in comp_rows}
        codes_in_votes = codes_in_comp & vote_codes
        # If exactly one code in the component appears in vote data, reattribute
        # every row in the component to that code. Otherwise, leave each row's
        # ms_code as-is (handles ambiguous components and within-code chains
        # like BLR Byelorussian-SSR→Belarus where both rows are already BLR).
        if len(codes_in_votes) == 1:
            target = next(iter(codes_in_votes))
        else:
            target = None
        for r in comp_rows:
            out_code = target if target else r["ms_code"]
            for vf, vt in r["segments"]:
                segments.append((out_code, r["name"], vf, vt, r["m49"]))
    segments.extend(FALLBACK_NAME_SEGMENTS)
    return segments


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            yield i, row


def ingest():
    OUT_DIR.mkdir(exist_ok=True)
    skipped_path = OUT_DIR / "skipped.log"
    skipped = []

    # Scan vote files once for the set of ms_codes actually used. The auth
    # parser uses this to merge name-chains onto the modern code present in
    # vote data (e.g. HVO segments → BFA).
    vote_codes: set[str] = set()
    for f in (GA_FILE, SC_FILE):
        for _line, row in read_csv(f):
            c = clean(row.get("ms_code"))
            if c:
                vote_codes.add(c)

    # Load authoritative name history.
    name_segments = parse_auths(vote_codes)
    segments_by_code: dict[str, list[tuple]] = {}
    for ms_code, name, vf, vt, m49 in name_segments:
        segments_by_code.setdefault(ms_code, []).append((name, vf, vt, m49))
    for code, segs in segments_by_code.items():
        segs.sort(key=lambda s: s[1])

    def resolve_name(ms_code, vote_date):
        for name, vf, vt, _m49 in segments_by_code.get(ms_code, ()):
            if vf <= vote_date and (vt is None or vote_date <= vt):
                return name
        return None

    # Anchor table: just the set of ms_codes. Names live in country_names.
    countries: set[str] = set(segments_by_code.keys()) | vote_codes
    vote_name_disagreements: set[tuple[str, str, str]] = set()
    unresolved_pairs: set[tuple[str, str]] = set()
    resolutions: dict[int, dict] = {}
    votes: list[dict] = []
    # Subject names are globally unique. Same name under different parents is
    # the same node — the parent relationship is a DAG, not a tree (REPORTS
    # legitimately appears under many parents).
    subject_names: set[str] = set()
    subject_edges: set[tuple[str, str]] = set()  # (child_name, parent_name)
    # (undl_id, leaf_name) — each |-separated reference links to its leaf only.
    resolution_subjects: set[tuple[int, str]] = set()

    def register_subject(path):
        for seg in path:
            subject_names.add(seg)
        for i in range(1, len(path)):
            subject_edges.add((path[i], path[i - 1]))

    def log_skip(source, line, reason):
        skipped.append(f"{source}:{line}:{reason}")

    def check_country(ms_code, ms_name, vote_date):
        """Verify the auth file resolves a name for this (code, date) and that
        it roughly matches what the vote CSV claims. Logs disagreements once."""
        if ms_code not in countries:
            print(f"WARN: ms_code {ms_code} ('{ms_name}') has no auth-file entry")
            return
        resolved = resolve_name(ms_code, vote_date)
        if resolved is None:
            unresolved_pairs.add((ms_code, vote_date.isoformat()))
            return
        if ms_name and resolved.upper() != ms_name.upper():
            vote_name_disagreements.add((ms_code, ms_name, resolved))

    def process_resolution(undl_id, fields, source, line):
        if undl_id in resolutions:
            existing = resolutions[undl_id]
            for k, v in fields.items():
                if existing.get(k) != v:
                    print(
                        f"WARN: undl_id {undl_id} field '{k}' disagrees: "
                        f"'{existing.get(k)}' vs '{v}' ({source}:{line}) — keeping first"
                    )
        else:
            resolutions[undl_id] = fields

    # --- GA ---
    for line, row in read_csv(GA_FILE):
        source = GA_FILE.name
        undl_id = to_int_or_none(row.get("undl_id"))
        if undl_id is None:
            log_skip(source, line, "missing/invalid undl_id")
            continue

        vote_date = parse_date(row.get("date"))
        if vote_date is None:
            log_skip(source, line, f"invalid date '{row.get('date')}'")
            continue
        if not (MIN_DATE <= vote_date <= MAX_DATE):
            log_skip(source, line, f"date {vote_date} out of range")
            continue

        ms_code = clean(row.get("ms_code"))
        if not ms_code or len(ms_code) != 3 or not ms_code.isupper() or not ms_code.isalpha():
            log_skip(source, line, f"invalid ms_code '{row.get('ms_code')}'")
            continue

        vote_code = clean(row.get("ms_vote"))
        if vote_code not in VALID_VOTES:
            log_skip(source, line, f"invalid ms_vote '{vote_code}'")
            continue

        check_country(ms_code, clean(row.get("ms_name")), vote_date)

        drafts = parse_drafts(row.get("draft"))
        subjects = parse_subjects(row.get("subjects"))

        res_fields = {
            "body": "GA",
            "resolution_code": clean(row.get("resolution")),
            "session": to_int_or_none(row.get("session")),
            "vote_date": vote_date,
            "title": clean(row.get("title")),
            "agenda": clean(row.get("agenda_title")),
            "drafts": drafts,
            "committee_report": clean(row.get("committee_report")),
            "meeting": clean(row.get("meeting")),
            "modality": None,
            "vote_note": clean(row.get("vote_note")),
            "total_yes": to_int_or_none(row.get("total_yes")),
            "total_no": to_int_or_none(row.get("total_no")),
            "total_abstentions": to_int_or_none(row.get("total_abstentions")),
            "total_non_voting": to_int_or_none(row.get("total_non_voting")),
            "total_ms": to_int_or_none(row.get("total_ms")),
            "undl_link": clean(row.get("undl_link")),
        }
        process_resolution(undl_id, res_fields, source, line)

        for path in subjects:
            register_subject(path)
            resolution_subjects.add((undl_id, path[-1]))

        votes.append({
            "undl_id": undl_id,
            "ms_code": ms_code,
            "vote": vote_code,
            "permanent_member": None,
            "vote_note": clean(row.get("vote_note")),
        })

    # --- SC ---
    for line, row in read_csv(SC_FILE):
        source = SC_FILE.name
        undl_id = to_int_or_none(row.get("undl_id"))
        if undl_id is None:
            log_skip(source, line, "missing/invalid undl_id")
            continue

        vote_date = parse_date(row.get("date"))
        if vote_date is None:
            log_skip(source, line, f"invalid date '{row.get('date')}'")
            continue
        if not (MIN_DATE <= vote_date <= MAX_DATE):
            log_skip(source, line, f"date {vote_date} out of range")
            continue

        ms_code = clean(row.get("ms_code"))
        if not ms_code or len(ms_code) != 3 or not ms_code.isupper() or not ms_code.isalpha():
            log_skip(source, line, f"invalid ms_code '{row.get('ms_code')}'")
            continue

        vote_code = clean(row.get("ms_vote"))
        if vote_code not in VALID_VOTES:
            log_skip(source, line, f"invalid ms_vote '{vote_code}'")
            continue

        check_country(ms_code, clean(row.get("ms_name")), vote_date)

        drafts = parse_drafts(row.get("draft"))
        subjects = parse_subjects(row.get("subjects"))

        res_fields = {
            "body": "SC",
            "resolution_code": clean(row.get("resolution")),
            "session": None,
            "vote_date": vote_date,
            "title": clean(row.get("description")),
            "agenda": clean(row.get("agenda")),
            "drafts": drafts,
            "committee_report": None,
            "meeting": clean(row.get("meeting")),
            "modality": clean(row.get("modality")),
            "vote_note": clean(row.get("vote_note")),
            "total_yes": to_int_or_none(row.get("total_yes")),
            "total_no": to_int_or_none(row.get("total_no")),
            "total_abstentions": to_int_or_none(row.get("total_abstentions")),
            "total_non_voting": to_int_or_none(row.get("total_non_voting")),
            "total_ms": to_int_or_none(row.get("total_ms")),
            "undl_link": clean(row.get("undl_link")),
        }
        process_resolution(undl_id, res_fields, source, line)

        for path in subjects:
            register_subject(path)
            resolution_subjects.add((undl_id, path[-1]))

        perm = parse_bool(row.get("permanent_member"))
        if ms_code in P5:
            perm = True
        votes.append({
            "undl_id": undl_id,
            "ms_code": ms_code,
            "vote": vote_code,
            "permanent_member": perm,
            "vote_note": clean(row.get("vote_note")),
        })

    # --- Assign subject IDs (alphabetical for determinism) ---
    ordered_names = sorted(subject_names)
    subject_id_map: dict[str, int] = {
        name: i + 1 for i, name in enumerate(ordered_names)
    }

    # --- Write outputs (sorted by PK) ---
    def w(name):
        return open(OUT_DIR / name, "w", newline="", encoding="utf-8")

    def sql_val(v):
        if v is None:
            return ""
        if isinstance(v, bool):
            return "true" if v else "false"
        return v

    # countries.csv (FK anchor — names live in country_names)
    with w("countries.csv") as f:
        wr = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        wr.writerow(["ms_code"])
        for code in sorted(countries):
            wr.writerow([code])

    # country_names.csv (history of names per ms_code)
    with w("country_names.csv") as f:
        wr = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        wr.writerow(["ms_code", "name", "valid_from", "valid_to", "m49_code"])
        rows = []
        for code, segs in segments_by_code.items():
            for name, vf, vt, m49 in segs:
                rows.append((code, name, vf, vt, m49))
        rows.sort(key=lambda r: (r[0], r[2]))
        for code, name, vf, vt, m49 in rows:
            wr.writerow([
                code,
                name,
                vf.isoformat(),
                vt.isoformat() if vt else "",
                sql_val(m49),
            ])

    # subjects.csv (globally unique names; hierarchy lives in subject_parents)
    with w("subjects.csv") as f:
        wr = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        wr.writerow(["id", "name"])
        for name in ordered_names:
            wr.writerow([subject_id_map[name], name])

    # subject_parents.csv (many-to-many child → parent edges; the subject DAG)
    with w("subject_parents.csv") as f:
        wr = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        wr.writerow(["child_id", "parent_id"])
        edge_rows = sorted(
            (subject_id_map[child], subject_id_map[parent])
            for child, parent in subject_edges
        )
        for child_id, parent_id in edge_rows:
            wr.writerow([child_id, parent_id])

    # resolutions.csv
    res_cols = [
        "undl_id", "body", "resolution_code", "session", "vote_date",
        "title", "agenda", "drafts", "committee_report", "meeting",
        "modality", "vote_note", "total_yes", "total_no",
        "total_abstentions", "total_non_voting", "total_ms", "undl_link",
    ]
    with w("resolutions.csv") as f:
        wr = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        wr.writerow(res_cols)
        for undl_id in sorted(resolutions):
            r = resolutions[undl_id]
            wr.writerow([
                undl_id,
                r["body"],
                sql_val(r["resolution_code"]),
                sql_val(r["session"]),
                r["vote_date"].isoformat(),
                sql_val(r["title"]),
                sql_val(r["agenda"]),
                drafts_to_pg_array(r["drafts"]),
                sql_val(r["committee_report"]),
                sql_val(r["meeting"]),
                sql_val(r["modality"]),
                sql_val(r["vote_note"]),
                sql_val(r["total_yes"]),
                sql_val(r["total_no"]),
                sql_val(r["total_abstentions"]),
                sql_val(r["total_non_voting"]),
                sql_val(r["total_ms"]),
                sql_val(r["undl_link"]),
            ])

    # votes.csv
    with w("votes.csv") as f:
        wr = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        wr.writerow(["undl_id", "ms_code", "vote", "permanent_member", "vote_note"])
        for v in sorted(votes, key=lambda x: (x["undl_id"], x["ms_code"])):
            wr.writerow([
                v["undl_id"],
                v["ms_code"],
                v["vote"],
                sql_val(v["permanent_member"]),
                sql_val(v["vote_note"]),
            ])

    # resolution_subjects.csv
    rs_rows = sorted(
        {(undl_id, subject_id_map[name]) for undl_id, name in resolution_subjects},
        key=lambda x: (x[0], x[1]),
    )
    with w("resolution_subjects.csv") as f:
        wr = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        wr.writerow(["undl_id", "subject_id"])
        for undl_id, sid in rs_rows:
            wr.writerow([undl_id, sid])

    # skipped.log
    with open(skipped_path, "w", encoding="utf-8") as f:
        for line in skipped:
            f.write(line + "\n")

    # --- Validation ---
    total_segments = sum(len(s) for s in segments_by_code.values())
    print(f"countries:           {len(countries)}")
    print(f"country_names:       {total_segments}")
    children = {child for child, _ in subject_edges}
    roots = len(subject_names - children)
    print(f"subjects:            {len(subject_names)} (roots={roots}, edges={len(subject_edges)})")
    print(f"resolutions:         {len(resolutions)}")
    print(f"votes:               {len(votes)}")
    print(f"resolution_subjects: {len(resolution_subjects)}")
    print(f"skipped rows:        {len(skipped)}")

    # Vote tally sanity check
    tally: dict[int, dict] = {}
    for v in votes:
        t = tally.setdefault(v["undl_id"], {"Y": 0, "N": 0, "A": 0, "X": 0})
        t[v["vote"]] += 1
    mismatches = []
    for undl_id, t in tally.items():
        total = t["Y"] + t["N"] + t["A"] + t["X"]
        expected = resolutions[undl_id].get("total_ms")
        if expected is not None and total != expected:
            mismatches.append((undl_id, total, expected))
    if mismatches:
        print(f"\nVote tally mismatches ({len(mismatches)}):")
        for undl_id, got, want in mismatches[:20]:
            print(f"  undl_id={undl_id}: counted={got} total_ms={want}")
        if len(mismatches) > 20:
            print(f"  ... and {len(mismatches) - 20} more")

    bad_codes = [c for c in countries if not (len(c) == 3 and c.isupper() and c.isalpha())]
    if bad_codes:
        print(f"\nInvalid ms_codes: {bad_codes}")

    if unresolved_pairs:
        print(f"\nVote (ms_code, vote_date) pairs with no name in auth file: {len(unresolved_pairs)}")
        for code, date in sorted(unresolved_pairs)[:20]:
            print(f"  {code} @ {date}")
        if len(unresolved_pairs) > 20:
            print(f"  ... and {len(unresolved_pairs) - 20} more")

    if vote_name_disagreements:
        print(f"\nVote-CSV vs auth-file name disagreements: {len(vote_name_disagreements)}")
        for code, vote_name, auth_name in sorted(vote_name_disagreements)[:20]:
            print(f"  {code}: vote='{vote_name}' auth='{auth_name}'")
        if len(vote_name_disagreements) > 20:
            print(f"  ... and {len(vote_name_disagreements) - 20} more")


if __name__ == "__main__":
    ingest()
