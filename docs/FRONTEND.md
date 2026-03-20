# Frontend Architecture

The frontend is a **plain JavaScript SPA** (no frameworks) with ~1,540 LOC organized into modular components. It follows a **Vue-style observable state pattern** combined with specialized editors for grids and puzzles.

## File Organization

```
frontend/
├── index.html              # Single HTML entry point
└── static/
    ├── css/
    │   └── style.css       # Global styles (2-column layouts, dialogs, buttons)
    └── js/
        ├── app.js          # Main entry point, navigation, event wiring
        ├── state.js        # Observable state management
        ├── api.js          # Promise-based HTTP API client
        ├── grid-editor.js   # SVG grid rendering & cell toggling
        ├── puzzle-editor.js # SVG puzzle rendering & word list
        ├── word-editor.js  # Clue editor & live word suggestions
        └── dialogs.js      # Modal dialogs (new grid, new puzzle, errors)
```

---

## Core Concepts

### 1. State Management (`state.js`)

Simple observable pattern (similar to Vue Reactivity API):

```javascript
State.set({ mode: 'puzzle', currentPuzzle: 'Sunday' })  // Update state
State.get('mode')                                         // Get single value
State.get()                                               // Get all state
State.subscribe(newState => console.log(newState))       // Subscribe to changes
```

**Global state object:**
```javascript
{
  mode: 'list' | 'grid' | 'puzzle',
  currentGrid: null | string,
  currentPuzzle: null | string,
  grids: [],
  puzzles: []
}
```

**Subscribers** are functions called whenever state changes. Used by `app.js` for logging (console.log on every state update).

---

### 2. API Client (`api.js`)

Promise-based HTTP client wrapping all backend endpoints. All methods return `Promise<response>` and throw on HTTP or JSON errors.

#### Grid Operations

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `listGrids()` | GET `/api/grids` | List all grids for user |
| `createGrid(name, size)` | POST `/api/grids` | Create new grid |
| `loadGrid(name)` | GET `/api/grids/<name>` | Load grid by name |
| `deleteGrid(name)` | DELETE `/api/grids/<name>` | Delete grid |
| `toggleBlackCell(name, r, c)` | PUT `/api/grids/<name>/cells/<r>/<c>` | Toggle black cell at row, col |
| `rotateGrid(name)` | POST `/api/grids/<name>/rotate` | Rotate 90° counterclockwise |
| `undoGrid(name)` | POST `/api/grids/<name>/undo` | Undo last grid operation |
| `redoGrid(name)` | POST `/api/grids/<name>/redo` | Redo last undone grid operation |

#### Puzzle Operations

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `listPuzzles()` | GET `/api/puzzles` | List all puzzles for user |
| `createPuzzle(name, gridName)` | POST `/api/puzzles` | Create puzzle from grid |
| `loadPuzzle(name)` | GET `/api/puzzles/<name>` | Load puzzle by name |
| `deletePuzzle(name)` | DELETE `/api/puzzles/<name>` | Delete puzzle |
| `setCellLetter(name, r, c, letter)` | PUT `/api/puzzles/<name>/cells/<r>/<c>` | Set letter in cell |
| `getWordAt(name, seq, direction)` | GET `/api/puzzles/<name>/words/<seq>/<direction>` | Get word metadata |
| `setWordClue(name, seq, dir, clue)` | PUT `/api/puzzles/<name>/words/<seq>/<direction>` | Save clue for word |
| `undoPuzzle(name)` | POST `/api/puzzles/<name>/undo` | Undo last puzzle operation |
| `redoPuzzle(name)` | POST `/api/puzzles/<name>/redo` | Redo last undone puzzle operation |
| `replacePuzzleGrid(name, newGridName)` | PUT `/api/puzzles/<name>/grid` | Swap grid for puzzle |

#### Word Operations

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `getSuggestions(pattern)` | GET `/api/words/suggestions?pattern=<pattern>` | Get words matching pattern (e.g., `?HALE`) |
| `getAllWords()` | GET `/api/words/all` | Get all words in dictionary |
| `validateWord(word)` | GET `/api/words/validate?word=<word>` | Check if word is valid |

