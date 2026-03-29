from dataclasses import dataclass

from .word import Word


@dataclass(frozen=True)
class SlotInfo:
    seq: int
    direction: str
    length: int
    text: str
    is_complete: bool
    cells: tuple[tuple[int, int], ...]

    @property
    def location(self) -> str:
        return f"{self.seq}{self.direction}"

    @staticmethod
    def from_word(word: Word) -> "SlotInfo":
        cells = tuple(word.cell_iterator())
        return SlotInfo(
            seq=word.seq,
            direction=word.direction,
            length=word.length,
            text=word.get_text(),
            is_complete=word.is_complete(),
            cells=cells,
        )


def iter_slots(puzzle):
    for word in puzzle.across_words.values():
        yield SlotInfo.from_word(word)
    for word in puzzle.down_words.values():
        yield SlotInfo.from_word(word)


def get_slots(puzzle) -> list[SlotInfo]:
    return list(iter_slots(puzzle))


@dataclass(frozen=True)
class SlotPriority:
    seq: int
    direction: str
    length: int
    text: str
    is_complete: bool
    critical: bool
    component_count: int
    component_sizes: tuple[int, ...]
    score: int

    @property
    def location(self) -> str:
        return f"{self.seq}{self.direction}"


def get_white_components(puzzle, excluded_cells=None) -> list[set[tuple[int, int]]]:
    excluded = set(excluded_cells or [])
    white_cells = {
        (r, c)
        for r in range(1, puzzle.n + 1)
        for c in range(1, puzzle.n + 1)
        if not puzzle.grid.is_black_cell(r, c) and (r, c) not in excluded
    }

    components = []
    unseen = set(white_cells)
    while unseen:
        start = unseen.pop()
        component = {start}
        stack = [start]

        while stack:
            r, c = stack.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)

        components.append(component)

    return components


class FillPriorityAnalyzer:

    def analyze_slot(self, puzzle, slot: SlotInfo) -> SlotPriority:
        components = get_white_components(puzzle, excluded_cells=slot.cells)
        component_sizes = tuple(sorted(len(component) for component in components))
        component_count = len(component_sizes)
        critical = component_count > 1

        score = 0
        if critical:
            score += 100
            score += 20 * (component_count - 1)
            score += component_sizes[0]

        if not slot.is_complete:
            score += 10

        score += max(0, 10 - slot.length)

        return SlotPriority(
            seq=slot.seq,
            direction=slot.direction,
            length=slot.length,
            text=slot.text,
            is_complete=slot.is_complete,
            critical=critical,
            component_count=component_count,
            component_sizes=component_sizes,
            score=score,
        )

    def rank_slots(self, puzzle) -> list[SlotPriority]:
        priorities = [self.analyze_slot(puzzle, slot) for slot in get_slots(puzzle)]
        priorities.sort(
            key=lambda slot: (
                -slot.score,
                -int(slot.critical),
                slot.length,
                slot.seq,
                slot.direction,
            )
        )
        return priorities
