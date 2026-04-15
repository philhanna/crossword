CREATE TABLE users (
    id              INTEGER PRIMARY KEY,    -- User ID
    username        TEXT,                   -- User name
    password        BLOB,                   -- Encrypted password
    created         TEXT,                   -- Datetime this user was created
    last_access     TEXT,                   -- Datetime this user last used the system
    email           TEXT,                   -- User email
    confirmed       TEXT,                   -- Datetime email confirmed
    author_name     TEXT,                   -- Name as author
    address_line_1  TEXT,                   -- Address line 1
    address_line_2  TEXT,                   -- Address line 2, if required
    address_city    TEXT,                   -- Author city
    address_state   TEXT,                   -- Author state code
    address_zip     TEXT                    -- Author zip code
);
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
