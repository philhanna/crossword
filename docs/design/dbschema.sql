CREATE TABLE IF NOT EXISTS "puzzles" (
    id              INTEGER PRIMARY KEY,
    userid          INTEGER NOT NULL,
    puzzlename      TEXT NOT NULL,
    created         TEXT NOT NULL,
    modified        TEXT NOT NULL,
    last_mode       TEXT NOT NULL DEFAULT 'puzzle'
                        CHECK (last_mode IN ('grid', 'puzzle')),
    jsonstr         TEXT NOT NULL,
    UNIQUE (userid, puzzlename)
);
CREATE UNIQUE INDEX idx_puzzles_userid_puzzlename
        ON puzzles(userid, puzzlename)
        ;
