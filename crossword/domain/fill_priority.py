from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class FillPriorityItem:
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
    """
    Rank incomplete puzzle slots by how urgent they are to fill next.

    Candidate scarcity is the primary signal; structural criticality is used as
    a boost and as explanation text for slots that act like bridges in the
    white-cell graph.
    """

    def __init__(self, word_uc):
        self.word_uc = word_uc

    def rank_slots(self, puzzle, top_n: int = 5) -> list[FillPriorityItem]:
        if not self.word_uc or not self.word_uc.get_all_words():
            return []

        ranked = []
        for direction, words in (("across", puzzle.across_words), ("down", puzzle.down_words)):
            for seq, word in sorted(words.items()):
                if word.is_complete():
                    continue
                ranked.append(self._analyze_slot(seq, direction, word, puzzle))

        ranked.sort(key=lambda item: (
            item.candidate_count,
            0 if item.critical else 1,
            item.length,
            item.seq,
            item.direction,
        ))
        return ranked[:top_n]

    def _analyze_slot(self, seq: int, direction: str, word, puzzle) -> FillPriorityItem:
        candidate_count = self.word_uc.get_candidate_count(word)
        component_count, _ = self._component_stats(puzzle, excluded_cells=set(word.cell_iterator()))
        critical = component_count > 1
        reason = self._reason(candidate_count, critical, component_count)
        label = f"{seq}{'A' if direction == 'across' else 'D'}"
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
                for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if neighbor in remaining:
                        todo.append(neighbor)
            sizes.append(size)
        return len(sizes), sizes

    def _reason(self, candidate_count: int, critical: bool, component_count: int) -> str:
        if candidate_count == 0:
            return "No candidates"
        if candidate_count == 1:
            return "Only 1 candidate"
        if critical and component_count > 2:
            return "Splits grid"
        if critical:
            return "Critical bridge"
        if candidate_count <= 3:
            return f"Only {candidate_count} candidates"
        if candidate_count <= 8:
            return "Tight crossings"
        return f"{candidate_count} candidates"
