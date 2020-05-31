# Crossword Editor
This application allows the user to create
a crossword puzzle. What follows is a list of
the objects it uses and a discussion of their
capabilities.

## Table of Contents

- [Grid](#grid)
- [Puzzle](#puzzle)
    - [Features](#puzzle-features)
        - [Cell numbering](#cell-numbering)
        - [Save and restore](#load-and-save)
        - [Export](#export)
- [Clue](#clues)
- [Wordlist](#wordlist)
- [User interface](#user-interface)

## Grid

This provides information about the size of the puzzle
and the location of all the black cells, which are
automatically arranged symmetrically.

## Puzzle

A puzzle is an _n x n_ grid of cells, each of which can be either:

1. Empty
2. Black
3. Filled with a letter A-Z

***n*** must be odd. The black spaces in the puzzle are symmetrical
along the _(1,n)--(n,1)_ axis.

There is a design phase, where a new puzzle is
set up with a specific size and set of black
cells.

Following this, the user adds letters
to the puzzle. At the same time (or at the end),
clue are entered for the across and down words.

### Puzzle features:

#### Cell numbering

Automatic numbering of across/down during setup.
The program will go through each cell
in the grid checking for whether
a word can begin here, either across
or down.  Black cells are automatically
skipped.  Here are the rules:
    
**Across** - a cell starts an "across" word if:

- It starts in column 1, or
- Immediately to the left is a black cell
    
To exclude one-letter words, there is an
additional requirement that:

- The cell is not in the n<sup>th</sup> column, and
- The cell to its right is not a black cell
    
**Down** - a cell starts an "down" word if:

- It starts in row 1, or
- Immediately above it is a black cell
    
To exclude one-letter words, there is an
additional requirement that:

- The cell is not in the n<sup>th</sup> row, and
- The cell below it is not a black cell

Then, after all cells in the grid
have been examined and the word starting cells
have been identified, they are numbered
from right to left, top to bottom.

#### Load and save

Program supports loading from a file and saving to a file.
This includes `to_json as`.  The file is in `JSON` format.
The saved version
needs to include the puzzle and clues. Here is
what needs to be stored in the file:

- The size of the puzzle (n)
- The grid (for a quick visual comparison)
- The black cell coordinates
- The list of cells that start an across and/or a down word
- The list of across words and their clues
- The list of down words and their clues

The `from_json` function operates by creating an empty puzzle
of the correct dimensions and then "replaying" the operations
that created the puzzle to begin with.

The `to_json` and `from_json` functions can be explicitly called
at any time.  This will allow a version control system
like `git` to keep track of changes to a saved file.
There could also be an `autosave` feature that saves the
current version at a configurable frequency.  This "autosave"
file, however, should not be allowed to overlay files the
user has explicitly saved.

#### Export and import clues

The `export_clues` method creates a `.csv` file with the following:

Column headings:
    - Sequence (the clue number)
    - Direction ("across" or "down")
    - Word (the text of the word)
    - Clue (the clue for the word)
    
then a list of all the across words, then all the down words.
The first three columns are just to identify the word.
Only the `clue` column is intended to be updated.

The `import_clues` method reads a `.csv` file and updates
the puzzle with the updated clue text.  

#### Export

Can export a crossword file to various formats, such as:

- [New York Times](https://www.nytimes.com/puzzles/submissions/crossword)
- [Lost Angeles Times](https://www.cruciverb.com/index.php?action=ezportal;sa=page;p=9)
- [Wall Street Journal](https://www.mikeshenk.com/wsj/WSJCrosswordSpecs.pdf)
- [Fireball Puzzles](http://www.fireballcrosswords.com/SpecSheet.pdf)
- [Chronicle of Higher Education](https://www.chronicle.com/section/Crosswords/43?cid=megamenu)
- [Puzzle Society](https://www.cruciverb.com/index.php?action=ezportal;sa=page;p=74)
- etc.

The export format and logic should be "pluggable"
so that new formats can be added as needed.

#### SVG generation

An image of either a grid or a puzzle can generated.
I use [SVG (Scalable Vector Graphics)](https://en.wikipedia.org/wiki/Scalable_Vector_Graphics)
as the image format, for several reasons:
- It is represented in text format (XML), rather than some obscure binary format.
This makes it much easier to generate
- It is human-readable
- It is scalable, meaning that images can easily be resized

##### Problems with SVG

I had trouble with using SVG at the start because the images were
getting clipped.  I learned the following:
- The grid size (visually) needs to be cellsize * number of cells.
The cell size is 50 pixels.
- In the XML, the `<svg>` element needs to have the following attributes:
    - A `width` attribute equal to "100%"
    - A `height` attribute also at "100%"
    - The `viewbox(0 0 xwidth ywidth)`attribute
    needs to have the grid size (see above) as both
    `xwidth` and `ywidth`
    - There needs to be a `transform"scale(d)"` attribute
    that causes the whole image to be resized to the correct
    scale.  The `d` above I have found heuristically to be
    a function of the grid size n:
```python
    def scale(n):
        m = -1 / 30
        b = 1.3
        return n * m + b
```    
The bounding rectange `<rect>` also needs to have 
`width` and `height` equal to the grid size (e.g., 750)

- In the HTML, the puzzle should be rendered simply as
an `<img>` element
    - The `src` attribute should be the simple name
    of the `.svg` file in the same directory as the `.html` file
    - There should be a `width` attribute equal to the visual grid size
    (see above)
    - There should be a `height` attribute equal to the visual grid size
    (see above)
    

## Clues

When the puzzle is first set up, it identifies
the starting cells of the `across` and `down` words
beginning and length. Then, associated with this puzzle,
the list of `across` and `down` clues are created.
Internally, the clues are not numbered consecutively
(i.e., not "13 ACROSS"), but rather, just indexed by
the row and column, so that if the puzzle is later changed
by adding or deleting a black cell, existing clues
will not have to be reentered (except for those
affected by the black cell change).

The clues are saved and loaded with the overall puzzle.

## WordList

A list of legal crossword words which can be searched
with a simple regular expression to obtain
the sublist of words that match that expression.
For example, for a list of all 4-letter words
that start with "D" and end with "H", the
pattern ```D..H``` will return the list
```
DASH
DISH
DOTH
```
The default list is obtained from 
the Linux ```/usr/share/dict/words``` file,
with

- All words converted to uppercase
- Foreign characters converted to close ASCII equivalents
- Special characters (such as apostrophes) removed
- Word list then re-sorted
- Duplicates removed

## User interface

### Startup screen

The startup screen has only the menu:
- Grids
    - New grid...
    - Open grid...
    - Save grid
    - Save grid as...
- Puzzles
    - New puzzle...
    - Open puzzle...
    - Save puzzle
    - Save puzzle as...
- Word list
- Export
    - New York Times format
- Help

Only the appropriate menu options are enabled.

The following are the use cases handled by the menu options.
 
#### New grid
In `menu.html`, the user selects *New grid...*.  This invokes
`do_new_grid()` in `do-new-grid.js`.

##### do-new-grid.js
The `do_new_grid()` javascript function turns on the
`new-grid-dialog.html` display attribute, making the
modal dialog visible.

##### new-grid-dialog.html
This dialog has a form that prompts the user for a grid size (`n`).
- If the user clicks `Cancel`, the system turns off the
`new-grid-dialog.html` display attribute, making the
modal dialog invisible.
- If the user clicks `OK`, the system calls the form's
action="`{{ url_for('new_grid_screen') }}`", which does
a `POST` with the value for `n` in the form.

##### webapp.new_grid_screen()
- Retrieves the grid size from the form data
- Sets a default grid name and stores it in the session
- Creates a grid of that size and stores it in the session
- Creates the SVG from the current grid
- Renders the `grid.html` template

##### grid.html
- Displays the grid from the SVG passed to the template
- Waits for mouse clicks
- When user clicks a cell:
    - Javascript `clickRC()` function converts the x, y
    of the mouse click event to a row and column in the
    grid.
    - Next, the function sends an AJAX GET request to the
    server at `{{ url_for("grid_click")}}` with r, c
    parameters appended.
    - When the AJAX request returns, it has updated SVG
    to be displayed.
    
##### webapp.grid_click
This is used via AJAX to update the status of the specified
black cell at r, c.


1. A square grid of size _n x n_ is displayed, with all cells empty.
1. The user can click on any empty cell to turn it black.
The corresponding symmetric cell is also turned black.
1. If the user clicks on a black cell, it is returned to white

#### Open
1. The user is presented with a list of saved grids
presented as table rows.  For each row, there is an
option to select or delete the grid.
1. If the user clicks `select` for a grid,
that file name is passed back to the server,
which loads the file into the user session
and redirects back to the grid edit screen

#### Save grid
1. The user clicks `Save grid` or `Save grid as...` to indicate
that all the black cells have been chosen.
Then the system calculates the locations of all the cells that start
an across or down word (numbered cells).
