#! /usr/bin/python3

import json
import os
import re
import tempfile
from http import HTTPStatus
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

from flask import Flask
from flask import flash
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask_session import Session

from crossword import PuzzlePublishAcrossLite, Word
from crossword import Configuration
from crossword import Grid
from crossword import GridToSVG, PuzzleToSVG
from crossword import PuzzlePublishNYTimes
from crossword import Puzzle
from crossword import WordList

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.config["DEBUG"] = True

# Secret key comes from os.urandom(24)
app.secret_key = b'\x8aws+6\x99\xd9\x87\xf0\xd6\xe8\xad\x9b\xfd\xed\xb9'

# This is required to add server-side session support

app.config["SESSION_TYPE"] = "filesystem"
Session(app)

wordlist = WordList()


#   ============================================================
#   Screen handlers
#   ============================================================
@app.route('/')
def main_screen():
    """ Handles top-level request """

    # Clear any existing session (except messages)
    messages = session.get('_flashes')
    session.clear()
    if messages:
        session['_flashes'] = messages

    enabled = {
        "grid_new": True,
        "grid_open": True,
        "puzzle_new": True,
        "puzzle_open": True,
    }
    return render_template('main.html',
                           enabled=enabled)


#   ============================================================
#   Menu option handlers
#   ============================================================
@app.route('/grid-new', methods=['POST'])
def grid_new():
    # Get the grid size from the form

    n = int(request.form.get('n'))

    # Remove any leftover grid name in the session
    session.pop('gridname', None)

    # Create the grid
    grid = Grid(n)
    jsonstr = grid.to_json()
    session['grid'] = jsonstr
    session['grid.initial'] = jsonstr

    return redirect(url_for('grid_screen'))


@app.route('/grid-open')
def grid_open():
    # Get the chosen grid name from the query parameters
    gridname = request.args.get('gridname')

    # Open the corresponding file and read its contents as json
    # and recreate the grid from it
    rootdir = Configuration.get_grids_root()
    filename = os.path.join(rootdir, gridname + ".json")
    with open(filename) as fp:
        jsonstr = fp.read()
    grid = Grid.from_json(jsonstr)

    # Store the grid and grid name in the session
    session['grid'] = jsonstr
    session['grid.initial'] = jsonstr
    session['gridname'] = gridname

    return redirect(url_for('grid_screen'))


@app.route('/grid-save', methods=['GET'])
def grid_save():
    gridname = session.get('gridname', request.args.get('gridname'))
    session['gridname'] = gridname
    return grid_save_common(gridname)


@app.route('/grid-save-as', methods=['GET'])
def grid_save_as():
    newgridname = request.args.get('newgridname')
    return grid_save_common(newgridname)


@app.route('/grid-delete')
def grid_delete():
    # Get the name of the grid to be deleted from the session
    # Delete the file

    gridname = session.get('gridname', None)
    if gridname:
        filename = os.path.join(Configuration.get_grids_root(), gridname + ".json")
        if os.path.exists(filename):
            os.remove(filename)
            flash(f"{gridname} grid deleted")
        else:
            flash(f"{gridname} was never saved - no need to delete")
    else:
        flash("There is no grid to delete")

    # Redirect to the main screen
    return redirect(url_for('main_screen'))


@app.route('/puzzle', methods=['GET'])
def puzzle_screen():
    # Get the existing puzzle from the session
    puzzle = Puzzle.from_json(session['puzzle'])
    puzzlename = session.get('puzzlename', None)

    # Create the SVG
    svg = PuzzleToSVG(puzzle)
    boxsize = svg.boxsize
    svgstr = svg.generate_xml()

    enabled = {
        "puzzle_save": True,
        "puzzle_save_as": True,
        "puzzle_stats": True,
        "puzzle_title": True,
        "puzzle_undo": len(puzzle.undo_stack) > 0,
        "puzzle_redo": len(puzzle.redo_stack) > 0,
        "puzzle_close": True,
        "puzzle_delete": puzzlename is not None,
    }

    # Send puzzle.html to the client
    return render_template('puzzle.html',
                           enabled=enabled,
                           puzzlename=puzzlename,
                           puzzletitle=puzzle.get_title(),
                           n=puzzle.n,
                           boxsize=boxsize,
                           svgstr=svgstr)


