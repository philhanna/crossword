""" Handles requests having to do with puzzles
"""
# System packages
import json
import logging
import re
from datetime import datetime
from http import HTTPStatus

# Installed packages
from flask import Blueprint
from flask import flash
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from sqlalchemy import desc

# My own packages
from crossword import Grid
from crossword import Puzzle
from crossword import PuzzleToSVG
from crossword import sha256
from crossword.ui import DBGrid
from crossword.ui import DBPuzzle
from crossword.ui import db

# Register this blueprint
uipuzzle = Blueprint('uipuzzle', __name__)


@uipuzzle.route('/puzzle')
def puzzle_screen():
    """ Renders the puzzle screen """

    # Get the existing puzzle from the session
    puzzle = Puzzle.from_json(session['puzzle'])
    puzzlename = session.get('puzzlename', None)

    # Get the clues
    clues = {
        "across": [
            {"seq": seq, "text": word.get_clue() or ""}
            for seq, word in puzzle.across_words.items()
        ],
        "down": [
            {"seq": seq, "text": word.get_clue() or ""}
            for seq, word in puzzle.down_words.items()
        ],
    }

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
                           clues=clues,
                           scrollTopAcross=session.get('scrollTopAcross', None),
                           scrollTopDown=session.get('scrollTopDown', None),
                           boxsize=boxsize,
                           svgstr=svgstr)


@uipuzzle.route('/puzzle-new')
def puzzle_new():
    """ Creates a new puzzle and redirects to puzzle screen """

    # Get the chosen grid name from the query parameters
    gridname = request.args.get('gridname')

    # Open the corresponding file and read its contents as json
    # and recreate the grid from it
    userid = 1  # TODO replace hard-coded user ID
    query = DBGrid.query.filter_by(userid=userid, gridname=gridname)
    jsonstr = query.first().jsonstr
    grid = Grid.from_json(jsonstr)

    # Now pass this grid to the Puzzle() constructor
    puzzle = Puzzle(grid)

    # Save puzzle in the session
    jsonstr = puzzle.to_json()
    session['puzzle'] = jsonstr
    session['puzzle.initial.sha'] = sha256(jsonstr)

    # Remove any leftover puzzle name in the session
    session.pop('puzzlename', None)

    return redirect(url_for('uipuzzle.puzzle_screen'))


@uipuzzle.route('/puzzle-open')
def puzzle_open():
    """ Opens a new puzzle and redirects to puzzle screen """

    # Get the chosen puzzle name from the query parameters
    puzzlename = request.args.get('puzzlename')

    # Open the corresponding file and read its contents as json
    # and recreate the puzzle from it
    userid = 1  # TODO Replace hard coded user id
    jsonstr = puzzle_load_common(userid, puzzlename)

    # Store the puzzle and puzzle name in the session
    session['puzzle'] = jsonstr
    session['puzzle.initial.sha'] = sha256(jsonstr)
    session['puzzlename'] = puzzlename

    return redirect(url_for('uipuzzle.puzzle_screen'))