#### Export Operations

| Method | Endpoint | Return |
|--------|----------|--------|
| `exportGridPDF(name)` | GET `/api/export/grids/<name>/pdf` | Blob |
| `exportGridPNG(name)` | GET `/api/export/grids/<name>/png` | Blob |
| `exportPuzzlePUZ(name)` | GET `/api/export/puzzles/<name>/puz` | Blob |
| `exportPuzzleXML(name)` | GET `/api/export/puzzles/<name>/xml` | String |

---

## UI Architecture

### Three Main Views

Views are toggled by showing/hiding `<section>` elements via `display: none|block`. State drives which view is active.

#### **List View** (default)
```html
<section id="list-section">
  <div id="grid-list">           <!-- Left: grids list -->
  <div id="puzzle-list">         <!-- Right: puzzles list -->
</section>
```

- **Display:** Two-column layout (CSS Grid)
- **Behavior:**
  - On load, fetch grids and puzzles via API
  - Render as clickable `<li>` elements
  - Click grid → `loadAndDisplayGrid(name)`
  - Click puzzle → `loadAndDisplayPuzzle(name)`
  - "New Grid" / "New Puzzle" buttons open dialogs

#### **Grid Editor View**
```html
<section id="grid-section">
  <div id="grid-editor"></div>        <!-- SVG canvas -->
  <div id="grid-toolbar">
    <button id="btn-rotate-grid">Rotate</button>
    <button id="btn-undo-grid">Undo</button>
    <button id="btn-redo-grid">Redo</button>
    <button id="btn-delete-grid">Delete Grid</button>
  </div>
</section>
```

**GridEditor module** (`grid-editor.js`):
- Renders grid as **SVG** with 30×30px cells
- **Black cells:** solid black (`#000`), unclickable
- **White cells:** white, clickable with pointer cursor
- Click white cell → `toggleBlackCell()` API call → re-render

**Toolbar actions:**
- **Rotate:** rotates grid 90° CCW
- **Undo/Redo:** navigation through operation history
- **Delete:** with browser confirmation (cannot be undone)

#### **Puzzle Editor View**
```html
<section id="puzzle-section">
  <div class="puzzle-layout">           <!-- CSS Grid: 1fr 200px -->
    <div id="puzzle-editor"></div>       <!-- Left: SVG grid -->
    <div id="word-editor">               <!-- Right: sidebar -->
      <div id="word-clue-editor">...</div>      <!-- Clue input -->
      <div id="word-suggestions">...</div>      <!-- Pattern matcher -->
    </div>
  </div>
  <div id="puzzle-toolbar">
    <button id="btn-undo-puzzle">Undo</button>
    <button id="btn-redo-puzzle">Redo</button>
    <button id="btn-save-puzzle">Save Puzzle</button>
    <button id="btn-delete-puzzle">Delete Puzzle</button>
    <button id="btn-export-xml">Export XML</button>
  </div>
</section>
```

**PuzzleEditor module** (`puzzle-editor.js`):
- Renders puzzle as **SVG** (similar to grid)
- Each cell displays:
  - **Number** (if word starts here): 8pt bold text in top-left
  - **Letter** (if cell has answer): 20pt bold centered
- Cells clickable → `selectCell()` (logs for now)
- Word list sidebar grouped by Across/Down
- Click word item → shows clue editor + pattern suggestions

**WordEditor module** (`word-editor.js`):
- **Clue editor:** Text input for word clue, "Save Clue" button
- **Pattern input:** Live pattern matching (e.g., `S?MMER`)
  - On input → `getSuggestions(pattern)` API call
  - Shows up to 20 matching words from dictionary
  - Hover effect on suggestions (background color change)
  - Click suggestion → focus clue input (for manual entry)

**Toolbar actions:**
- **Undo/Redo:** puzzle operation history
- **Save Puzzle:** confirmation message (changes are API-persisted)
- **Delete Puzzle:** with confirmation
- **Export XML:** downloads `.xml` file via blob + `createObjectURL`

---

## View Transitions

