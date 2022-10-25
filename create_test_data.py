#! /usr/bin/python

import pickle
from pathlib import Path

from crossword.grids import Grid
from crossword.puzzles import Puzzle
from tests import testdata, load_test_object


def create_test_data_file(obj, filename):
    fullpath = Path(testdata).joinpath(filename)
    with open(fullpath, "wb") as out:
        pickle.dump(obj, out)


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
    puzzle = Puzzle(grid)
    create_test_data_file(puzzle, "puzzle")


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
    create_test_data_file(puzzle, "atlantic_puzzle")


def create_atlantic_puzzle_with_some_words():
    puzzle = load_test_object("atlantic_puzzle")
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
    create_test_data_file(puzzle, "atlantic_puzzle_with_some_words")


def create_solved_atlantic_puzzle():
    puzzle = load_test_object("atlantic_puzzle")
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

    create_test_data_file(puzzle, "solved_atlantic_puzzle")


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
    puzzle = Puzzle(grid)
    create_test_data_file(puzzle, "nyt_puzzle")


def create_nyt_daily():
    """ from https://www.nytimes.com/crosswords/game/daily/2016/09/20 """
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
        (14, "SHIV"),
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
        puzzle.get_across_word(seq).set_clue(clue)

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

    create_test_data_file(puzzle, "nyt_daily")


