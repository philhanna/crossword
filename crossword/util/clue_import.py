#! /usr/bin/python3

import os
import sys
sys.path.append('../..')

from crossword.clue_import_visitor import ClueImportVisitor
from crossword.configuration import Configuration
from crossword.puzzle import Puzzle
from crossword.util import list_puzzles


def main(args):
    puzzles_root = Configuration.get_puzzles_root()

    # If the --list option was specified, just show the
    # list of puzzles in the puzzles root directory

    if args.list:
        list_puzzles(puzzles_root)
        exit(0)

    # Load the puzzle from the configured puzzles root directory

    if not args.puzzle:
        raise ValueError("No puzzle name specified")

    puzzle_filename = os.path.join(puzzles_root, (args.puzzle + ".json"))
    if not os.path.exists(puzzle_filename):
        raise FileNotFoundError(f"Puzzle file {puzzle_filename} does not exist")

    with open(puzzle_filename) as fp:
        jsonstr = fp.read()
    puzzle = Puzzle.from_json(jsonstr)

    # Open the input file and load the CSV it contains.

    if not args.filename:
        raise ValueError("No CSV file name specified")

    if not os.path.exists(args.filename):
        raise FileNotFoundError(f"CSV file {args.filename} does not exist")

    with open(args.filename) as fp:
        csvstr = fp.read()

    # Update the clues in the puzzle

    visitor = ClueImportVisitor(csvstr)
    puzzle.accept(visitor)

    # Rewrite the puzzle

    with open(puzzle_filename, "wt") as fp:
        fp.write(puzzle.to_json())


#   ============================================================
#   Mainline
#   ============================================================
if __name__ == '__main__':
    import argparse

    description = '''Imports clues for a crossword puzzle from .csv format'''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-l", "--list", action="store_true",
                        help="List puzzles in the puzzle directory")
    parser.add_argument("filename", nargs="?",
                        help="Input CSV file containing clues", default=None)
    parser.add_argument("puzzle", nargs="?",
                        help="Puzzle name")
    args = parser.parse_args()

    try:
        main(args)
    except Exception as e:
        print(e)
        exit(-2)
