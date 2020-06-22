# Crossword Editor

This is a web-based application that allows the user
to create and edit crossword puzzles.

## Table of contents
- [Setup](#setup)
    - [Install python](#install-python)
    - [Install git](#install-git)
    - [Install the crossword application](#install-the-crossword-application)
    - [Configuration](#configuration)
        - [Data directories](#data-directories)
        - [`.crossword_config.ini` file](#crossword-configini-file)
- [Starting the server](#starting-the-server)
- [Starting the application](#starting-the-application)

## Setup

Depending on what is already installed on your computer,
you may or may not have to do all these steps.

### Install python
[Python 3.7+](https://www.python.org/) is required.
If you don't already have it installed, see the
[Python downloads](https://www.python.org/downloads/release) page.

### Install git
`git` is the source code version control system used by **GitHub**.
If you do not already have it installed, see the 
[git book official website](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

### Install the crossword application
From a command prompt in your **user home directory** (referred to
below as `$HOME`), do the following:
```
cd $HOME
git clone https://github.com/philhanna/crossword
cd crossword
pip install -r requirements.txt
```
This last step (install requirements.txt) installs the
following, if required:
- The [Flask](https://flask.palletsprojects.com/en/1.1.x/) package,
for running the web application.
- The [Flask-Session](https://flasksession.readthedocs.io/en/latest/)
package, which provides support for server-side sessions.

### Configuration

The application needs to use three directories for storing your work,
as well as a word dictionary.  These parameters are:

#### Data directories

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

You must ensure that these directories and files actually exist
before you attempt to run the application.

There are sample grids, puzzles, and a word database
in the `samples` directory. Copy the contents of this directory
to some convenient place, such as the following:

MacOS/Linux:
```
/home/myuserid/.local/share/crossword
```

Windows:
```
C:\Users\myuserid\AppData\local\crossword
```

#### crossword_config.ini file
You provide this information in a configuration file
in your home directory named **.crossword_config.ini**.
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

On Windows:

```ini
[data]
grids_root=C:\Users\myuserid\AppData\local\crossword\grids
puzzles_root=C:\Users\myuserid\AppData\local\crossword\puzzles
wordlists_root=C:\Users\myuserid\AppData\local\crossword\wordlists
words_filename=C:\Users\myuserid\AppData\local\crossword\words

[author]
name=John Q. Puzzlemaker
address=123 Main Street
city_state_zip=Anytown USA
email=jqpuzzlemaker@gmail.com
```

The **[author]** section is used by the **publish** features
of the application.

## Starting the server

The program uses the Python `flask` framework for web applications.
The Python program that runs the application is named `webapp.py`.
It uses Flask to run a small HTTP server that you connect to with
a web browser.

To start the HTTP server, run `webapp.py`, as follows:

MacOS/Linux:
```
cd $HOME/crossword
python3 webapp.py
```

Windows:
```bat
C:> cd $HOME\crossword
C:> python webapp.py
```

This runs an HTTP server on port 5000 on your computer.
You can leave it running or cancel it at any time with Ctrl-C.

## Starting the application

Finally, to start using the application:

1. Open a web browser
_(Note: The application works in Chrome, Microsoft Edge, and Opera.
Firefox is not supported at present because of a
bug in translating mouse clicks into grid row and column values.
See [issue #8](https://github.com/philhanna/crossword/issues/8)
in the GitHub repository)_
2. Go to http://localhost:5000

There is a **Help** button on the far right of the menu bar
that takes you to the user's guide.
You can also access this guide directly at the project's
[github wiki](https://github.com/philhanna/crossword/wiki).
