import json
from io import StringIO

from crossword import Puzzle
from crossword.ui import create_app, list_puzzles, DBPuzzle


class PuzzleExport:
    """ Exports a puzzle from the database to a file in JSON format """

    def __init__(self, args):
        self.list = args.list
        self.puzzlename = args.puzzlename
        self.output = args.output

    def run(self):
        """ Runs the application """
        app = create_app()
        app.app_context().push()

        userid = 1  # TODO replace hard-coded user id

        # If the --list option was specified, just show the
        # list of puzzles in the puzzles root directory
        if self.list:
            list_puzzles(userid)
            return

        # Make sure a puzzle name was specified
        if not args.puzzlename:
            raise ValueError("No puzzle name specified")
        puzzlename = self.puzzlename

        # Load the puzzle
        row = DBPuzzle.query.filter_by(userid=userid, puzzlename=puzzlename).first()
        jsonstr = row.jsonstr
        puzzle = Puzzle.from_json(jsonstr)

        # Create the JSON representation
        jsonstr = self.create_json(puzzle, puzzlename)

        # Write to output
        if self.output:
            with open(self.output, "wt") as fp:
                print(jsonstr, file=fp)
        else:
            print(jsonstr)

    @staticmethod
    def create_json(puzzle, puzzlename):
        with StringIO() as fp:

            # Start of object
            fp.write('{\n')

            # Puzzle name
            fp.write(f'  "puzzlename": "{puzzlename}",\n')

            # n
            fp.write(f'  "n": {puzzle.n},\n')

            # title
            title = '"' + puzzle.get_title() + '"' if puzzle.get_title() else "null"
            fp.write(f'  "title": {title},\n')

            # Cells
            fp.write(f'  "cells": [\n')
            cellrows = str(puzzle).split('\n')
            for i, cellrow in enumerate(cellrows):
                comma = '' if i == len(cellrows) - 1 else ','
                fp.write(f'    "{cellrow}"{comma}\n')
            fp.write(f'  ],\n')

            # Black cells
            fp.write(f'  "black_cells": [\n')
            for i, black_cell in enumerate([black_cell
                                            for black_cell in puzzle.black_cells]):
                comma = '' if i == len(puzzle.black_cells) - 1 else ','
                r, c = black_cell
                fp.write(f'    [{r},{c}]{comma}\n')
            fp.write(f'  ],\n')

            # Numbered cells
            fp.write(f'  "numbered_cells": [\n')
            for i, numbered_cell in enumerate(numbered_cell
                                              for numbered_cell in puzzle.numbered_cells):
                comma = '' if i == len(puzzle.numbered_cells) - 1 else ','
                fp.write(f'    {json.dumps(vars(numbered_cell))}{comma}\n')
            fp.write(f'  ],\n')

            def write_words(wdict):
                wlist = [{'seq': seq,
                          'text': wdict[seq].get_text(),
                          'clue': wdict[seq].get_clue()
                          } for seq in sorted(wdict.keys())]
                for i, word in enumerate(word for word in wlist):
                    comma = '' if i == len(wlist) - 1 else ','
                    fp.write(f'    {json.dumps(word)}{comma}\n')

            # Across words
            fp.write(f'  "across_words": [\n')
            write_words(puzzle.across_words)
            fp.write(f'  ],\n')

            # Down words
            fp.write(f'  "down_words": [\n')
            write_words(puzzle.down_words)
            fp.write(f'  ]\n')  # Note: no comma after last field

            # End of object
            fp.write('}')

            jsonstr = fp.getvalue()

        return jsonstr


#   ============================================================
#   Mainline
#   ============================================================
if __name__ == '__main__':
    import argparse

    description = '''Exports a crossword puzzle to JSON format'''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-l", "--list", action="store_true",
                        help="List puzzles in the puzzle directory")
    parser.add_argument("-o", "--output",
                        help="Output file name (default=stdout)")
    parser.add_argument("puzzlename", nargs="?",
                        help="Input JSON file containing puzzle", default=None)
    args = parser.parse_args()

    app = PuzzleExport(args)
    app.run()
