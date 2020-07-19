from datetime import datetime

from crossword import sha256


class MockUser:
    """ Mock object modelled after DBUser:

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

    """
    def __init__(self):
        self.id = 1
        self.username = "jqpmaker"
        self.password = sha256('My Password')
        dateformat = "%Y-%m-%dT%H:%M:%S.%f"
        self.created = datetime(2020, 5, 31, 18, 23, 56).strftime(dateformat)
        self.modified = datetime(2020, 6, 28, 1, 2, 3).strftime(dateformat)
        self.last_access = datetime(2020, 7, 20, 4, 5, 6).strftime(dateformat)
        self.email = "jqpmaker@mail.myisp.com"
        self.confirmed = datetime(2020, 5, 31, 19, 0, 0).strftime(dateformat)
        self.author_name = "John Q. Puzzlemaker"
        self.address_line_1 = "123 Main Street"
        self.address_line_2 = "Apt. 456"
        self.address_city = "Anytown"
        self.address_state = "NY"
        self.address_zip = "12345"
