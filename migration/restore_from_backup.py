import pickle
from pathlib import Path
import sqlite3

from crossword.grids import Grid
from crossword.puzzles import Puzzle

dboutfile = Path.home().joinpath("crossword_new.db")
if dboutfile.exists():
    dboutfile.unlink()

with sqlite3.connect(dboutfile) as con:
    con.executescript("""
CREATE TABLE grids (
    id              INTEGER PRIMARY KEY,    -- Grid ID
    userid          INTEGER,                -- The user who owns the grid
    gridname        TEXT,                   -- Grid name
    created         TEXT,                   -- Datetime when created
    modified        TEXT,                   -- Datetime last modified
    jsonstr         TEXT                    -- JSON representation
);
CREATE TABLE puzzles (
    id              INTEGER PRIMARY KEY,    -- Puzzle ID
    userid          INTEGER,                -- The user who owns this puzzle
    puzzlename      TEXT,                   -- Puzzle name
    created         TEXT,                   -- Datetime when created
    modified        TEXT,                   -- Datetime last modified
    jsonstr         TEXT                    -- JSON representation
);
""")

dbinfile = Path.home().joinpath("crossword_backup.db")
with sqlite3.connect(dbinfile) as con:

    # Connect to the output database
    con.execute(f"""attach database "{dboutfile}" as new""")

    # Copy users
    con.execute("""create table new.users as select * from users""")
    con.commit()

    # Convert grids
    res = con.execute("select id, userid, gridname, created, modified, pickled from grids")
    for row in res.fetchall():
        (id, userid, gridname, created, modified, pickled) = row
        grid = pickle.loads(pickled)
        jsonstr = grid.to_json()
        con.execute("""
            INSERT into new.grids
            VALUES(?, ?, ?, ?, ?, ?)
        """, (
            id, userid, gridname, created, modified, jsonstr))
    con.commit()

    # Convert puzzles
    res = con.execute("select id, userid, puzzlename, created, modified, pickled from puzzles")
    for row in res.fetchall():
        (id, userid, puzzlename, created, modified, pickled) = row
        puzzle = pickle.loads(pickled)
        jsonstr = puzzle.to_json()
        con.execute("""
            INSERT into new.puzzles
            VALUES(?, ?, ?, ?, ?, ?)
        """, (
            id, userid, puzzlename, created, modified, jsonstr))
    con.commit()

    # Copy words
    con.execute("""create table new.words as select * from words""")
