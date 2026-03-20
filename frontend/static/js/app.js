// Crossword Puzzle Editor — main application script

// ---------------------------------------------------------------------------
// Application state
// ---------------------------------------------------------------------------

const AppState = {
    view: 'home',       // 'home' | 'grid-editor' | 'puzzle-editor'
    gridName: null,     // name of the currently-open grid, or null
    puzzleName: null,   // name of the currently-open puzzle, or null
};

// ---------------------------------------------------------------------------
// Utility helpers
// ---------------------------------------------------------------------------

function showElement(id) {
    document.getElementById(id).style.display = 'block';
}

function hideElement(id) {
    document.getElementById(id).style.display = 'none';
}

// ---------------------------------------------------------------------------
// Modal dialogs
// ---------------------------------------------------------------------------

/**
 * Show a simple confirmation dialog.
 * @param {string} title   - Dialog heading
 * @param {string} prompt  - HTML body text
 * @param {string} ok      - URL or "javascript:..." to invoke on OK
 * @param {Function|null} okCallback - optional JS callback instead of href
 */
function messageBox(title, prompt, ok, okCallback) {
    document.getElementById('mb-title').innerHTML = title;
    document.getElementById('mb-prompt').innerHTML = prompt;
    const mbOk = document.getElementById('mb-ok');
    if (okCallback) {
        mbOk.removeAttribute('href');
        mbOk.onclick = () => { hideElement('mb'); okCallback(); };
    } else {
        mbOk.onclick = null;
        mbOk.setAttribute('href', ok);
    }
    showElement('mb');
}

/**
 * Show a text-input dialog.
 * @param {string}   title       - Dialog heading
 * @param {string}   label       - HTML label for the input field
 * @param {string}   value       - Pre-filled input value
 * @param {Function} onSubmit    - Callback receiving the entered string
 */
function inputBox(title, label, value, onSubmit) {
    document.getElementById('ib-title').innerHTML = title;
    document.getElementById('ib-label').innerHTML = label;
    document.getElementById('ib-input').value = value;

    const form = document.getElementById('ib-form');
    form.onsubmit = (e) => {
        e.preventDefault();
        const entered = document.getElementById('ib-input').value;
        hideElement('ib');
        onSubmit(entered);
    };

    showElement('ib');
    document.getElementById('ib-input').focus();
}

// ---------------------------------------------------------------------------
// Menu enable / disable
// ---------------------------------------------------------------------------

const MENU_ITEMS = [
    'menu-grid-new',
    'menu-grid-new-from-puzzle',
    'menu-grid-open',
    'menu-grid-save',
    'menu-grid-save-as',
    'menu-grid-close',
    'menu-grid-delete',
    'menu-puzzle-new',
    'menu-puzzle-open',
    'menu-puzzle-save',
    'menu-puzzle-save-as',
    'menu-puzzle-close',
    'menu-puzzle-delete',
    'menu-publish-acrosslite',
    'menu-publish-cwcompiler',
    'menu-publish-nytimes',
];

function menuEnable(id)  { document.getElementById(id).classList.remove('w3-disabled'); }
function menuDisable(id) { document.getElementById(id).classList.add('w3-disabled'); }

/**
 * Update all menu items based on current AppState.view.
 * Three mutually exclusive states: 'home', 'grid-editor', 'puzzle-editor'.
 * Mirrors exactly the enabled/disabled state seen in the reference HTML pages.
 */
function updateMenu() {
    const home   = AppState.view === 'home';
    const grid   = AppState.view === 'grid-editor';
    const puzzle = AppState.view === 'puzzle-editor';

    // Grid menu
    home  ? menuEnable('menu-grid-new')             : menuDisable('menu-grid-new');
    home  ? menuEnable('menu-grid-new-from-puzzle') : menuDisable('menu-grid-new-from-puzzle');
    home  ? menuEnable('menu-grid-open')            : menuDisable('menu-grid-open');
    grid  ? menuEnable('menu-grid-save')            : menuDisable('menu-grid-save');
    grid  ? menuEnable('menu-grid-save-as')         : menuDisable('menu-grid-save-as');
    grid  ? menuEnable('menu-grid-close')           : menuDisable('menu-grid-close');
    menuDisable('menu-grid-delete'); // skipped for now

    // Puzzle menu
    home   ? menuEnable('menu-puzzle-new')          : menuDisable('menu-puzzle-new');
    home   ? menuEnable('menu-puzzle-open')         : menuDisable('menu-puzzle-open');
    puzzle ? menuEnable('menu-puzzle-save')         : menuDisable('menu-puzzle-save');
    puzzle ? menuEnable('menu-puzzle-save-as')      : menuDisable('menu-puzzle-save-as');
    puzzle ? menuEnable('menu-puzzle-close')        : menuDisable('menu-puzzle-close');
    puzzle ? menuEnable('menu-puzzle-delete')       : menuDisable('menu-puzzle-delete');

    // Publish menu — always enabled
    menuEnable('menu-publish-acrosslite');
    menuEnable('menu-publish-cwcompiler');
    menuEnable('menu-publish-nytimes');
}

