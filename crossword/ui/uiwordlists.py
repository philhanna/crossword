""" Handles requests for word pattern matches
"""
import json
import logging
import re
from datetime import datetime
from http import HTTPStatus

from flask import Blueprint
from flask import request
from flask import make_response

from crossword import get_elapsed_time

from crossword.ui import DBWord

# Register this blueprint
uiwordlists = Blueprint('uiwordlists', __name__)

# TODO Got to be a better way to do this, rather than a global variable
wordlist = None


def is_loaded():
    return wordlist is not None


def get_wordlist():
    global wordlist
    if not is_loaded():
        logname = __name__
        stime = datetime.now()
        logging.info(f"{logname}: loading word list")
        wordlist = [x.word for x in DBWord.query.all()]
        etime = datetime.now()
        seconds = get_elapsed_time(stime, etime)
        logging.info(f"{logname}: done loading word list")
        logging.info(f"{logname}: {len(wordlist)} words in the list")
        logging.info(f"{logname}: elapsed time {seconds} seconds")
    return wordlist


def get_matching_words(pattern):
    wordlist = get_wordlist()
    regexp = re.compile(pattern, re.IGNORECASE)
    return [line for line in wordlist if regexp.match(line)]


@uiwordlists.route('/wordlists')
def wordlists():
    """ Returns the list of matches for a regex pattern """

    pattern = request.args.get('pattern')
    pattern = "^" + pattern + "$"
    pattern = re.sub('[ ?]', '.', pattern)
    words = get_matching_words(pattern)

    jsonstr = json.dumps(words)
    resp = make_response(jsonstr, HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"

    return resp
