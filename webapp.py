#! /usr/bin/python3
import json
import os
import re
import tempfile
from http import HTTPStatus
from flask import Flask, flash, request, make_response, redirect, render_template, session, url_for

from configuration import Configuration
from grid import Grid
from nytimes_output import NYTimesOutput
from puzzle import Puzzle
from to_svg import GridToSVG, PuzzleToSVG
from wordlist import WordList

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.config["DEBUG"] = True
# Secret key comes from os.urandom(24)
app.secret_key = b'\x8aws+6\x99\xd9\x87\xf0\xd6\xe8\xad\x9b\xfd\xed\xb9'

config = Configuration()
wordlist = WordList()


#   ============================================================
#   Screen handlers
#   ============================================================
@app.route('/')
def main_screen():
    """ Handles top-level request """
    enabled = {
        "new_grid": True,
        "open_grid": True,
        "new_puzzle": True,
        "open_puzzle": True,
    }
    return render_template('main.html',
                           enabled=enabled)


#   ============================================================
#   Menu option handlers
#   ============================================================
@app.route('/new-grid', methods=['POST'])
def new_grid_screen():
    # Get the grid size from the form

    n = int(request.form.get('n'))

    # Remove any leftover grid name in the session
    session.pop('gridname', None)

    # Create the grid
    grid = Grid(n)
    session['grid'] = grid.to_json()

    # Create the SVG
    svg = GridToSVG(grid)
    boxsize = svg.boxsize
    svgstr = svg.generate_xml()

    # Enable menu options
    enabled = {
        "save_grid_as": True,
        "close_grid": True
    }

    # Show the grid.html screen
    return render_template('grid.html',
                           enabled=enabled,
                           n=n,
                           boxsize=boxsize,
                           svgstr=svgstr)


@app.route('/open-grid')
def open_grid_screen():
    # Get the chosen grid name from the query parameters
    gridname = request.args.get('gridname')

    # Open the corresponding file and read its contents as json
    # and recreate the grid from it
    rootdir = config.get_grids_root()
    filename = os.path.join(rootdir, gridname + ".json")
    with open(filename) as fp:
        jsonstr = fp.read()
    grid = Grid.from_json(jsonstr)

    # Store the grid and grid name in the session
    session['grid'] = jsonstr
    session['gridname'] = gridname

    # Create the SVG
    svg = GridToSVG(grid)
    boxsize = svg.boxsize
    svgstr = svg.generate_xml()

    # Enable the menu options
    enabled = {
        "save_grid": True,
        "save_grid_as": True,
        "close_grid": True
    }

    # Go to grid.html
    return render_template('grid.html',
                           enabled=enabled,
                           n=grid.n,
                           gridname=gridname,
                           boxsize=boxsize,
                           svgstr=svgstr)

    pass


@app.route('/grid-save', methods=['GET'])
def grid_save():
    gridname = session['gridname']
    return grid_common_save(gridname)


@app.route('/grid-save-as', methods=['GET'])
def grid_save_as():
    gridname = request.args.get('gridname')
    session['gridname'] = gridname
    return grid_common_save(gridname)


@app.route('/new-puzzle')
def new_puzzle_screen():
    # Get the chosen grid name from the query parameters
    gridname = request.args.get('gridname')

    # Open the corresponding file and read its contents as json
    # and recreate the grid from it
    rootdir = config.get_grids_root()
    filename = os.path.join(rootdir, gridname + ".json")
    with open(filename) as fp:
        jsonstr = fp.read()
    grid = Grid.from_json(jsonstr)

    # Now pass this grid to the Puzzle() constructor
    puzzle = Puzzle(grid)
    n = puzzle.n

    # Save puzzle in the session
    session['puzzle'] = puzzle.to_json()

    # Remove any leftover puzzlde name in the session
    session.pop('puzzlename', None)

    return redirect(url_for('puzzle_screen'))

    pass


@app.route('/open-puzzle')
def open_puzzle_screen():
    # Get the chosen puzzle name from the query parameters
    puzzlename = request.args.get('puzzlename')

    # Open the corresponding file and read its contents as json
    # and recreate the puzzle from it
    rootdir = config.get_puzzles_root()
    filename = os.path.join(rootdir, puzzlename + ".json")
    with open(filename) as fp:
        jsonstr = fp.read()
    puzzle = Puzzle.from_json(jsonstr)

    # Store the puzzle and puzzle name in the session
    session['puzzle'] = jsonstr
    session['puzzlename'] = puzzlename

    return redirect(url_for('puzzle_screen'))


@app.route('/puzzle-save', methods=['GET'])
def puzzle_save():
    puzzlename = session['puzzlename']
    return puzzle_save_common(puzzlename)


@app.route('/puzzle-save-as', methods=['GET'])
def puzzle_save_as():
    puzzlename = request.args.get('puzzlename')
    session['puzzlename'] = puzzlename
    return puzzle_save_common(puzzlename)


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
        "save_puzzle": puzzlename is not None,
        "save_puzzle_as": True,
        "close_puzzle": True
    }

    # Send puzzle.html to the client
    return render_template('puzzle.html',
                           enabled=enabled,
                           puzzlename=puzzlename,
                           n=puzzle.n,
                           boxsize=boxsize,
                           svgstr=svgstr)


