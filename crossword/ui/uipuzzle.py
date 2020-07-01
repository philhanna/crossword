""" Handles requests having to do with puzzles
"""
import json
import os
import re
from http import HTTPStatus

from flask import session, redirect, render_template, request, url_for, flash, make_response

from crossword import Puzzle, PuzzleToSVG, Configuration, Grid


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


def puzzle_new():
    """ Creates a new puzzle and redirects to puzzle screen """

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

    # Save puzzle in the session
    jsonstr = puzzle.to_json()
    session['puzzle'] = jsonstr
    session['puzzle.initial'] = jsonstr

    # Remove any leftover puzzle name in the session
    session.pop('puzzlename', None)

    return redirect(url_for('puzzle_screen'))


def puzzle_open():
    """ Opens a new puzzle and redirects to puzzle screen """

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


def puzzle_preview():
    """ Creates a puzzle preview and returns it to ??? """

    # Get the chosen puzzle name from the query parameters
    puzzlename = request.args.get('puzzlename')

    # Open the corresponding file and read its contents as json
    # and recreate the puzzle from it
    rootdir = Configuration.get_puzzles_root()
    filename = os.path.join(rootdir, puzzlename + ".json")
    with open(filename) as fp:
        jsonstr = fp.read()
    puzzle = Puzzle.from_json(jsonstr)

    scale = 0.75
    svgobj = PuzzleToSVG(puzzle, scale=scale)
    width = (svgobj.boxsize * puzzle.n + 32) * scale;
    svgstr = svgobj.generate_xml()

    obj = {
        "puzzlename" : puzzlename,
        "width": width,
        "wordcount": puzzle.get_word_count(),
        "svgstr": svgstr
    }
    resp = make_response(json.dumps(obj), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


def puzzle_save():
    """ Saves a puzzle """

    puzzlename = session.get('puzzlename', request.args.get('puzzlename'))
    session['puzzlename'] = puzzlename
    return puzzle_save_common(puzzlename)


def puzzle_save_as():
    """ Saves a puzzle under a new name """
    newpuzzlename = request.args.get('newpuzzlename')
    return puzzle_save_common(newpuzzlename)


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
    return redirect(url_for('puzzle_screen'))


def puzzle_delete():
    """ Deletes a puzzle and redirects to main screen """

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


def puzzle_click_across():
    """ Handles a puzzle click across request """

    scrollTop = request.args.get('scrollTop', None)
    session['scrollTopAcross'] = scrollTop
    return puzzle_click('Across')


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


def puzzle_changed():
    """ REST method that returns whether the puzzle has changed since it was opened """

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


def puzzle_statistics():
    """ REST method to return the puzzle statistics in a JSON string """

    jsonstr = session['puzzle']
    puzzle = Puzzle.from_json(jsonstr)
    stats = puzzle.get_statistics()
    resp = make_response(json.dumps(stats), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


def puzzle_undo():
    """ Undoes the last puzzle action then redirects to puzzle screen """

    jsonstr = session.get('puzzle', None)
    puzzle = Puzzle.from_json(jsonstr)
    puzzle.undo()
    jsonstr = puzzle.to_json()
    session['puzzle'] = jsonstr
    return redirect(url_for('puzzle_screen'))


def puzzle_redo():
    """ Redoes the last puzzle action then redirects to puzzle screen """

    jsonstr = session.get('puzzle', None)
    puzzle = Puzzle.from_json(jsonstr)
    puzzle.redo()
    jsonstr = puzzle.to_json()
    session['puzzle'] = jsonstr
    return redirect(url_for('puzzle_screen'))



def puzzles():
    """ REST method to return a list of all puzzles """

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