All three views are mutually exclusive. State changes drive visibility:

```javascript
// Go from list → grid
State.set({ mode: 'grid', currentGrid: 'Sunday Grid' })
document.getElementById('list-section').style.display = 'none'
document.getElementById('grid-section').style.display = 'block'
document.getElementById('puzzle-section').style.display = 'none'

// Then render the grid
GridEditor.render(gridData)
```

**Return to list:** `returnToList()` function resets state and shows list section.

---

## Event Flow Example: Editing a Puzzle

```
1. User clicks puzzle name in list view
   └─> onClick handler calls loadAndDisplayPuzzle('Sunday Puzzle')

2. In loadAndDisplayPuzzle()
   └─> CrosswordAPI.loadPuzzle('Sunday Puzzle')
       └─> HTTP GET /api/puzzles/Sunday%20Puzzle
       └─> Returns: { grid: {...}, puzzle: {...} }

3. Update state & show puzzle section
   └─> State.set({ currentPuzzle: 'Sunday Puzzle', mode: 'puzzle' })
   └─> Show puzzle-section, hide others

4. PuzzleEditor.render(puzzleData)
   └─> Create SVG grid with cells, numbers, letters
   └─> Render word list sidebar (across/down)
   └─> Wire up click handlers for word items

5. User clicks word in list (e.g., "1 Across: 7 letters")
   └─> WordEditor.render(wordData)
   └─> Show clue editor with current clue
   └─> Show pattern input for suggestions

6. User types pattern "S?MME?"
   └─> WordEditor.updateSuggestions('S?MME?')
       └─> CrosswordAPI.getSuggestions('S?MME?')
       └─> HTTP GET /api/words/suggestions?pattern=S%3FMME%3F
       └─> Returns: { suggestions: ['SUMMER', 'SLIMMER', ...] }
   └─> Render suggestion divs with hover effects

7. User types clue and clicks "Save Clue"
   └─> WordEditor.saveClue(puzzleName, seq, direction)
   └─> CrosswordAPI.setWordClue('Sunday Puzzle', 1, 'across', 'Warm season')
       └─> HTTP PUT /api/puzzles/Sunday%20Puzzle/words/1/across
           with body: { clue: 'Warm season' }
   └─> Update local wordData.clue and show "Clue saved" status
```

---

## Dialogs

**Three dialogs** are pre-rendered as hidden `<div class="dialog">`:

### New Grid Dialog
```javascript
Dialogs.showNewGrid()
// → Clears form, focuses name input, shows dialog
// → User enters: name, size (1-25)
// → Button: Create → Dialogs.confirmNewGrid()
//   └─> CrosswordAPI.createGrid(name, size)
//   └─> loadGridsAndPuzzles() (refresh lists)
//   └─> loadAndDisplayGrid(name) (open new grid)
// → Button: Cancel → hide dialog
```

### New Puzzle Dialog
```javascript
Dialogs.showNewPuzzle()
// → Fetch grid list via CrosswordAPI.listGrids()
// → Populate <select> with available grids
// → User enters: name, selects grid
// → Button: Create → Dialogs.confirmNewPuzzle()
//   └─> CrosswordAPI.createPuzzle(name, gridName)
//   └─> loadGridsAndPuzzles()
//   └─> loadAndDisplayPuzzle(name)
// → Button: Cancel → hide dialog
```

### Error Dialog
```javascript
showError(message)
// → Set error text, show dialog
// → Button: OK → hide dialog
```

**Styling** (`style.css`):
- Fixed positioning, overlay background (rgba(0,0,0,0.5))
- Centered content box with shadow
- Backdrop click does NOT close (not wired)

---

## Styling (`style.css`)

