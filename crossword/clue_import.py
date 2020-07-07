#! /usr/bin/python3
import csv
import os
import sqlite3
from datetime import datetime
from io import StringIO

from crossword import Puzzle, dbfile


def list_puzzles(userid):
    names = []
    with sqlite3.connect(dbfile()) as con:
        cursor = con.cursor()
        try:
            cursor.execute('''
                SELECT      puzzlename, modified
                FROM        puzzles
                WHERE       userid = ?
                ORDER BY    2 desc, 1
            ''', (userid,))
            row = cursor.fetchone()
            name = row[0]
            names.append(name)
        except sqlite3.Error as e:
            msg = (
                f"Unable to get list of puzzles for userid {userid}"
                f", error={e}"
            )
            raise RuntimeError(msg)
    return names


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

    with sqlite3.connect(dbfile()) as con:
        cursor = con.cursor()
        try:
            cursor.execute("""
                SELECT      jsonstr
                FROM        puzzles
                WHERE       userid = ?
                AND         puzzlename = ?
            """, (userid, puzzlename))
            row = cursor.fetchone()
            jsonstr = row[0]
            pass
        except sqlite3.Error as e:
            msg = (
                f"Unable to get load puzzle {puzzlename} for userid {userid}"
                f", error={e}"
            )
            raise RuntimeError(msg)

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
    with sqlite3.connect(dbfile()) as con:
        con.row_factory = sqlite3.Row
        c = con.cursor
        modified = datetime.now().isoformat()
        jsonstr = puzzle.to_json()
        try:
            c.execute('''
                UPDATE      puzzles
                SET         modified=?, jsonstr=?
                WHERE       userid=?
                AND         puzzlename=?
                ''', (modified, jsonstr, userid))
        except sqlite3.Error as e:
            msg = (
                f"Could not update puzzle {puzzlename} for userid {userid}"
                f", error={e}"
            )
            raise RuntimeError(msg)


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
