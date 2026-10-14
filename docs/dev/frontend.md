# Frontend

The frontend is the web page the server sends to the browser: one HTML file,
six stylesheets and about thirty small JavaScript files under `frontend/`. It
has no build step. The files in the repository are exactly the files the
browser gets, so a change shows up on the next page reload.

It uses no framework. Each JavaScript file is an *ES module*: it lists the
functions it shares with other files (`export`) and the ones it uses from
them (`import`), and the browser loads them in the right order by itself.

## How the page starts

`index.html` holds the page skeleton: the app bar and its menus, the empty
editor panes, and the HTML for every dialog. At the bottom it loads one
script:

```html
<script type="module" src="/static/js/main.js"></script>
```

`main.js` imports every other module. As each module loads, it registers the
click handlers it owns (see [Clicks and other events](#clicks-and-other-events)).
Then `main.js` starts listening for clicks, reads the message timeout from
`/api/config`, and shows the dashboard.

## Where things live

```
frontend/
  index.html                 page skeleton, menus, dialog HTML
  static/css/                base, controls, dialogs, editor, dashboard, settings
  static/js/
    main.js                  startup
    core/                    no knowledge of puzzles or screens
      actions.js             the click-handler table and the listeners
      api.js                 apiFetch() and ApiError
      dom.js                 escapeHtml, showElement, hideElement
      hash.js                checksum for "unsaved changes"
      state.js               AppState: which view, which puzzle
    ui/                      pieces of the page shared by every screen
      view.js                switching between dashboard and editor
      menu.js                which top-menu items are enabled when
      message-line.js        the notice/error line under the app bar
      dialogs.js             askText, askFields, askConfirm, showAlert
      chooser.js             the paged list of puzzle previews
      context-menu.js        the right-click menu
    dashboard/
      dashboard.js           the cards and the puzzle table
      state-dialog.js        changing a puzzle's state
      history-popup.js       a puzzle's history, and restoring an old version
    editor/
      editor.js              draws the editor; Grid mode / Puzzle mode; undo
      grid-mode.js           toggling black cells, rotate, generate
      selection.js           the selected word and saving it
      grid-clicks.js         single click = Across, double click = Down
      keyboard.js            typing into the grid
      word-editor.js         the word editor panel and its suggestions
      clues-panel.js         the clue list and editing a clue in place
      stats-panel.js         the Stats panel
      fill-order-panel.js    the Fill order panel
    puzzle-file/
      lifecycle.js           new, open, save, save as, rename, close, delete
      import.js              the Import menu
      export.js              the Export menu
    settings/settings.js     the settings panel
    svg/grid-svg.js          drawing the grid as an SVG picture
```

Two rules decide where new code goes:

- **A module that draws something doesn't talk to the server, and a module
  that talks to the server doesn't build HTML.** The split isn't perfect yet:
  most editor panels still fetch their own data. Lean this way when adding
  code.
- **Each piece of state has one owner** (see [Who owns which state](#who-owns-which-state)).

## Clicks and other events

Elements don't carry `onclick="..."` attributes. Instead they say what they
do in a data attribute, and each module registers a handler for every name
it owns:

```html
<a id="menu-puzzle-save" class="app-menu-item" data-action="puzzle-save">Save</a>
```

```js
// in puzzle-file/lifecycle.js
registerActions({
    'puzzle-save': () => do_puzzle_save(),
});
```

`core/actions.js` puts one listener per kind of event on the whole page. When
something is clicked, it looks for the nearest element with `data-action`,
finds the handler registered under that name, and calls it with the element
and the event: `handler(element, event)`. Because the listener sits on the
page rather than on each button, HTML that is redrawn later works without
re-attaching anything.

| Attribute | Runs on |
|---|---|
| `data-action` | a click on the element or anything inside it |
| `data-backdrop-action` | a click on the element itself but not its contents (the dimmed area around a dialog) |
| `data-input` | typing in a text box |
| `data-change` | a changed checkbox, dropdown or radio button |
| `data-submit` | a submitted form |
| `data-contextmenu` | a right-click |

Any other `data-*` attributes are the handler's arguments, read from
`element.dataset`:

```html
<button data-action="export" data-format="xd">xword xd…</button>
```

```js
registerActions({
    'export': (el) => do_export(el.dataset.format),
});
```

Registering the same name twice, or using a name nobody registered, throws
an error, which the browser tests catch.

A few things still use ordinary listeners, because they need to: the grid
picture's click handler (it needs the click position), the two keyboard
handlers, and closures built in code, such as the context menu's items.

### Keyboard handling

Keys typed into the grid go to one of two handlers in `editor/keyboard.js`:
`_peKeydown` while a word is selected, `_weKeydown` while the word editor
panel is open. Opening and closing the word editor swaps them. Exactly one
may be attached at a time, or each key is handled twice. The browser tests
check this (type, open the word editor, close it, type again).

### Single and double clicks on the grid

A single click on the grid waits 280 ms before acting, to be sure it isn't
the first half of a double click. A single click selects the Across word, a
double click the Down word. See `editor/grid-clicks.js`.

## Who owns which state

`AppState` (in `core/state.js`) holds only what every part of the app needs:
which view is showing, and the open puzzle's names, data, saved checksum,
lifecycle state and theme word lengths. Everything else belongs to the module
that uses it, which keeps it in one object or variable that only it changes.
Other modules go through the functions it exports.

| State | Owner | Read / change it with |
|---|---|---|
| View, open puzzle | `core/state.js` | `AppState` |
| The selected word and its draft | `editor/selection.js` | `getSelectedWord()`, `selectWord()`, `clearSelection()` |
| Which sidebar panel shows | `editor/editor.js` | `getSidebarTab()`, `setSidebarTab()` |
| Stats data, Slots/Words sub-tab | `editor/stats-panel.js` | `statsLoaded()`, `forgetStats()` |
| Fill-order results, "loading" flag | `editor/fill-order-panel.js` | `cachedFillOrder()`, `isFillOrderLoading()`, `forgetFillOrders()` |
| "Grid changed since Grid mode" | `editor/grid-mode.js` | `takeGridStructureChanged()`, `forgetGridChanges()` |
| Clue list direction, pending clue save | `editor/clues-panel.js` | (private) |
| Click timing | `editor/grid-clicks.js` | (private) |
| Suggestions and their page | `editor/word-editor.js` | (private) |
| Chooser contents and page | `ui/chooser.js` | (private) |
| Message timeout and timer | `ui/message-line.js` | `messageLineTimeout()`, `setMessageLineTimeout()` |
| Dashboard rows, tab, sort | `dashboard/dashboard.js` | `DashboardState` |

When a puzzle is opened or closed, `resetEditor()` in `editor/editor.js`
clears the editor's state in one go.

Two details worth knowing:

- Other modules may change the selected word's *draft* fields (typing does
  that), but only `selection.js` creates, replaces or clears the selection.
- In-place clue edits are saved one after another: each new edit waits for
  the previous save (`clues.pendingSave`), so they reach the server in the
  order they were made.

## Dialogs

`ui/dialogs.js` opens the message box and the input box and returns a
*promise*, a value that arrives once the user closes the dialog. With
`await`, a series of questions reads top to bottom:

```js
const name = await askText('Rename puzzle', 'New name:', currentName);
if (name === null) return;          // Cancel
if (!await askConfirm('Overwrite puzzle', 'It already exists. Overwrite it?', 'Overwrite')) return;
```

| Function | Resolves to |
|---|---|
| `askText(title, label, value)` | the text typed, or `null` on Cancel |
| `askFields(title, fields)` | `{ name: value, … }`, or `null` on Cancel |
| `askConfirm(title, prompt, okLabel)` | `true` for OK, `false` for Cancel |
| `showAlert(title, prompt)` | nothing; settles when the box is closed |

Titles, labels and prompts are HTML, so pass any user-entered text through
`escapeHtml()` first. They aren't called `confirm` and `alert` because those
names belong to the browser's own dialogs. A forgotten import would then
silently show the wrong one.

## Talking to the server

`apiFetch(method, path, body)` in `core/api.js` sends JSON and returns the
parsed reply. If the server answers with an error status, it throws an
`ApiError` whose message is the server's own `{"error": "..."}` text. The
usual pattern:

```js
try {
    AppState.puzzleData = await apiFetch('POST', `/api/puzzles/${encodeURIComponent(wn)}/clear`);
    renderPuzzleEditor();
} catch (e) { showRequestError('Error clearing puzzle', e); }
```

`showRequestError(what, e)` shows "*what*: *server's message*" on the message
line, or just "*what*" when the request never got an answer.

## Styles

The stylesheets load in this order, and later ones refine earlier ones:

| File | Holds |
|---|---|
| `base.css` | the reset, colors and spacing (CSS variables), app bar, page layout, message line |
| `controls.css` | top-menu dropdowns, buttons, text boxes, the disabled look, the right-click menu |
| `dialogs.css` | the dimmed backdrop, dialog frame, the chooser |
| `editor.css` | action bar, grid, sidebar panels, word editor |
| `dashboard.css` | the dashboard |
| `settings.css` | the settings panel |
| `theme.css` | made by the server from the `theme_color` setting; overrides the color variables |

Each file keeps its narrow-window rules (`@media`) at its end. Disabled
buttons and menu items get the `is-disabled` class.

The server tells the browser to check for a newer copy of every script and
stylesheet on each load (`Cache-Control: no-cache`). A stale cached module
next to fresh ones would otherwise fail in confusing ways. Images may still
be cached.

## How to…

### Add a menu item

1. Add it to the menu in `index.html`, with an `id` and a `data-action`:

   ```html
   <a id="menu-puzzle-print" class="app-menu-item" data-action="puzzle-print">Print…</a>
   ```

2. Write the function in the module it belongs to and register it:

   ```js
   registerActions({
       'puzzle-print': () => do_puzzle_print(),
   });
   ```

3. Say when it's enabled, in `MENU_RULES` in `ui/menu.js`:

   ```js
   { id: 'menu-puzzle-print', enabledWhen: (s) => s.inEditor },
   ```

   The rule gets `{ onDashboard, inEditor, hasName, mode, wordEditorOpen }`.
   A menu item without a rule stays enabled all the time.

### Add a side panel

The sidebar in Puzzle mode shows one of the Clues, Word, Stats and Fill
order panels. Grid mode shows the Grid or Stats panel.

1. Make a module in `editor/`, say `editor/notes-panel.js`, with:
   - a function that returns the panel's HTML from data it is given or keeps
     itself;
   - a function that fetches that data, then calls `setSidebarTab('notes')`
     and `renderPuzzleEditor()`;
   - a `registerActions({...})` for its buttons, including the one that
     opens it (put that button in `renderActionBar()` in `editor/editor.js`).
2. In `editor/editor.js`:
   - add a `case 'notes':` to `renderPuzzleEditorRhs()` that calls the
     panel's render function;
   - add a label to `renderSidebarTabs()`, and add `'notes'` to `tabList` in
     `renderPuzzleEditorRhs()` if it should have a tab button (Stats and
     Fill order don't; they open from the action bar);
   - if the panel needs fetching before it can show, handle that in
     `switchSidebarTab()`, the way Stats does;
   - if it holds state about the open puzzle, give it a `forget…()` function
     and call that from `resetEditor()`.
3. Add its styles to `static/css/editor.css`.

### Add an import format

1. Add the server endpoint (see [endpoints.md](endpoints.md)). It should take
   `{ name, content }` for a text file or `{ name, content_b64 }` for a
   binary one.
2. Add a row to `IMPORT_FORMATS` in `puzzle-file/import.js`:

   ```js
   jpz: { title: 'Import jpz puzzle', accept: '.jpz', read: 'text', endpoint: '/api/import/jpz' },
   ```

   `accept` lists the file extensions the file picker offers. The suggested
   puzzle name is the file name without them.
3. Add the menu item in `index.html`:

   ```html
   <a id="menu-import-jpz" class="app-menu-item" data-action="import" data-format="jpz">jpz…</a>
   ```

4. Add `{ id: 'menu-import-jpz', enabledWhen: (s) => s.onDashboard }` to
   `MENU_RULES` in `ui/menu.js`. Imports are only offered from the
   dashboard, because importing opens the new puzzle.
5. Add the format to `IMPORTS` in `crossword/tests/frontend/test_import_export.py`.

## Tests

`crossword/tests/frontend/` drives the real app in a real browser
(Chromium, through Playwright). Each test starts the server on a free port
with a throwaway database and settings file, then clicks through a task from
start to finish: the dashboard, Grid mode, typing and the word editor, every
Puzzle menu item, import and export in every format, and settings. A test
fails if the page throws a JavaScript error.

They run with the rest of the suite (`pytest crossword/tests/`). Once, after
`pip install -e .`, download the browser:

```
playwright install chromium
```

To run only the browser tests, use `pytest crossword/tests/frontend/`. Add
`--headed --slowmo 300` to watch them.

`crossword/tests/frontend/helpers.py` has the shared steps: open a menu
item, click a grid cell, fill in a dialog. When the page's structure
changes, fix them there.

Some things are easier to check by eye, such as how dialogs look and both
color themes. A checklist for those is in
[refactor_frontend.md](../refactor_frontend.md#manual-checks).
