""" Handles requests having to do with publishing a puzzle
"""
import os
import tempfile
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

from flask import Blueprint
from flask import make_response
from flask import request

from crossword.puzzles import Puzzle
from crossword.ui import DBPuzzle, DBUser, PuzzlePublishAcrossLite, PuzzlePublishNYTimes, PuzzleToXML

userid = 1  # TODO Replace hard-coded user ID

# Register this blueprint
uipublish = Blueprint('uipublish', __name__)


@uipublish.route('/puzzle-publish-acrosslite')
def puzzle_publish_acrosslite():
    """ Publishes a puzzle in across lite form """

    # Get the chosen puzzle name from the query parameters
    puzzlename = request.args.get('puzzlename')

    # Open the corresponding row in the database, read its JSON
    # and recreate the puzzle from it
    jsonstr = puzzle_load_common(userid, puzzlename)
    puzzle = Puzzle.from_json(jsonstr)

    # Generate the output
    user = DBUser.query.filter_by(id=userid).first()
    publisher = PuzzlePublishAcrossLite(user, puzzle, puzzlename)

    # Text file
    filename = os.path.join(tempfile.gettempdir(), puzzlename + ".txt")
    txt_filename = filename
    with open(filename, "wt") as fp:
        fp.write(publisher.get_txt() + "\n")

    # JSON
    filename = os.path.join(tempfile.gettempdir(), puzzlename + ".json")
    json_filename = filename
    with open(filename, "wt") as fp:
        fp.write(jsonstr + "\n")

    # Create an in-memory zip file
    with BytesIO() as fp:
        with ZipFile(fp, mode="w", compression=ZIP_DEFLATED) as zf:
            zf.write(txt_filename, puzzlename + ".txt")
            zf.write(json_filename, puzzlename + ".json")
        zipbytes = fp.getvalue()

    # Return it as an attachment
    zipfilename = f"acrosslite-{puzzlename}.zip"
    resp = make_response(zipbytes)
    resp.headers['Content-Type'] = "application/zip"
    resp.headers['Content-Disposition'] = f'attachment; filename="{zipfilename}"'
    return resp


@uipublish.route('/puzzle-publish-cwcompiler')
def puzzle_publish_cwcompiler():
    """ Publishes a puzzle in the Crossword Compiler XML format """

    # Get the chosen puzzle name from the query parameters
    puzzlename = request.args.get('puzzlename')

    # Open the corresponding row in the database, read its JSON
    # and recreate the puzzle from it
    jsonstr = puzzle_load_common(userid, puzzlename)
    puzzle = Puzzle.from_json(jsonstr)

    # Generate the output
    user = DBUser.query.filter_by(id=userid).first()
    publisher = PuzzleToXML(user, puzzle)

    # XML file
    xml_filename = filename = os.path.join(tempfile.gettempdir(), puzzlename + ".xml")
    with open(filename, "wt") as fp:
        fp.write(publisher.xmlstr + "\n")

    # JSON
    json_filename = filename = os.path.join(tempfile.gettempdir(), puzzlename + ".json")
    with open(filename, "wt") as fp:
        fp.write(jsonstr + "\n")

    # Create an in-memory zip file
    with BytesIO() as fp:
        with ZipFile(fp, mode="w", compression=ZIP_DEFLATED) as zf:
            zf.write(xml_filename, puzzlename + ".xml")
            zf.write(json_filename, puzzlename + ".json")
        zipbytes = fp.getvalue()

    # Return it as an attachment
    zipfilename = f"cwcompiler-{puzzlename}.zip"
    resp = make_response(zipbytes)
    resp.headers['Content-Type'] = "application/zip"
    resp.headers['Content-Disposition'] = f'attachment; filename="{zipfilename}"'
    return resp


@uipublish.route('/puzzle-publish-nytimes')
def puzzle_publish_nytimes():
    """ Publishes a puzzle in New York Times format (PDF) """

    # Get the chosen puzzle name from the query parameters
    puzzlename = request.args.get('puzzlename')

    # Open the corresponding row in the database, read its JSON
    # and recreate the puzzle from it
    jsonstr = puzzle_load_common(userid, puzzlename)
    puzzle = Puzzle.from_json(jsonstr)

    # Generate the output
    publisher = PuzzlePublishNYTimes(puzzle, puzzlename)

    # SVG
    filename = os.path.join(tempfile.gettempdir(), puzzlename + ".svg")
    svg_filename = filename
    with open(filename, "wt") as fp:
        fp.write(publisher.get_svg() + "\n")

    # HTML
    filename = os.path.join(tempfile.gettempdir(), puzzlename + ".html")
    html_filename = filename
    with open(filename, "wt") as fp:
        fp.write(publisher.get_html() + "\n")

    # JSON
    filename = os.path.join(tempfile.gettempdir(), puzzlename + ".json")
    json_filename = filename
    with open(filename, "wt") as fp:
        fp.write(jsonstr + "\n")

    # Create an in-memory zip file
    with BytesIO() as fp:
        with ZipFile(fp, mode="w", compression=ZIP_DEFLATED) as zf:
            zf.write(svg_filename, puzzlename + ".svg")
            zf.write(html_filename, puzzlename + ".html")
            zf.write(json_filename, puzzlename + ".json")
        zipbytes = fp.getvalue()

    # Return it as an attachment
    zipfilename = f"nytimes-{puzzlename}.zip"
    resp = make_response(zipbytes)
    resp.headers['Content-Type'] = "application/zip"
    resp.headers['Content-Disposition'] = f'attachment; filename="{zipfilename}"'
    return resp


#   ============================================================
#   Internal methods
#   ============================================================


def puzzle_load_common(userid, puzzlename):
    """ Loads the JSON string for a puzzle """
    row = DBPuzzle.query.filter_by(userid=userid, puzzlename=puzzlename).first()
    jsonstr = row.jsonstr
    return jsonstr
