""" Handles requests having to do with words """
import json
import logging
import re
from http import HTTPStatus

from flask import Blueprint
from flask import make_response
from flask import redirect
from flask import request
from flask import session
from flask import url_for

from crossword import Puzzle, LetterList
from crossword import Word

from .uiwordlists import get_matching_words

# Register this blueprint
uiword = Blueprint('uiword', __name__)


def get_word(session):
    """ Internal method to get
    the puzzle, seq, direction, length, and word from the session """

    # Reconstruct the puzzle from the JSON stored in the session
    jsonstr = session.get('puzzle', None)
    puzzle = Puzzle.from_json(jsonstr)

    # Get the word location (seq, direction), like "25 A" for 25 across
    seq = session.get('seq', None)

    direction = session.get('direction', None)
    direction = Word.ACROSS if direction.upper()[0] == Word.ACROSS else Word.DOWN
    if direction == Word.ACROSS:
        word = puzzle.get_across_word(seq)
    elif direction == Word.DOWN:
        word = puzzle.get_down_word(seq)
    else:
        raise RuntimeError("Direction is not A or D")
    pass

    # Get the word length
    length = session.get('length', None)

    # Return all this to the caller
    return puzzle, seq, direction, length, word


@uiword.route('/word-edit', methods=['POST'])
def word_edit():
    """ Updates the word text and clue, then redirects to puzzle screen """

    puzzle, seq, direction, length, word = get_word(session)

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
    puzzle, seq, direction, length, word = get_word(session)

    # Send cleared text back to the client in JSON
    new_text = word.get_clear_word()
    new_text = re.sub(' ', '.', new_text)
    resp = make_response(json.dumps(new_text), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


@uiword.route('/word-constraints')
def word_constraints():
    """ Returns a table of constraints on this word """

    # Get the puzzle, word seq, word direction, and word length from the session
    puzzle, seq, direction, length, word = get_word(session)

    crossers = get_crossers(word)
    constraints = {
        'word': word.get_text(),
        'location': word.location,
        'length': length,
        'crossers': crossers,
        'pattern': ''.join([crosser['regexp']
                            for crosser in crossers])
    }

    # Send the object back to the client
    resp = make_response(json.dumps(constraints), HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp


def get_crossers(word):
    word_coordinates = [(r, c) for (r, c) in word.cell_iterator()]
    wordtext = word.get_text()
    crossers = []
    for i, crossword in enumerate(word.get_crossing_words()):
        crosser = dict()  # Constraint for this letter in the word
        crosser['pos'] = i + 1  # Index within this word (1, 2, ..., length)
        crosser['letter'] = wordtext[i]  # Letter of this word
        crosser['text'] = crossword.get_text().replace(' ', '.')  # Text of crossing word
        crosser['location'] = crossword.location

        # Now figure out the position in the crossing word where
        # it crosses this word
        index = 0
        for (r, c) in crossword.cell_iterator():
            index += 1
            if (r, c) in word_coordinates:
                break
        crosser['index'] = index  # Point at which we cross the crossing word

        # Examine all possible values for the crossing word and keep track
        # of their letter at the crossing index
        pattern = "^" + crossword.get_text() + "$"
        pattern = re.sub('[ ?]', '.', pattern)

        # Figure out the regular expression for this letter position
        letter_set = set()
        nchoices = 0
        for word in get_matching_words(pattern):
            nchoices += 1
            letter_set.add(word[index - 1])
        letters = ''.join(list(letter_set))
        regexp = LetterList.regexp(letters)
        if not regexp:  # Special case - word is used but not in dictionary
            regexp = wordtext[i]
            nchoices = 1
        crosser['regexp'] = regexp  # Regular expression for the crossing point
        crosser['choices'] = nchoices

        # Add to the constraint list
        crossers.append(crosser)

    return crossers
