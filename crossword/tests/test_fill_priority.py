from crossword import Grid, Puzzle
from crossword.domain.fill_priority import FillPriorityAnalyzer


class StubWordUseCases:
    def __init__(self, candidate_counts):
        self.candidate_counts = candidate_counts

    def get_all_words(self):
        return ["aaa", "bbb", "ccc"]

    def get_candidate_count(self, word):
        direction = "across" if word.direction == word.ACROSS else "down"
        return self.candidate_counts[(word.seq, direction)]


class TestFillPriorityAnalyzer:
    def test_ranks_fewer_candidates_first(self):
        puzzle = Puzzle(Grid(3))
        analyzer = FillPriorityAnalyzer(StubWordUseCases({
            (1, "across"): 9,
            (4, "across"): 7,
            (5, "across"): 8,
            (1, "down"): 2,
            (2, "down"): 5,
            (3, "down"): 6,
        }))

        ranked = analyzer.rank_slots(puzzle, top_n=6)

        assert ranked[0].label == "1D"
        assert ranked[0].candidate_count == 2

    def test_prefers_critical_slot_when_candidate_counts_tie(self):
        puzzle = Puzzle(Grid(3))
        analyzer = FillPriorityAnalyzer(StubWordUseCases({
            (1, "across"): 5,
            (4, "across"): 4,
            (5, "across"): 8,
            (1, "down"): 7,
            (2, "down"): 5,
            (3, "down"): 9,
        }))

        ranked = analyzer.rank_slots(puzzle, top_n=6)

        assert ranked[1].label == "2D"
        assert ranked[1].critical is True
        assert ranked[2].label == "1A"
        assert ranked[2].critical is False

    def test_uses_bridge_reason_for_critical_slot(self):
        puzzle = Puzzle(Grid(3))
        analyzer = FillPriorityAnalyzer(StubWordUseCases({
            (1, "across"): 9,
            (4, "across"): 4,
            (5, "across"): 8,
            (1, "down"): 7,
            (2, "down"): 6,
            (3, "down"): 5,
        }))

        ranked = analyzer.rank_slots(puzzle, top_n=6)
        middle_row = next(item for item in ranked if item.label == "4A")

        assert middle_row.critical is True
        assert middle_row.reason == "Critical bridge"
