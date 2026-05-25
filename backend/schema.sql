CREATE TABLE IF NOT EXISTS countries (
    ms_code CHAR(3) PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS country_names (
    ms_code    CHAR(3) NOT NULL REFERENCES countries(ms_code),
    name       TEXT    NOT NULL,
    valid_from DATE    NOT NULL,
    valid_to   DATE,
    m49_code   INTEGER,
    PRIMARY KEY (ms_code, valid_from)
);

CREATE TABLE IF NOT EXISTS subjects (
    id   SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS resolutions (
    undl_id           INTEGER PRIMARY KEY,
    body              CHAR(2) NOT NULL,
    resolution_code   TEXT,
    session           INTEGER,
    vote_date         DATE NOT NULL,
    title             TEXT,
    agenda            TEXT,
    drafts            TEXT[],
    committee_report  TEXT,
    meeting           TEXT,
    modality          TEXT,
    vote_note         TEXT,
    total_yes         INTEGER,
    total_no          INTEGER,
    total_abstentions INTEGER,
    total_non_voting  INTEGER,
    total_ms          INTEGER,
    undl_link         TEXT
);

CREATE TABLE IF NOT EXISTS votes (
    undl_id          INTEGER NOT NULL REFERENCES resolutions(undl_id),
    ms_code          CHAR(3) NOT NULL REFERENCES countries(ms_code),
    vote             CHAR(1) NOT NULL,
    permanent_member BOOLEAN,
    vote_note        TEXT,
    PRIMARY KEY (undl_id, ms_code)
);

CREATE TABLE IF NOT EXISTS resolution_subjects (
    undl_id    INTEGER NOT NULL REFERENCES resolutions(undl_id),
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    PRIMARY KEY (undl_id, subject_id)
);

CREATE INDEX IF NOT EXISTS votes_ms_code_idx       ON votes(ms_code);
CREATE INDEX IF NOT EXISTS resolutions_date_idx    ON resolutions(vote_date);
CREATE INDEX IF NOT EXISTS resolutions_body_idx    ON resolutions(body);
CREATE INDEX IF NOT EXISTS country_names_lookup_idx ON country_names(ms_code, valid_from, valid_to);
