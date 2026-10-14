# Frontend refactoring plan

## Status

Carried out on 2026-10-13, one commit per phase (Phase 4 and Phase 7 in
several). The result is described in [dev/frontend.md](dev/frontend.md).
"Where things stand today" below describes the code *before* the work.

Where the result differs from the plan:

- The confirm and alert dialogs are `askConfirm` and `showAlert`, not
  `confirm` and `alert`. Those names belong to the browser's own dialogs,
  so a forgotten import would silently show the wrong one.
- Two files not in the target layout: `editor/selection.js` (the selected
  word, used by the click, keyboard, clue and word-editor code alike) and
  `ui/view.js` (switching between dashboard and editor).
- Fonts and icons still load from Google (the optional last step of Phase 7).
- Error messages are now worded the same way everywhere: "*what failed*:
  *the server's reason*".

Three bugs turned up and were fixed on the way:

- Text typed into the word editor's clue box and then cancelled with Escape
  was saved anyway with the next edit (Phase 3).
- Renaming a puzzle to a name already in use showed a garbled message box
  and then did nothing (Phase 5).
- ipuz and Crossword Compiler import stayed enabled in the editor while the
  other three formats did not (Phase 1). All five are now dashboard-only.

Screenshots of 26 screens, menus and dialogs were compared with the original
code once Phases 1–6 were done, and again after each step of Phase 7, in two
color themes (and, for Phase 7.2, at two window widths). They match pixel for
pixel, apart from timestamps.

## Purpose

The frontend works, but its insides have grown hard to change safely. This
plan rebuilds the frontend's internal structure **without changing what the
user sees or does**. Every screen, menu, dialog, keyboard shortcut and
color should look and behave the same afterwards. The backend API does
not change.

The work is split into phases. After each phase the app still runs and can
be committed, so the refactoring can be paused at any point without leaving
things half-broken.

## Where things stand today

The frontend is about 6,250 lines:

| File                  | Lines | What it holds                                          |
|-----------------------|------:|--------------------------------------------------------|
| `index.html`          |   291 | Page skeleton, menus, every dialog's HTML              |
| `css/style.css`       | 1,930 | All styling                                            |
| `js/puzzle-editor.js` | 1,515 | Editor screen, grid mode, side panels, open/save/import/export |
| `js/word-editor.js`   | 1,037 | Clicking on the grid, typing letters, word editor panel |
| `js/dashboard.js`     |   527 | Dashboard screen, state-change dialog, history popup   |
| `js/ui.js`            |   489 | Message line, dialogs, puzzle chooser, menus, view switching |
| `js/settings.js`      |   270 | Settings panel, and the page's startup code            |
| `js/svg.js`           |   160 | Drawing the grid as an SVG picture                     |
| `js/state.js`         |    31 | Shared application state                               |

### The main problems

1. **Everything is global.** The seven script files are loaded one after
   another with plain `<script>` tags. Every function and variable lands
   in one shared space, so any file can call or change anything in any
   other file. Nothing shows which file depends on which, and the order of
   the `<script>` tags matters in ways that aren't written down.

2. **Clicks are wired up inside HTML text.** There are 42
   `onclick="..."` attributes in `index.html` and another 53 inside HTML
   strings built in JavaScript. Every function they name has to be global,
   and a code search can't tell you which functions are used, because many
   of the calls are buried inside strings. That is how unused functions
   pile up. Seven are dead today: `buildGridSvg`, `closeFillOrderPanel`,
   `closeStatsPanel`, `rejectIfNameExists`, `showChooser`, `_weHasChanges`
   and `_weRenderLhs`.

3. **State is scattered.** `AppState` in `state.js` holds some of it.
   `DashboardState` holds more. About twenty more module-level variables
   are spread across files: `_ch*` (chooser), `_we*` (word editor),
   `_click*` (click timing), `_lastClueDirection`, `_inlineClueSave`, and
   so on. No single place shows what the app currently "knows".