def create_word_puzzle():
    jsonstr = r'''{
"n": 15,
"black_cells": [
[1,5],[1,11],[2,5],[2,11],[3,5],[3,11],[4,14],
[4,15],[5,7],[5,12],[6,1],[6,2],[6,3],
[6,8],[6,9],[7,4],[8,5],[8,6],[8,10],
[8,11],[9,12],[10,7],[10,8],[10,13],[10,14],
[10,15],[11,4],[11,9],[12,1],[12,2],[13,5],
[13,11],[14,5],[14,11],[15,5],[15,11]],
"numbered_cells": [
{ "seq": 1, "r": 1, "c": 1, "a": 4, "d": 5 },
{ "seq": 2, "r": 1, "c": 2, "a": 0, "d": 5 },
{ "seq": 3, "r": 1, "c": 3, "a": 0, "d": 5 },
{ "seq": 4, "r": 1, "c": 4, "a": 0, "d": 6 },
{ "seq": 5, "r": 1, "c": 6, "a": 5, "d": 7 },
{ "seq": 6, "r": 1, "c": 7, "a": 0, "d": 4 },
{ "seq": 7, "r": 1, "c": 8, "a": 0, "d": 5 },
{ "seq": 8, "r": 1, "c": 9, "a": 0, "d": 5 },
{ "seq": 9, "r": 1, "c": 10, "a": 0, "d": 7 },
{ "seq": 10, "r": 1, "c": 12, "a": 4, "d": 4 },
{ "seq": 11, "r": 1, "c": 13, "a": 0, "d": 9 },
{ "seq": 12, "r": 1, "c": 14, "a": 0, "d": 3 },
{ "seq": 13, "r": 1, "c": 15, "a": 0, "d": 3 },
{ "seq": 14, "r": 2, "c": 1, "a": 4, "d": 0 },
{ "seq": 15, "r": 2, "c": 6, "a": 5, "d": 0 },
{ "seq": 16, "r": 2, "c": 12, "a": 4, "d": 0 },
{ "seq": 17, "r": 3, "c": 1, "a": 4, "d": 0 },
{ "seq": 18, "r": 3, "c": 6, "a": 5, "d": 0 },
{ "seq": 19, "r": 3, "c": 12, "a": 4, "d": 0 },
{ "seq": 20, "r": 4, "c": 1, "a": 13, "d": 0 },
{ "seq": 21, "r": 4, "c": 5, "a": 0, "d": 4 },
{ "seq": 22, "r": 4, "c": 11, "a": 0, "d": 4 },
{ "seq": 23, "r": 5, "c": 1, "a": 6, "d": 0 },
{ "seq": 24, "r": 5, "c": 8, "a": 4, "d": 0 },
{ "seq": 25, "r": 5, "c": 13, "a": 3, "d": 0 },
{ "seq": 26, "r": 5, "c": 14, "a": 0, "d": 5 },
{ "seq": 27, "r": 5, "c": 15, "a": 0, "d": 5 },
{ "seq": 28, "r": 6, "c": 4, "a": 4, "d": 0 },
{ "seq": 29, "r": 6, "c": 7, "a": 0, "d": 4 },
{ "seq": 30, "r": 6, "c": 10, "a": 6, "d": 0 },
{ "seq": 31, "r": 6, "c": 12, "a": 0, "d": 3 },
{ "seq": 32, "r": 7, "c": 1, "a": 3, "d": 5 },
{ "seq": 33, "r": 7, "c": 2, "a": 0, "d": 5 },
{ "seq": 34, "r": 7, "c": 3, "a": 0, "d": 9 },
{ "seq": 35, "r": 7, "c": 5, "a": 11, "d": 0 },
{ "seq": 36, "r": 7, "c": 8, "a": 0, "d": 3 },
{ "seq": 37, "r": 7, "c": 9, "a": 0, "d": 4 },
{ "seq": 38, "r": 8, "c": 1, "a": 4, "d": 0 },
{ "seq": 39, "r": 8, "c": 4, "a": 0, "d": 3 },
{ "seq": 40, "r": 8, "c": 7, "a": 3, "d": 0 },
{ "seq": 41, "r": 8, "c": 12, "a": 4, "d": 0 },
{ "seq": 42, "r": 9, "c": 1, "a": 11, "d": 0 },
{ "seq": 43, "r": 9, "c": 5, "a": 0, "d": 4 },
{ "seq": 44, "r": 9, "c": 6, "a": 0, "d": 7 },
{ "seq": 45, "r": 9, "c": 10, "a": 0, "d": 7 },
{ "seq": 46, "r": 9, "c": 11, "a": 0, "d": 4 },
{ "seq": 47, "r": 9, "c": 13, "a": 3, "d": 0 },
{ "seq": 48, "r": 10, "c": 1, "a": 6, "d": 0 },
{ "seq": 49, "r": 10, "c": 9, "a": 4, "d": 0 },
{ "seq": 50, "r": 10, "c": 12, "a": 0, "d": 6 },
{ "seq": 51, "r": 11, "c": 1, "a": 3, "d": 0 },
{ "seq": 52, "r": 11, "c": 5, "a": 4, "d": 0 },
{ "seq": 53, "r": 11, "c": 7, "a": 0, "d": 5 },
{ "seq": 54, "r": 11, "c": 8, "a": 0, "d": 5 },
{ "seq": 55, "r": 11, "c": 10, "a": 6, "d": 0 },
{ "seq": 56, "r": 11, "c": 13, "a": 0, "d": 5 },
{ "seq": 57, "r": 11, "c": 14, "a": 0, "d": 5 },
{ "seq": 58, "r": 11, "c": 15, "a": 0, "d": 5 },
{ "seq": 59, "r": 12, "c": 3, "a": 13, "d": 0 },
{ "seq": 60, "r": 12, "c": 4, "a": 0, "d": 4 },
{ "seq": 61, "r": 12, "c": 9, "a": 0, "d": 4 },
{ "seq": 62, "r": 13, "c": 1, "a": 4, "d": 3 },
{ "seq": 63, "r": 13, "c": 2, "a": 0, "d": 3 },
{ "seq": 64, "r": 13, "c": 6, "a": 5, "d": 0 },
{ "seq": 65, "r": 13, "c": 12, "a": 4, "d": 0 },
{ "seq": 66, "r": 14, "c": 1, "a": 4, "d": 0 },
{ "seq": 67, "r": 14, "c": 6, "a": 5, "d": 0 },
{ "seq": 68, "r": 14, "c": 12, "a": 4, "d": 0 },
{ "seq": 69, "r": 15, "c": 1, "a": 4, "d": 0 },
{ "seq": 70, "r": 15, "c": 6, "a": 5, "d": 0 },
{ "seq": 71, "r": 15, "c": 12, "a": 4, "d": 0 }
],
"across_words": [
{ "seq": 1, "text": "ACTS", "clue": "____ of the Apostles" },
{ "seq": 5, "text": "PLASM", "clue": "Suffix with ecto- or proto-" },
{ "seq": 10, "text": "ENVY", "clue": "" },
{ "seq": 14, "text": "SHIM", "clue": "Blade in the pen" },
{ "seq": 15, "text": "     ", "clue": null },
{ "seq": 16, "text": "V   ", "clue": null },
{ "seq": 17, "text": "NINE", "clue": "The Nazgul sum" },
{ "seq": 18, "text": "     ", "clue": null },
{ "seq": 19, "text": "I   ", "clue": null },
{ "seq": 20, "text": "ENTERTAINMENT", "clue": "" },
{ "seq": 23, "text": "RASCAL", "clue": "" },
{ "seq": 24, "text": "    ", "clue": null },
{ "seq": 25, "text": "   ", "clue": null },
{ "seq": 28, "text": "H   ", "clue": "" },
{ "seq": 30, "text": "      ", "clue": null },
{ "seq": 32, "text": "   ", "clue": null },
{ "seq": 35, "text": "           ", "clue": null },
{ "seq": 38, "text": "    ", "clue": null },
{ "seq": 40, "text": "   ", "clue": null },
{ "seq": 41, "text": "    ", "clue": null },
{ "seq": 42, "text": "           ", "clue": null },
{ "seq": 47, "text": "   ", "clue": null },
{ "seq": 48, "text": "      ", "clue": null },
{ "seq": 49, "text": "    ", "clue": null },
{ "seq": 51, "text": "   ", "clue": null },
{ "seq": 52, "text": "    ", "clue": null },
{ "seq": 55, "text": "      ", "clue": null },
{ "seq": 59, "text": "             ", "clue": null },
{ "seq": 62, "text": "    ", "clue": null },
{ "seq": 64, "text": "     ", "clue": null },
{ "seq": 65, "text": "    ", "clue": null },
{ "seq": 66, "text": "    ", "clue": null },
{ "seq": 67, "text": "     ", "clue": null },
{ "seq": 68, "text": "    ", "clue": null },
{ "seq": 69, "text": "    ", "clue": null },
{ "seq": 70, "text": "     ", "clue": null },
{ "seq": 71, "text": "    ", "clue": null }
],
"down_words": [
{ "seq": 1, "text": "ASNER", "clue": "Ed of \"Up\"" },
{ "seq": 2, "text": "CHINA", "clue": "" },
{ "seq": 3, "text": "TINTS", "clue": null },
{ "seq": 4, "text": "SMEECH", "clue": null },
{ "seq": 5, "text": "P  TL  ", "clue": null },
{ "seq": 6, "text": "L  A", "clue": null },
{ "seq": 7, "text": "A  I ", "clue": null },
{ "seq": 8, "text": "S  N ", "clue": null },
{ "seq": 9, "text": "M  M   ", "clue": null },
{ "seq": 10, "text": "EVIN", "clue": "" },
{ "seq": 11, "text": "N  T     ", "clue": null },
{ "seq": 12, "text": "V  ", "clue": null },
{ "seq": 13, "text": "Y  ", "clue": null },
{ "seq": 21, "text": "RA  ", "clue": null },
{ "seq": 22, "text": "E   ", "clue": null },
{ "seq": 26, "text": "     ", "clue": null },
{ "seq": 27, "text": "     ", "clue": null },
{ "seq": 29, "text": "    ", "clue": null },
{ "seq": 31, "text": "   ", "clue": null },
{ "seq": 32, "text": "     ", "clue": null },
{ "seq": 33, "text": "     ", "clue": null },
{ "seq": 34, "text": "         ", "clue": null },
{ "seq": 36, "text": "   ", "clue": null },
{ "seq": 37, "text": "    ", "clue": null },
{ "seq": 39, "text": "   ", "clue": null },
{ "seq": 43, "text": "    ", "clue": null },
{ "seq": 44, "text": "       ", "clue": null },
{ "seq": 45, "text": "       ", "clue": null },
{ "seq": 46, "text": "    ", "clue": null },
{ "seq": 50, "text": "      ", "clue": null },
{ "seq": 53, "text": "     ", "clue": null },
{ "seq": 54, "text": "     ", "clue": null },
{ "seq": 56, "text": "     ", "clue": null },
{ "seq": 57, "text": "     ", "clue": null },
{ "seq": 58, "text": "     ", "clue": null },
{ "seq": 60, "text": "    ", "clue": null },
{ "seq": 61, "text": "    ", "clue": null },
{ "seq": 62, "text": "   ", "clue": null },
{ "seq": 63, "text": "   ", "clue": null }
]
}'''
    puzzle = Puzzle.from_json(jsonstr)
    create_test_data_file(puzzle, "word_puzzle")


