# Web application for crossword package

__all__ = [
    'create_app',
    'db',
    'DBGrid',
    'DBPuzzle',
    'DBUser',
    'DBWord',
]
from flask import Flask
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy

from crossword import dbfile, config

db = SQLAlchemy()


def create_app():

    import logging
    import os

    log_level = config['log_level']
    log_level_number = logging.getLevelName(log_level)
    logname = __name__
    if type(log_level_number) == int:
        logging.basicConfig(level=log_level_number)
    else:
        logging.basicConfig(level=logging.INFO)
        logging.warning("log_level must be CRITICAL, ERROR, WARNING, INFO, DEBUG, or NOTSET")
    logging.info(f"{logname}: starting crossword server")

    app = Flask(__name__)
    logging.info(f"{logname}: flask app created")

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{dbfile()}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    logging.info(f"{logname}: SQLAlchemy configured")

    app.config["JSON_SORT_KEYS"] = False
    app.config["DEBUG"] = True

    # Get flask secret key from an environment variable
    # If the variable does not exist, use this one
    # generated by os.urandom(24)
    secret_key = os.getenv("FLASK_SECRET_KEY")
    if not secret_key:
        secret_key = "8a77732b3699d987f0d6e8ad9bfdedb9"
    app.secret_key = bytes.fromhex(secret_key)
    logging.info(f"{logname}: secret_key initialized")

    # The following is required to add server-side session support
    app.config["SESSION_TYPE"] = "filesystem"
    Session(app)
    logging.info(f"{logname}: server-side sessions initiated")

    # Tell SQLAlchemy about this app
    db.init_app(app)
    logging.info(f"{logname}: SQLAlchemy init_app called")

    return app


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
