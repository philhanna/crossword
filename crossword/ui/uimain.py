from threading import Thread

from flask import Blueprint, session, render_template

from crossword.ui import is_loaded, get_wordlist, lock

uimain = Blueprint('uimain', __name__)


@uimain.route('/')
def main_screen():
    """ Handles top-level request """

    # Preload the wordlist if it is not already initialized
    with lock:
        if not is_loaded():
            get_wordlist()

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