def create_rotate_good_grid():
    jsonstr = """
        {
  "n": 9,
  "cells": [
    "+-----------------+",
    "|*| | | |*| | | | |",
    "|*| | | |*| | | | |",
    "| | | | |*| | | | |",
    "| | | | | |*| | | |",
    "| | | | | | | | | |",
    "| | | |*| | | | | |",
    "| | | | |*| | | | |",
    "| | | | |*| | | |*|",
    "| | | | |*| | | |*|",
    "+-----------------+"
  ],
  "black_cells": [
    [ 1, 1 ],
    [ 1, 5 ],
    [ 2, 1 ],
    [ 2, 5 ],
    [ 3, 5 ],
    [ 4, 6 ],
    [ 6, 4 ],
    [ 7, 5 ],
    [ 8, 5 ],
    [ 8, 9 ],
    [ 9, 5 ],
    [ 9, 9 ]
  ],
  "numbered_cells": [
    { "seq": 1, "r": 1, "c": 2, "a": 3, "d": 9 },
    { "seq": 2, "r": 1, "c": 3, "a": 0, "d": 9 },
    { "seq": 3, "r": 1, "c": 4, "a": 0, "d": 5 },
    { "seq": 4, "r": 1, "c": 6, "a": 4, "d": 3 },
    { "seq": 5, "r": 1, "c": 7, "a": 0, "d": 9 },
    { "seq": 6, "r": 1, "c": 8, "a": 0, "d": 9 },
    { "seq": 7, "r": 1, "c": 9, "a": 0, "d": 7 },
    { "seq": 8, "r": 2, "c": 2, "a": 3, "d": 0 },
    { "seq": 9, "r": 2, "c": 6, "a": 4, "d": 0 },
    { "seq": 10, "r": 3, "c": 1, "a": 4, "d": 7 },
    { "seq": 11, "r": 3, "c": 6, "a": 4, "d": 0 },
    { "seq": 12, "r": 4, "c": 1, "a": 5, "d": 0 },
    { "seq": 13, "r": 4, "c": 5, "a": 0, "d": 3 },
    { "seq": 14, "r": 4, "c": 7, "a": 3, "d": 0 },
    { "seq": 15, "r": 5, "c": 1, "a": 9, "d": 0 },
    { "seq": 16, "r": 5, "c": 6, "a": 0, "d": 5 },
    { "seq": 17, "r": 6, "c": 1, "a": 3, "d": 0 },
    { "seq": 18, "r": 6, "c": 5, "a": 5, "d": 0 },
    { "seq": 19, "r": 7, "c": 1, "a": 4, "d": 0 },
    { "seq": 20, "r": 7, "c": 4, "a": 0, "d": 3 },
    { "seq": 21, "r": 7, "c": 6, "a": 4, "d": 0 },
    { "seq": 22, "r": 8, "c": 1, "a": 4, "d": 0 },
    { "seq": 23, "r": 8, "c": 6, "a": 3, "d": 0 },
    { "seq": 24, "r": 9, "c": 1, "a": 4, "d": 0 },
    { "seq": 25, "r": 9, "c": 6, "a": 3, "d": 0 }
  ]
}
"""
    grid = Grid.from_json(jsonstr)
    create_test_data_file(grid, "rotate_good_grid")