4. **Files mix unrelated jobs.** `puzzle-editor.js` draws the editor, runs
   grid mode, manages three side panels, and also holds the whole
   Puzzle / Import / Export menu (new, open, save, save as, rename, close,
   delete, five importers, exporting). `settings.js` holds the page's
   startup code. `word-editor.js` holds both click handling on the grid
   and the word editor panel.

5. **Copy-and-paste code.** The five import functions
   (`do_puzzle_import`, `_import_xd`, `_import_ipuz`, `_import_ccxml`,
   `_import_puz`) are about 40 lines each and nearly identical. The menu
   enable/disable code in `updateMenu()` is a long run of repeated
   one-line `if`s. It has also drifted out of step: AcrossLite, `.puz` and
   xd imports are disabled while a puzzle is open, but ipuz and Crossword
   Compiler imports are not.

6. **Dialogs use nested callbacks.** `inputBox(title, label, value,
   onSubmit)` takes a function to run when the user clicks OK. Asking two
   questions in a row means a callback inside a callback, which is why
   functions like `do_puzzle_new()` contain helper functions inside
   themselves.

7. **Server errors are handled ad hoc.** `apiFetch()` never checks whether
   the request succeeded. Every caller has to remember to look for
   `data.error`, and each one words its error message its own way.

8. **Outside dependencies loaded from the web.** The W3.CSS stylesheet
   loads from `www.w3schools.com` on every page load, for about 70 class
   uses (dropdowns, buttons, cards, the "disabled" look). If that site is
   slow or down, the app looks broken.

9. **No frontend tests.** The backend has about 9,400 lines of tests. The
   frontend has none. Today the only way to know a frontend change didn't
   break something is to click around by hand.

### What is in good shape and should be kept

- No build step. The files the server sends are the files in the repo.
  For a single-user tool that is a real advantage, and this plan keeps it.
- No framework. The app is small enough that plain JavaScript is fine.
- The color theme already runs on CSS variables, which `theme.css`
  (generated by the server) overrides. That design stays.
- `svg.js` is already self-contained and easy to follow.

## Decisions

These are the choices the plan is built on. Each one is a recommendation,
open to change before work starts.

- **Use the browser's built-in module system ("ES modules").** Each file
  says which functions it shares (`export`) and which ones it uses from
  other files (`import`). The browser loads them in the right order by
  itself. This fixes problems 1 and 2 at the root and needs no build tool.
  The page loads one file, `main.js`, with `<script type="module">`.
- **No framework, no build step, no TypeScript.** Adding React or Vue
  would mean rewriting every screen and adding a build toolchain to look
  after, which is a lot of cost for one user. For editor help with types,
  files can optionally start with `// @ts-check` and use JSDoc comments.
  VS Code then catches many mistakes, with nothing to install.
- **Wire up clicks in code, not in HTML.** A button gets a label such as
  `data-action="puzzle-save"` instead of `onclick="do_puzzle_save()"`.
  One listener per region of the page catches every click, reads the
  label, and looks it up in a table of actions. (This technique is called
  "event delegation".) It works the same for HTML built on the fly, so
  re-rendering a panel never needs listeners re-attached.
- **One owner for each piece of state.** Each part of the app (dashboard,
  editor, word editor, chooser) keeps its own state in its own module and
  changes it only through functions it exports. `AppState` shrinks to the
  facts that really are shared: which view is showing and which puzzle is
  open.
- **Dialogs return promises.** `const name = await askText('Save as',
  'Puzzle name:')` instead of a callback. A sequence of questions then
  reads top to bottom. Cancel resolves to `null`.
- **Write tests before moving code.** See Phase 0.

## Target layout

