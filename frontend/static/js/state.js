// Crossword Puzzle Editor — application state and constants

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const BOXSIZE = 32;
let MESSAGE_LINE_TIMEOUT_MS = 3000; // default; may be overridden by /api/config

// ---------------------------------------------------------------------------
// Application state
// ---------------------------------------------------------------------------

const AppState = {
    view: 'home',            // 'home' | 'editor'
    puzzleName: null,        // user-facing name of the open puzzle; null until first Save
    puzzleOriginalName: null,// backend name of the original (may be '__new__…' for unnamed)
    puzzleWorkingName: null, // working copy name (e.g. '__wc__a1b2c3d4')
    puzzleData: null,        // response from GET /api/puzzles/{workingName}
    puzzleSavedHash: null,   // checksum of puzzle at last open/save
    selectedWord: null,      // null | {seq, direction, cells, originalText, draftText, originalClue, draftClue, cursorIdx, editorMode}
    showingStats: false,     // true = puzzle editor RHS shows stats panel
    showingFillOrder: false, // true = puzzle editor RHS shows fill-order panel
    sidebarTab: 'clues',     // active sidebar tab: 'clues'|'word'|'stats'|'fill-order'|'grid'
    _statsData: null,         // cached puzzle stats response
    _fillOrderCache: null,    // Map<cellHash, fill-order response> | null when no puzzle open
    fillOrderLoading: false,  // true while fill-order suggestions are loading
    gridStructureChanged: false, // true after Grid-mode edits until user returns to Puzzle mode
    puzzleThemeSpec: null,       // int[] | null — theme word lengths entered at puzzle creation
};
