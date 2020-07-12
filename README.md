# Crossword Editor

This is a web-based application that allows the user
to create and edit crossword puzzles.

## Table of contents
- [Setup](#setup)
    - [Install python](#install-python)
    - [Install git](#install-git)
    - [Install the crossword application](#install-the-crossword-application)
    - [Configuration](#configuration)
- [Starting the server](#starting-the-server)
- [Starting the application](#starting-the-application)

## Setup

Depending on what is already installed on your computer,
you may or may not have to do all these steps.

### Install python
[Python 3.6 or greater](https://www.python.org/) is required.
If you don't already have it installed, see the
[Python downloads](https://www.python.org/downloads/release) page.

### Install git
`git` is the source code version control system used by **GitHub**.
If you do not already have it installed, see the 
[git book official website](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

### Install the crossword application

#### Installing for the first time
If this is the first time you have downloaded the software
onto this computer, clone it from the GitHub repository,
like this:

**On Windows:**
```bat
cd %USERPROFILE%
git clone https://github.com/philhanna/crossword
```

**On MacOS/Linux:**
```bash
cd $HOME
git clone https://github.com/philhanna/crossword
```

#### Upgrading to a newer version
If you are upgrading to a newer version, you only need
to run "git pull" from the crossword directory:

**On Windows:**
```bat
cd %USERPROFILE%\crossword
git pull
```

**On MacOS/Linux:**
```bash
cd $HOME/crossword
git pull
```

#### Creating a virtual environment and installing the application
Then install the application in a Python virtual environment:

**On Windows:**
```bat
cd %USERPROFILE%\crossword
python -m venv venv
venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m pip install .
```

**On MacOS/Linux:**
```bash
cd $HOME/crossword
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install .
```

The `pip install -r requirements.txt` step installs the
following, if required:
- The [Flask](https://flask.palletsprojects.com/en/1.1.x/) package,
for running the web application.
- The [Flask-Session](https://flasksession.readthedocs.io/en/latest/)
package, which provides support for server-side sessions.

The `pip install .` command (**note the dot!**) actually installs
the application in your Python system.

### Configuration

The application uses the following default configuration:
- A sample database named `samples.db`
- A logging level of `INFO`

You can change the configuration by creating a text file
named `.config.ini` in your user HOME directory.  This
file has the format:
```ini
[DEFAULT]
#
# dbfile -  The fully qualified path to the crossword database.
#           This is an SQLite 3 database.
# See https://www.sqlite.org/index.html
#
dbfile=/path/to/crossword.db
#
# log_level -   This must one of the following:
#               CRITICAL
#               ERROR
#               WARNING
#               INFO
#               DEBUG
#               NOTSET
# See https://docs.python.org/3.7/library/logging.html#levels
#
log_level=INFO
```
Other configuration options may be added in future releases.

## Starting the server

The program uses the Python `flask` framework for web applications.
The Python program that runs the application is named `webapp.py`.
It uses Flask to run a small HTTP server that you connect to with
a web browser.

To start the HTTP server, run `main.py`, as follows:

**On Windows:**
```bat
cd %USERPROFILE%
venv\Scripts\activate.bat
python -m crossword.ui.main
```

**On MacOS/Linux:**
```bash
cd $HOME/crossword
source venv/bin/activate
python -m crossword.ui.main
```

This runs an HTTP server on port 5000 on your computer.
You can leave it running or cancel it at any time with Ctrl-C.
You may wish to create a script (or a .bat file, on Windows)
to run these steps.

## Starting the application

Finally, to start using the application:

1. Open a web browser
_(Note: The application works in Chrome, Microsoft Edge, and Opera.
Firefox is not supported at present because of a
bug in translating mouse clicks into grid row and column values.
See [issue #8](https://github.com/philhanna/crossword/issues/8)
in the GitHub repository)_
2. Go to http://localhost:5000
_(Note: Sometimes I have to use http://127.0.0.1:5000 the first time)_

There is a **Help** button on the far right of the menu bar
that takes you to the user's guide.
You can also access this guide directly at the project's
[github wiki](https://github.com/philhanna/crossword/wiki).
