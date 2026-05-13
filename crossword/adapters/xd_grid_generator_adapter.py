# crossword.adapters.xd_grid_generator_adapter
import json
import sqlite3

from crossword.domain.grid import Grid
from crossword.ports.grid_generator_port import GridGeneratorPort


class XdGridGeneratorAdapter(GridGeneratorPort):
    def __init__(self, xdfile: str):
        self.xdfile = xdfile

    def generate(self, n: int) -> Grid:
        with sqlite3.connect(self.xdfile) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT grid_text, size FROM grids WHERE size = ? ORDER BY RANDOM() LIMIT 1",
                (n,),
            ).fetchone()

        if row is None:
            raise RuntimeError(f"No grid of size {n} found in xdfile database")

        rows = row["grid_text"].split("\n")
        black_cells = [
            [r + 1, c + 1]
            for r, row_str in enumerate(rows)
            for c, ch in enumerate(row_str)
            if ch == "#"
        ]
        return Grid.from_json(json.dumps({"n": row["size"], "black_cells": black_cells}))
