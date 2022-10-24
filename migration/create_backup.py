import pickle
from pathlib import Path
import sqlite3

from crossword import Grid, Puzzle

dboutfile = Path.home().joinpath("crossword_backup.db")
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
    pickled         BLOB                    -- Pickled representation
);
CREATE TABLE puzzles (
    id              INTEGER PRIMARY KEY,    -- Puzzle ID
    userid          INTEGER,                -- The user who owns this puzzle
    puzzlename      TEXT,                   -- Puzzle name
    created         TEXT,                   -- Datetime when created
    modified        TEXT,                   -- Datetime last modified
    pickled         BLOB                    -- Pickled representation
);
""")

dbinfile = Path.home().joinpath("crossword.db")
with sqlite3.connect(dbinfile) as con:

    # Connect to the output database
    con.execute(f"""attach database "{dboutfile}" as backup""")

    # Copy users
    con.execute("""create table backup.users as select * from users""")
    con.commit()

    # Convert grids
    res = con.execute("select id, userid, gridname, created, modified, jsonstr from grids")
    for row in res.fetchall():
        (id, userid, gridname, created, modified, jsonstr) = row
        grid = Grid.from_json(jsonstr)
        pickled = pickle.dumps(grid)
        con.execute("""
            INSERT into backup.grids
            VALUES(?, ?, ?, ?, ?, ?)
        """, (
            id, userid, gridname, created, modified, pickled))
    con.commit()

    # Convert puzzles
    res = con.execute("select id, userid, puzzlename, created, modified, jsonstr from puzzles")
    for row in res.fetchall():
        (id, userid, puzzlename, created, modified, jsonstr) = row
        puzzle = Puzzle.from_json(jsonstr)
        pickled = pickle.dumps(puzzle)
        con.execute("""
            INSERT into backup.puzzles
            VALUES(?, ?, ?, ?, ?, ?)
        """, (
            id, userid, puzzlename, created, modified, pickled))
    con.commit()

    # Copy words
    con.execute("""create table backup.words as select * from words""")