- **Font:** System fonts (`-apple-system`, `BlinkMacSystemFont`, etc.)
- **Colors:** Blue theme (#3498db primary, #2c3e50 dark header)
- **Responsive:**
  - List view: 2-column grid
  - Puzzle view: 1fr 200px grid (editor + sidebar)
- **Interactive:**
  - Buttons with hover/active states
  - SVG cells with cursor pointer on hover
  - List items with left border, hover background
  - Suggestions with background color transitions
- **Layout:** Flexbox and CSS Grid; max-width 1400px container

---

## Data Flow Architecture

```
┌─────────────────────────────────────┐
│         HTML (index.html)           │
│  - Markup for sections & dialogs    │
│  - Script imports @ bottom          │
└──────────────────┬──────────────────┘
                   │
        ┌──────────┴──────────────────────┐
        │   JavaScript Modules (loaded in order):
        │   1. api.js       — HTTP client
        │   2. state.js     — State management
        │   3. grid-editor.js, puzzle-editor.js, word-editor.js
        │   4. dialogs.js   — Modal utilities
        │   5. app.js       — Main: loads data, wires events
        └──────────────────────────────────┘
        │
        │ User Events (clicks, input)
        ↓
┌─────────────────────────────────────┐
│  app.js Event Handlers              │
│  - Grid/puzzle clicks               │
│  - Dialog confirmations             │
│  - Toolbar actions (undo, rotate)   │
└────────────┬────────────────────────┘
             │
        ┌────┴─────────────────────────┐
        ↓                              ↓
   CrosswordAPI.*(…)        State.set({...})
   (HTTP requests)          (update state)
        │                              │
        ↓                              ↓
   /api/* endpoints          Subscribers notified
   (backend use cases)       (console.log in app.js)
        │
        ↓
   HTTP Response JSON
        │
        ↓
   GridEditor/PuzzleEditor.render(data)
   (SVG renders to DOM)
```

**Key principle:** Frontend is **stateless**. All mutations go through the API. Undo/redo are server-side (domain layer history). UI just reflects server state.

---

## Entry Point (`app.js`)

1. **DOMContentLoaded event:**
   - `loadGridsAndPuzzles()` → fetch grids & puzzles
   - `setupEventListeners()` → wire all buttons
   - `State.subscribe()` → log state changes

2. **Global helper functions:**
   - `loadAndDisplayGrid(name)` — show grid section, render
   - `loadAndDisplayPuzzle(name)` — show puzzle section, render
   - `returnToList()` — show list section, reset state
   - `showStatus(message)` — update header status text
   - `showError(message)` — show error dialog
   - `renderGridsList(grids)` — populate list
   - `renderPuzzlesList(puzzles)` — populate list

3. **Event listeners wired in `setupEventListeners()`:**
   - New Grid button → `Dialogs.showNewGrid()`
   - New Puzzle button → `Dialogs.showNewPuzzle()`
   - Grid toolbar buttons → rotate, undo, redo, delete
   - Puzzle toolbar buttons → undo, redo, save, delete, export
   - Error dialog close button

---

## Design Decisions

| Aspect | Choice | Rationale |
|--------|--------|-----------|
| **Framework** | None (vanilla JS) | Hexagonal architecture doesn't need framework overhead; keeps SPA lightweight |
| **State Management** | Observable pattern | Vue-like simplicity without Vue dependency; reactive updates |
| **Rendering** | SVG | Vector graphics scale perfectly; click detection via `data-*` attributes |
| **API** | Static class methods | Promise-based; clean error handling; no instance state |
| **CSS** | Grid + Flexbox | Modern layout primitives; no CSS framework bloat |
| **Modularization** | Separate .js files | Each module handles one concern (grid, puzzle, words, dialogs) |
| **State Location** | Global State object | Single source of truth; subscribers for reactive UI (though app.js only logs) |

---

## Development Notes

- **No build step:** Direct browser ES6 module imports via `<script>` tags
- **No transpilation:** Modern browser targets (ES2015+)
- **CORS:** All `/api/*` requests are same-origin (served by same HTTP server)
- **Browser APIs used:** Fetch, DOM manipulation, SVG, Blob, URL.createObjectURL
- **Error handling:** Try-catch in async handlers; errors show via `showError()` dialog

---

## Future Extensibility

- Add grid rotation preview before confirm
- Keyboard navigation (arrow keys to move between cells)
- Word highlighting for selected word
- Clue printing / PDF generation
- Collaborative editing (WebSocket sync)
