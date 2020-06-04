# Crossword Editor
This application allows the user to create
a crossword puzzle. What follows is a list of
the objects it uses and a discussion of their
capabilities.

See the technical details at the
[github project wiki](https://github.com/philhanna/crossword/wiki)

## Table of Contents

- [Clue](#clues)
- [Wordlist](#wordlist)
- [User interface](#user-interface)


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
