import sqlite3
from collections import Counter


class SQLiteGridAdapter:
    """Read-only grid search against the external grids database.

    If ``db_path`` is None the adapter is disabled and ``search`` always
    returns an empty list.
    """

    def __init__(self, db_path: str | None) -> None:
        self._conn = None
        if db_path:
            self._conn = sqlite3.connect(
                f"file:{db_path}?mode=ro", uri=True, check_same_thread=False
            )

    def search(self, spec: list[int], size: int) -> list[str]:
        """Return filenames of grids whose across slots match the slot spec.

        Args:
            spec: List of slot lengths to match (duplicates express count).
            size: Grid dimension to restrict results to.

        Returns:
            Sorted list of matching grid filenames, or [] if no DB is configured.
        """
        if self._conn is None:
            return []

        spec_counts = Counter(spec)
        spec_lengths = sorted(spec_counts.keys())
        max_spec = max(spec_lengths)

        gap_lengths = [
            n
            for i in range(len(spec_lengths) - 1)
            for n in range(spec_lengths[i] + 1, spec_lengths[i + 1])
        ]

        join_clauses = []
        params: list = []
        for i, length in enumerate(spec_lengths):
            alias = f"sc{i}"
            join_clauses.append(
                f"JOIN slot_counts {alias}"
                f" ON {alias}.grid_id = g.id"
                f" AND {alias}.direction = 'A'"
                f" AND {alias}.length = ? AND {alias}.count = ?"
            )
            params.extend([length, spec_counts[length]])

        params.append(size)

        not_exists_parts = ["bad.length > ?"]
        params.append(max_spec)

        if gap_lengths:
            placeholders = ",".join("?" * len(gap_lengths))
            not_exists_parts.append(f"bad.length IN ({placeholders})")
            params.extend(gap_lengths)

        length_placeholders = ",".join("?" * len(spec_lengths))
        not_exists_parts.append(
            f"(bad.direction = 'D' AND bad.length IN ({length_placeholders}))"
        )
        params.extend(spec_lengths)

        not_exists_cond = "\n           OR ".join(not_exists_parts)
        joins = "\n".join(join_clauses)

        sql = (
            f"SELECT g.filename\nFROM grids g\n{joins}\n"
            f"WHERE g.size = ?\n"
            f"  AND NOT EXISTS (\n"
            f"      SELECT 1 FROM slot_counts bad\n"
            f"      WHERE bad.grid_id = g.id\n"
            f"        AND ({not_exists_cond})\n"
            f"  )\n"
            f"ORDER BY g.filename"
        )

        cur = self._conn.execute(sql, params)
        return [row[0] for row in cur.fetchall()]
