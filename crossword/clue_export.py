#! /usr/bin/python3
import csv
import sqlite3
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


def visit_puzzle(puzzle):
    """ Writes the words and clues to a string in CSV format """
    with StringIO(newline=None) as fp:

        cfp = csv.writer(fp)

        # Column headings
        cfp.writerow(['seq', 'direction', 'word', 'clue'])

        # Across
        for seq in sorted(puzzle.across_words):
            across_word = puzzle.across_words[seq]
            direction = 'across'
            text = across_word.get_text()
            clue = across_word.get_clue()
            cfp.writerow([seq, direction, text, clue])

        # Down
        for seq in sorted(puzzle.down_words):
            down_word = puzzle.down_words[seq]
            direction = 'down'
            text = down_word.get_text()
            clue = down_word.get_clue()
            cfp.writerow([seq, direction, text, clue])

        value = fp.getvalue().strip()  # Hack to work around final extra \n CSVWriter adds
        csvstr = value
        return csvstr


def main(args):
    userid = 1  # TODO replace hard-coded user id

    # If the --list option was specified, just show the
    # list of puzzles in the puzzles root directory

    if args.list:
        list_puzzles(userid)
        exit(0)

    # Open the input file and load the JSON it contains.
    # Construct a puzzle from it

    if not args.puzzlename:
        raise ValueError("No puzzle name specified")
    puzzlename = args.puzzlename

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

    # Create the CSV output
    csvstr = visit_puzzle(puzzle)

    if args.output:
        with open(args.output, "wt") as fp:
            print(csvstr, file=fp)
    else:
        # Stdout
        print(csvstr)


#   ============================================================
#   Mainline
#   ============================================================
if __name__ == '__main__':
    import argparse

    description = '''Exports a crossword puzzle to .csv format'''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-l", "--list", action="store_true",
                        help="List puzzles in the puzzle directory")
    parser.add_argument("-o", "--output",
                        help="Output file name (default=stdout)")
    parser.add_argument("puzzlename", nargs="?",
                        help="Input JSON file containing puzzle", default=None)
    args = parser.parse_args()

    main(args)
