""" Handles requests for word pattern matches
"""
import json
from http import HTTPStatus

from crossword import WordList
from flask import request, make_response

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
