# crossword.adapters.xd_grid_generator_adapter
import json
import logging
import sqlite3

from crossword.domain.grid import Grid
from crossword.ports.grid_generator_port import GridGeneratorPort

logger = logging.getLogger(__name__)


class XdGridGeneratorAdapter(GridGeneratorPort):
    def __init__(self, xdfile: str):
        self.xdfile = xdfile

    def generate(self, n: int) -> Grid:
        logger.info("XdGridGeneratorAdapter.generate: entering, n=%d, xdfile=%s", n, self.xdfile)
        with sqlite3.connect(self.xdfile) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT grid_text, size FROM grids WHERE size = ? ORDER BY RANDOM() LIMIT 1",
                (n,),
            ).fetchone()

        logger.info("XdGridGeneratorAdapter.generate: row=%s", row)
        if row is None:
            raise RuntimeError(f"No grid of size {n} found in xdfile database")

        rows = json.loads(row["grid_text"])
        black_cells = [
            [r + 1, c + 1]
            for r, row_str in enumerate(rows)
            for c, ch in enumerate(row_str)
            if ch == "#"
        ]
        grid = Grid.from_json(json.dumps({"n": row["size"], "black_cells": black_cells}))
        logger.info("XdGridGeneratorAdapter.generate: leaving, grid size=%d, black_cells=%d", n, len(black_cells))
        return grid