def create_good_grid():
    jsonstr = """
{
"n": 15,
"black_cells": [
[ 1, 4 ],
[ 1, 5 ],
[ 1, 11 ],
[ 2, 5 ],
[ 2, 11 ],
[ 3, 5 ],
[ 3, 11 ],
[ 4, 1 ],
[ 4, 2 ],
[ 4, 8 ],
[ 4, 14 ],
[ 4, 15 ],
[ 5, 1 ],
[ 5, 2 ],
[ 5, 3 ],
[ 5, 7 ],
[ 5, 8 ],
[ 5, 13 ],
[ 5, 14 ],
[ 5, 15 ],
[ 6, 8 ],
[ 6, 9 ],
[ 6, 10 ],
[ 7, 5 ],
[ 7, 11 ],
[ 8, 5 ],
[ 8, 11 ],
[ 9, 5 ],
[ 9, 11 ],
[ 10, 6 ],
[ 10, 7 ],
[ 10, 8 ],
[ 11, 1 ],
[ 11, 2 ],
[ 11, 3 ],
[ 11, 8 ],
[ 11, 9 ],
[ 11, 13 ],
[ 11, 14 ],
[ 11, 15 ],
[ 12, 1 ],
[ 12, 2 ],
[ 12, 8 ],
[ 12, 14 ],
[ 12, 15 ],
[ 13, 5 ],
[ 13, 11 ],
[ 14, 5 ],
[ 14, 11 ],
[ 15, 5 ],
[ 15, 11 ],
[ 15, 12 ]
],
"numbered_cells": [
{ "seq": 1, "r": 1, "c": 1, "a": 3, "d": 3 },
{ "seq": 2, "r": 1, "c": 2, "a": 0, "d": 3 },
{ "seq": 3, "r": 1, "c": 3, "a": 0, "d": 4 },
{ "seq": 4, "r": 1, "c": 6, "a": 5, "d": 9 },
{ "seq": 5, "r": 1, "c": 7, "a": 0, "d": 4 },
{ "seq": 6, "r": 1, "c": 8, "a": 0, "d": 3 },
{ "seq": 7, "r": 1, "c": 9, "a": 0, "d": 5 },
{ "seq": 8, "r": 1, "c": 10, "a": 0, "d": 5 },
{ "seq": 9, "r": 1, "c": 12, "a": 4, "d": 14 },
{ "seq": 10, "r": 1, "c": 13, "a": 0, "d": 4 },
{ "seq": 11, "r": 1, "c": 14, "a": 0, "d": 3 },
{ "seq": 12, "r": 1, "c": 15, "a": 0, "d": 3 },
{ "seq": 13, "r": 2, "c": 1, "a": 4, "d": 0 },
{ "seq": 14, "r": 2, "c": 4, "a": 0, "d": 14 },
{ "seq": 15, "r": 2, "c": 6, "a": 5, "d": 0 },
{ "seq": 16, "r": 2, "c": 12, "a": 4, "d": 0 },
{ "seq": 17, "r": 3, "c": 1, "a": 4, "d": 0 },
{ "seq": 18, "r": 3, "c": 6, "a": 5, "d": 0 },
{ "seq": 19, "r": 3, "c": 12, "a": 4, "d": 0 },
{ "seq": 20, "r": 4, "c": 3, "a": 5, "d": 0 },
{ "seq": 21, "r": 4, "c": 5, "a": 0, "d": 3 },
{ "seq": 22, "r": 4, "c": 9, "a": 5, "d": 0 },
{ "seq": 23, "r": 4, "c": 11, "a": 0, "d": 3 },
{ "seq": 24, "r": 5, "c": 4, "a": 3, "d": 0 },
{ "seq": 25, "r": 5, "c": 9, "a": 4, "d": 0 },
{ "seq": 26, "r": 6, "c": 1, "a": 7, "d": 5 },
{ "seq": 27, "r": 6, "c": 2, "a": 0, "d": 5 },
{ "seq": 28, "r": 6, "c": 3, "a": 0, "d": 5 },
{ "seq": 29, "r": 6, "c": 7, "a": 0, "d": 4 },
{ "seq": 30, "r": 6, "c": 11, "a": 5, "d": 0 },
{ "seq": 31, "r": 6, "c": 13, "a": 0, "d": 5 },
{ "seq": 32, "r": 6, "c": 14, "a": 0, "d": 5 },
{ "seq": 33, "r": 6, "c": 15, "a": 0, "d": 5 },
{ "seq": 34, "r": 7, "c": 1, "a": 4, "d": 0 },
{ "seq": 35, "r": 7, "c": 6, "a": 5, "d": 0 },
{ "seq": 36, "r": 7, "c": 8, "a": 0, "d": 3 },
{ "seq": 37, "r": 7, "c": 9, "a": 0, "d": 4 },
{ "seq": 38, "r": 7, "c": 10, "a": 0, "d": 9 },
{ "seq": 39, "r": 7, "c": 12, "a": 4, "d": 0 },
{ "seq": 40, "r": 8, "c": 1, "a": 4, "d": 0 },
{ "seq": 41, "r": 8, "c": 6, "a": 5, "d": 0 },
{ "seq": 42, "r": 8, "c": 12, "a": 4, "d": 0 },
{ "seq": 43, "r": 9, "c": 1, "a": 4, "d": 0 },
{ "seq": 44, "r": 9, "c": 6, "a": 5, "d": 0 },
{ "seq": 45, "r": 9, "c": 12, "a": 4, "d": 0 },
{ "seq": 46, "r": 10, "c": 1, "a": 5, "d": 0 },
{ "seq": 47, "r": 10, "c": 5, "a": 0, "d": 3 },
{ "seq": 48, "r": 10, "c": 9, "a": 7, "d": 0 },
{ "seq": 49, "r": 10, "c": 11, "a": 0, "d": 3 },
{ "seq": 50, "r": 11, "c": 4, "a": 4, "d": 0 },
{ "seq": 51, "r": 11, "c": 6, "a": 0, "d": 5 },
{ "seq": 52, "r": 11, "c": 7, "a": 0, "d": 5 },
{ "seq": 53, "r": 11, "c": 10, "a": 3, "d": 0 },
{ "seq": 54, "r": 12, "c": 3, "a": 5, "d": 4 },
{ "seq": 55, "r": 12, "c": 9, "a": 5, "d": 4 },
{ "seq": 56, "r": 12, "c": 13, "a": 0, "d": 4 },
{ "seq": 57, "r": 13, "c": 1, "a": 4, "d": 3 },
{ "seq": 58, "r": 13, "c": 2, "a": 0, "d": 3 },
{ "seq": 59, "r": 13, "c": 6, "a": 5, "d": 0 },
{ "seq": 60, "r": 13, "c": 8, "a": 0, "d": 3 },
{ "seq": 61, "r": 13, "c": 12, "a": 4, "d": 0 },
{ "seq": 62, "r": 13, "c": 14, "a": 0, "d": 3 },
{ "seq": 63, "r": 13, "c": 15, "a": 0, "d": 3 },
{ "seq": 64, "r": 14, "c": 1, "a": 4, "d": 0 },
{ "seq": 65, "r": 14, "c": 6, "a": 5, "d": 0 },
{ "seq": 66, "r": 14, "c": 12, "a": 4, "d": 0 },
{ "seq": 67, "r": 15, "c": 1, "a": 4, "d": 0 },
{ "seq": 68, "r": 15, "c": 6, "a": 5, "d": 0 },
{ "seq": 69, "r": 15, "c": 13, "a": 3, "d": 0 }
]
}

"""
    grid = Grid.from_json(jsonstr)
    create_test_data_file(grid, "good_grid")


