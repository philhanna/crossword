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


@uiwordlists.route('/wordlists')
def wordlists():
    """ Returns the list of matches for a regex pattern """
    global wordlist
    if not wordlist:
        logname = __name__
        stime = datetime.now()
        logging.info(f"{logname}: loading word list")
        wordlist = [x.word for x in DBWord.query.all()]
        etime = datetime.now()
        seconds = get_elapsed_time(stime, etime)
        logging.info(f"{logname}: done loading word list")

    pattern = request.args.get('pattern')
    pattern = "^" + pattern + "$"
    pattern = re.sub('[ ?]', '.', pattern)

    regexp = re.compile(pattern, re.IGNORECASE)
    words = [line for line in wordlist if regexp.match(line)]

    jsonstr = json.dumps(words)
    resp = make_response(jsonstr, HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"

    return resp