@app.route('/puzzle-new')
def puzzle_new():
    # Get the chosen grid name from the query parameters
    gridname = request.args.get('gridname')

    # Open the corresponding file and read its contents as json
    # and recreate the grid from it
    rootdir = Configuration.get_grids_root()
    filename = os.path.join(rootdir, gridname + ".json")
    with open(filename) as fp:
        jsonstr = fp.read()
    grid = Grid.from_json(jsonstr)

    # Now pass this grid to the Puzzle() constructor
    puzzle = Puzzle(grid)
    n = puzzle.n

    # Save puzzle in the session
    jsonstr = puzzle.to_json()
    session['puzzle'] = jsonstr
    session['puzzle.initial'] = jsonstr

    # Remove any leftover puzzle name in the session
    session.pop('puzzlename', None)

    return redirect(url_for('puzzle_screen'))

    pass


@app.route('/puzzle-open')
def puzzle_open():
    # Get the chosen puzzle name from the query parameters
    puzzlename = request.args.get('puzzlename')

    # Open the corresponding file and read its contents as json
    # and recreate the puzzle from it
    rootdir = Configuration.get_puzzles_root()
    filename = os.path.join(rootdir, puzzlename + ".json")
    with open(filename) as fp:
        jsonstr = fp.read()

    # Store the puzzle and puzzle name in the session
    session['puzzle'] = jsonstr
    session['puzzle.initial'] = jsonstr
    session['puzzlename'] = puzzlename

    return redirect(url_for('puzzle_screen'))


@app.route('/puzzle-save', methods=['GET'])
def puzzle_save():
    puzzlename = session.get('puzzlename', request.args.get('puzzlename'))
    session['puzzlename'] = puzzlename
    return puzzle_save_common(puzzlename)


@app.route('/puzzle-save-as', methods=['GET'])
def puzzle_save_as():
    newpuzzlename = request.args.get('newpuzzlename')
    return puzzle_save_common(newpuzzlename)


@app.route('/puzzle-delete')
def puzzle_delete():
    # Get the name of the puzzle to be deleted from the session
    # Delete the file

    puzzlename = session.get('puzzlename', None)
    if puzzlename:
        filename = os.path.join(Configuration.get_puzzles_root(), puzzlename + ".json")
        if os.path.exists(filename):
            os.remove(filename)
            flash(f"{puzzlename} puzzle deleted")
        else:
            flash(f"{puzzlename} was never saved - no need to delete")
    else:
        flash("There is no puzzle to delete")

    # Redirect to the main screen

    return redirect(url_for('main_screen'))


@app.route('/puzzle-undo', methods=['GET'])
def puzzle_undo():
    jsonstr = session.get('puzzle', None)
    puzzle = Puzzle.from_json(jsonstr)
    puzzle.undo()
    jsonstr = puzzle.to_json()
    session['puzzle'] = jsonstr
    return redirect(url_for('puzzle_screen'))


@app.route('/puzzle-redo', methods=['GET'])
def puzzle_redo():
    jsonstr = session.get('puzzle', None)
    puzzle = Puzzle.from_json(jsonstr)
    puzzle.redo()
    jsonstr = puzzle.to_json()
    session['puzzle'] = jsonstr
    return redirect(url_for('puzzle_screen'))


@app.route('/puzzle-click-across', methods=['GET'])
def puzzle_click_across():
    return puzzle_click('Across')


@app.route('/puzzle-click-down', methods=['GET'])
def puzzle_click_down():
    return puzzle_click('Down')