// ---------------------------------------------------------------------------
// View rendering — stubs; each view will be filled in future phases
// ---------------------------------------------------------------------------

function showView(view) {
    AppState.view = view;
    updateMenu();
    document.getElementById('lhs').innerHTML = '';
    document.getElementById('rhs').innerHTML = '';
    // Delegate to per-view render functions (defined in later phases)
    switch (view) {
        case 'home':          renderHome();         break;
        case 'grid-editor':   renderGridEditor();   break;
        case 'puzzle-editor': renderPuzzleEditor(); break;
        default:
            document.getElementById('lhs').innerHTML =
                `<div class="w3-container"><p>Unknown view: ${view}</p></div>`;
    }
}

function renderHome() {
    document.getElementById('lhs').innerHTML =
        '<div class="w3-container"><p>Use the Grid or Puzzle menu to get started.</p></div>';
}

function renderGridEditor()   { /* Phase 2 */ }
function renderPuzzleEditor() { /* Phase 4 */ }

// ---------------------------------------------------------------------------
// Menu action stubs — Grid
// ---------------------------------------------------------------------------

function do_grid_new() {
    inputBox(
        'New grid',
        '<b>Grid size:</b> <em>(a single odd positive integer)</em>',
        '',
        (value) => {
            let n = Number(value);
            if (!value || isNaN(n)) { alert(value + ' is not a number'); return; }
            if (n % 2 === 0)        { alert(n + ' is not an odd number'); return; }
            if (n < 1)              { alert(n + ' is not a positive number'); return; }
            // TODO Phase 2: call API then open grid editor
            alert(`Create ${n}×${n} grid — coming in Phase 2`);
        }
    );
}

function do_grid_new_from_puzzle() {
    // TODO Phase 2: show puzzle chooser then create grid
    alert('New grid from puzzle — coming in Phase 2');
}

function do_grid_open() {
    // TODO Phase 2: show grid chooser
    alert('Open grid — coming in Phase 2');
}

function do_grid_save() {
    if (!AppState.gridName) {
        do_grid_save_as();
        return;
    }
    // TODO Phase 2: call PUT /api/grids/<name>
    alert(`Save grid "${AppState.gridName}" — coming in Phase 2`);
}

function do_grid_save_as() {
    inputBox('Save grid as', 'Grid name:', '', (name) => {
        if (!name) return;
        // TODO Phase 2: call API
        alert(`Save grid as "${name}" — coming in Phase 2`);
    });
}

function do_grid_close() {
    // TODO Phase 2: check changed, confirm, then return home
    AppState.gridName = null;
    showView('home');
}

function do_grid_delete() {
    if (!AppState.gridName) return;
    messageBox(
        'Delete grid',
        `Are you sure you want to delete grid <b>'${AppState.gridName}'</b>?`,
        null,
        () => {
            // TODO Phase 2: call DELETE /api/grids/<name>
            alert(`Delete grid "${AppState.gridName}" — coming in Phase 2`);
        }
    );
}

// ---------------------------------------------------------------------------
// Menu action stubs — Puzzle
// ---------------------------------------------------------------------------

function do_puzzle_new() {
    // TODO Phase 3: show grid chooser to pick the grid for the new puzzle
    alert('New puzzle — coming in Phase 3');
}

function do_puzzle_open() {
    // TODO Phase 3: show puzzle chooser
    alert('Open puzzle — coming in Phase 3');
}

function do_puzzle_save() {
    if (!AppState.puzzleName) { do_puzzle_save_as(); return; }
    // TODO Phase 3: call API
    alert(`Save puzzle "${AppState.puzzleName}" — coming in Phase 3`);
}

function do_puzzle_save_as() {
    inputBox('Save puzzle as', 'Puzzle name:', '', (name) => {
        if (!name) return;
        alert(`Save puzzle as "${name}" — coming in Phase 3`);
    });
}

function do_puzzle_close() {
    AppState.puzzleName = null;
    showView(AppState.gridName ? 'grid-editor' : 'home');
}

function do_puzzle_delete() {
    if (!AppState.puzzleName) return;
    messageBox(
        'Delete puzzle',
        `Are you sure you want to delete puzzle <b>'${AppState.puzzleName}'</b>?`,
        null,
        () => { alert(`Delete puzzle "${AppState.puzzleName}" — coming in Phase 3`); }
    );
}

// ---------------------------------------------------------------------------
// Menu action stubs — Publish
// ---------------------------------------------------------------------------

function do_publish(format) {
    if (!AppState.puzzleName) return;
    // TODO Phase 5: trigger export download
    alert(`Publish "${AppState.puzzleName}" as ${format} — coming in Phase 5`);
}

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
    showView('home');
});
