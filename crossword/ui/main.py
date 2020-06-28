""" Top-level script for the crossword editor web UI.
Contains only routing directives to handler functions
"""
from flask import Flask
from flask_session import Session
from crossword.ui import *

# Imports of crossword classes

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.config["DEBUG"] = True

# Secret key comes from os.urandom(24)
app.secret_key = b'\x8aws+6\x99\xd9\x87\xf0\xd6\xe8\xad\x9b\xfd\xed\xb9'

# The following is required to add server-side session support

app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#   ============================================================
#   URL routing to handler functions
#   ============================================================

# Main
app.add_url_rule('/', view_func=main_screen)

# Grid
app.add_url_rule('/grid', view_func=grid_screen)
app.add_url_rule('/grids', view_func=grids)
app.add_url_rule('/grid-changed', view_func=grid_changed)
app.add_url_rule('/grid-click', view_func=grid_click)
app.add_url_rule('/grid-delete', view_func=grid_delete)
app.add_url_rule('/grid-new', view_func=grid_new, methods=['POST'])
app.add_url_rule('/grid-open', view_func=grid_open)
app.add_url_rule('/grid-preview', view_func=grid_preview)
app.add_url_rule('/grid-rotate', view_func=grid_rotate)
app.add_url_rule('/grid-save', view_func=grid_save)
app.add_url_rule('/grid_save_as', view_func=grid_save_as)
app.add_url_rule('/grid-statistics', view_func=grid_statistics)

# Puzzle
app.add_url_rule('/puzzle', view_func=puzzle_screen)
app.add_url_rule('/puzzles', view_func=puzzles)
app.add_url_rule('/puzzle-changed', view_func=puzzle_changed)
app.add_url_rule('/puzzle-click-across', view_func=puzzle_click_across)
app.add_url_rule('/puzzle-click-down', view_func=puzzle_click_down)
app.add_url_rule('/puzzle-delete', view_func=puzzle_delete)
app.add_url_rule('/puzzle-new', view_func=puzzle_new)
app.add_url_rule('/puzzle-open', view_func=puzzle_open)
app.add_url_rule('/puzzle-save', view_func=puzzle_save)
app.add_url_rule('/puzzle-save-as', view_func=puzzle_save_as)
app.add_url_rule('/puzzle-undo', view_func=puzzle_undo)
app.add_url_rule('/puzzle-redo', view_func=puzzle_redo)
app.add_url_rule('/puzzle_statistics', view_func=puzzle_statistics)
app.add_url_rule('/puzzle-title', view_func=puzzle_title, methods=['POST'])

# Publish
app.add_url_rule('/puzzle-publish-acrosslite', view_func=puzzle_publish_acrosslite)
app.add_url_rule('/puzzle-publish-nytimes', view_func=puzzle_publish_nytimes)

# Word
app.add_url_rule('/word-edit', view_func=word_edit, methods=['POST'])
app.add_url_rule('/word-reset', view_func=word_reset)

# Wordlist
app.add_url_rule('/wordlists', view_func=wordlists)

#   ============================================================
#   Mainline
#   ============================================================
if __name__ == '__main__':
    app.run()
