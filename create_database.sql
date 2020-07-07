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

CREATE TABLE grids (
    id              INTEGER PRIMARY KEY,    -- Grid ID
    userid          INTEGER,                -- User who owns this grid
    gridname        TEXT,                   -- Grid name
    created         TEXT,                   -- Datetime when created
    modified        TEXT,                   -- Datetime last modified
    jsonstr         TEXT                    -- JSON representation
);

CREATE TABLE puzzles (
    id              INTEGER PRIMARY KEY,    -- Puzzle ID
    userid          INTEGER,                -- User who owns this puzzle
    puzzlename      TEXT,                   -- Puzzle name
    created         TEXT,                   -- Datetime when created
    modified        TEXT,                   -- Datetime last modified
    jsonstr         TEXT                    -- JSON representation
);

CREATE TABLE words (
    word            TEXT NOT NULL           -- The word
);
