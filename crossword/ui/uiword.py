""" Handles requests having to do with words """
import json
import re
from http import HTTPStatus

from flask import Blueprint
from flask import make_response
from flask import redirect
from flask import request
from flask import session
from flask import url_for

from crossword import Puzzle
from crossword import Word

# Register this blueprint
uiword = Blueprint('uiword', __name__)


@uiword.route('/word-edit', methods=['POST'])
def word_edit():
    """ Updates the word text and clue, then redirects to puzzle screen """

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

    # Set the word text and clue and save the puzzle in the session again
    puzzle = Puzzle.from_json(session.get('puzzle'))
    puzzle.set_text(seq, direction, text)
    puzzle.set_clue(seq, direction, clue)
    session['puzzle'] = puzzle.to_json()

    # Now redirect to puzzle_screen()
    return redirect(url_for('uipuzzle.puzzle_screen'))


@uiword.route('/word-reset')
def word_reset():
    """ Resets the word then redirects back to the puzzle screen

    Resetting a word means setting all its letters to blanks
    unless they are part of a completed word in the other direction.
    """
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
