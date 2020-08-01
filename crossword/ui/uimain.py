from threading import Thread

from flask import Blueprint, session, render_template

from crossword.ui import is_loaded, get_wordlist, lock, UIState

uimain = Blueprint('uimain', __name__)


@uimain.route('/')
def main_screen():
    """ Handles top-level request """

    # Preload the wordlist if it is not already initialized
    with lock:
        if not is_loaded():
            get_wordlist()

    # Clear any existing session (except messages)
    messages = session.get('_flashes', None)
    session.clear()
    if messages:
        session['_flashes'] = messages

    session['uistate'] = UIState.MAIN_MENU
    enabled = session['uistate'].get_enabled()

    return render_template('main.html', enabled=enabled)
