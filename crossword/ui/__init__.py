# Web application for crossword package

__all__ = ['app', 'db', 'DBUser', 'DBGrid', 'DBPuzzle', 'DBWord']

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from crossword import dbfile

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{dbfile()}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class DBUser(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String)
    password = db.Column(db.BLOB)
    created = db.Column(db.String)
    last_access = db.Column(db.String)
    email = db.Column(db.String)
    confirmed = db.Column(db.String)
    author_name = db.Column(db.String)
    address_line_1 = db.Column(db.String)
    address_line_2 = db.Column(db.String)
    address_city = db.Column(db.String)
    address_state = db.Column(db.String)
    address_zip = db.Column(db.String)


class DBGrid(db.Model):
    __tablename__ = "grids"
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer)
    gridname = db.Column(db.String)
    created = db.Column(db.String)
    modified = db.Column(db.String)
    jsonstr = db.Column(db.String)


class DBPuzzle(db.Model):
    __tablename__ = "puzzles"
    id = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer)
    puzzlename = db.Column(db.String)
    created = db.Column(db.String)
    modified = db.Column(db.String)
    jsonstr = db.Column(db.String)


class DBWord(db.Model):
    __tablename__ = "words"
    word = db.Column(db.String, primary_key=True)


from .uigrid import *
from .uimain import *
from .uipublish import *
from .uipuzzle import *
from .uiwordlists import *
from .uiword import *