```
frontend/
  index.html                 page skeleton + dialog HTML, no onclick
  static/css/
    base.css                 variables, page layout, typography
    controls.css             buttons, dropdown menus, inputs (replaces W3.CSS)
    dialogs.css
    dashboard.css
    editor.css               grid, side panels, word editor
    settings.css
  static/js/
    main.js                  startup: load config, attach listeners, show dashboard
    core/
      api.js                 fetch wrapper; throws ApiError on any failure
      state.js               shared app state (current view, open puzzle)
      actions.js             the data-action table and the click listener
      dom.js                 escapeHtml, show/hide, small helpers
      hash.js
    ui/
      message-line.js
      dialogs.js             askText, askFields, confirm, alert (promise based)
      chooser.js             the puzzle preview chooser
      context-menu.js
      menu.js                top menu + a table of "enabled when" rules
    dashboard/
      dashboard.js
      state-dialog.js
      history-popup.js
    editor/
      editor.js              show the editor, switch between grid and puzzle mode
      grid-mode.js
      clues-panel.js
      stats-panel.js
      fill-order-panel.js
      grid-clicks.js         single vs. double click, selecting a word
      keyboard.js            typing letters into the grid
      word-editor.js         the word editor panel and its suggestions
    puzzle-file/
      lifecycle.js           new, open, save, save as, rename, close, delete
      import.js              one importer driven by a table of formats
      export.js
    settings/
      settings.js
    svg/
      grid-svg.js
```

The guide for drawing the lines between modules: **a module that draws
something doesn't talk to the server, and a module that talks to the
server doesn't build HTML.** `editor/clues-panel.js` builds the clue list
from data it is handed. `puzzle-file/lifecycle.js` calls the API and then
asks the editor to redraw.

## Phases

Each phase ends with: all tests passing, a manual run-through of the
checklist in Phase 0, and a commit.

### Phase 0 — Safety net

Before moving any code, add tests that click through the real app in a
real browser, so later phases can show that nothing changed.

- Add `pytest-playwright` to `[project.dependencies]` in `pyproject.toml`.
  Playwright is a library that drives a real browser from a test. Then
  run `playwright install chromium` once.
- Add `crossword/tests/frontend/` containing a test fixture (a shared
  setup step) that starts the server on a free port with a throwaway
  SQLite file, plus a handful of end-to-end tests. Each test performs a
  user task from start to finish:
  - Dashboard loads and lists puzzles. Filter tabs and sorting work.
  - New puzzle → grid mode → click to place black cells → undo/redo →
    switch to puzzle mode.
  - Click a word, type letters, Tab to the next word, double-click to
    open the word editor, pick a suggestion, edit a clue, OK.
  - Save (with comment), Save as, Rename, Close, Delete.
  - Import one sample file in each format. Export the open puzzle in
    each format (check that a download happens, not its contents).
  - Change a setting, reload, and confirm it stuck.
  - Change a puzzle's state from the dashboard. View its history.
- Write a short manual checklist (in this file, under "Manual checks")
  for things that are awkward to automate, such as the exact look of
  dialogs and the light and dark themes.

Expected size: a day. This phase pays for itself in every later phase.

### Phase 1 — Clean up in place

Small fixes that make the later moves smaller:

- Delete the seven unused functions listed above.
- Remove CSS rules that nothing uses. A first scan flagged `crosstb`,
  `crosstb-icon`, `grid-context-hint`, `settings-close-btn`,
  `settings-header-actions` and `stat-section-title`. Check each one by
  hand first: a class name built from pieces in JavaScript (as the
  `dash-card-1` to `dash-card-4` classes may be) won't show up in a plain
  text search.
- Make `apiFetch()` check the HTTP status and throw an error carrying the
  server's `{"error": ...}` message. Callers then use `try`/`catch`
  instead of checking `data.error`. Do this one caller at a time.
- Rewrite `updateMenu()` as a table, `{ id, enabledWhen: (state) =>
  ... }`, so every menu item has exactly one rule. Settle the ipuz and
  Crossword Compiler import inconsistency while doing it.

