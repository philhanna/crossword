""" Handles requests having to do with grids
"""

# System packages
import json
import logging
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
from crossword import Grid, GridToSVG, sha256
from crossword.ui import db, DBGrid, UIState, DBPuzzle

# Register this route handler

uigrid = Blueprint('uigrid', __name__)


@uigrid.route('/grid-chooser/<path:nexturl>')
def grid_chooser(nexturl):
    """ Redirects to grid chooser dialog """

    # Make a list of all the saved grids
    userid = 1  # TODO replace hard-coded user ID
    gridlist = get_grid_list(userid)

    # Set the state to grid chooser
    session['uistate'] = UIState.GRID_CHOOSER
    enabled = UIState.GRID_CHOOSER.get_enabled()

    return render_template("grid-chooser.html",
                           enabled=enabled,
                           objectlist=gridlist,
                           nexturl=nexturl)


@uigrid.route('/grid')
def grid_screen():
    """ Renders the grid screen """

    # Get the existing grid from the session
    grid = Grid.from_json(session['grid'])
    gridname = session.get('gridname', None)

    # Create the SVG
    svg = GridToSVG(grid)
    boxsize = svg.boxsize
    svgstr = svg.generate_xml()

    # Set the state to editing grid
    session['uistate'] = UIState.EDITING_GRID
    enabled = session['uistate'].get_enabled()
    enabled["grid_undo"] = len(grid.undo_stack) > 0
    enabled["grid_redo"] = len(grid.redo_stack) > 0
    enabled["grid_delete"] = gridname is not None

    # Show the grid.html screen
    return render_template('grid.html',
                           enabled=enabled,
                           n=grid.n,
                           gridname=gridname,
                           boxsize=boxsize,
                           svgstr=svgstr)


@uigrid.route('/grid-new', methods=['GET'])
def grid_new():
    """ Creates a new grid and redirects to grid screen """

    # Get the grid size from the form
    n = int(request.args.get('n'))

    # Remove any leftover grid name in the session
    session.pop('gridname', None)

    # Create the grid
    grid = Grid(n)
    jsonstr = grid.to_json()
    session['grid'] = jsonstr
    session['grid.initial.sha'] = sha256(jsonstr)

    return redirect(url_for('uigrid.grid_screen'))


@uigrid.route('/grid-new-from-puzzle')
def grid_new_from_puzzle():
    """ Creates a new grid from the specified puzzle """

    puzzlename = request.args.get('puzzlename')
    userid = 1  # TODO replace hard-coded user ID
    query = DBPuzzle.query.filter_by(userid=userid, puzzlename=puzzlename)
    jsonstr = query.first().jsonstr
    grid = Grid.from_json(jsonstr)
    grid.undo_stack = []
    grid.redo_stack = []
    jsonstr = grid.to_json()

    # Save grid in the session
    session['grid'] = jsonstr
    session['grid.initial.sha'] = sha256(jsonstr)

    # Remove any leftover grid name in the session
    session.pop('gridname', None)

    return redirect(url_for('uigrid.grid_screen'))


@uigrid.route('/grid-open')
def grid_open():
    """ Opens a new grid and redirects to grid screen """

    # Get the chosen grid name from the query parameters
    gridname = request.args.get('gridname')

    # Open the corresponding file and read its contents as json
    # and recreate the grid from it
    userid = 1  # TODO Replace hard coded user id
    jsonstr = grid_load_common(userid, gridname)

    # Store the grid and grid name in the session
    session['grid'] = jsonstr
    session['grid.initial.sha'] = sha256(jsonstr)
    session['gridname'] = gridname

    return redirect(url_for('uigrid.grid_screen'))


