from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class FillPriorityItem:
    """Snapshot of one unfilled puzzle slot and its fill urgency metrics.

    Attributes:
        seq: The word's sequence number within its direction group.
        direction: "across" or "down".
        label: Human-readable slot identifier, e.g. "7A" or "12D".
        pattern: Current partial fill with blanks replaced by ".", ready for
            regex or word-list matching (e.g. "C.T").
        candidate_count: Number of dictionary words that match `pattern` given
            all current crossing constraints.
        critical: True when removing this slot's cells would disconnect the
            remaining white-cell graph, making it a structural bridge.
        component_count: Number of connected components in the white-cell graph
            after this slot's cells are excluded.  Normally 1; >1 means the
            slot is critical.
        reason: Short human-readable explanation of the urgency, e.g.
            "Only 2 candidates" or "Critical bridge".
        length: Number of cells in the slot.
    """

    seq: int
    direction: str
    label: str
    pattern: str
    candidate_count: int
    critical: bool
    component_count: int
    reason: str
    length: int


class FillPriorityAnalyzer:
    """Rank incomplete puzzle slots by how urgent they are to fill next.

    The ranking heuristic uses two independent signals:

    1. **Candidate scarcity** — slots with fewer matching dictionary words are
       ranked higher because they are at greatest risk of becoming unsolvable if
       their crossing neighbors are filled first.  A slot with 0 candidates
       already indicates a contradiction in the current fill.

    2. **Structural criticality** — slots whose cells act as the only bridge
       between two regions of white cells are flagged ``critical``.  Filling
       such a slot first keeps the remaining empty region connected, which
       preserves solver flexibility.

    Tie-breaking within the same candidate count: critical slots before
    non-critical, shorter slots before longer (fewer degrees of freedom), then
    by sequence number and direction for determinism.

    Usage::

        analyzer = FillPriorityAnalyzer(word_use_case)
        items = analyzer.rank_slots(puzzle, top_n=5)
        for item in items:
            print(item.label, item.reason)
    """

    def __init__(self, word_uc):
        """
        Args:
            word_uc: A ``WordUseCases`` instance (or compatible) that exposes
                ``get_all_words()`` and ``get_candidate_count(word)``.  If
                ``None`` or the word list is empty, ``rank_slots`` returns an
                empty list rather than raising.
        """
        self.word_uc = word_uc

    def rank_slots(self, puzzle, top_n: int = 5) -> list[FillPriorityItem]:
        """Return the top-N most urgent unfilled slots in *puzzle*.

        Slots that are already complete (no blank cells) are skipped.  The
        result list is ordered from most urgent to least urgent.

        Args:
            puzzle: A ``Puzzle`` domain object with ``across_words``,
                ``down_words``, ``is_black_cell(r, c)``, and ``n`` (grid size).
            top_n: Maximum number of items to return.  Defaults to 5.

        Returns:
            A list of :class:`FillPriorityItem` objects, length ≤ ``top_n``.
            Returns ``[]`` when the word-list is unavailable or the puzzle has
            no incomplete slots.
        """
        if not self.word_uc or not self.word_uc.get_all_words():
            return []

        ranked = []
        for direction, words in (("across", puzzle.across_words), ("down", puzzle.down_words)):
            for seq, word in sorted(words.items()):
                if word.is_complete():
                    continue
                ranked.append(self._analyze_slot(seq, direction, word, puzzle))

        # Primary sort key is candidate_count (ascending) so the most
        # constrained slot rises to the top.  Subsequent keys break ties.
        ranked.sort(key=lambda item: (
            item.candidate_count,
            0 if item.critical else 1,  # critical slots before non-critical
            item.length,
            item.seq,
            item.direction,
        ))
        return ranked[:top_n]

    def _analyze_slot(self, seq: int, direction: str, word, puzzle) -> FillPriorityItem:
        """Build a :class:`FillPriorityItem` for a single incomplete slot.

        Delegates candidate counting to the word use-case and connectivity
        analysis to :meth:`_component_stats`.

        Args:
            seq: Slot sequence number.
            direction: "across" or "down".
            word: The ``Word`` domain object for this slot.
            puzzle: The containing ``Puzzle``.

        Returns:
            A fully populated :class:`FillPriorityItem`.
        """
        candidate_count = self.word_uc.get_candidate_count(word)

        # Check whether removing this slot's cells disconnects the white-cell
        # graph.  component_count > 1 means the slot is a bridge.
        component_count, _ = self._component_stats(puzzle, excluded_cells=set(word.cell_iterator()))
        critical = component_count > 1

        reason = self._reason(candidate_count, critical, component_count)
        label = f"{seq}{'A' if direction == 'across' else 'D'}"

        # Replace blank spaces with "." to produce a matchable pattern string.
        pattern = word.get_text().replace(" ", ".")

        return FillPriorityItem(
            seq=seq,
            direction=direction,
            label=label,
            pattern=pattern,
            candidate_count=candidate_count,
            critical=critical,
            component_count=component_count,
            reason=reason,
            length=word.length,
        )

    def _component_stats(self, puzzle, excluded_cells: set[tuple[int, int]]):
        """Count connected components in the white-cell graph after exclusions.

        Performs a BFS/DFS flood-fill over all non-black cells in the puzzle,
        skipping any cells in *excluded_cells*.  This is used to detect whether
        a particular slot's cells act as a bridge: if removing them splits the
        remaining white cells into two or more disconnected regions, the slot is
        structurally critical.

        Args:
            puzzle: The ``Puzzle`` whose grid is analysed.  Cells are indexed
                1-based from (1, 1) to (n, n).
            excluded_cells: Set of ``(row, col)`` tuples to treat as absent
                (typically the cells belonging to the slot being tested).

        Returns:
            A 2-tuple ``(count, sizes)`` where *count* is the number of
            connected components and *sizes* is a list of their cell counts.
            Returns ``(0, [])`` when no white cells remain after exclusion.
        """
        # Build the full set of candidate cells (white, non-excluded).
        cells = {
            (r, c)
            for r in range(1, puzzle.n + 1)
            for c in range(1, puzzle.n + 1)
            if not puzzle.is_black_cell(r, c) and (r, c) not in excluded_cells
        }
        if not cells:
            return 0, []

        remaining = set(cells)
        sizes = []

        # Iterative flood-fill: each outer loop iteration discovers one component.
        while remaining:
            start = next(iter(remaining))
            todo = deque([start])
            size = 0
            while todo:
                cell = todo.pop()
                if cell not in remaining:
                    continue
                remaining.remove(cell)
                size += 1
                r, c = cell
                # Expand to the four orthogonal neighbours that are still reachable.
                for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if neighbor in remaining:
                        todo.append(neighbor)
            sizes.append(size)

        return len(sizes), sizes

    def _reason(self, candidate_count: int, critical: bool, component_count: int) -> str:
        """Produce a short human-readable explanation for a slot's urgency.

        The message is shown in the UI's fill-priority panel.  Ordering mirrors
        the sort key: scarcity is described first, then structural criticality.

        Args:
            candidate_count: Number of valid dictionary matches for the slot.
            critical: Whether the slot bridges disconnected white-cell regions.
            component_count: Number of components when the slot's cells are removed.

        Returns:
            A short string suitable for display, e.g. "Only 2 candidates".
        """
        if candidate_count == 0:
            return "No candidates"
        if candidate_count == 1:
            return "Only 1 candidate"
        # Splitting into more than two pieces is more severe than a simple bridge.
        if critical and component_count > 2:
            return "Splits grid"
        if critical:
            return "Critical bridge"
        if candidate_count <= 3:
            return f"Only {candidate_count} candidates"
        if candidate_count <= 8:
            return "Tight crossings"
        return f"{candidate_count} candidates"