@app.route('/word-edit', methods=['POST'])
def word_edit():
    # Get the seq, direction, and length from the session
    seq = session.get('seq')
    length = session.get('length')
    direction = session.get('direction')
    direction = Word.ACROSS if direction.upper()[0] == Word.ACROSS else Word.DOWN

    # Get the word and clue from the form
    text = request.form.get('text')
    clue = request.form.get('clue')

    # Make the text uppercase and replace "." with blanks
    text = text.upper()
    text = re.sub(r'\.', ' ', text)
    if len(text) < length:
        text += " " * length
        text = text[:length]
    # If the word is not complete, change the clue to blanks
    if ' ' in text:
        clue = ""

    # Set the word text and clue and save the puzzle in the session again
    puzzle = Puzzle.from_json(session.get('puzzle'))
    puzzle.set_text(seq, direction, text)
    puzzle.set_clue(seq, direction, clue)
    session['puzzle'] = puzzle.to_json()

    # Now redirect to puzzle_screen()
    return redirect(url_for('puzzle_screen'))


@app.route('/puzzle_publish_acrosslite')
def puzzle_publish_acrosslite():
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


@app.route('/puzzle_publish_nytimes')
def puzzle_publish_nytimes():
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


#   ============================================================
#   REST api - functions that just return JSON
#   ============================================================

