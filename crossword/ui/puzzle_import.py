import csv
import json
import os
from datetime import datetime
from io import StringIO

from crossword import Puzzle
from crossword.ui import DBPuzzle, PuzzleToXML, create_app, DBUser, PuzzleFromXML, db
from crossword.ui.puzzle_from_acrosslite import PuzzleFromAcrossLite


class PuzzleImport:
    """ Imports a puzzle from one of three formats:

    json    - The JSON stored in the database
    puz     - An AcrossLite puzzle
    xml     - XML in the format used by Crossword Compiler
    csv     - Just the clues, for use in a spreadsheet
    """

    def __init__(self, user, puzzlename, filename, filetype=None):
        """ Creates a PuzzleImport object

        :param user a DBUser
        :param puzzlename the name of the puzzle to be imported
        :param filename the input file name
        :param filetype one of 'json', 'puz', 'xml', or 'csv' (optional)
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
        if filetype not in ['JSON', 'PUZ', 'XML', 'CSV']:
            errmsg = f"File type must be JSON, PUZ, XML, or CSV, not {filetype}"
            raise ValueError(errmsg)
        self.filetype = filetype

        # Load the data
        opentype = 'rb' if filetype == 'PUZ' else 'rt'
        with open(filename, opentype) as fp:
            self.data = fp.read()

    def run(self):
        """ Runs the import for the specified type """
        if self.filetype == 'JSON':
            puzzle = self.run_json()
        elif self.filetype == 'PUZ':
            puzzle = self.run_puz()
        elif self.filetype == 'XML':
            puzzle = self.run_xml()
        elif self.filetype == 'CSV':
            puzzle = self.run_csv()
        else:
            errmsg = f"Unknown file type {self.filetype}"
            raise ValueError(errmsg)

        # Rewrite the puzzle
        jsonstr = puzzle.to_json()
        puzzle = DBPuzzle.query.filter_by(userid=self.user.id, puzzlename=self.puzzlename).first()
        if not puzzle:
            created = modified = datetime.now().isoformat()
            puzzle = DBPuzzle(
                userid = self.user.id,
                puzzlename = self.puzzlename,
                created = created,
                modified = modified,
                jsonstr = jsonstr
            )
            db.session.add(puzzle)
            pass
        else:
            modified = datetime.now().isoformat()
            puzzle.jsonstr = jsonstr
            puzzle.modified = modified
            pass
        db.session.commit()
        pass

    def run_json(self):
        """ Creates puzzle from JSON input """
        return Puzzle.from_json(self.data)

    def run_puz(self):
        """ Creates the puzzle from an AcrossLite file """
        return PuzzleFromAcrossLite(self.data).puzzle

    def run_xml(self):
        """ Creates puzzle from XML input """
        return PuzzleFromXML(self.data).puzzle

    def run_csv(self):
        """ Uploads puzzle clues from CSV input """
        csvstr = self.data
        user = self.user
        userid = user.id
        puzzlename = self.puzzlename
        puzzle = DBPuzzle.query.filter_by(userid=userid, puzzlename=puzzlename).first()
        if not puzzle:
            errmsg = f"Puzzle '{puzzlename}' does not exist"
            raise ValueError(errmsg)
        jsonstr = puzzle.jsonstr
        puzzle = Puzzle.from_json(jsonstr)

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

        return puzzle


#   ============================================================
#   Mainline
#   ============================================================
if __name__ == '__main__':
    app = create_app()
    app.app_context().push()

    import argparse

    description = r"""
Imports a puzzle from one of three formats:

JSON    - The JSON stored in the database
PUZ     - An AcrossLite puzzle file
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
                        help="Input file containing puzzle in the specified format")
    parser.add_argument("filetype", nargs="?",
                        help="one of JSON, PUZ, XML, or CSV")
    args = parser.parse_args()

    user = DBUser.query.filter_by(id=args.userid).first()
    puzzlename = args.puzzlename
    filename = args.filename
    filetype = args.filetype

    app = PuzzleImport(user, puzzlename, filename, filetype)
    app.run()