@app.route('/puzzle-click-across', methods=['GET'])
def puzzle_click_across():
    return puzzle_click('Across')


@app.route('/puzzle-click-down', methods=['GET'])
def puzzle_click_down():
    return puzzle_click('Down')


@app.route('/edit-word', methods=['POST'])
def edit_word_screen():
    # Get the seq, direction, and length from the session
    seq = session.get('seq')
    direction = session.get('direction')
    length = session.get('length')

    # Get the word and clue from the form
    text = request.form.get('text')
    clue = request.form.get('clue')

    # Get the word
    puzzle = Puzzle.from_json(session.get('puzzle'))
    if direction.startswith('A'):
        word = puzzle.get_across_word(seq)
    else:
        word = puzzle.get_down_word(seq)
    pass

    # Make the text uppercase and replace "." with blanks
    text = text.upper()
    text = re.sub('\.', ' ', text)

    # Update the word in the puzzle
    word.set_text(text)
    word.set_clue(clue)
    session['puzzle'] = puzzle.to_json()
    puzzlename = session.get('puzzlename', None)

    # Create the SVG
    svg = PuzzleToSVG(puzzle)
    boxsize = svg.boxsize
    svgstr = svg.generate_xml()

    # Enable the appropriate menu options
    enabled = {
        "save_puzzle": puzzlename is not None,
        "save_puzzle_as": True,
        "close_puzzle": True,
    }

    # Send puzzle.html to the client
    return render_template('puzzle.html',
                           enabled=enabled,
                           puzzlename=puzzlename,
                           n=puzzle.n,
                           boxsize=boxsize,
                           svgstr=svgstr)


@app.route('/publish_nytimes')
def publish_nytimes_screen():
    # Get the chosen puzzle name from the query parameters
    puzzlename = request.args.get('puzzlename')

    # Open the corresponding file and read its contents as json
    # and recreate the puzzle from it
    rootdir = config.get_puzzles_root()
    filename = os.path.join(rootdir, puzzlename + ".json")
    with open(filename) as fp:
        jsonstr = fp.read()
    puzzle = Puzzle.from_json(jsonstr)

    # Get directory for output files
    filename = os.path.join(tempfile.gettempdir(), puzzlename)
    app = NYTimesOutput(filename, puzzle)
    svg_filename = app.generate_svg()
    html_filename = app.generate_html()

    flash(f"SVG written to {svg_filename}")
    flash(f"HTML written to {html_filename}")

    return redirect(url_for('main_screen'))


#   ============================================================
#   REST api - functions that just return JSON
#   ============================================================

@app.route('/grids')
def grids():
    # Make a list of all the saved grids
    gridlist = []
    rootdir = config.get_grids_root()
    for filename in os.listdir(rootdir):
        if filename.endswith(".json"):
            basename = os.path.splitext(filename)[0]
            gridlist.append(basename)

    # Send this back to the client in JSON
    resp = make_response(json.dumps(gridlist), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


@app.route('/puzzles')
def puzzles():
    # Make a list of all the saved puzzles
    puzzlelist = []
    rootdir = config.get_puzzles_root()
    for filename in os.listdir(rootdir):
        if filename.endswith(".json"):
            basename = os.path.splitext(filename)[0]
            puzzlelist.append(basename)

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


#   ============================================================
#   Internal methods
#   ============================================================

def grid_common_save(gridname):
    jsonstr = session['grid']

    # Save the file
    rootdir = config.get_grids_root()
    filename = os.path.join(rootdir, gridname + ".json")
    with open(filename, "w") as fp:
        print(jsonstr, file=fp)

    # Send message about save
    flash(f"Grid saved as {gridname}")

    # Create the grid
    grid = Grid.from_json(jsonstr)
    session['grid'] = grid.to_json()

    # Create the SVG
    svg = GridToSVG(grid)
    boxsize = svg.boxsize
    svgstr = svg.generate_xml()

    # Enable menu options
    enabled = {
        "save_grid": True,
        "save_grid_as": True,
        "close_grid": True,
    }

    # Show the grid.html screen
    return render_template('grid.html',
                           enabled=enabled,
                           n=grid.n,
                           gridname=gridname,
                           boxsize=boxsize,
                           svgstr=svgstr)


def puzzle_save_common(puzzlename):
    jsonstr = session['puzzle']

    # Save the file
    rootdir = config.get_puzzles_root()
    filename = os.path.join(rootdir, puzzlename + ".json")
    with open(filename, "w") as fp:
        print(session['puzzle'], file=fp)

    # Send message about the save
    flash(f"Puzzle saved as {puzzlename}")

    # Create the puzzle
    jsonstr = session['puzzle']
    puzzle = Puzzle.from_json(jsonstr)

    # Create the SVG
    svg = PuzzleToSVG(puzzle)
    boxsize = svg.boxsize
    svgstr = svg.generate_xml()

    # Enable menu options
    enabled = {
        "save_puzzle": True,
        "save_puzzle_as": True,
        "close_puzzle": True,
    }

    # Show the puzzle.html screen
    return render_template('puzzle.html',
                           enabled=enabled,
                           n=puzzle.n,
                           puzzlename=puzzlename,
                           boxsize=boxsize,
                           svgstr=svgstr)


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

    # Invoke the puzzle edit word

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