@app.route('/grids')
def grids():
    # Make a list of all the saved grids
    gridlist = []
    rootdir = Configuration.get_grids_root()
    for filename in os.listdir(rootdir):
        if filename.endswith(".json"):
            fullpath = os.path.join(rootdir, filename)
            filetime = os.path.getmtime(fullpath)
            basename = os.path.splitext(filename)[0]
            gridlist.append(f"{filetime}|{basename}")
    gridlist.sort(reverse=True)
    gridlist = [gridname.split('|', 2)[1] for gridname in gridlist]

    # Send this back to the client in JSON
    resp = make_response(json.dumps(gridlist), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


@app.route('/grid-statistics', methods=['GET'])
def grid_statistics():
    # Get the grid name and grid from the session
    gridname = session.get('gridname', '(Untitled)')
    grid = Grid.from_json(session['grid'])
    stats = grid.get_statistics()
    resp = make_response(json.dumps(stats), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


@app.route('/puzzle-statistics', methods=['GET'])
def puzzle_statistics():
    jsonstr = session['puzzle']
    puzzle = Puzzle.from_json(jsonstr)
    stats = puzzle.get_statistics()
    resp = make_response(json.dumps(stats), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


@app.route('/puzzle-title', methods=['POST'])
def puzzle_title():
    title = request.form.get('title', None)
    if title:
        jsonstr = session['puzzle']
        puzzle = Puzzle.from_json(jsonstr)
        puzzle.set_title(title)
        jsonstr = puzzle.to_json()
        session['puzzle'] = jsonstr
        flash(f"Puzzle title set to {puzzle.get_title()}")

    # Show the puzzle screen
    return redirect(url_for('puzzle_screen'))


@app.route('/puzzles')
def puzzles():
    # Make a list of all the saved puzzles
    puzzlelist = []
    rootdir = Configuration.get_puzzles_root()
    for filename in os.listdir(rootdir):
        if filename.endswith(".json"):
            fullpath = os.path.join(rootdir, filename)
            filetime = os.path.getmtime(fullpath)
            basename = os.path.splitext(filename)[0]
            puzzlelist.append(f"{filetime}|{basename}")
    puzzlelist.sort(reverse=True)
    puzzlelist = [puzzlename.split('|', 2)[1] for puzzlename in puzzlelist]

    # Send this back to the client in JSON
    resp = make_response(json.dumps(puzzlelist), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


@app.route('/wordlists', methods=['GET'])
def wordlists():
    # Get the pattern from the query parameters
    pattern = request.args.get('pattern')
    words = wordlist.lookup(pattern)
    jsonstr = json.dumps(words)

    # Send this back to the client in JSON
    resp = make_response(jsonstr, HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


@app.route('/grid-changed', methods=['GET'])
def grid_changed():
    # Compare the original grid loaded to its current values.
    # Return True if they are different, False if they are the same.
    jsonstr_initial = session.get('grid.initial', None)
    jsonstr_current = session.get('grid', None)
    changed = not (jsonstr_current == jsonstr_initial)
    obj = {"changed": changed}

    # Send this back to the client in JSON
    resp = make_response(json.dumps(obj), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


@app.route('/puzzle-changed', methods=['GET'])
def puzzle_changed():
    # Compare the original puzzle loaded to its current values.
    # Return True if they are different, False if they are the same.
    jsonstr_initial = session.get('puzzle.initial', None)
    jsonstr_current = session.get('puzzle', None)
    changed = not (jsonstr_current == jsonstr_initial)

    obj = {"changed": changed}

    # Send this back to the client in JSON
    resp = make_response(json.dumps(obj), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


@app.route('/word-reset', methods=['GET'])
def word_reset():
    # Get the puzzle, word seq, word direction, and word length from the session
    puzzle = Puzzle.from_json(session['puzzle'])
    seq = session.get('seq')
    length = session.get('length')
    direction = session.get('direction')
    direction = Word.ACROSS if direction.upper()[0] == Word.ACROSS else Word.DOWN

    # Get the word
    if direction == Word.ACROSS:
        word = puzzle.get_across_word(seq)
    elif direction == Word.DOWN:
        word = puzzle.get_down_word(seq)
    else:
        raise RuntimeError("Direction is not A or D")

    # Send cleared text back to the client in JSON
    new_text = word.get_clear_word()
    new_text = re.sub(' ', '.', new_text)
    resp = make_response(json.dumps(new_text), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


@app.route('/grid-rotate', methods=['GET'])
def grid_rotate():
    # Rotate the grid
    jsonstr = session.get('grid', None)
    grid = Grid.from_json(jsonstr)
    grid.rotate()

    # Save the updated grid in the session
    session['grid'] = grid.to_json()

    # Send the new SVG data to the client
    svg = GridToSVG(grid)
    svgstr = svg.generate_xml()
    response = make_response(svgstr, HTTPStatus.OK)
    return response


#   ============================================================
#   Internal methods
#   ============================================================

def grid_save_common(gridname):
    # Recreate the grid from the JSON in the session
    # and validate it
    jsonstr = session.get('grid', None)
    grid = Grid.from_json(jsonstr)
    ok, messages = grid.validate()
    if not ok:
        flash("Grid not saved")
        for message_type in messages:
            message_list = messages[message_type]
            if len(message_list) > 0:
                flash(f"*** {message_type} ***")
                for message in message_list:
                    flash("   " + message)
    else:
        # Save the file
        rootdir = Configuration.get_grids_root()
        filename = os.path.join(rootdir, gridname + ".json")
        with open(filename, "w") as fp:
            fp.write(jsonstr)

        # Send message about save
        flash(f"Grid saved as {gridname}")

        # Store the saved version of the grid in the session
        # as 'grid.initial' so that we can detect whether
        # it has been changed since it was last saved
        session['grid.initial'] = jsonstr

    # Show the grid screen
    return redirect(url_for('grid_screen'))


@app.route('/grid', methods=['GET'])
def grid_screen():
    # Get the existing grid from the session
    grid = Grid.from_json(session['grid'])
    gridname = session.get('gridname', None)

    # Create the SVG
    svg = GridToSVG(grid)
    boxsize = svg.boxsize
    svgstr = svg.generate_xml()

    # Enable menu options
    enabled = {
        "grid_save": True,
        "grid_save_as": True,
        "grid_stats": True,
        "grid_rotate": True,
        "grid_close": True,
        "grid_delete": gridname is not None,
    }

    # Show the grid.html screen
    return render_template('grid.html',
                           enabled=enabled,
                           n=grid.n,
                           gridname=gridname,
                           boxsize=boxsize,
                           svgstr=svgstr)


def puzzle_save_common(puzzlename):
    # Recreate the puzzle from the JSON in the session
    # and validate it
    jsonstr = session.get('puzzle', None)
    puzzle = Puzzle.from_json(jsonstr)
    ok, messages = puzzle.validate()
    if not ok:
        flash("Puzzle not saved")
        for message_type in messages:
            message_list = messages[message_type]
            if len(message_list) > 0:
                flash(f"*** {message_type} ***")
                for message in message_list:
                    flash("   " + message)
    else:
        # Save the file
        rootdir = Configuration.get_puzzles_root()
        filename = os.path.join(rootdir, puzzlename + ".json")
        with open(filename, "w") as fp:
            fp.write(jsonstr)

        # Send message about the save
        flash(f"Puzzle saved as {puzzlename}")

        # Store the saved version of the puzzle in the session
        # as 'puzzle.initial' so that we can detect whether
        # it has been changed since it was last saved
        session['puzzle.initial'] = jsonstr

    # Show the puzzle screen
    return redirect(url_for('puzzle_screen'))


def puzzle_click(direction):
    """ Internal method to avoid duplication across/down"""
    # Get the row and column clicked from the query parms
    r = int(request.args.get('r'))
    c = int(request.args.get('c'))

    # Get the existing puzzle from the session
    puzzle = Puzzle.from_json(session['puzzle'])

    # Get the numbered cell at (r, c)
    numbered_cell = puzzle.get_numbered_cell(r, c)
    if not numbered_cell:
        errmsg = f"({r},{c}) is not a numbered cell"
        response = make_response(errmsg, HTTPStatus.NOT_FOUND)
        return response

    # Get the word word at (r, c)
    if direction.startswith('A'):
        word = puzzle.get_across_word(numbered_cell.seq)
        if not word:
            errmsg = f"({r},{c}) is not the start of an across word"
            response = make_response(errmsg, HTTPStatus.NOT_FOUND)
            return response
    else:
        word = puzzle.get_down_word(numbered_cell.seq)
        if not word:
            errmsg = f"({r},{c}) is not the start of a down word"
            response = make_response(errmsg, HTTPStatus.NOT_FOUND)
            return response
        pass

    # Save seq, direction, and length in the session
    session['seq'] = numbered_cell.seq
    session['direction'] = direction
    session['length'] = word.length

    # Get the existing text and clue from this word
    # and replace blanks with "."
    text = word.get_text()
    text = re.sub(' ', '.', text)
    clue = word.get_clue()
    if not clue:
        clue = ""

    # Store parameters in a JSON string
    parms = {
        "seq": numbered_cell.seq,
        "direction": direction,
        "text": text,
        "clue": clue,
        "length": word.length
    }
    parmstr = json.dumps(parms)

    # Invoke the puzzle word editor

    resp = make_response(parmstr, HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"

    return resp


@app.route('/grid-click', methods=['GET'])
def grid_click():
    # Get the row and column clicked from the query parms
    r = int(request.args.get('r'))
    c = int(request.args.get('c'))

    # Get the existing grid from the session
    jsonstr = session['grid']
    grid = Grid.from_json(jsonstr)

    # Toggle the black cell status
    if grid.is_black_cell(r, c):
        grid.remove_black_cell(r, c)
    else:
        grid.add_black_cell(r, c)

    # Save the updated grid in the session
    session['grid'] = grid.to_json()

    # Send the new SVG data to the client
    svg = GridToSVG(grid)
    svgstr = svg.generate_xml()
    response = make_response(svgstr, HTTPStatus.OK)
    return response


#   ============================================================
#   Mainline
#   ============================================================
if __name__ == '__main__':
    app.run()
