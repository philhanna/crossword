import logging
import os
from datetime import datetime

from crossword.ui import list_puzzles, create_app, DBPuzzle, db

userid = 1  # TODO Replace hard-coded userID


class JSONImport:
    """ Updates a puzzle database with data from a JSON file """

    def __init__(self, args):
        """ Creates a new JSONImport object"""
        self.list = args.get('list', None)
        self.filename = args.get('filename', None)
        self.puzzlename = args.get('puzzle', None)

    def run(self):
        """ Runs the import """

        app = create_app()
        app.app_context().push()

        # If the --list option was specified, just list
        # the existing puzzles and exit
        if self.list:
            list_puzzles(userid)
            exit(0)

        # Make sure a file name and puzzle name were specified on the command line
        if not self.filename:
            raise ValueError("No file name specified")
        if not self.puzzlename:
            raise ValueError("No puzzle name specified")

        # Load the JSON from the file
        filename = os.path.expanduser(self.filename)
        if not filename.endswith(".json"):
            filename = filename + ".json"
        filename = os.path.abspath(filename)
        logging.info(f"Loading JSON from {filename}")
        with open(filename) as fp:
            jsonstr = fp.read()

        # See if the puzzle exists in the database
        dbpuzzle = DBPuzzle.query.filter_by(userid=userid, puzzlename=self.puzzlename).first()
        if dbpuzzle:
            # Existing puzzle. This is an update
            logging.info(f"Updating {self.puzzlename} puzzle with id={dbpuzzle.id}")
            dbpuzzle.modified = datetime.now().isoformat()
            dbpuzzle.jsonstr = jsonstr
            db.session.commit()
        else:
            # New puzzle. This is an add
            logging.info(f"Adding {self.puzzlename} puzzle")
            created = modified = datetime.now().isoformat()
            dbpuzzle = DBPuzzle(userid=userid,
                                puzzlename=self.puzzlename,
                                created=created,
                                modified=modified,
                                jsonstr=jsonstr)
            db.session.add(dbpuzzle)
            db.session.commit()
            pass
        logging.info("Done")

#   ============================================================
#   Mainline
#   ============================================================
if __name__ == '__main__':
    import argparse

    description = """\
Imports data from a JSON file created by puzzle_export.
It may either be for an existing puzzle (SQL UPDATE) or
a new one (SQL INSERT).  In the latter case, the JSON
was likely created by another user.
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("-l", "--list", action="store_true",
                        help="List puzzles in the puzzle directory")
    parser.add_argument("filename", nargs="?",
                        help="Input JSON file", default=None)
    parser.add_argument("puzzle", nargs="?",
                        help="Puzzle name")
    args = parser.parse_args()

    try:
        importer = JSONImport(vars(args))
        importer.run()
    except Exception as e:
        print(f"Puzzle import failed: {e}")
        exit(-2)