@uipuzzle.route('/puzzle-preview')
def puzzle_preview():
    """ Creates a puzzle preview and returns it to ??? """
    userid = 1  # TODO Replace hard coded user id

    # Get the chosen puzzle name from the query parameters
    puzzlename = request.args.get('puzzlename')

    # Open the corresponding file and read its contents as json
    # and recreate the puzzle from it
    jsonstr = puzzle_load_common(userid, puzzlename)
    puzzle = Puzzle.from_json(jsonstr)

    # Get the top two word lengths
    heading_list = [
        f"{puzzle.get_word_count()} words"
    ]
    wlens = puzzle.get_word_lengths()
    wlenkeys = sorted(wlens.keys(), reverse=True)
    wlenkeys = wlenkeys[:min(2, len(wlenkeys))]
    for wlen in wlenkeys:
        entry = wlens[wlen]
        total = 0
        if entry["alist"]:
            total += len(entry["alist"])
        if entry["dlist"]:
            total += len(entry["dlist"])
        heading_list.append(f"{wlen}-letter: {total}")
    heading = f'{puzzlename}({", ".join(heading_list)})'

    scale = 0.75
    svgobj = PuzzleToSVG(puzzle, scale=scale)
    width = (svgobj.boxsize * puzzle.n + 32) * scale
    svgstr = svgobj.generate_xml()

    obj = {
        "puzzlename": puzzlename,
        "heading": heading,
        "width": width,
        "svgstr": svgstr
    }
    resp = make_response(json.dumps(obj), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


@uipuzzle.route('/puzzle-save')
def puzzle_save():
    """ Saves a puzzle """

    puzzlename = session.get('puzzlename', request.args.get('puzzlename'))
    session['puzzlename'] = puzzlename
    return puzzle_save_common(puzzlename)


@uipuzzle.route('/puzzle-save-as')
def puzzle_save_as():
    """ Saves a puzzle under a new name """
    newpuzzlename = request.args.get('newpuzzlename')
    return puzzle_save_common(newpuzzlename)


@uipuzzle.route('/puzzle-title', methods=['POST'])
def puzzle_title():
    """ Changes the puzzle title and redirects back to the puzzle screen """

    title = request.form.get('title', None)
    if title:
        jsonstr = session['puzzle']
        puzzle = Puzzle.from_json(jsonstr)
        puzzle.set_title(title)
        jsonstr = puzzle.to_json()
        session['puzzle'] = jsonstr
        flash(f"Puzzle title set to {puzzle.get_title()}")

    # Show the puzzle screen
    return redirect(url_for('uipuzzle.puzzle_screen'))


@uipuzzle.route('/puzzle-delete')
def puzzle_delete():
    """ Deletes a puzzle and redirects to main screen """

    # Get the name of the puzzle to be deleted from the session
    # Delete the file
    puzzlename = session.get('puzzlename', None)
    if puzzlename:
        userid = 1  # TODO Replace hard-coded user ID
        query = DBPuzzle.query.filter_by(userid=userid, puzzlename=puzzlename)
        oldpuzzle = query.first()
        if oldpuzzle:
            db.session.delete(oldpuzzle)
            db.session.commit()
            flash(f"{puzzlename} puzzle deleted")

    # Redirect to the main screen
    return redirect(url_for('uimain.main_screen'))


@uipuzzle.route('/puzzle-click-across')
def puzzle_click_across():
    """ Handles a puzzle click across request """

    scrollTop = request.args.get('scrollTop', None)
    session['scrollTopAcross'] = scrollTop
    return puzzle_click('Across')


@uipuzzle.route('/puzzle-click-down')
def puzzle_click_down():
    """ Handles a puzzle click down request """

    scrollTop = request.args.get('scrollTop', None)
    session['scrollTopDown'] = scrollTop
    return puzzle_click('Down')


def puzzle_click(direction):
    """ Common REST method used by both puzzle_click_across and puzzle_click_down """

    # Get the seq or row and column clicked from the query parms

    r = request.args.get('r', None)
    c = request.args.get('c', None)
    seq = request.args.get('seq', None)

    # Get the existing puzzle from the session
    puzzle = Puzzle.from_json(session['puzzle'])

    if r is not None and c is not None:
        r = int(r)
        c = int(c)
        # Get the numbered cell at (r, c)
        numbered_cell = puzzle.get_numbered_cell(r, c)
        if not numbered_cell:
            errmsg = f"({r},{c}) is not a numbered cell"
            response = make_response(errmsg, HTTPStatus.NOT_FOUND)
            return response
        seq = numbered_cell.seq
    elif seq is not None:
        seq = int(seq)

    # Get the word
    if direction.startswith('A'):
        word = puzzle.get_across_word(seq)
        if not word:
            errmsg = f"(Not the start of an across word"
            response = make_response(errmsg, HTTPStatus.NOT_FOUND)
            return response
    else:
        word = puzzle.get_down_word(seq)
        if not word:
            errmsg = f"(Not the start of a down word"
            response = make_response(errmsg, HTTPStatus.NOT_FOUND)
            return response
        pass

    # Save seq, direction, and length in the session
    session['seq'] = seq
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
        "seq": seq,
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


@uipuzzle.route('/puzzle-changed')
def puzzle_changed():
    """ REST method that returns whether the puzzle has changed since it was opened """

    # Compare the original puzzle loaded to its current values.
    # Return True if they are different, False if they are the same.
    jsonstr_initial_sha = session.get('puzzle.initial.sha', sha256(None))
    jsonstr_current_sha = sha256(session.get('puzzle', None))
    changed = not (jsonstr_current_sha == jsonstr_initial_sha)

    obj = {"changed": changed}

    # Send this back to the client in JSON
    resp = make_response(json.dumps(obj), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


@uipuzzle.route('/puzzle_statistics')
def puzzle_statistics():
    """ REST method to return the puzzle statistics in a JSON string """

    jsonstr = session['puzzle']
    puzzle = Puzzle.from_json(jsonstr)
    stats = puzzle.get_statistics()
    resp = make_response(json.dumps(stats), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


@uipuzzle.route('/puzzle-undo')
def puzzle_undo():
    """ Undoes the last puzzle action then redirects to puzzle screen """

    jsonstr = session.get('puzzle', None)
    puzzle = Puzzle.from_json(jsonstr)
    puzzle.undo()
    jsonstr = puzzle.to_json()
    session['puzzle'] = jsonstr
    return redirect(url_for('uipuzzle.puzzle_screen'))


@uipuzzle.route('/puzzle-redo')
def puzzle_redo():
    """ Redoes the last puzzle action then redirects to puzzle screen """

    jsonstr = session.get('puzzle', None)
    puzzle = Puzzle.from_json(jsonstr)
    puzzle.redo()
    jsonstr = puzzle.to_json()
    session['puzzle'] = jsonstr
    return redirect(url_for('uipuzzle.puzzle_screen'))


@uipuzzle.route('/puzzles')
def puzzles():
    """ REST method to return a list of all puzzles """

    # Make a list of all the saved puzzles
    userid = 1  # TODO replace hard-coded user ID
    puzzlelist = get_puzzle_list(userid)

    # Send this back to the client in JSON
    resp = make_response(json.dumps(puzzlelist), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp

#   ============================================================
#   Internal methods
#   ============================================================


def get_puzzle_list(userid):
    """ Returns the list of puzzle file names for the specified userid

    :param userID the id of the user who owns these puzzles
    :returns the list of base file names, sorted with most recently updated first
    """
    query = DBPuzzle.query \
        .filter_by(userid=userid) \
        .order_by(desc(DBPuzzle.modified), DBPuzzle.puzzlename) \
        .all()
    filelist = [x.puzzlename for x in query]
    return filelist


def puzzle_load_common(userid, puzzlename):
    """ Common method used to load puzzle from database """
    oldpuzzle = DBPuzzle.query.filter_by(userid=userid, puzzlename=puzzlename).first()
    return oldpuzzle.jsonstr


def puzzle_save_common(puzzlename):
    """ Common method used by both puzzle_save and puzzle_save_as """

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
        userid = 1  # TODO Replace hard coded user id
        query = DBPuzzle.query.filter_by(userid=userid, puzzlename=puzzlename)
        if not query.all():
            # No puzzle in the database. This is an insert
            logging.debug(f"Inserting puzzle {puzzlename} into puzzles table")
            created = modified = datetime.now().isoformat()
            newpuzzle = DBPuzzle(userid=userid,
                                 puzzlename=puzzlename,
                                 created=created,
                                 modified=modified,
                                 jsonstr=jsonstr)
            db.session.add(newpuzzle)
            db.session.commit()
        else:
            # Existing puzzle. This is an update
            logging.debug(f"Updating puzzle {puzzlename} in puzzles table")
            oldpuzzle = query.first()
            oldpuzzle.modified = datetime.now().isoformat()
            oldpuzzle.jsonstr = jsonstr
            db.session.commit()

        # Send message about the save
        flash(f"Puzzle saved as {puzzlename}")

        # Store the sha of the saved version of the puzzle
        # in the session as 'puzzle.initial.sha' so that we can
        # detect whether it has been changed since it was last saved
        session['puzzle.initial.sha'] = sha256(jsonstr)

    # Show the puzzle screen
    return redirect(url_for('uipuzzle.puzzle_screen'))