def create_bad_grid():
    jsonstr = """
    {
    "n": 7,
    "black_cells": [
    [ 1, 3 ], [ 2, 3 ], [ 3, 3 ], [ 3, 4 ], [ 3, 5 ], [ 4, 2 ],
    [ 4, 6 ], [ 5, 3 ], [ 5, 4 ], [ 5, 5 ], [ 6, 5 ], [ 7, 5 ]
    ],
    "numbered_cells": [
    { "seq": 1, "r": 1, "c": 1, "a": 2, "d": 7 },
    { "seq": 2, "r": 1, "c": 2, "a": 0, "d": 3 },
    { "seq": 3, "r": 1, "c": 4, "a": 4, "d": 2 },
    { "seq": 4, "r": 1, "c": 5, "a": 0, "d": 2 },
    { "seq": 5, "r": 1, "c": 6, "a": 0, "d": 3 },
    { "seq": 6, "r": 1, "c": 7, "a": 0, "d": 7 },
    { "seq": 7, "r": 2, "c": 1, "a": 2, "d": 0 },
    { "seq": 8, "r": 2, "c": 4, "a": 4, "d": 0 },
    { "seq": 9, "r": 3, "c": 1, "a": 2, "d": 0 },
    { "seq": 10, "r": 3, "c": 6, "a": 2, "d": 0 },
    { "seq": 11, "r": 4, "c": 3, "a": 3, "d": 0 },
    { "seq": 12, "r": 5, "c": 1, "a": 2, "d": 0 },
    { "seq": 13, "r": 5, "c": 2, "a": 0, "d": 3 },
    { "seq": 14, "r": 5, "c": 6, "a": 2, "d": 3 },
    { "seq": 15, "r": 6, "c": 1, "a": 4, "d": 0 },
    { "seq": 16, "r": 6, "c": 3, "a": 0, "d": 2 },
    { "seq": 17, "r": 6, "c": 4, "a": 0, "d": 2 },
    { "seq": 18, "r": 6, "c": 6, "a": 2, "d": 0 },
    { "seq": 19, "r": 7, "c": 1, "a": 4, "d": 0 },
    { "seq": 20, "r": 7, "c": 6, "a": 2, "d": 0 }
    ]
    }        
    """
    grid = Grid.from_json(jsonstr)
    create_test_data_file(grid, "bad_grid")


