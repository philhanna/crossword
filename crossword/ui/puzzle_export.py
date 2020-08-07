import csv
import json
import os
from io import StringIO

from crossword import Puzzle
from crossword.ui import DBPuzzle, PuzzleToXML, create_app, DBUser


class PuzzleExport:
    """ Exports a puzzle into one of three formats:

    json    - The JSON stored in the database
    xml     - XML in the format used by Crossword Compiler
    csv     - Just the clues, for use in a spreadsheet
    """

    def __init__(self, user, puzzlename, filename, filetype=None):
        """ Creates a PuzzleExport object

        :param user a DBUser
        :param puzzlename the name of the puzzle to be exported
        :param filename the output file name
        :param filetype one of 'json', 'xml', or 'csv' (optional)
        """
        self.user = user
        self.puzzlename = puzzlename
        self.filename = filename
        if not filetype:
            base, ext = os.path.splitext(filename)
            if not ext:
                errmsg = "Unable to determine file type from extension"
                raise ValueError(errmsg)
            filetype = ext
        filetype = filetype.upper()
        if filetype.startswith("."):
            filetype = filetype[1:]
        if filetype not in ['JSON', 'XML', 'CSV']:
            errmsg = f"File type must be JSON, XML, or CSV, not {filetype}"
            raise ValueError(errmsg)
        self.filetype = filetype

        # Load the puzzle
        userid = user.id
        row = DBPuzzle.query.filter_by(userid=userid, puzzlename=puzzlename).first()
        jsonstr = row.jsonstr
        self.puzzle = Puzzle.from_json(jsonstr)

    def run(self):
        """ Runs the export for the specified type """
        if self.filetype == 'JSON':
            output = self.run_json()
        elif self.filetype == 'XML':
            output = self.run_xml()
        elif self.filetype == 'CSV':
            output = self.run_csv()
        else:
            errmsg = f"Unknown file type {self.filetype}"
            raise ValueError(errmsg)

        with open(self.filename, "w") as fp:
            fp.write(output)

    def run_json(self):
        """ Creates JSON output """
        puzzle = self.puzzle
        puzzlename = self.puzzlename

        with StringIO() as fp:

            fp.write('{\n')
            fp.write(f'  "puzzlename": "{puzzlename}",\n')
            fp.write(f'  "n": {puzzle.n},\n')
            title = '"' + puzzle.title() + '"' if puzzle.title() else "null"
            fp.write(f'  "title": {title},\n')
            fp.write(f'  "cells": [\n')
            cellrows = str(puzzle).split('\n')
            for i, cellrow in enumerate(cellrows):
                comma = '' if i == len(cellrows) - 1 else ','
                fp.write(f'    "{cellrow}"{comma}\n')
            fp.write(f'  ],\n')
            fp.write(f'  "black_cells": [\n')
            for i, black_cell in enumerate([black_cell
                                            for black_cell in puzzle.black_cells]):
                comma = '' if i == len(puzzle.black_cells) - 1 else ','
                r, c = black_cell
                fp.write(f'    [{r},{c}]{comma}\n')
            fp.write(f'  ],\n')
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

            fp.write(f'  "across_words": [\n')
            write_words(puzzle.across_words)
            fp.write(f'  ],\n')

            fp.write(f'  "down_words": [\n')
            write_words(puzzle.down_words)
            fp.write(f'  ]\n')  # Note: no comma after last field

            fp.write('}')

            jsonstr = fp.getvalue()

        return jsonstr

    def run_xml(self):
        """ Creates XML output """
        return PuzzleToXML(self.user, self.puzzle).xmlstr

    def run_csv(self):
        """ Creates CSV output """
        puzzle = self.puzzle

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


#   ============================================================
#   Mainline
#   ============================================================
if __name__ == '__main__':
    app = create_app()
    app.app_context().push()

    import argparse

    description = r"""
Exports a puzzle into one of three formats:

JSON    - The JSON stored in the database
XML     - XML in the format used by Crossword Compiler
CSV     - Just the clues, for use in a spreadsheet
"""

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=description)
    parser.add_argument("-u", "--userid", default="1",
                        help="User ID (default = 1)")
    parser.add_argument("puzzlename",
                        help="Name of puzzle in the database")
    parser.add_argument("filename",
                        help="Output file containing puzzle in the specified format")
    parser.add_argument("filetype", nargs="?",
                        help="one of JSON, XML, or CSV")
    args = parser.parse_args()

    user = DBUser.query.filter_by(id=args.userid).first()
    puzzlename = args.puzzlename
    filename = args.filename
    filetype = args.filetype

    app = PuzzleExport(user, puzzlename, filename, filetype)
    app.run()