### Phase 2 — Switch to modules (mechanical)

Turn each file into a module without reorganizing anything yet:

- Change the seven `<script>` tags to a single `<script type="module"
  src="/static/js/main.js">`. Move the startup code out of `settings.js`
  into `main.js`.
- Add `export` and `import` lines to each file.
- The `onclick` attributes still need global functions. Add a temporary
  `legacy-globals.js` that copies the functions they use onto `window`.
  That file is a to-do list: Phase 3 empties it and then deletes it.
- Watch for circular imports, where two files each import from the
  other. Today, `ui.js` calls into the editor and the editor calls back
  into `ui.js`. Modules allow this as long as nothing is used while the
  files are still loading, but each case is a hint about where Phase 4
  should draw a line.

At the end of this phase the code is in the same files doing the same
things, but every dependency between files is written down.

### Phase 3 — Replace `onclick` with `data-action`

- Add `core/actions.js` with a `registerActions({ 'puzzle-save':
  doPuzzleSave, ... })` function and one click listener on `document`.
- Change the HTML a region at a time: the top menu, the dialogs, the
  dashboard, the editor action bar, the side panels, the word editor.
  Remove each function from `legacy-globals.js` once nothing uses it.
- `oninput`, `onchange` and `onkeydown` attributes get the same treatment
  (`data-input="..."` and so on).
- Delete `legacy-globals.js` when it is empty.

### Phase 4 — Split the large files

Move code into the target layout, one area per commit:

1. `puzzle-file/` first. Moving open, save, import and export out of
   `puzzle-editor.js` is the largest single cut and the easiest, because
   those functions mostly call the API and then redraw.
2. Collapse the five importers into one function plus a table:

   ```js
   const IMPORT_FORMATS = {
       acrosslite: { label: 'AcrossLite text',    accept: '.txt',  read: 'text',   endpoint: '/api/import/acrosslite' },
       puz:        { label: 'AcrossLite binary',  accept: '.puz',  read: 'base64', endpoint: '/api/import/puz' },
       ...
   };
   ```

   One hidden file input with its `accept` setting changed per format
   replaces the five hidden inputs in `index.html`. (Check the real
   endpoint names and how each format sends its file before writing the
   table.)
3. `editor/`: split `puzzle-editor.js` and `word-editor.js` along the
   lines in the target layout. Move each module's private variables in
   with it.
4. `dashboard/` and `ui/`: the chooser, the context menu and the dialogs
   each get their own file.

### Phase 5 — Promise-based dialogs

- Add `askText`, `askFields`, `confirm` and `alert` to `ui/dialogs.js`,
  each returning a promise.
- Convert callers one at a time. Have the old callback versions call the
  new ones until no callers remain, then remove them.
- `do_puzzle_new()` and Save as are the best first targets: they have
  the deepest nesting today.

### Phase 6 — State

- Move each group of scattered variables (`_ch*`, `_we*`, `_click*`,
  and so on) into the module that owns it, as one object that only that
  module changes.
- Shrink `AppState` to what is truly shared. Leftover fields, such as
  `view: 'home'` (the dashboard replaced the home screen) and the
  `'home'` alias in `showView`, go away.
- The editor's three right-hand panels (clues, stats, fill order) are
  currently tracked by three overlapping fields: `showingStats`,
  `showingFillOrder` and `sidebarTab`. Replace them with one field.

### Phase 7 — CSS

- Replace the W3.CSS classes with a small `controls.css` of our own,
  covering dropdown menus, buttons, cards, the disabled look and modal
  dialogs, and drop the link to w3schools.com. Do this region by region,
  checking the look in both themes.
- Split `style.css` along the same lines as the JavaScript.
- Consider serving Google Fonts and Material Icons from
  `frontend/static/` too, so the app works fully offline. This is
  optional.

### Phase 8 — Documentation

