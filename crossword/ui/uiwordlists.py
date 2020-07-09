""" Handles requests for word pattern matches
"""
import json
import re
from http import HTTPStatus

from flask import request, make_response

from crossword.ui import DBWord


class WordList:
    """ Given a regular expression, returns a list of all the words that match the pattern """

    def __init__(self):
        self.words = [x.word for x in DBWord.query.all()]

    def lookup(self, pattern):
        pattern = "^" + pattern + "$"
        pattern = re.sub('[ ?]', '.', pattern)
        regexp = re.compile(pattern, re.IGNORECASE)
        result = [line for line in self.words if regexp.match(line)]
        return result


wordlist = WordList()


def wordlists():
    """ REST method to return the list of matches for a regex pattern """

    # Get the pattern from the query parameters
    pattern = request.args.get('pattern')
    words = wordlist.lookup(pattern)
    jsonstr = json.dumps(words)

    # Send this back to the client in JSON
    resp = make_response(jsonstr, HTTPStatus.OK)
    resp.headers['Content-Type'] = "application/json"
    return resp