def create_puzzle_undo():
    jsonstr = """{
"n": 9,
"cells": [
"+-----------------+",
"|D|A|B|*|*|E|F|T|S|",
"|S|L|I|M|*|R|I|O|T|",
"|L|O|C|A|V|O|R|E|S|",
"|R|E|U|N|I| |E|D|*|",
"|*|*|R|A|P|I|D|*|*|",
"|*|R|I|C|E|C|A|K|E|",
"|C|O|O|L|R|A|N|C|H|",
"|C|L|U|E|*| |C|A| |",
"|R|O|S|S|*|*|E|R|E|",
"+-----------------+"
],
"black_cells": [
[ 1, 4 ],
[ 1, 5 ],
[ 2, 5 ],
[ 4, 9 ],
[ 5, 1 ],
[ 5, 2 ],
[ 5, 8 ],
[ 5, 9 ],
[ 6, 1 ],
[ 8, 5 ],
[ 9, 5 ],
[ 9, 6 ]
],
"numbered_cells": [
{ "seq": 1, "r": 1, "c": 1, "a": 3, "d": 4 },
{ "seq": 2, "r": 1, "c": 2, "a": 0, "d": 4 },
{ "seq": 3, "r": 1, "c": 3, "a": 0, "d": 9 },
{ "seq": 4, "r": 1, "c": 6, "a": 4, "d": 8 },
{ "seq": 5, "r": 1, "c": 7, "a": 0, "d": 9 },
{ "seq": 6, "r": 1, "c": 8, "a": 0, "d": 4 },
{ "seq": 7, "r": 1, "c": 9, "a": 0, "d": 3 },
{ "seq": 8, "r": 2, "c": 1, "a": 4, "d": 0 },
{ "seq": 9, "r": 2, "c": 4, "a": 0, "d": 8 },
{ "seq": 10, "r": 2, "c": 6, "a": 4, "d": 0 },
{ "seq": 11, "r": 3, "c": 1, "a": 9, "d": 0 },
{ "seq": 12, "r": 3, "c": 5, "a": 0, "d": 5 },
{ "seq": 13, "r": 4, "c": 1, "a": 8, "d": 0 },
{ "seq": 14, "r": 5, "c": 3, "a": 5, "d": 0 },
{ "seq": 15, "r": 6, "c": 2, "a": 8, "d": 4 },
{ "seq": 16, "r": 6, "c": 8, "a": 0, "d": 4 },
{ "seq": 17, "r": 6, "c": 9, "a": 0, "d": 4 },
{ "seq": 18, "r": 7, "c": 1, "a": 9, "d": 3 },
{ "seq": 19, "r": 8, "c": 1, "a": 4, "d": 0 },
{ "seq": 20, "r": 8, "c": 6, "a": 4, "d": 0 },
{ "seq": 21, "r": 9, "c": 1, "a": 4, "d": 0 },
{ "seq": 22, "r": 9, "c": 7, "a": 3, "d": 0 }
],
"across_words": [
{ "seq": 1, "text": "DAB", "clue": null },
{ "seq": 4, "text": "EFTS", "clue": null },
{ "seq": 8, "text": "SLIM", "clue": null },
{ "seq": 10, "text": "RIOT", "clue": null },
{ "seq": 11, "text": "LOCAVORES", "clue": null },
{ "seq": 13, "text": "REUNI ED", "clue": null },
{ "seq": 14, "text": "RAPID", "clue": null },
{ "seq": 15, "text": "RICECAKE", "clue": null },
{ "seq": 18, "text": "COOLRANCH", "clue": null },
{ "seq": 19, "text": "CLUE", "clue": null },
{ "seq": 20, "text": " CA ", "clue": null },
{ "seq": 21, "text": "ROSS", "clue": null },
{ "seq": 22, "text": "ERE", "clue": null }
],
"down_words": [
{ "seq": 1, "text": "DSLR", "clue": null },
{ "seq": 2, "text": "ALOE", "clue": null },
{ "seq": 3, "text": "BICURIOUS", "clue": null },
{ "seq": 4, "text": "ERO ICA ", "clue": null },
{ "seq": 5, "text": "FIREDANCE", "clue": null },
{ "seq": 6, "text": "TOED", "clue": null },
{ "seq": 7, "text": "STS", "clue": null },
{ "seq": 9, "text": "MANACLES", "clue": null },
{ "seq": 12, "text": "VIPER", "clue": null },
{ "seq": 15, "text": "ROLO", "clue": null },
{ "seq": 16, "text": "KCAR", "clue": null },
{ "seq": 17, "text": "EH E", "clue": null },
{ "seq": 18, "text": "CCR", "clue": null }
],
"undo_stack": [],
"redo_stack": []
}
"""
    puzzle = Puzzle.from_json(jsonstr)
    create_test_data_file(puzzle, "puzzle_undo")


