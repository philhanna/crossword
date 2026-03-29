from crossword.domain.fill_priority import (
    FillPriorityAnalyzer,
    SlotInfo,
    get_slots,
    get_white_components,
)
from crossword.tests import TestPuzzle


class TestFillPriority:

    def test_get_slots_returns_across_then_down(self):
        puzzle = TestPuzzle.create_puzzle()

        slots = get_slots(puzzle)

        assert len(slots) == puzzle.get_word_count()
        assert [(slot.seq, slot.direction) for slot in slots] == [
            (1, "A"),
            (3, "A"),
            (5, "A"),
            (7, "A"),
            (9, "A"),
            (10, "A"),
            (1, "D"),
            (2, "D"),
            (4, "D"),
            (6, "D"),
            (7, "D"),
            (8, "D"),
        ]

    def test_slot_info_from_word_captures_uniform_shape(self):
        puzzle = TestPuzzle.create_atlantic_puzzle_with_some_words()
        word = puzzle.get_across_word(11)

        slot = SlotInfo.from_word(word)

        assert slot.seq == 11
        assert slot.direction == "A"
        assert slot.length == 9
        assert slot.text == "LOCAVORES"
        assert slot.is_complete
        assert slot.cells == (
            (3, 1),
            (3, 2),
            (3, 3),
            (3, 4),
            (3, 5),
            (3, 6),
            (3, 7),
            (3, 8),
            (3, 9),
        )
        assert slot.location == "11A"

    def test_slot_info_preserves_incomplete_text(self):
        puzzle = TestPuzzle.create_atlantic_puzzle()
        word = puzzle.get_down_word(4)

        slot = SlotInfo.from_word(word)

        assert slot.direction == "D"
        assert slot.length == 8
        assert slot.text == "        "
        assert not slot.is_complete

    def test_get_white_components_returns_single_component_for_whole_grid(self):
        puzzle = TestPuzzle.create_atlantic_puzzle()

        components = get_white_components(puzzle)

        assert len(components) == 1
        assert len(components[0]) == 69

    def test_get_white_components_can_exclude_cells_without_mutating_grid(self):
        puzzle = TestPuzzle.create_puzzle()
        original_black_cells = puzzle.grid.get_black_cells()

        components = get_white_components(puzzle, excluded_cells={(3, 3)})

        assert sorted(len(component) for component in components) == [3, 3, 4, 4]
        assert puzzle.grid.get_black_cells() == original_black_cells

    def test_get_white_components_returns_empty_when_all_white_cells_excluded(self):
        puzzle = TestPuzzle.create_puzzle()
        white_cells = {
            (r, c)
            for r in range(1, puzzle.n + 1)
            for c in range(1, puzzle.n + 1)
            if not puzzle.grid.is_black_cell(r, c)
        }

        components = get_white_components(puzzle, excluded_cells=white_cells)

        assert components == []

    def test_analyze_slot_marks_structurally_critical_slot(self):
        puzzle = TestPuzzle.create_atlantic_puzzle()
        analyzer = FillPriorityAnalyzer()
        slot = next(slot for slot in get_slots(puzzle) if slot.location == "11A")

        priority = analyzer.analyze_slot(puzzle, slot)

        assert priority.location == "11A"
        assert priority.critical
        assert priority.component_count == 3
        assert priority.component_sizes == (7, 8, 45)
        assert priority.score == 158

    def test_analyze_slot_marks_noncritical_slot(self):
        puzzle = TestPuzzle.create_atlantic_puzzle()
        analyzer = FillPriorityAnalyzer()
        slot = next(slot for slot in get_slots(puzzle) if slot.location == "1A")

        priority = analyzer.analyze_slot(puzzle, slot)

        assert priority.location == "1A"
        assert not priority.critical
        assert priority.component_count == 1
        assert priority.component_sizes == (66,)
        assert priority.score == 17

    def test_rank_slots_prefers_critical_slots(self):
        puzzle = TestPuzzle.create_atlantic_puzzle()
        analyzer = FillPriorityAnalyzer()

        priorities = analyzer.rank_slots(puzzle)

        assert priorities[0].location in {"12D", "14A"}
        first_noncritical = next(priority for priority in priorities if not priority.critical)
        assert priorities[0].score > first_noncritical.score
