""" Handles requests having to do with grids
"""
import json
import logging
from datetime import datetime
from http import HTTPStatus

from flask import redirect, request, session, url_for, flash, make_response, render_template
from sqlalchemy import desc

from crossword import Grid, GridToSVG, sha256
from crossword.ui import DBGrid, db


def grid_screen():
    """ Renders the grid screen """

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


def grid_new():
    """ Creates a new grid and redirects to grid screen """

    # Get the grid size from the form

    n = int(request.form.get('n'))

    # Remove any leftover grid name in the session
    session.pop('gridname', None)

    # Create the grid
    grid = Grid(n)
    jsonstr = grid.to_json()
    session['grid'] = jsonstr
    session['grid.initial.sha'] = sha256(jsonstr)

    return redirect(url_for('grid_screen'))


def grid_load_common(userid, gridname):
    """ Loads the JSON string for a grid """
    result = DBGrid.query \
        .filter_by(userid=userid, gridname=gridname) \
        .first()
    jsonstr = result.jsonstr
    return jsonstr


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

    return redirect(url_for('grid_screen'))


def grid_preview():
    """ Creates a grid preview and returns it to ??? """

    # Get the chosen grid name from the query parameters
    gridname = request.args.get('gridname')
    userid = 1  # TODO Replace hard coded user id
    jsonstr = grid_load_common(userid, gridname)

    # Open the corresponding file and read its contents as json
    # and recreate the grid from it

    grid = Grid.from_json(jsonstr)

    scale = 0.75
    svgobj = GridToSVG(grid, scale=scale)
    width = (svgobj.boxsize * grid.n + 32) * scale
    svgstr = svgobj.generate_xml()

    obj = {
        "gridname": gridname,
        "wordcount": grid.get_word_count(),
        "width": width,
        "svgstr": svgstr
    }
    resp = make_response(json.dumps(obj), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


def grid_save():
    """ Saves a grid """
    gridname = session.get('gridname', request.args.get('gridname'))
    session['gridname'] = gridname
    return grid_save_common(gridname)


def grid_save_as():
    """ Saves a grid under a new name """
    newgridname = request.args.get('newgridname')
    return grid_save_common(newgridname)


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
    return redirect(url_for('grid_screen'))


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
            flash(f"{gridname} gridname deleted")

    # Redirect to the main screen
    return redirect(url_for('main_screen'))


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

    # Send the new SVG data to the client
    svg = GridToSVG(grid)
    svgstr = svg.generate_xml()
    response = make_response(svgstr, HTTPStatus.OK)
    return response


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


def grid_statistics():
    """ REST method to return the grid statistics in a JSON string """

    # Get the grid name and grid from the session
    gridname = session.get('gridname', '(Untitled)')
    grid = Grid.from_json(session['grid'])
    stats = grid.get_statistics()
    resp = make_response(json.dumps(stats), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


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


def grids():
    """ REST method to return the list of grids """

    # Make a list of all the saved grids
    userid = 1  # TODO replace hard-coded user ID
    gridlist = get_grid_list(userid)

    # Send this back to the client in JSON
    resp = make_response(json.dumps(gridlist), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp
