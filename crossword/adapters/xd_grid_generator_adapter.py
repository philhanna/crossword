# crossword.adapters.xd_grid_generator_adapter
import json
import sqlite3
from collections import Counter

from crossword.domain.grid import Grid
from crossword.ports.grid_generator_port import GridGeneratorPort


class XdGridGeneratorAdapter(GridGeneratorPort):
    def __init__(self, xdfile: str):
        self.xdfile = xdfile

    def generate(self, n: int, spec: list[int] | None = None) -> Grid:
        with sqlite3.connect(self.xdfile) as conn:
            conn.row_factory = sqlite3.Row
            if spec:
                row = self._query_with_spec(conn, n, spec)
            else:
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

    def _query_with_spec(self, conn: sqlite3.Connection, n: int, spec: list[int]):
        counts = Counter(spec)               # {length: required_across_count}
        sorted_lengths = sorted(counts)
        max_len = sorted_lengths[-1]

        # Integers that fall in a gap between consecutive distinct lengths
        gaps = [
            length
            for a, b in zip(sorted_lengths, sorted_lengths[1:])
            for length in range(a + 1, b)
        ]

        # One JOIN per distinct Across length to enforce exact counts
        joins = []
        join_params: list = []
        for i, length in enumerate(sorted_lengths):
            alias = f"sc{i}"
            joins.append(
                f"JOIN slot_counts {alias}"
                f" ON {alias}.grid_id = g.id"
                f" AND {alias}.direction = 'A'"
                f" AND {alias}.length = ?"
                f" AND {alias}.count = ?"
            )
            join_params.extend([length, counts[length]])

        # NOT EXISTS: reject any slot (either direction) with a forbidden length
        forbidden_parts = ["sc_f.length > ?"]
        forbidden_params: list = [max_len]
        if gaps:
            forbidden_parts.append(f"sc_f.length IN ({','.join('?' * len(gaps))})")
            forbidden_params.extend(gaps)

        sql = (
            "SELECT g.grid_text, g.size\n"
            "FROM grids g\n"
            + "\n".join(joins) + "\n"
            "WHERE g.size = ?\n"
            "AND NOT EXISTS (\n"
            "    SELECT 1 FROM slot_counts sc_f\n"
            "    WHERE sc_f.grid_id = g.id\n"
            f"    AND ({' OR '.join(forbidden_parts)})\n"
            ")\n"
            "ORDER BY RANDOM()\n"
            "LIMIT 1"
        )
        params = join_params + [n] + forbidden_params
        return conn.execute(sql, params).fetchone()