- Add `docs/dev/frontend.md`. It should describe the module layout, how
  `data-action` works, which module owns which state, and how to add a
  new menu item, a new side panel and a new import format.
- Update the project memory and the README where they describe the
  frontend files.

## Things to watch out for

- **Browser caching.** Modules are cached file by file, and a stale copy
  of one file next to fresh copies of the others produces confusing
  errors. During the refactoring, keep "Disable cache" on in DevTools.
  Consider having the server send `Cache-Control: no-cache` for
  `/static/js/`. That makes the browser check for a newer copy on every
  load, which costs nothing noticeable on localhost.
- **Keyboard handling is the riskiest area.** The grid's typing handler
  and the word editor's typing handler are swapped in and out by adding
  and removing listeners on the whole page. If two are ever attached at
  once, each key gets handled twice. Phase 0's typing test must cover:
  open the word editor, close it, then type in the grid.
- **Single vs. double click.** A single click on the grid waits 280 ms
  to make sure it isn't the first half of a double-click. Keep that logic
  exactly as it is, and test both cases.
- **Clue saves happen in order.** `_inlineClueSave` chains clue saves so
  they reach the server in the order they were made. Keep that guarantee
  when the code moves.
- **Module code runs later.** Module scripts run only after the whole
  page has loaded, while plain scripts run as they are reached. Code that
  quietly relied on running early will now run late. The startup code
  already waits for `DOMContentLoaded`, so little or nothing should be
  affected, but check.

## Not part of this plan

- Visual redesign or new features.
- Changes to the backend API.
- A JavaScript framework, a bundler, or TypeScript compilation.

## Automated checks

The end-to-end tests live in `crossword/tests/frontend/` and run with the
rest of the suite (`pytest crossword/tests/`). After `pip install -e .`, run
`playwright install chromium` once to download the browser they drive.
Run only the browser tests with `pytest crossword/tests/frontend/`, and add
`--headed --slowmo 300` to watch them.

## Manual checks

Things the tests don't cover, mostly how the page looks. Go through them at
the end of each phase, with "Disable cache" on in DevTools.

- **Both themes.** With `theme_color` set (say `#104080`) and with it
  blank: app bar, action bar, sidebar and buttons pick up the color, and
  text stays readable.
- **Top menus.** Hovering Puzzle, Import and Export drops each menu down
  under its button. Disabled items look greyed out and don't react to the
  mouse. The dividers in the Puzzle menu show.
- **Dialogs.** The message box, input box, chooser, state dialog, history,
  constraints and definitions popups sit centered over a dimmed page, with
  the header icon, title and × button lined up. Clicking the backdrop
  closes the constraints, definitions and history popups and the state
  dialog, but not the message box, input box or chooser.
- **Chooser cards.** Preview pictures are 150×150, cards highlight on
  hover, and the « ‹ › » buttons grey out at the ends.
- **Dashboard.** Four colored cards on top with the progress bars in "In
  progress"; tabs and the table below, scrolling inside its card.
- **Editor.** Grid centered in the left pane with the title above it and
  the key hints below. Selected word is blue, the cursor cell pink, locked
  words pale yellow. Action bar buttons grey out when disabled (Generate on
  even sizes, Close and Delete while the word editor is open, Grid Mode when
  a word is locked, with its tooltip).
- **Word editor panel.** Lock icon inside the Answer box when locked;
  suggestion bars scaled by score; the chosen suggestion highlighted blue;
  pager arrows.
- **Definitions.** The Definitions button looks up a complete word (this
  calls the configured online dictionary, so the tests skip it).
- **Message line.** Appears just under the action bar (or under the app bar
  on the dashboard), green text for notices and red for errors, and goes
  away after the configured timeout (most errors stay until closed).
- **Settings.** Tabs down the left, one panel at a time, footer buttons at
  the bottom right.
- **Offline.** Icons and fonts load (or fall back cleanly) with the network
  cable out.
