""" Handles requests having to do with publishing a puzzle
"""
import os
import sqlite3
import tempfile
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
from flask import request, make_response
from crossword import Puzzle, PuzzlePublishAcrossLite, PuzzlePublishNYTimes, dbfile


def puzzle_publish_acrosslite():
    """ Publishes a puzzle in across lite form """

    # Get the chosen puzzle name from the query parameters
    puzzlename = request.args.get('puzzlename')

    # Open the corresponding row in the database, read its JSON
    # and recreate the puzzle from it
    userid = 1      # TODO replace the hard-coded user ID
    jsonstr = puzzle_load_common(userid, puzzlename)
    puzzle = Puzzle.from_json(jsonstr)

    # Generate the output
    publisher = PuzzlePublishAcrossLite(puzzle, puzzlename)

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


def puzzle_publish_nytimes():
    """ Publishes a puzzle in New York Times format (PDF) """

    # Get the chosen puzzle name from the query parameters
    puzzlename = request.args.get('puzzlename')

    # Open the corresponding row in the database, read its JSON
    # and recreate the puzzle from it
    userid = 1      # TODO replace the hard-coded user ID
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


def puzzle_load_common(userid, puzzlename):
    """ Loads the JSON string for a puzzle """
    with sqlite3.connect(dbfile()) as con:
        try:
            con.row_factory = sqlite3.Row
            c = con.cursor()
            c.execute('''
                SELECT  jsonstr
                FROM    puzzles
                WHERE   userid=?
                AND     puzzlename=?''', (userid, puzzlename))
            row = c.fetchone()
            jsonstr = row['jsonstr']
        except sqlite3.Error as e:
            msg = (
                f"Unable to load puzzle"
                f", userid={userid}"
                f", puzzlename={puzzlename}"
                f", error={e}"
            )
            jsonstr = None
        return jsonstr
