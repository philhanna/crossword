from flask import Blueprint, session, render_template

uimain = Blueprint('uimain', __name__)


@uimain.route('/')
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