def create_puzzle_validate():
    jsonstr = """{
  "n": 9,
  "cells": [
    "+-----------------+",
    "|D|A|B|*|*|E|F|T|S|",
    "|S|L|I|M|*|R|I|O|T|",
    "|L|O|C|A|V|O|R|E|S|",
    "|R|E|U|N|I| |E|D|*|",
    "|*|*|R|A|P|I|D|*|*|",
    "|*|R|I|C|E|C|A|K|E|",
    "|C|O|O|L|R|A|N|C|H|",
    "|C|L|U|E|*| |C|A| |",
    "|R|O|S|S|*|*|E|R|E|",
    "+-----------------+"
  ],
  "black_cells": [
    [ 1, 4 ],
    [ 1, 5 ],
    [ 2, 5 ],
    [ 4, 9 ],
    [ 5, 1 ],
    [ 5, 2 ],
    [ 5, 8 ],
    [ 5, 9 ],
    [ 6, 1 ],
    [ 8, 5 ],
    [ 9, 5 ],
    [ 9, 6 ]
  ],
  "numbered_cells": [
    { "seq": 1, "r": 1, "c": 1, "a": 3, "d": 4 },
    { "seq": 2, "r": 1, "c": 2, "a": 0, "d": 4 },
    { "seq": 3, "r": 1, "c": 3, "a": 0, "d": 9 },
    { "seq": 4, "r": 1, "c": 6, "a": 4, "d": 8 },
    { "seq": 5, "r": 1, "c": 7, "a": 0, "d": 9 },
    { "seq": 6, "r": 1, "c": 8, "a": 0, "d": 4 },
    { "seq": 7, "r": 1, "c": 9, "a": 0, "d": 3 },
    { "seq": 8, "r": 2, "c": 1, "a": 4, "d": 0 },
    { "seq": 9, "r": 2, "c": 4, "a": 0, "d": 8 },
    { "seq": 10, "r": 2, "c": 6, "a": 4, "d": 0 },
    { "seq": 11, "r": 3, "c": 1, "a": 9, "d": 0 },
    { "seq": 12, "r": 3, "c": 5, "a": 0, "d": 5 },
    { "seq": 13, "r": 4, "c": 1, "a": 8, "d": 0 },
    { "seq": 14, "r": 5, "c": 3, "a": 5, "d": 0 },
    { "seq": 15, "r": 6, "c": 2, "a": 8, "d": 4 },
    { "seq": 16, "r": 6, "c": 8, "a": 0, "d": 4 },
    { "seq": 17, "r": 6, "c": 9, "a": 0, "d": 4 },
    { "seq": 18, "r": 7, "c": 1, "a": 9, "d": 3 },
    { "seq": 19, "r": 8, "c": 1, "a": 4, "d": 0 },
    { "seq": 20, "r": 8, "c": 6, "a": 4, "d": 0 },
    { "seq": 21, "r": 9, "c": 1, "a": 4, "d": 0 },
    { "seq": 22, "r": 9, "c": 7, "a": 3, "d": 0 }
  ],
  "across_words": [
    { "seq": 1, "text": "DAB", "clue": null },
    { "seq": 4, "text": "EFTS", "clue": null },
    { "seq": 8, "text": "SLIM", "clue": null },
    { "seq": 10, "text": "RIOT", "clue": null },
    { "seq": 11, "text": "LOCAVORES", "clue": null },
    { "seq": 13, "text": "REUNI ED", "clue": null },
    { "seq": 14, "text": "RAPID", "clue": null },
    { "seq": 15, "text": "RICECAKE", "clue": null },
    { "seq": 18, "text": "COOLRANCH", "clue": null },
    { "seq": 19, "text": "CLUE", "clue": null },
    { "seq": 20, "text": " CA ", "clue": null },
    { "seq": 21, "text": "ROSS", "clue": null },
    { "seq": 22, "text": "ERE", "clue": null }
  ],
  "down_words": [
    { "seq": 1, "text": "DSLR", "clue": null },
    { "seq": 2, "text": "ALOE", "clue": null },
    { "seq": 3, "text": "BICURIOUS", "clue": null },
    { "seq": 4, "text": "ERO ICA ", "clue": null },
    { "seq": 5, "text": "FIREDANCE", "clue": null },
    { "seq": 6, "text": "TOED", "clue": null },
    { "seq": 7, "text": "STS", "clue": null },
    { "seq": 9, "text": "MANACLES", "clue": null },
    { "seq": 12, "text": "VIPER", "clue": null },
    { "seq": 15, "text": "ROLO", "clue": null },
    { "seq": 16, "text": "KCAR", "clue": null },
    { "seq": 17, "text": "EH E", "clue": null },
    { "seq": 18, "text": "CCR", "clue": null }
  ],
  "undo_stack": [],
  "redo_stack": []
}
"""
    puzzle = Puzzle.from_json(jsonstr)
    create_test_data_file(puzzle, "puzzle_validate")


