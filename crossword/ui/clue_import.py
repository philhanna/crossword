#! /usr/bin/python3
import csv
import os
from datetime import datetime
from io import StringIO

from sqlalchemy import desc, asc

from crossword import Puzzle
from crossword.ui import create_app, db, DBPuzzle, list_puzzles


def visit_puzzle(csvstr, puzzle):
    """ Reads the words and clues from a string in CSV format """
    with StringIO(csvstr) as fp:
        cfp = csv.reader(fp)
        next(cfp)  # Skip column headings
        for row in cfp:
            seq = int(row[0])
            direction = row[1]
            text = row[2]
            clue_text = row[3]
            if direction == 'across':
                word = puzzle.get_across_word(seq)
                if not word:
                    errmsg = f'{seq} across is not defined'
                    raise RuntimeError(errmsg)
                previous_text = word.get_text()
                if text != previous_text:
                    errmsg = f'Word at {seq} across should be "{previous_text}", not "{text}"'
                    raise RuntimeError(errmsg)
                word.set_clue(clue_text)
            elif direction == 'down':
                word = puzzle.get_down_word(seq)
                if not word:
                    errmsg = f'{seq} down is not defined'
                    raise RuntimeError(errmsg)
                previous_text = word.get_text()
                if text != previous_text:
                    errmsg = f'Word at {seq} down should be "{previous_text}", not "{text}"'
                    raise RuntimeError(errmsg)
                word.set_clue(clue_text)
            else:
                errmsg = f'Direction is "{direction}", not "across" or "down"'
                raise RuntimeError(errmsg)
    pass


def main(args):

    app = create_app()
    app.app_context().push()

    userid = 1  # TODO replace hard-coded user id

    # If the --list option was specified, just show the
    # list of puzzles in the puzzles root directory

    if args.list:
        list_puzzles(userid)
        exit(0)

    # Load the puzzle from the configured puzzles root directory

    if not args.puzzle:
        raise ValueError("No puzzle name specified")
    puzzlename = args.puzzle
    row = DBPuzzle.query \
        .filter_by(userid=userid, puzzlename=puzzlename) \
        .order_by(desc(DBPuzzle.modified), asc(DBPuzzle.puzzlename)) \
        .first()
    jsonstr = row.jsonstr
    puzzle = Puzzle.from_json(jsonstr)

    # Open the input file and load the CSV it contains.

    if not args.filename:
        raise ValueError("No CSV file name specified")

    if not os.path.exists(args.filename):
        raise FileNotFoundError(f"CSV file {args.filename} does not exist")

    with open(args.filename) as fp:
        csvstr = fp.read()

    # Update the clues in the puzzle
    visit_puzzle(csvstr, puzzle)

    # Rewrite the puzzle
    jsonstr = puzzle.to_json()
    modified = datetime.now().isoformat()
    thePuzzle = DBPuzzle \
        .query \
        .filter_by(userid=userid, puzzlename=puzzlename) \
        .first()
    thePuzzle.jsonstr = jsonstr
    thePuzzle.modified = modified
    db.session.commit()


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
