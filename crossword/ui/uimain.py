from flask import Blueprint, session, render_template

from crossword.ui import UIState

uimain = Blueprint('uimain', __name__)


@uimain.route('/')
def main_screen():
    """ Handles top-level request """

    # Clear any existing session (except messages)
    messages = session.get('_flashes', None)
    session.clear()
    if messages:
        session['_flashes'] = messages

    session['uistate'] = UIState.MAIN_MENU
    enabled = session['uistate'].get_enabled()

    return render_template('main.html', enabled=enabled)
