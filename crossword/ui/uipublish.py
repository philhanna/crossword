""" Handles requests having to do with publishing a puzzle
"""
import os
import tempfile
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

from flask import request, make_response

from crossword import Configuration, Puzzle, PuzzlePublishAcrossLite, PuzzlePublishNYTimes


def puzzle_publish_acrosslite():
    """ Publishes a puzzle in across lite form """

    # Get the chosen puzzle name from the query parameters
    puzzlename = request.args.get('puzzlename')

    # Open the corresponding file and read its contents as json
    # and recreate the puzzle from it
    rootdir = Configuration.get_puzzles_root()
    filename = os.path.join(rootdir, puzzlename + ".json")
    with open(filename) as fp:
        jsonstr = fp.read()
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

    # Open the corresponding file and read its contents as json
    # and recreate the puzzle from it
    rootdir = Configuration.get_puzzles_root()
    filename = os.path.join(rootdir, puzzlename + ".json")
    with open(filename) as fp:
        jsonstr = fp.read()
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
