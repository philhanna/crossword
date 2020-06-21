# Crossword Editor

This application allows the user to create
crossword puzzles suitable for publication.

## Table of contents
- [Installation](#installation)
    - [Python requirements](#python-requirements)
    - [Download the code](#download-the-code)
    - [Configuration](#configuration)
        - [Paths to be configured](#paths-to-be-configured)
        - [`.crosswords_config.ini` file](#crosswords-configini-file)
- [Starting the application](#starting-the-application)
- [User's guide](#users-guide)

## Installation

### Python requirements

The application requires Python 3.7 or greater and several Python packages.
You may wish to use a
[virtual environment](
https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)
in which to install these packages and run the application, but it is not required.
Here are the required components:

- [Python 3.7+](https://www.python.org/).
You can download and install this from the
[Python downloads](https://www.python.org/downloads/release) page.
- [Pip](https://www.w3schools.com/python/python_pip.asp),
the Python package installer.
_If you have Python 3 or later, **Pip** is already installed._
- The [Flask](https://flask.palletsprojects.com/en/1.1.x/) package,
for running the web application.
- The [Flask-Session](https://flasksession.readthedocs.io/en/latest/)
package, which provides support for server-side sessions.
- A web browser, such as Google Chrome, Microsoft Edge, or Opera.
(_Note: Firefox is not supported at present due to a bug in
finding rows and columns from the x and y coordinates of
a mouse click.  See issue #8 in the GitHub repository._)

### Download the code

You can download the code from the GitHub repository
at [https://github.com/philhanna/crossword](https://github.com/philhanna/crossword).

1. Click the green **Clone or download** button
and then click [**Download ZIP**].
2. Unzip the zip file to a location of your choice

### Configuration

The application needs to use three directories for storing your work,
as well as a word dictionary.  These parameters are:

#### Paths to be configured

- The **grids** directory.
Here is where JSON files representing grids are stored.
- The **puzzles** directory.
Here is where JSON files representing puzzles are stored.
- The **wordlists** directory.
This is used by some utilities, but the application is not
directly dependent on it.
- The path to the words dictionary.
This is a simple text file of possible words, all uppercase
and without spaces, numbers, or special characters.
You can make your own file, or download it from numerous
places.

#### crosswords_config.ini file
You provide this information in a configuration file
in your home directory named **.crosswords_config.ini**.
You can create this file with any ordinary text editor.
It *must* be stored in the home directory of the user
who is running the application.
It looks like this:

```ini
[data]
grids_root=/home/myuserid/.local/share/crossword/grids
puzzles_root=/home/myuserid/.local/share/crossword/puzzles
wordlists_root=/home/myuserid/.local/share/crossword/wordlists
words_filename=/home/myuserid/.local/share/crossword/words

[author]
name=John Q. Puzzlemaker
address=123 Main Street
city_state_zip=Anytown USA
email=jqpuzzlemaker@gmail.com
```

On Windows, the `[data]` section might look like this:

```ini
[data]
grids_root=C:\Users\myuserid\AppData\local\crossword\grids
puzzles_root=C:\Users\myuserid\AppData\local\crossword\puzzles
wordlists_root=C:\Users\myuserid\AppData\local\crossword\wordlists
words_filename=C:\Users\myuserid\AppData\local\crossword\words
```

The `[author]` section is used by the **publish** features
of the application.

You must ensure that these directories and files actually exist
before you attempt to run the application. There are sample
grids, puzzles, and a word database in the `samples` directory.

## Starting the application

The application uses the Python `flask` framework for web applications.
The Python program that runs the application is named `webapp.py`.
It uses Flask to run a small HTTP server that you connect to with
a web browser.

To start the HTTP server, run `webapp.py`, as follows:

```bash
$ cd path/to/crossword-master
$ ./webapp.py
```

On Windows, this would be:

```bat
C:> cd path\to\crossword-master
C:> python webapp.py
```

> If you are using a virtual environment,
> you will need to activate the environment
> before you start the server.
> See the [venv docs](https://docs.python.org/3/library/venv.html)
> for details.

Finally, to start using the application:

1. Open a web browser
2. Go to http://localhost:5000

## User's guide

See details at the
[github project wiki](https://github.com/philhanna/crossword/wiki)
