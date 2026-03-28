# Plan: Session Puzzle Activity Log

GitHub issue: `#197` — "Show running log of user activity"

## Goal

Add a user-facing activity log to the SPA home view so the user can quickly remember what puzzle work has happened during the current browser session.

After implementation:

- the home view shows a running log of recent puzzle activity
- the log records actions that correspond to items under the **Puzzle** menu
- entries persist only for the lifetime of the currently loaded single-page app
- the log is cleared automatically on full page reload or browser/tab close
- the log is informational only, not a debug console or server log

## Product Interpretation

The purpose of the feature is to remind the user what he or she has been working on in the current session.

That means the log should emphasize user-recognizable puzzle actions such as:

- creating a new puzzle
- opening an existing puzzle
- saving a puzzle
- saving a puzzle under a new name
- deleting a puzzle
- closing a dirty puzzle without saving

Although some of these actions happen while editing, the log itself should be visible in the **home** state so it acts as a recent-activity summary whenever the user returns there.

## Scope

### In scope

- frontend-only session state for activity entries
- rendering the log in the home view
- appending entries for Puzzle-menu actions
- clear, human-readable entry text using puzzle names where available
- preserving entries across view changes within the SPA

### Out of scope

- persistence to local storage, cookies, or the backend
- logging non-Puzzle-menu actions such as word edits, grid edits, publish actions, or stats views
- server-side audit/history features
- multi-user or cross-browser synchronization

## Current State

The current SPA already has:

- a `home` view rendered by `renderHome()`
- an in-memory global `AppState` object in `frontend/static/js/app.js`
- a single-line message area `#ml` used for passive notifications

There is not yet any persistent per-session activity history shown on the home screen.

## Proposed UX

### Placement

Show the activity log inside the home view, beneath the existing introductory text or in place of it if the combined layout reads better.

Suggested home-view structure:

- short reminder text about using the Puzzle menu
- newest entries first so the most recent work is immediately visible

### Empty state

Before any puzzle activity occurs in the session, show a short empty-state message such as:

- `No puzzle activity yet in this session.`

### Entry wording

Entries should be concise and action-focused. Suggested examples:

- `Created puzzle "Sunday 15".`
- `Worked on puzzle "Themeless-03".`
- `Saved puzzle "Themeless-03".`
- `Saved puzzle as "Themeless-03-rev2".`
- `Closed puzzle "Themeless-03" without saving changes.`
- `Deleted puzzle "Old Draft".`

### Timestamps

Include a lightweight client-side timestamp for each entry so the log better supports the memory-aid goal.

Suggested format:

- local browser time only
- short display such as `2:41 PM` or `14:41`

Exact formatting can be chosen during implementation, but it should remain simple and readable.

## Data Model

Keep the log entirely in browser memory.

Suggested `AppState` addition:

```js
activityLog: [], // [{ time, text, kind }]
```

Notes:

- `time` can be a `Date`-derived display string or raw timestamp
- `text` is the final user-facing message
- `kind` can remain optional unless we later want visual distinctions

No backend API changes should be required.

## Logging Rules

Append one entry when these user actions complete successfully:

1. **New puzzle**
   - after puzzle creation succeeds
2. **Open puzzle**
   - after the requested puzzle is opened successfully
3. **Save puzzle**
   - after save succeeds
4. **Save puzzle as**
   - after the copy/save-as succeeds
5. **Close puzzle without saving**
   - after the user confirms closing a dirty puzzle and the close completes
6. **Delete puzzle**
   - after deletion succeeds

### Important distinction

Do not log actions when the user merely opens a dialog or chooser.

Examples:

- opening the **Open puzzle...** chooser is not itself a log entry
- opening the **Save puzzle as...** input box is not itself a log entry
- only the successfully completed resulting action should be logged

## Interaction With Existing Notifications

The existing message line should remain available for short live feedback during editing.

The new activity log serves a different purpose:

- message line: immediate transient feedback
- home-view log: session memory of completed puzzle actions

The two features may share wording helpers, but they should not be conflated conceptually.

## Rendering Strategy

### Home view

Update `renderHome()` in `frontend/static/js/app.js` to render:

- the existing instructional text
- a log panel populated from `AppState.activityLog`

### Visual style

Use the existing W3/CSS style language already present in the project.

Suggested presentation:

- card or bordered panel
- compact rows
- timestamp in muted text
- activity text as the main content
- newest-first ordering
- capped height with scrolling only if needed

## Implementation Phases

### Phase 1: Add session log state

- extend `AppState` with an in-memory activity collection
- add helper functions such as:
  - `appendActivityLog(text)`
  - `renderActivityLog()`

### Phase 2: Render the log on the home view

- update `renderHome()` to include the activity log directly under the introductory text
- add any required CSS for row spacing, timestamp text, and empty-state styling

### Phase 3: Hook Puzzle-menu success paths

Add log entries to the successful completion paths for:

- `do_puzzle_new()`
- `_openPuzzleInEditor()` or its successful caller
- `do_puzzle_save()`
- `_savePuzzleAsName(newName)`
- `_doPuzzleCloseConfirmed()`
- `do_puzzle_delete()`

### Phase 4: Dirty-close wording

- when closing with unsaved changes after user confirmation, log the more specific message:
  - `Closed puzzle "Name" without saving changes.`

### Phase 5: Documentation update

Update `docs/design/frontend.md` to document:

- the new `AppState` session activity log
- home-view activity log rendering
- the distinction between transient notifications and the session activity log

## Testing Checklist

Manual checks:

1. Load the SPA and confirm the home view shows an empty-state activity panel.
2. Create a new puzzle and confirm a `Created puzzle ...` entry appears.
3. Return home and confirm the entry is still visible.
4. Open an existing puzzle and confirm a `Worked on puzzle ...` entry appears.
5. Save a puzzle and confirm a `Saved puzzle ...` entry appears.
6. Use Save As and confirm a `Saved puzzle as ...` entry appears with the new name.
7. Close a clean puzzle and confirm no new close entry is added.
8. Close a dirty puzzle without saving and confirm the wording mentions unsaved changes.
9. Delete a puzzle and confirm a `Deleted puzzle ...` entry appears.
10. Refresh the page and confirm the session log is reset.
11. Close the browser tab/window and reopen the app; confirm the previous session log is gone.

## Risks And Decisions

- If both the message line and the home-view log use identical wording, that is acceptable, but the home-view log should remain readable without depending on transient notifications.
- Logging too early could create misleading entries for actions the user cancels; therefore entries should be appended only after success.
- If the home view becomes visually crowded, the activity panel should take priority over repeating long instructional text.

## Progress Tracking

- [x] Requirements clarified with the user
- [x] Planning document created
- [ ] Implementation started
- [ ] Frontend documentation updated
- [ ] Manual browser verification completed
