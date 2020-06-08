import os
import tempfile
from unittest import TestCase

from grid import Grid
from puzzle import Puzzle


class TestPuzzle(TestCase):

    @staticmethod
    def create_puzzle():
        """
        Creates sample puzzle as:
        +---------+
        | | |*| | |
        | | |*|*| |
        |*|*| |*|*|
        | |*|*| | |
        | | |*| | |
        +---------+
        """
        n = 5
        grid = Grid(n)
        for (r, c) in [
            (1, 3),
            (2, 3),
            (2, 4),
            (3, 1),
            (3, 2),
        ]:
            grid.add_black_cell(r, c)
        return Puzzle(grid)

    @staticmethod
    def create_atlantic_puzzle():
        """ Creates a puzzle from the Atlantic puzzle of May 15, 2020
        +-----------------+
        |D|A|B|*|*|E|F|T|S|
        |S|L|I|M|*|R|I|O|T|
        |L|O|C|A|V|O|R|E|S|
        |R|E|U|N|I|T|E|D|*|
        |*|*|R|A|P|I|D|*|*|
        |*|R|I|C|E|C|A|K|E|
        |C|O|O|L|R|A|N|C|H|
        |C|L|U|E|*|C|A|L|X|
        |R|O|S|S|*|*|E|R|E|
        +-----------------+
        """
        n = 9
        grid = Grid(n)
        for (r, c) in [
            (1, 4), (1, 5),
            (2, 5),
            (4, 9),
            (5, 8), (5, 9),
        ]:
            grid.add_black_cell(r, c)
        puzzle = Puzzle(grid)
        puzzle.title = 'My Atlantic Theme'
        return puzzle

    @staticmethod
    def create_atlantic_puzzle_with_some_words():
        puzzle = TestPuzzle.create_atlantic_puzzle()
        for seq, text in [
            [4, "EFTS"],
            [8, "SLIM"],
            [10, "RIOT"],
            [11, "LOCAVORES"],
            [14, "RAPID"],
            [15, "RICECAKE"],
            [18, "COOLRANCH"],
            [19, "CLUE"],
            [21, "ROSS"],
            [22, "ERE"],
        ]:
            puzzle.get_across_word(seq).set_text(text)

        for seq, text in [
            [1, "DSLR"],
            [2, "ALOE"],
            [3, "BICURIOUS"],
            [5, "FIREDANCE"],
            [6, "TOED"],
            [7, "STS"],
            [9, "MANACLES"],
            [12, "VIPER"],
            [15, "ROLO"],
            [16, "KCAR"],
            [18, "CCR"],
        ]:
            puzzle.get_down_word(seq).set_text(text)
        return puzzle

    @staticmethod
    def create_solved_atlantic_puzzle():
        puzzle = TestPuzzle.create_atlantic_puzzle()
        for seq, text in [
            (1, "DAB"),
            (4, "EFTS"),
            (8, "SLIM"),
            (10, "RIOT"),
            (11, "LOCAVORES"),
            (13, "REUNITED"),
            (14, "RAPID"),
            (15, "RICECAKE"),
            (18, "COOLRANCH"),
            (19, "CLUE"),
            (20, "SCAR"),
            (21, "ROSS"),
            (22, "ERE"),
        ]:
            puzzle.get_across_word(seq).set_text(text)

        for seq, clue in [
            (1, "Dance move that's a hit?"),
            (4, "Newborns in a terrarium"),
            (8, "Reed-like"),
            (10, "Hit at the Comedy Cellar, say"),
            (11, "Frequent farmers' market patrons, perhaps"),
            (13, "Together again"),
            (14, "Swift"),
            (15, "Quaker offering"),
            (18, "Flavor in a blue bag"),
            (19, "One of things this puzzle has 26 of"),
            (20, "What Capone had on his face"),
            (21, "Big name in flag design"),
            (22, "Bard's \"Before\""),
        ]:
            puzzle.get_across_word(seq).set_clue(clue)

        for seq, clue in [
            (1, "Gift for a shutterbug, briefly"),
            (2, "Healing succulent"),
            (3, "Open to expanding one's sense of identity"),
            (4, "Bold choice for subway reading (pl.)"),
            (5, "Burning Man performance"),
            (6, "Open-______"),
            (7, "Hagiographic subjects: Abbr."),
            (9, "Some shackles"),
            (12, "Treacherous slitherer"),
            (15, "Candy in a gold wrapper"),
            (16, "'80s Chrysler offering"),
            (17, "Honor, to Fritz"),
            (18, "\"Fortunate Son\" band, briefly"),
        ]:
            puzzle.get_down_word(seq).set_clue(clue)

        return puzzle

    @staticmethod
    def create_nyt_puzzle():
        """
        Creates a puzzle from a real New York Times crossword of March 15, 2020
        +-----------------------------------------+
        |A|B|B|A|*| | | |*| | | | | |*| | | | | | |
        | | | | |*| | | |*| | | | | |*| | | | | | |
        | | | | | | | | | | | | | | |*| | | | | | |
        | | | | | |*| | | | | |*| | | |*| | | | | |
        | | | |*| | | | | |*|*| | | | | |*|*| | | |
        |*|*|*| | | | | | | | | | | | | | | | | | |
        | | | | | | |*|*| | | | | | |*| | | | | | |
        | | | | |*| | | |*| | | |*|*| | | | | | | |
        | | | | | | | | | | | | | | | | | | |*|*|*|
        | | | |*| | | | | |*| | | | | | |*| | | | |
        | | | | | |*| | | | |*| | | | |*| | | | | |
        | | | | |*| | | | | | |*| | | | | |*| | | |
        |*|*|*| | | | | | | | | | | | | | | | | | |
        | | | | | | | |*|*| | | |*| | | |*| | | | |
        | | | | | | |*| | | | | | |*|*| | | | | | |
        | | | | | | | | | | | | | | | | | | |*|*|*|
        | | | |*|*| | | | | |*|*| | | | | |*| | | |
        | | | | | |*| | | |*| | | | | |*| | | | | |
        | | | | | | |*| | | | | | | | | | | | | | |
        | | | | | | |*| | | | | |*| | | |*| | | | |
        | | | | | | |*| | | | | |*| | | |*| | | | |
        +-----------------------------------------+
        """
        n = 21
        grid = Grid(n)
        for (r, c) in [
            (1, 5), (1, 9), (1, 15),
            (2, 5), (2, 9), (2, 15),
            (3, 15),
            (4, 6), (4, 12), (4, 16),
            (5, 4), (5, 10), (5, 11), (5, 17), (5, 18),
            (6, 1), (6, 2), (6, 3),
            (7, 7), (7, 8), (7, 15),
            (8, 5), (8, 9), (8, 13), (8, 14),
            (9, 19), (9, 20), (9, 21),
            (10, 4), (10, 10),
            (11, 6), (11, 11),
            (12, 5),
            (13, 1), (13, 2), (13, 3),
            (14, 8),
            (15, 7),
            (17, 4), (17, 5)
        ]:
            grid.add_black_cell(r, c)
        return Puzzle(grid)

    @staticmethod
    def create_nyt_daily():
        """ Tuesday, September 20, 2016 """
        grid = Grid(15)
        for r, c in [
            (1, 5), (1, 11),
            (2, 5), (2, 11),
            (3, 5), (3, 11),
            (4, 14), (4, 15),
            (5, 7), (5, 12),
            (6, 1), (6, 2), (6, 3), (6, 8), (6, 9),
            (7, 4),
            (8, 5), (8, 6), (8, 10), (8, 11),
            (11, 4)

        ]:
            grid.add_black_cell(r, c)
        puzzle = Puzzle(grid)
        for seq, text in [
            (1, "ACTS"),
            (5, "PLASM"),
            (10, "EDGY"),
            (14, "SHIM"),
            (15, "RUCHE"),
            (16, "VALE"),
            (17, "NINE"),
            (18, "USUAL"),
            (19, "IRON"),
            (20, "ENGLISHTRIFLE"),
            (23, "RASTAS"),
            (24, "EDNA"),
            (25, "WAS"),
            (28, "EMIT"),
            (30, "DIGEST"),
            (32, "MAY"),
            (35, "BAKEDALASKA"),
            (38, "ALOT"),
            (40, "ONO"),
            (41, "BAER"),
            (42, "PLUMPUDDING"),
            (47, "YDS"),
            (48, "LESSON"),
            (49, "TIOS"),
            (51, "EYE"),
            (52, "OHMS"),
            (55, "CLUMSY"),
            (59, "NOPIECEOFCAKE"),
            (62, "UNDO"),
            (64, "NAOMI"),
            (65, "KRIS"),
            (66, "SIMP"),
            (67, "GLOMS"),
            (68, "EIRE"),
            (69, "EXES"),
            (70, "ESTEE"),
            (71, "RATS")
        ]:
            puzzle.get_across_word(seq).set_text(text)

        for seq, clue in [
            (1, "___ of the Apostles"),
            (5, "Ending with neo- or proto-"),
            (10, "Pushing conventional limits"),
            (14, "Blade in the pen"),
            (15, "Strip of fabric used for trimming"),
            (16, "Low ground, poetically"),
            (17, "Rock's ___ Inch Nails"),
            (18, "Habitual customer's order, with \"the\""),
            (19, "Clothes presser"),
            (20, "Layers of sherry-soaked torte, homemade custard and fruit served chilled in a giant stem glass"),
            (23, "Dreadlocked ones, informally"),
            (24, "Comical \"Dame\""),
            (25, "\"Kilroy ___ here\""),
            (28, "Give off, as vibes"),
            (30, "Summary"),
            (32, "___-December romance"),
            (35, "Ice cream and sponge topped with meringue and placed in a very hot oven for a few minutes"),
            (38, "Oodles"),
            (40, "Singer with the site imaginepeace.com"),
            (41, "Boxer Max"),
            (42,
             "Steamed-for-hours, aged-for-months concoction of treacle, brandy, fruit and spices, set afire and served at Christmas"),
            (47, "Fabric purchase: Abbr."),
            (48, "Teacher's plan"),
            (49, "Uncles, in Acapulco"),
            (51, "___ contact"),
            (52, "Units of resistance"),
            (55, "Ham-handed"),
            (59, "What a chef might call each dessert featured in this puzzle, literally or figuratively"),
            (62, "Command-Z command"),
            (64, "Actress Watts"),
            (65, "Kardashian matriarch"),
            (66, "Fool"),
            (67, "Latches (onto)"),
            (68, "Land of Blarney"),
            (69, "Ones who are splitsville"),
            (70, "Lauder of cosmetics"),
            (71, "\"Phooey!\""),
        ]:
            puzzle.get_across_word(seq).get_clue()

        for seq, clue in [
            (1, "Ed of \"Up\""),
            (2, "Set traditionally handed down to an eldest daughter"),
            (3, "Tiny bell sounds"),
            (4, "Willowy"),
            (5, "German kingdom of old"),
            (6, "Growing luxuriantly"),
            (7, "Severe and short, as an illness"),
            (8, "Glass fragment"),
            (9, "Gates of philanthropy"),
            (10, "Voldemort-like"),
            (11, "\"Hesitating to mention it, but...\""),
            (12, "Mop &amp; ___"),
            (13, "Itch"),
            (21, "da-DAH"),
            (22, "Pass's opposite"),
            (26, "\"___ and answered\" (courtroom objection)"),
            (27, "Constellation units"),
            (29, "Walloped to win the bout, in brief"),
            (31, "Chew the fat"),
            (32, "Sugar ___"),
            (33, "Locale for urban trash cans"),
            (34, "Sam Cooke's first #1 hit"),
            (36, "Come to a close"),
            (37, "\"I dare you!\""),
            (39, "Designs with ® symbols: Abbr."),
            (43, "Lowdown, in slang"),
            (44, "Drive mad"),
            (45, "Salade ___"),
            (46, "Club game"),
            (50, "Lollipop"),
            (53, "\"Square\" things, ideally"),
            (54, "\"Git!\""),
            (56, "\"West Side Story\" seamstress"),
            (57, "Mini, e.g."),
            (58, "Positive R.S.V.P.s"),
            (60, "Error report?"),
            (61, "J.Lo's daughter with a palindromic name"),
            (62, "Manipulate"),
            (63, "Kill, as an idea"),
        ]:
            puzzle.get_down_word(seq).set_clue(clue)
        return puzzle

    def test_nyt_daily(self):
        puzzle = TestPuzzle.create_nyt_daily()

    def test_cell_type(self):
        puzzle = TestPuzzle.create_puzzle()
        cell = puzzle.get_cell(1, 1)
        self.assertEqual(type(cell), str)
        cell = puzzle.get_cell(1, 3)
        self.assertEqual(type(cell), str)
        puzzle.set_cell(1, 5, 'D')
        cell = puzzle.get_cell(1, 5)
        self.assertEqual(type(cell), str)

    def test_set_cell(self):
        n = 5
        puzzle = Puzzle(Grid(n))
        puzzle.set_cell(2, 3, 'D')
        cell = puzzle.get_cell(2, 3)
        self.assertEqual('D', cell)
        for r in range(1, n + 1):
            if r == 2:
                continue
            for c in range(1, n + 1):
                if c == 3:
                    continue
                cell = puzzle.get_cell(r, c)
                self.assertEqual(Puzzle.WHITE, cell, f'Mismatch at ({r}, {c})')

    def test_add_black(self):
        n = 5
        grid = Grid(n)
        black_cells = [
            (1, 1),
            (1, 3),
            (2, 3),
            (2, 4),
            (3, 1),
            (3, 2),
        ]
        for (r, c) in black_cells:
            grid.add_black_cell(r, c)

        puzzle = Puzzle(grid)

        expected_cells = [
            ["*", " ", "*", " ", " "],
            [" ", " ", "*", "*", " "],
            ["*", "*", " ", "*", "*"],
            [" ", "*", "*", " ", " "],
            [" ", " ", "*", " ", "*"],
        ]
        for r in range(1, n + 1):
            for c in range(1, n + 1):
                expected = expected_cells[r - 1][c - 1]
                actual = puzzle.get_cell(r, c)
                self.assertEqual(expected, actual, f'Mismatch at ({r},{c})')

    def test_set_across_word(self):
        puzzle = TestPuzzle.create_atlantic_puzzle()
        seq = 10
        parm = "RIOT"
        puzzle.get_across_word(seq).set_text(parm)
        expected = parm
        actual = puzzle.get_across_word(seq).get_text()
        self.assertEqual(expected, actual)

    def test_set_down_word(self):
        puzzle = TestPuzzle.create_atlantic_puzzle()
        seq = 22
        parm = "BUBBA"
        puzzle.get_across_word(seq).set_text(parm)
        expected = "BUB"
        actual = puzzle.get_across_word(seq).get_text()
        self.assertEqual(expected, actual)

    def test_save(self):
        puzzle = TestPuzzle.create_solved_atlantic_puzzle()
        jsonstr = puzzle.to_json()
        filename = os.path.join(tempfile.gettempdir(), "test_puzzle.test_save.json")
        with open(filename, "wt") as fp:
            print(jsonstr, file=fp)

    def test_load_atlantic(self):

        # Make sure the saved file is there: create it in /tmp
        self.test_save()
        filename = os.path.join(tempfile.gettempdir(), "test_puzzle.test_save.json")

        # Load the file
        with open(filename, "rt") as fp:
            jsonstr = fp.read()
        puzzle = Puzzle.from_json(jsonstr)

        # Check some contents

        self.assertEqual(9, puzzle.n)

        word = puzzle.get_across_word(8)
        self.assertEqual("SLIM", word.get_text())
        self.assertEqual("Reed-like", word.get_clue())

        word = puzzle.get_down_word(17)
        self.assertEqual("EHRE", word.get_text())
        self.assertEqual("Honor, to Fritz", word.get_clue())

    def test_word_count(self):
        puzzle = TestPuzzle.create_atlantic_puzzle()
        expected = 26
        actual = puzzle.get_word_count()
        self.assertEqual(expected, actual)