@uigrid.route('/grid-preview')
def grid_preview():
    """ Creates a grid preview and returns it to ??? """
    userid = 1  # TODO Replace hard coded user id

    # Get the chosen grid name from the query parameters
    gridname = request.args.get('gridname')

    # Open the corresponding file and read its contents as json
    # and recreate the grid from it
    jsonstr = grid_load_common(userid, gridname)
    grid = Grid.from_json(jsonstr)

    # Get the top two word lengths
    heading_list = [
        f"{grid.get_word_count()} words"
    ]
    wlens = grid.get_word_lengths()
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
    heading = f'Grid {gridname}({", ".join(heading_list)})'

    scale = 0.75
    svgobj = GridToSVG(grid, scale=scale)
    width = (svgobj.boxsize * grid.n + 32) * scale
    svgstr = svgobj.generate_xml()

    obj = {
        "gridname": gridname,
        "heading": heading,
        "width": width,
        "svgstr": svgstr
    }
    resp = make_response(json.dumps(obj), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


@uigrid.route('/grid-save')
def grid_save():
    """ Saves a grid """
    gridname = session.get('gridname', request.args.get('gridname'))
    session['gridname'] = gridname
    return grid_save_common(gridname)


@uigrid.route('/grid_save_as')
def grid_save_as():
    """ Saves a grid under a new name """
    newgridname = request.args.get('newgridname')
    return grid_save_common(newgridname)


@uigrid.route('/grid-delete')
def grid_delete():
    """ Deletes a grid and redirects to main screen """

    # Get the name of the grid to be deleted from the session
    # Delete the file
    gridname = session.get('gridname', None)
    if gridname:
        userid = 1  # TODO remove hard-coded userID
        query = DBGrid.query.filter_by(userid=userid, gridname=gridname)
        oldgrid = query.first()
        if oldgrid:
            db.session.delete(oldgrid)
            db.session.commit()
            flash(f"{gridname} grid deleted")

    # Redirect to the main screen
    return redirect(url_for('uimain.main_screen'))


@uigrid.route('/grid-click')
def grid_click():
    """ Adds or removes a black cell then returns the new SVG """

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

    return redirect(url_for('uigrid.grid_screen'))

@uigrid.route('/grid-rotate')
def grid_rotate():
    """ Rotates the grid 90 degrees left then returns the new SVG """

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


@uigrid.route('/grid-changed')
def grid_changed():
    """ REST method to determine whether the grid has changed """

    # Compare the original grid loaded to its current values.
    # Return True if they are different, False if they are the same.
    jsonstr_initial_sha = session.get('grid.initial.sha', sha256(None))
    jsonstr_current_sha = sha256(session.get('grid', None))
    changed = not (jsonstr_current_sha == jsonstr_initial_sha)
    obj = {"changed": changed}

    # Send this back to the client in JSON
    resp = make_response(json.dumps(obj), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


@uigrid.route('/grid-statistics')
def grid_statistics():
    """ Return the grid statistics in a JSON string """

    # Get the grid from the session
    grid = Grid.from_json(session['grid'])
    stats = grid.get_statistics()
    enabled = {}

    svgstr = GridToSVG(grid).generate_xml()

    # Render with grid statistics template
    return render_template("grid-statistics.html", enabled=enabled, svgstr=svgstr, stats=stats);


@uigrid.route('/grids')
def grids():
    """ REST method to return the list of grids """

    # Make a list of all the saved grids
    userid = 1  # TODO replace hard-coded user ID
    gridlist = get_grid_list(userid)

    # Send this back to the client in JSON
    resp = make_response(json.dumps(gridlist), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp
@uigrid.route('/grid-undo')
def grid_undo():
    """ Undoes the last grid action then redirects to grid screen """

    jsonstr = session.get('grid', None)
    grid = Grid.from_json(jsonstr)
    grid.undo()
    jsonstr = grid.to_json()
    session['grid'] = jsonstr
    return redirect(url_for('uigrid.grid_screen'))


@uigrid.route('/grid-redo')
def grid_redo():
    """ Redoes the last grid action then redirects to grid screen """

    jsonstr = session.get('grid', None)
    grid = Grid.from_json(jsonstr)
    grid.redo()
    jsonstr = grid.to_json()
    session['grid'] = jsonstr
    return redirect(url_for('uigrid.grid_screen'))


#   ============================================================
#   Internal methods
#   ============================================================

def get_grid_list(userid):
    """ Returns the list of grid file names for the specified userid

    :param userID the id of the user who owns these grids
    :returns the list of base file names, sorted with most recently updated first
    """
    query = DBGrid.query \
        .filter_by(userid=userid) \
        .order_by(desc(DBGrid.modified), DBGrid.gridname)
    filelist = [dbgrid.gridname for dbgrid in query.all()]
    return filelist


def grid_load_common(userid, gridname):
    """ Loads the JSON string for a grid """
    result = DBGrid.query \
        .filter_by(userid=userid, gridname=gridname) \
        .first()
    jsonstr = result.jsonstr
    return jsonstr


def grid_save_common(gridname):
    """ Common method used by both grid_save and grid_save_as """

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
        userid = 1  # TODO Replace hard coded user id
        query = DBGrid.query.filter_by(userid=userid, gridname=gridname)
        if not query.all():
            # No grid in the database. This is an insert
            logging.debug(f"Inserting grid '{gridname}' into grids table")
            created = modified = datetime.now().isoformat()
            newgrid = DBGrid(userid=userid,
                             gridname=gridname,
                             created=created,
                             modified=modified,
                             jsonstr=jsonstr
                             )
            db.session.add(newgrid)
            db.session.commit()
        else:
            # There is a grid. This is an update
            logging.debug(f"Updating grid '{gridname}' in grids table")
            oldgrid = query.first()
            oldgrid.modified = datetime.now().isoformat()
            oldgrid.jsonstr = jsonstr
            db.session.commit()

        # Send message about save
        flash(f"Grid saved as {gridname}")

        # Store the sha256 of the saved version of the grid
        # in the session as 'grid.initial.sha' so that we can detect
        # whether it has been changed since it was last saved
        session['grid.initial.sha'] = sha256(jsonstr)

    # Show the grid screen
    return redirect(url_for('uigrid.grid_screen'))
