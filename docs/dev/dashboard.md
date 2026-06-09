Add a dashboard, a new view to the SPA.  The dashboard contains
a top and bottom half.

## Top half

The top half is spanned by four cards, labeled with the categories
"IN PROGRESS", "COMPLETED", "SUBMITTED", and "ARCHIVED".

These consist of information about puzzles in that state:
1. "IN PROGRESS" is for draft,
2. "COMPLETED" is for filled or finished,
3. "SUBMITTED" is for submitted or published
4. "ARCHIVED" is for archived.

Each card consists of the title at the top and 4 rows for puzzles underneath.
The title consists of the card name in bold followed by the total number of
puzzles in that category in parentheses.

The card background colors are the same as those specified in 
https://www.w3schools.com/w3css/5/w3.css, in particular,

- Card 1 background color is `w3-pale-yellow`
- Card 2 background color is `w3-pale-green`
- Card 3 background color is `w3-pale-blue`
- Card 4 background color is `w3-light-grey`

Do not include that stylesheet in the project, just extract the RGB hex information for the colors specified above.

The puzzle rows contain information on a single puzzle.
Each puzzle row contains the title of the puzzle, in a bold font
smaller than the category title, then under that:
1. the date last modified in mm/dd format
2. the puzzle size (n x n)
3. the number of words in the top two lengths (similar to what is done in PuzzleUseCases.get_puzzle_preview)

and other information about that puzzle, depending on the category, as described below.

Card 1 rows include a rendering, flush right on the same row as the
puzzle title, of the percentage of words filled,
something like:
```html
<div class="progress-wrap">
    <div class="progress-bar">
        <div class="progress-fill" style="width: 92%">
        </div>
    </div>
    <div class="progress-text">92% filled</div>
</div>
```
Where `progress-fill` is a rounded line changing colors from green to
light gray at the percentage point.

Card 2 rows contain the words "fully clued" flush right, if the state is
"finished"

Card 3 rows contain the words "submitted to" + <publisher>, if state is
"submitted", or "published by" + <publisher>, if state = "published"

## Bottom half
The bottom half is a full width card with tabs across the top
and rows for puzzles underneath.

### Tabs
The tabs are labelled
* draft
* filled
* finished
* submitted
* published
* archived
* all

### Rows
The rows are a scrollable list of all puzzles in the state of the
tab label, or all puzzles, if the tab label is "all".

Each row in the list starts with a "State" button, which is a
dropdown list of all possible state, with the current state
selected.  Selecting another state invokes a state change dialog,
which consists of:
    - puzzle name: xxxxxxxxxxx
    - current state: xxxxxxxxx [publisher: xxx if the current state is submitted or published]
    - new state: xxxxxxxxxxxxx [publisher: xxx if the new state is submitted or published]
    - OK and Cancel buttons
Clicking the OK button causes the puzzle to be saved in the new state.
If the new state is submitted or published, the publisher field must be
filled in.  Otherwise, the publisher field is optional.

#### draft tab
The column headings are State, Name, Title, Size, Words, Modified.
The size is rendered as n x n.

#### filled tab
Same format as the draft tab

#### finished tab
Same format as the draft tab

#### submitted tab
Similar format to draft tab, but includes a "Publisher" column after
State

#### published tab
Same format as submitted tab

#### all tab
Same format as submitted tab