def create_puzzle_statistics():
    jsonstr = """{
"n": 9,
"cells": [
"+-----------------+",
"|D|A|B|*|*|E|F|T|S|",
"|S|L|I|M|*|R|I|O|T|",
"|L|O|C|A|V|O|R|E|S|",
"|R|E|U|N|I| |E|D|*|",
"|*|*|R|A|P|I|D|*|*|",
"|*|R|I|C|E|C|A|K|E|",
"|C|O|O|L|R|A|N|C|H|",
"|C|L|U|E|*| |C|A| |",
"|R|O|S|S|*|*|E|R|E|",
"+-----------------+"
],
"black_cells": [
[ 1, 4 ],
[ 1, 5 ],
[ 2, 5 ],
[ 4, 9 ],
[ 5, 1 ],
[ 5, 2 ],
[ 5, 8 ],
[ 5, 9 ],
[ 6, 1 ],
[ 8, 5 ],
[ 9, 5 ],
[ 9, 6 ]
],
"numbered_cells": [
{ "seq": 1, "r": 1, "c": 1, "a": 3, "d": 4 },
{ "seq": 2, "r": 1, "c": 2, "a": 0, "d": 4 },
{ "seq": 3, "r": 1, "c": 3, "a": 0, "d": 9 },
{ "seq": 4, "r": 1, "c": 6, "a": 4, "d": 8 },
{ "seq": 5, "r": 1, "c": 7, "a": 0, "d": 9 },
{ "seq": 6, "r": 1, "c": 8, "a": 0, "d": 4 },
{ "seq": 7, "r": 1, "c": 9, "a": 0, "d": 3 },
{ "seq": 8, "r": 2, "c": 1, "a": 4, "d": 0 },
{ "seq": 9, "r": 2, "c": 4, "a": 0, "d": 8 },
{ "seq": 10, "r": 2, "c": 6, "a": 4, "d": 0 },
{ "seq": 11, "r": 3, "c": 1, "a": 9, "d": 0 },
{ "seq": 12, "r": 3, "c": 5, "a": 0, "d": 5 },
{ "seq": 13, "r": 4, "c": 1, "a": 8, "d": 0 },
{ "seq": 14, "r": 5, "c": 3, "a": 5, "d": 0 },
{ "seq": 15, "r": 6, "c": 2, "a": 8, "d": 4 },
{ "seq": 16, "r": 6, "c": 8, "a": 0, "d": 4 },
{ "seq": 17, "r": 6, "c": 9, "a": 0, "d": 4 },
{ "seq": 18, "r": 7, "c": 1, "a": 9, "d": 3 },
{ "seq": 19, "r": 8, "c": 1, "a": 4, "d": 0 },
{ "seq": 20, "r": 8, "c": 6, "a": 4, "d": 0 },
{ "seq": 21, "r": 9, "c": 1, "a": 4, "d": 0 },
{ "seq": 22, "r": 9, "c": 7, "a": 3, "d": 0 }
],
"across_words": [
{ "seq": 1, "text": "DAB", "clue": null },
{ "seq": 4, "text": "EFTS", "clue": null },
{ "seq": 8, "text": "SLIM", "clue": null },
{ "seq": 10, "text": "RIOT", "clue": null },
{ "seq": 11, "text": "LOCAVORES", "clue": null },
{ "seq": 13, "text": "REUNI ED", "clue": null },
{ "seq": 14, "text": "RAPID", "clue": null },
{ "seq": 15, "text": "RICECAKE", "clue": null },
{ "seq": 18, "text": "COOLRANCH", "clue": null },
{ "seq": 19, "text": "CLUE", "clue": null },
{ "seq": 20, "text": " CA ", "clue": null },
{ "seq": 21, "text": "ROSS", "clue": null },
{ "seq": 22, "text": "ERE", "clue": null }
],
"down_words": [
{ "seq": 1, "text": "DSLR", "clue": null },
{ "seq": 2, "text": "ALOE", "clue": null },
{ "seq": 3, "text": "BICURIOUS", "clue": null },
{ "seq": 4, "text": "ERO ICA ", "clue": null },
{ "seq": 5, "text": "FIREDANCE", "clue": null },
{ "seq": 6, "text": "TOED", "clue": null },
{ "seq": 7, "text": "STS", "clue": null },
{ "seq": 9, "text": "MANACLES", "clue": null },
{ "seq": 12, "text": "VIPER", "clue": null },
{ "seq": 15, "text": "ROLO", "clue": null },
{ "seq": 16, "text": "KCAR", "clue": null },
{ "seq": 17, "text": "EH E", "clue": null },
{ "seq": 18, "text": "CCR", "clue": null }
],
"undo_stack": [],
"redo_stack": []
}
"""
    puzzle = Puzzle.from_json(jsonstr)
    create_test_data_file(puzzle, "puzzle_statistics")


# ============================================================
# Mainline
# ============================================================
if __name__ == '__main__':
    create_puzzle()
    create_atlantic_puzzle()
    create_atlantic_puzzle_with_some_words()
    create_solved_atlantic_puzzle()
    create_nyt_puzzle()
    create_nyt_daily()
    create_word_puzzle()
    create_rotate_good_grid()
    create_good_grid()
    create_bad_grid()
    create_puzzle_undo()
    create_puzzle_validate()
    create_puzzle_statistics()
