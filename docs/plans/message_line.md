# Plan: Message Line Notifications

GitHub issue: `#195` — "Use message line instead of dialog box if no user input is needed"

## Goal

Add a single-line notification area to the SPA and use it for passive status messages.
Keep modal dialogs for flows that still require user input or explicit confirmation.

Issue requirements interpreted for the current frontend:

- Add a visible message line area in the UI
- Style it with dedicated CSS for this feature
- Use it when the app is only informing the user of something
- Keep dialogs for overwrite / delete / close-with-unsaved-changes and text entry
- First examples to migrate: "Grid saved" and "Puzzle saved"

---

## Current State

The SPA currently has three dialog primitives in [frontend/index.html](/home/saspeh/dev/python/crossword/frontend/index.html):

- `#mb` message box
- `#ib` input box
- `#ch` chooser

In [app.js](/home/saspeh/dev/python/crossword/frontend/static/js/app.js), `messageBox(...)` is used for two different jobs:

- true dialogs that need a decision, such as overwrite and delete confirmation
- passive notifications, such as:
  - "Puzzle saved"
  - "Grid saved"
  - "No saved grids found"
  - "No saved puzzles found"
  - publish/export failures

That mix is exactly what issue `#195` is trying to separate.

---

## UI Design

### New element in `index.html`

Add a permanent notification strip just below the menu bar and above the main content row.

Suggested markup:

```html
<div id="ml" class="message-line" style="display:none">
  <span id="ml-text"></span>
  <button id="ml-close" class="message-line-close" onclick="clearMessageLine()">&times;</button>
</div>
```

Design notes:

- Single line only, per the issue
- Hidden when empty
- Text-only content is sufficient; no buttons or links needed in v1
- Close button is useful, but auto-dismiss should also be supported

### CSS in `frontend/static/css/style.css`

Add styles for:

- `.message-line`
- `.message-line-error`
- `.message-line-notice`
- `.message-line-close`

Recommended behavior:

- full-width strip under the menu
- compact padding and slightly smaller text than `h3`
- `white-space: nowrap; overflow: hidden; text-overflow: ellipsis;`
- green for ordinary notifications
- red for error conditions

The old Flask templates rendered flash messages in a separate panel in
[main.html](/home/saspeh/dev/python/crossword/reference/templates/main.html); this SPA version can simplify that to just two states.

---

## Frontend API

### New helper functions in `app.js`

Add a lightweight notification helper alongside the existing modal helpers:

```js
let _messageLineTimer = null;

function showMessageLine(text, level = 'notice', timeoutMs = 3000) { ... }
function clearMessageLine() { ... }
```

Behavior:

- write escaped text into `#ml-text`
- switch CSS class based on `level`
- show the strip
- reset any previous timeout before starting a new one
- if `timeoutMs` is non-zero, auto-hide after the timeout
- `clearMessageLine()` hides the strip and clears the timer

### Keep `messageBox(...)` focused on decision-making

Do not delete `messageBox(...)`. Narrow its role to:

- confirm destructive actions
- confirm overwrites
- warn about unsaved changes
- report situations where the user must acknowledge before continuing

This avoids breaking existing flows while making intent clearer at each call site.

---

## First Migration Pass

### Definite conversions for issue `#195`

Replace these `messageBox(...)` calls with `showMessageLine(...)`:

- [frontend/static/js/app.js:1401](/home/saspeh/dev/python/crossword/frontend/static/js/app.js#L1401)
  `Puzzle saved`
- [frontend/static/js/app.js:1711](/home/saspeh/dev/python/crossword/frontend/static/js/app.js#L1711)
  `Grid saved`

Suggested level:

- notice

### Good candidates in the same pass

These also do not require user input:

- [frontend/static/js/app.js:1330](/home/saspeh/dev/python/crossword/frontend/static/js/app.js#L1330)
  `Open puzzle` / no saved puzzles found
- [frontend/static/js/app.js:1361](/home/saspeh/dev/python/crossword/frontend/static/js/app.js#L1361)
  `New puzzle` / no saved grids found
- [frontend/static/js/app.js:1668](/home/saspeh/dev/python/crossword/frontend/static/js/app.js#L1668)
  `New grid from puzzle` / no saved puzzles found
- [frontend/static/js/app.js:1693](/home/saspeh/dev/python/crossword/frontend/static/js/app.js#L1693)
  `Open grid` / no saved grids found
- [frontend/static/js/app.js:1810](/home/saspeh/dev/python/crossword/frontend/static/js/app.js#L1810)
  publish error response
- [frontend/static/js/app.js:1823](/home/saspeh/dev/python/crossword/frontend/static/js/app.js#L1823)
  export request failed
- [frontend/static/js/app.js:1836](/home/saspeh/dev/python/crossword/frontend/static/js/app.js#L1836)
  `Publish` / no saved puzzles found

Suggested levels:

- notice for "saved" and "nothing found" cases
- error for publish/export failures

### Leave as dialogs

Keep `messageBox(...)` for:

- overwrite confirmation in `confirmOverwriteIfExists(...)`
- invalid reserved-name warnings if we want explicit acknowledgement
- close-with-unsaved-changes confirmation
- delete confirmation

Also keep `inputBox(...)` and chooser dialogs unchanged.

---

## Save Flow Notes

Issue `#195` explicitly mentions the standard Save actions. That means:

- `do_puzzle_save()` should end with `showMessageLine(...)`
- `do_grid_save()` should end with `showMessageLine(...)`

For consistency, the same helper should also be used after successful Save As once the new name has been committed:

- `_savePuzzleAsName(newName)`
- `_saveGridAsName(newName)`

That part is not called out directly in the issue body, but it follows the same rule:
after the user has already provided input, the success result is just a notification.

---

## Documentation Updates

Update [docs/design/frontend.md](/home/saspeh/dev/python/crossword/docs/design/frontend.md):

- add `#ml` to the permanent UI elements
- document `showMessageLine()` / `clearMessageLine()`
- clarify that modal dialogs are now reserved for input and confirmation

---

## Testing Checklist

Manual checks:

1. Save an existing grid: message line appears, then auto-hides
2. Save an existing puzzle: message line appears, then auto-hides
3. Save grid as / puzzle as: input dialog still appears; success uses message line
4. Open grid with no saved grids: no modal opens; message line appears
5. Try delete / overwrite / close dirty item: modal confirmation still appears
6. Trigger publish failure: error variant of message line is visible
7. Trigger two notifications quickly: newest one replaces the old one cleanly
8. Resize narrow window: line stays single-row and does not break layout

---

## Implementation Order

1. Add `#ml` markup to `frontend/index.html`
2. Add message-line CSS to `frontend/static/css/style.css`
3. Add `showMessageLine()` / `clearMessageLine()` to `frontend/static/js/app.js`
4. Migrate `do_puzzle_save()` and `do_grid_save()` from modal to message line
5. Migrate Save As success paths
6. Convert other passive `messageBox(...)` call sites that do not require input
7. Update `docs/design/frontend.md`
8. Run a quick manual UI pass for save, empty-list, and confirm flows

---

## Risks / Decisions

- If the line auto-dismisses too quickly, save confirmations may feel easy to miss
- If it stays forever, the UI can look stale after the user moves on
- Some current informational dialogs are borderline cases; for example, "no saved grids found" is passive, but it does interrupt a user action. The issue wording suggests these should still move to the message line
- Using plain text in the message line is safer than allowing arbitrary HTML, even though `messageBox(...)` currently accepts HTML strings
