// Crossword Puzzle Editor — application state shared across modules

// Which view is showing and which puzzle is open. Everything else the app
// knows belongs to the module that uses it (see docs/dev/frontend.md).
export const AppState = {
    view: 'dashboard',       // 'dashboard' | 'editor'
    puzzleName: null,        // user-facing name of the open puzzle; null until first Save
    puzzleOriginalName: null,// backend name of the original (may be '__new__…' for unnamed)
    puzzleWorkingName: null, // working copy name (e.g. '__wc__<name>__a1b2c3d4')
    puzzleData: null,        // response from GET /api/puzzles/{workingName}
    puzzleSavedHash: null,   // checksum of puzzle at last open/save
    puzzleState: null,       // lifecycle state ('draft', 'submitted', …) for the app bar
    puzzleThemeSpec: null,   // int[] | null — theme word lengths entered at puzzle creation
};
