// Crossword Puzzle Editor — main application script

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
    editingWord: null,       // null | {seq, direction, cells, answer, clue}
    selectedWord: null,      // null | {seq, direction, cells, initialText, currentText}
    showingStats: false,     // true = puzzle editor RHS shows stats panel
    showingFillOrder: false, // true = puzzle editor RHS shows fill-order panel
    sidebarTab: 'clues',     // active sidebar tab: 'clues'|'word'|'stats'|'fill-order'|'grid'
    _statsData: null,        // cached puzzle stats response
    _fillOrderData: null,    // cached fill-order response
    gridStructureChanged: false, // true after Grid-mode edits until user returns to Puzzle mode
};

// ---------------------------------------------------------------------------
// Utility helpers
// ---------------------------------------------------------------------------

function _hash(obj) {
    // This is the djb2 hash function
    const s = JSON.stringify(obj);
    let h = 5381;
    for (let i = 0; i < s.length; i++)
        h = (h * 33 ^ s.charCodeAt(i)) >>> 0;
    return h;
}

function showElement(id) { document.getElementById(id).style.display = 'block'; }
function hideElement(id) { document.getElementById(id).style.display = 'none'; }

function escapeHtml(s) {
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function _closeSidePanels() {
    AppState.showingStats     = false;
    AppState.showingFillOrder = false;
    AppState.sidebarTab       = 'clues';
}

async function apiFetch(method, path, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body !== undefined) opts.body = JSON.stringify(body);
    const resp = await fetch(path, opts);
    return resp.json();
}

// ---------------------------------------------------------------------------
// Modal dialogs
// ---------------------------------------------------------------------------

let _messageLineTimer = null;

function positionMessageLine() {
    const ml = document.getElementById('ml');
    const ab = document.getElementById('action-bar');
    const appBar = document.querySelector('.app-bar');
    if (!ml || !appBar) return;
    const ref = (ab && ab.style.display !== 'none') ? ab : appBar;
    const rect = ref.getBoundingClientRect();
    ml.style.top = `${rect.bottom + 8}px`;
}

function clearMessageLine() {
    const ml = document.getElementById('ml');
    ml.style.display = 'none';
    ml.classList.remove('message-line-notice', 'message-line-error');
    document.getElementById('ml-text').textContent = '';
    if (_messageLineTimer) {
        clearTimeout(_messageLineTimer);
        _messageLineTimer = null;
    }
}

function showMessageLine(text, level = 'notice', timeoutMs = MESSAGE_LINE_TIMEOUT_MS) {
    const ml = document.getElementById('ml');
    document.getElementById('ml-text').textContent = text;
    ml.classList.remove('message-line-notice', 'message-line-error');
    ml.classList.add(level === 'error' ? 'message-line-error' : 'message-line-notice');
    positionMessageLine();
    ml.style.display = 'flex';
    if (_messageLineTimer) {
        clearTimeout(_messageLineTimer);
        _messageLineTimer = null;
    }
    if (timeoutMs > 0) {
        _messageLineTimer = setTimeout(() => {
            clearMessageLine();
        }, timeoutMs);
    }
}

function messageBox(title, prompt, ok, okCallback, okLabel = 'OK') {
    document.getElementById('mb-title').innerHTML = title;
    document.getElementById('mb-prompt').innerHTML = prompt;
    const mbOk = document.getElementById('mb-ok');
    mbOk.textContent = okLabel;
    if (okCallback) {
        mbOk.removeAttribute('href');
        mbOk.onclick = () => { hideElement('mb'); okCallback(); };
    } else if (ok) {
        mbOk.onclick = null;
        mbOk.setAttribute('href', ok);
    } else {
        mbOk.removeAttribute('href');
        mbOk.onclick = () => hideElement('mb');
    }
    showElement('mb');
}

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

async function confirmOverwriteIfExists(kind, name, listExistingNames, onConfirmSave) {
    const existingNames = await listExistingNames();
    if (!existingNames.includes(name)) {
        await onConfirmSave();
        return;
    }
    messageBox(
        `Overwrite ${kind}`,
        `${kind.charAt(0).toUpperCase() + kind.slice(1)} <b>${escapeHtml(name)}</b> already exists. Overwrite it?`,
        null,
        async () => {
            try {
                await onConfirmSave();
            } catch (e) {
                alert(`Save failed: ${e.message}`);
            }
        },
        'Overwrite'
    );
}

function validateUserFacingName(kind, name) {
    if (name.startsWith('__wc__')) {
        messageBox(
            `Invalid ${kind} name`,
            `Names starting with <b>__wc__</b> are reserved for internal working copies used while editing a ${kind}. Please choose a different ${kind} name.`,
            null,
            null
        );
        return false;
    }
    return true;
}

async function rejectIfNameExists(kind, name, listExistingNames) {
    const existingNames = await listExistingNames();
    if (!existingNames.includes(name)) {
        return false;
    }
    messageBox(
        `Duplicate ${kind} name`,
        `${kind.charAt(0).toUpperCase() + kind.slice(1)} <b>${escapeHtml(name)}</b> already exists. Choose a different ${kind} name when creating a new ${kind}.`,
        null,
        null
    );
    return true;
}

function showChooser(title, items, onSelect) {
    document.getElementById('ch-title').innerHTML = title;
    const listEl = document.getElementById('ch-list');
    listEl.innerHTML = '';
    for (const item of items) {
        const a = document.createElement('a');
        a.className = 'w3-bar-item w3-button w3-block w3-left-align';
        a.textContent = item;
        a.onclick = () => { hideElement('ch'); onSelect(item); };
        listEl.appendChild(a);
    }
    showElement('ch');
}

async function showPreviewChooser(title, names, apiPrefix, onSelect) {
    document.getElementById('ch-title').innerHTML = title;
    const listEl = document.getElementById('ch-list');
    listEl.innerHTML = '<div class="w3-container w3-padding">Loading previews…</div>';
    showElement('ch');

    const previews = await Promise.all(
        names.map(name =>
            apiFetch('GET', `${apiPrefix}/${encodeURIComponent(name)}/preview`)
                .catch(() => ({ name, heading: name, svgstr: '', error: true }))
        )
    );

    listEl.innerHTML = '';
    for (const p of previews) {
        const row = document.createElement('div');
        row.style.cssText = 'display:flex;align-items:center;cursor:pointer;padding:6px 8px;border-bottom:1px solid #ddd';
        row.onmouseover = () => row.style.background = '#f1f1f1';
        row.onmouseout  = () => row.style.background = '';
        row.onclick     = () => { hideElement('ch'); onSelect(p.name); };

        const svgDiv = document.createElement('div');
        svgDiv.style.cssText = 'flex-shrink:0;width:150px;overflow:hidden;margin-right:12px';
        if (p.svgstr) {
            svgDiv.innerHTML = p.svgstr;
            const svg = svgDiv.querySelector('svg');
            if (svg) { svg.setAttribute('width', '150'); svg.setAttribute('height', '150'); }
        }

        const textDiv = document.createElement('div');
        textDiv.innerHTML = `<b>${escapeHtml(p.name)}</b><br><small class="w3-text-gray">${escapeHtml(p.heading || '')}</small>`;

        row.appendChild(svgDiv);
        row.appendChild(textDiv);
        listEl.appendChild(row);
    }
}

// ---------------------------------------------------------------------------
// Menu enable / disable
// ---------------------------------------------------------------------------

const MENU_ITEMS = [
    'menu-puzzle-new', 'menu-puzzle-open',
    'menu-puzzle-save', 'menu-puzzle-save-as', 'menu-puzzle-rename', 'menu-puzzle-close', 'menu-puzzle-delete',
    'menu-puzzle-title', 'menu-puzzle-grid-mode', 'menu-puzzle-puzzle-mode',
    'menu-import-acrosslite',
    'menu-export-acrosslite', 'menu-export-cwcompiler', 'menu-export-nytimes', 'menu-export-solver-pdf',
];

function menuEnable(id)  { document.getElementById(id).classList.remove('w3-disabled'); }
function menuDisable(id) { document.getElementById(id).classList.add('w3-disabled'); }

function updateMenu() {
    const home   = AppState.view === 'home';
    const editor = AppState.view === 'editor';

    home   ? menuEnable('menu-puzzle-new')     : menuDisable('menu-puzzle-new');
    home   ? menuEnable('menu-puzzle-open')    : menuDisable('menu-puzzle-open');
    home   ? menuEnable('menu-import-acrosslite')  : menuDisable('menu-import-acrosslite');
    editor ? menuEnable('menu-puzzle-save')    : menuDisable('menu-puzzle-save');
    editor ? menuEnable('menu-puzzle-save-as') : menuDisable('menu-puzzle-save-as');
    (editor && AppState.puzzleName) ? menuEnable('menu-puzzle-rename') : menuDisable('menu-puzzle-rename');
    editor ? menuEnable('menu-puzzle-close')   : menuDisable('menu-puzzle-close');
    menuEnable('menu-puzzle-delete');

    const mode = editor ? _currentEditorMode() : null;
    mode === 'puzzle' ? menuEnable('menu-puzzle-title')       : menuDisable('menu-puzzle-title');
    mode === 'puzzle' ? menuEnable('menu-puzzle-grid-mode')   : menuDisable('menu-puzzle-grid-mode');
    mode === 'grid'   ? menuEnable('menu-puzzle-puzzle-mode') : menuDisable('menu-puzzle-puzzle-mode');

    menuEnable('menu-export-acrosslite');
    menuEnable('menu-export-cwcompiler');
    menuEnable('menu-export-nytimes');
    menuEnable('menu-export-solver-pdf');
}

// ---------------------------------------------------------------------------
// View management
// ---------------------------------------------------------------------------

function showView(view) {
    AppState.view = view;
    updateMenu();
    document.getElementById('lhs').innerHTML = '';
    document.getElementById('rhs').innerHTML = '';
    switch (view) {
        case 'home':
            updateAppBarPuzzleInfo();
            renderActionBar();
            renderHome();
            break;
        case 'editor':
            renderPuzzleEditor();
            break;
        default:
            renderActionBar();
            document.getElementById('lhs').innerHTML =
                `<div class="home-welcome"><p>Unknown view: ${view}</p></div>`;
    }
}

function renderHome() {
    document.getElementById('lhs').innerHTML =
        `<div class="home-welcome">
  <p>Use the Puzzle menu to create or open a crossword for editing.</p>
</div>`;
}

// ---------------------------------------------------------------------------
// Grid SVG renderer (client-side)
// ---------------------------------------------------------------------------

function computeGridNumbers(cells, n) {
    const nums = new Array(n * n).fill(null);
    let num = 1;
    for (let r = 1; r <= n; r++) {
        for (let c = 1; c <= n; c++) {
            const idx = (r - 1) * n + (c - 1);
            if (cells[idx]) continue; // black cell
            const startsAcross = (c === 1 || cells[(r - 1) * n + (c - 2)]) &&
                                  c < n && !cells[(r - 1) * n + c];
            const startsDown   = (r === 1 || cells[(r - 2) * n + (c - 1)]) &&
                                  r < n && !cells[r * n + (c - 1)];
            if (startsAcross || startsDown) nums[idx] = num++;
        }
    }
    return nums;
}

function buildGridSvg(cells, n) {
    const totalPx = n * BOXSIZE + 1;
    const nums    = computeGridNumbers(cells, n);
    const parts   = [
        `<svg xmlns="http://www.w3.org/2000/svg" id="grid-svg" class="svg-grid-mode" ` +
        `width="${totalPx}" height="${totalPx}" style="cursor:pointer;display:block">`,
    ];
    for (let r = 1; r <= n; r++) {
        for (let c = 1; c <= n; c++) {
            const idx   = (r - 1) * n + (c - 1);
            const x     = (c - 1) * BOXSIZE;
            const y     = (r - 1) * BOXSIZE;
            const black = cells[idx];
            parts.push(
                `<rect x="${x}" y="${y}" width="${BOXSIZE}" height="${BOXSIZE}" ` +
                `class="${black ? 'grid-cell-black' : 'grid-cell-white'}" ` +
                `fill="${black ? '#1a1a1a' : 'white'}" stroke="#c8c4bc" stroke-width="0.5"/>`
            );
            if (!black && nums[idx] !== null) {
                parts.push(
                    `<text x="${x + 2}" y="${y + 10}" ` +
                    `font-size="9" font-family="'IBM Plex Sans', sans-serif" fill="#555">${nums[idx]}</text>`
                );
            }
        }
    }
    parts.push(
        `<rect x="0" y="0" width="${totalPx - 1}" height="${totalPx - 1}" ` +
        `fill="none" stroke="#1a1a1a" stroke-width="2"/>`
    );
    parts.push('</svg>');
    return parts.join('');
}

// ---------------------------------------------------------------------------
// Puzzle SVG renderer (client-side)
// ---------------------------------------------------------------------------

function buildPuzzleSvg(puzzleData, editState = null) {
    const n           = puzzleData.grid.size;
    const blackCells  = puzzleData.grid.cells;        // bool[], true = black
    const puzzleCells = puzzleData.puzzle.cells;      // {"idx": {number?, letter?}}
    const totalPx     = n * BOXSIZE + 1;

    // Build edit-mode lookup structures
    let wordCellSet   = null;  // Set of flat indices belonging to the word
    let cursorFlatIdx = -1;
    let wordLetterMap = {};    // flat index -> letter from editState.text

    if (editState) {
        wordCellSet = new Set();
        const text = editState.text || '';
        editState.cells.forEach(([r, c], i) => {
            const fi = (r - 1) * n + (c - 1);
            wordCellSet.add(fi);
            const ch = text[i];
            if (ch && ch !== ' ') wordLetterMap[fi] = ch;
        });
        const [cr, cc] = editState.cells[editState.cursorIdx];
        cursorFlatIdx = (cr - 1) * n + (cc - 1);
    }

    const parts = [
        `<svg xmlns="http://www.w3.org/2000/svg" id="puzzle-svg" class="svg-puzzle-mode" ` +
        `width="${totalPx}" height="${totalPx}" style="cursor:pointer;display:block">`,
    ];

    for (let r = 1; r <= n; r++) {
        for (let c = 1; c <= n; c++) {
            const idx   = (r - 1) * n + (c - 1);
            const x     = (c - 1) * BOXSIZE;
            const y     = (r - 1) * BOXSIZE;
            const black = blackCells[idx];

            let fill, cellClass;
            if (black) {
                fill = '#1a1a1a'; cellClass = '';
            } else if (editState && wordCellSet.has(idx)) {
                if (idx === cursorFlatIdx) {
                    fill = '#f5cbcb'; cellClass = 'puzzle-cell-cursor'; // amber active cell
                } else {
                    fill = '#b8d4f5'; cellClass = 'puzzle-cell-word';   // selected word
                }
            } else {
                fill = 'white'; cellClass = 'puzzle-cell-plain';
            }

            parts.push(
                `<rect x="${x}" y="${y}" width="${BOXSIZE}" height="${BOXSIZE}" ` +
                `${cellClass ? `class="${cellClass}" ` : ''}` +
                `fill="${fill}" stroke="#c8c4bc" stroke-width="0.5"/>`
            );

            if (!black) {
                const cd = puzzleCells[String(idx)] || {};
                if (cd.number !== undefined) {
                    parts.push(
                        `<text x="${x + 2}" y="${y + 10}" ` +
                        `font-size="9" font-family="'IBM Plex Sans', sans-serif" fill="#555">${cd.number}</text>`
                    );
                }
                // In edit mode show weText letters for word cells; otherwise use puzzle data
                const letter = (editState && wordCellSet.has(idx))
                    ? (wordLetterMap[idx] || '')
                    : (cd.letter || '');
                if (letter) {
                    const letterFill = (idx === cursorFlatIdx) ? '#1a1a1a' : '#1a1a2e';
                    parts.push(
                        `<text x="${x + BOXSIZE / 2}" y="${y + BOXSIZE - 5}" ` +
                        `font-size="16" font-family="'IBM Plex Mono', monospace" font-weight="500" ` +
                        `fill="${letterFill}" text-anchor="middle">${escapeHtml(letter)}</text>`
                    );
                }
            }
        }
    }

    // Outer border
    parts.push(
        `<rect x="0" y="0" width="${totalPx - 1}" height="${totalPx - 1}" ` +
        `fill="none" stroke="#1a1a1a" stroke-width="2"/>`
    );

    parts.push('</svg>');
    return parts.join('');
}

// ---------------------------------------------------------------------------
// Puzzle editor — click handling (single = select across, double = select down)
// ---------------------------------------------------------------------------

let _clickState   = 0;
let _clickTimeout = null;
let _clickEvent   = null;
let _ignorePuzzleClicksUntil = 0;
const CLICK_DELAY = 280;

// ---------------------------------------------------------------------------
// Word editor — suggestion state
// ---------------------------------------------------------------------------

let _weSuggestions           = [];    // full list from last fetch: string[] or {word,score}[]
let _weSuggestionsConstrained = false; // true when last fetch was constrained (has scores)
let _wePage                  = 0;     // current page (0-indexed)
const WE_PAGE_SIZE           = 20;

// ---------------------------------------------------------------------------
// Word editor — state
// ---------------------------------------------------------------------------

let _weClueBeforeEdit = '';  // clue value on focus, for detecting changes on blur
let _weCursorIdx      = 0;   // position of typing cursor within the word cells (word editor)

// ---------------------------------------------------------------------------
// Puzzle editor — keyboard entry state
// ---------------------------------------------------------------------------

let _peCursorIdx    = 0;   // cursor position within selectedWord.cells
let _clueDirection  = 'across'; // active clue direction in Clues tab

function _weRenderLhs() {
    const container = document.getElementById('puzzle-svg-container');
    if (!container || !AppState.puzzleData) return;
    const ew        = AppState.editingWord;
    const editState = ew
        ? { cells: ew.cells, cursorIdx: _weCursorIdx, text: ew.answer || '' }
        : null;
    container.innerHTML = buildPuzzleSvg(AppState.puzzleData, editState);
    const svg = document.getElementById('puzzle-svg');
    if (svg) svg.addEventListener('click', handlePuzzleClick);
}

function handlePuzzleClick(event) {
    if (Date.now() < _ignorePuzzleClicksUntil) return;
    if (AppState.editingWord) {
        _clickState = 0;
        if (_clickTimeout) {
            clearTimeout(_clickTimeout);
            _clickTimeout = null;
        }
        _clickEvent = null;
        _ignorePuzzleClicksUntil = Date.now() + CLICK_DELAY;
        closeWordEditor();
        return;
    }
    _clickEvent = event;
    if (_clickState === 0) {
        _clickState = 1;
        _clickTimeout = setTimeout(() => {
            _clickState = 0;
            _clickTimeout = null;
            puzzleClickAt(_clickEvent, 'across');
        }, CLICK_DELAY);
    } else {
        _clickState = 0;
        clearTimeout(_clickTimeout);
        _clickTimeout = null;
        puzzleClickAt(event, 'down');
    }
}

async function puzzleClickAt(event, direction) {
    const svg = document.getElementById('puzzle-svg');
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const r = Math.floor(1 + y / BOXSIZE);
    const c = Math.floor(1 + x / BOXSIZE);
    const n = AppState.puzzleData.grid.size;
    if (r < 1 || r > n || c < 1 || c > n) return;
    if (AppState.puzzleData.grid.cells[(r - 1) * n + (c - 1)]) return; // black cell
    const word = findWordAtCell(r, c, direction);
    if (word) {
        await _peCommitWord();
        selectWord(word.seq, word.direction, r, c);
    }
}

function findWordAtCell(r, c, direction) {
    for (const word of AppState.puzzleData.puzzle.words) {
        if (word.direction !== direction) continue;
        for (const [wr, wc] of word.cells) {
            if (wr === r && wc === c) return word;
        }
    }
    return null;
}

// ---------------------------------------------------------------------------
// Puzzle editor — word selection and direct keyboard entry
// ---------------------------------------------------------------------------

function selectWord(seq, direction, clickR, clickC) {
    const word = AppState.puzzleData.puzzle.words.find(
        w => w.seq === seq && w.direction === direction
    );
    if (!word) return;
    const len  = word.cells.length;
    const text = (word.answer || '').padEnd(len).slice(0, len);
    AppState.selectedWord = {
        seq, direction,
        cells:       word.cells,
        initialText: text,
        currentText: text,
    };
    _closeSidePanels();
    if (clickR !== undefined) {
        const clickedIdx = word.cells.findIndex(([r, c]) => r === clickR && c === clickC);
        _peCursorIdx = clickedIdx >= 0 ? clickedIdx : 0;
    } else {
        const firstBlank = text.indexOf(' ');
        _peCursorIdx = firstBlank >= 0 ? firstBlank : 0;
    }
    _updatePuzzleToolbar();
    renderPuzzleEditorLhs();
    renderPuzzleEditorRhs();
}

async function _peCommitWord() {
    const sw = AppState.selectedWord;
    if (!sw) return;
    if (sw.currentText === sw.initialText) return;
    const wn = AppState.puzzleWorkingName;
    try {
        const data = await apiFetch('PUT',
            `/api/puzzles/${encodeURIComponent(wn)}/words/${sw.seq}/${sw.direction}`,
            { text: sw.currentText });
        if (data.error) { alert(`Error saving word: ${data.error}`); return; }
        AppState.puzzleData      = data;
        sw.initialText           = sw.currentText;
        _updatePuzzleUndoRedo();
    } catch (e) { alert('Error saving word'); }
}

function _peKeydown(e) {
    if (!AppState.selectedWord || AppState.editingWord) return;
    // Don't capture keystrokes going to modal inputs
    const tag = e.target.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

    const sw  = AppState.selectedWord;
    const len = sw.cells.length;
    const isAcross = sw.direction === 'across';

    if (e.key === 'Escape') {
        _peCommitWord().then(() => {
            AppState.selectedWord = null;
            _updatePuzzleToolbar();
            renderPuzzleEditorLhs();
        });
        e.preventDefault(); return;
    }

    if ((isAcross && e.key === 'ArrowRight') || (!isAcross && e.key === 'ArrowDown')) {
        _peCursorIdx = Math.min(_peCursorIdx + 1, len - 1);
        renderPuzzleEditorLhs(); e.preventDefault(); return;
    }
    if ((isAcross && e.key === 'ArrowLeft') || (!isAcross && e.key === 'ArrowUp')) {
        _peCursorIdx = Math.max(_peCursorIdx - 1, 0);
        renderPuzzleEditorLhs(); e.preventDefault(); return;
    }

    // Cross-direction navigation: switch to perpendicular word at the same cell
    const [curR, curC] = sw.cells[_peCursorIdx];
    if (!isAcross && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
        const neighbor = findWordAtCell(curR, curC, 'across');
        if (neighbor) { _peCommitWord().then(() => selectWord(neighbor.seq, neighbor.direction, curR, curC)); }
        e.preventDefault(); return;
    }
    if (isAcross && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
        const neighbor = findWordAtCell(curR, curC, 'down');
        if (neighbor) { _peCommitWord().then(() => selectWord(neighbor.seq, neighbor.direction, curR, curC)); }
        e.preventDefault(); return;
    }

    if (e.key === 'Delete') {
        const t = sw.currentText;
        sw.currentText = t.slice(0, _peCursorIdx) + ' ' + t.slice(_peCursorIdx + 1);
        renderPuzzleEditorLhs(); e.preventDefault(); return;
    }

    if (e.key === 'Backspace') {
        const t = sw.currentText;
        if (t[_peCursorIdx] !== ' ') {
            sw.currentText = t.slice(0, _peCursorIdx) + ' ' + t.slice(_peCursorIdx + 1);
        } else if (_peCursorIdx > 0) {
            _peCursorIdx--;
            sw.currentText = sw.currentText.slice(0, _peCursorIdx) + ' ' + sw.currentText.slice(_peCursorIdx + 1);
        }
        renderPuzzleEditorLhs(); e.preventDefault(); return;
    }

    if (e.key === 'Tab') {
        e.preventDefault();
        const words = [...AppState.puzzleData.puzzle.words].sort((a, b) =>
            a.direction === b.direction ? a.seq - b.seq : a.direction.localeCompare(b.direction));
        const idx = words.findIndex(w => w.seq === sw.seq && w.direction === sw.direction);
        const next = e.shiftKey
            ? words[(idx - 1 + words.length) % words.length]
            : words[(idx + 1) % words.length];
        _peCommitWord().then(() => selectWord(next.seq, next.direction));
        return;
    }

    if (e.key === ' ' || (e.key.length === 1 && /^[a-zA-Z]$/.test(e.key))) {
        const ch = e.key === ' ' ? ' ' : e.key.toUpperCase();
        const t = sw.currentText;
        sw.currentText = t.slice(0, _peCursorIdx) + ch + t.slice(_peCursorIdx + 1);
        // Advance cursor one step forward
        if (_peCursorIdx < len - 1) _peCursorIdx++;
        renderPuzzleEditorLhs(); e.preventDefault();
    }
}

async function do_puzzle_edit_word(seq, direction) {
    if (_currentEditorMode() !== 'puzzle') return;
    // Called from toolbar button (no args) or clue list (with args)
    const sw = AppState.selectedWord;
    let targetSeq = seq, targetDir = direction;
    if (targetSeq === undefined) {
        if (!sw) return;  // no word selected — silent
        targetSeq = sw.seq;
        targetDir = sw.direction;
    }
    await _peCommitWord();
    openWordEditor(targetSeq, targetDir);
}

// ---------------------------------------------------------------------------
// Puzzle editor — rendering
// ---------------------------------------------------------------------------

function _currentEditorMode() {
    return (AppState.puzzleData && AppState.puzzleData.mode) || 'puzzle';
}

function renderPuzzleEditor() {
    document.removeEventListener('keydown', _peKeydown);
    if (_currentEditorMode() === 'puzzle') {
        document.addEventListener('keydown', _peKeydown);
    }
    updateMenu();
    updateAppBarPuzzleInfo();
    renderActionBar();
    renderPuzzleEditorLhs();
    renderPuzzleEditorRhs();
}

function renderPuzzleEditorLhs() {
    const pd   = AppState.puzzleData;
    const mode = _currentEditorMode();

    const ew  = AppState.editingWord;
    const sw  = AppState.selectedWord;
    const editState = mode === 'puzzle' && ew
        ? { cells: ew.cells, cursorIdx: _weCursorIdx, text: ew.answer || '' }
        : mode === 'puzzle' && sw
        ? { cells: sw.cells, cursorIdx: _peCursorIdx, text: sw.currentText }
        : null;
    const clickHelp = mode === 'grid'
        ? `<div class="kb-hints">
             <span class="kb-hint"><kbd>Click</kbd> toggle cell</span>
             <span class="kb-hint"><kbd>Rotate</kbd> or <kbd>Generate</kbd> in toolbar</span>
           </div>`
        : AppState.editingWord
        ? `<div class="kb-hints">
             <span class="kb-hint"><kbd>Enter</kbd> suggest words</span>
             <span class="kb-hint"><kbd>Esc</kbd> cancel</span>
           </div>`
        : `<div class="kb-hints">
             <span class="kb-hint"><kbd>← → ↑ ↓</kbd> move</span>
             <span class="kb-hint"><kbd>Tab</kbd> next word</span>
             <span class="kb-hint"><kbd>A–Z</kbd> fill</span>
             <span class="kb-hint"><kbd>⌫</kbd> clear</span>
             <span class="kb-hint"><kbd>Esc</kbd> deselect</span>
           </div>`;

    updateAppBarPuzzleInfo();
    document.getElementById('lhs').innerHTML = `
<div class="grid-canvas-frame">
  <div id="puzzle-svg-container">
    ${pd ? buildPuzzleSvg(pd, editState) : ''}
  </div>
</div>
${clickHelp}`;

    const svg = document.getElementById('puzzle-svg');
    if (svg && mode === 'puzzle') svg.addEventListener('click', handlePuzzleClick);
    if (svg && mode === 'grid') svg.addEventListener('click', handleGridModeClick);
    _updatePuzzleUndoRedo();
}

function updateAppBarPuzzleInfo() {
    const el = document.getElementById('app-bar-puzzle-info');
    if (!el) return;
    if (AppState.view !== 'editor' || !AppState.puzzleData) {
        el.innerHTML = '';
        return;
    }
    const name = AppState.puzzleName || '(No name)';
    const mode = _currentEditorMode();
    const badgeClass = mode === 'grid' ? 'mode-badge mode-badge-grid' : 'mode-badge mode-badge-puzzle';
    const badgeText  = mode === 'grid' ? 'Grid Mode' : 'Puzzle Mode';
    const isDirty = AppState.puzzleSavedHash !== null &&
        _hash(AppState.puzzleData.puzzle) !== AppState.puzzleSavedHash;
    const saveHtml = isDirty
        ? `<span class="save-status save-status-dirty">● Unsaved</span>`
        : `<span class="save-status save-status-saved">✓ Saved</span>`;
    el.innerHTML =
        `<span class="puzzle-info-name">${escapeHtml(name)}</span>` +
        `<span class="${badgeClass}">${badgeText}</span>` +
        saveHtml;
}

function renderActionBar() {
    const ab = document.getElementById('action-bar');
    if (!ab) return;
    if (AppState.view !== 'editor') {
        ab.style.display = 'none';
        document.body.classList.remove('editor-open');
        return;
    }
    ab.style.display = 'flex';
    document.body.classList.add('editor-open');

    const pd   = AppState.puzzleData;
    const mode = _currentEditorMode();
    const size = pd ? pd.grid.size : 0;
    const genDisabled = (size >= 9 && size % 2 === 1) ? '' : ' w3-disabled';

    const modeSpecific = mode === 'grid' ? `
<div class="ab-group">
  <button class="ab-btn ab-mode-btn" onclick="do_switch_to_puzzle_mode()">Puzzle Mode</button>
  <button class="ab-btn ab-mode-btn ab-mode-active">Grid Mode</button>
</div>
<div class="ab-divider"></div>
<div class="ab-group">
  <button class="ab-btn" onclick="do_puzzle_rotate_grid()">
    <i class="material-icons">rotate_right</i><span>Rotate</span>
  </button>
  <button id="puzzle-generate-btn" class="ab-btn${genDisabled}" onclick="do_puzzle_generate_grid()">
    <i class="material-icons">casino</i><span>Generate</span>
  </button>
  <button class="ab-btn" onclick="do_puzzle_stats()">
    <i class="material-icons">info</i><span>Stats</span>
  </button>
</div>` : `
<div class="ab-group">
  <button class="ab-btn ab-mode-btn ab-mode-active">Puzzle Mode</button>
  <button class="ab-btn ab-mode-btn" onclick="do_switch_to_grid_mode()">Grid Mode</button>
</div>
<div class="ab-divider"></div>
<div class="ab-group">
  <button id="puzzle-editword-btn" class="ab-btn" onclick="do_puzzle_edit_word()">
    <i class="material-icons">edit</i><span>Edit word</span>
  </button>
  <button class="ab-btn" onclick="do_puzzle_fill_order()">
    <i class="material-icons">format_list_numbered</i><span>Fill order</span>
  </button>
  <button class="ab-btn" onclick="do_puzzle_stats()">
    <i class="material-icons">info</i><span>Stats</span>
  </button>
</div>`;

    ab.innerHTML = `
<div class="ab-group">
  <button class="ab-btn" onclick="do_puzzle_save()">
    <i class="material-icons">save</i><span>Save</span>
  </button>
</div>
<div class="ab-divider"></div>
<div class="ab-group">
  <button id="puzzle-undo-btn" class="ab-btn" onclick="do_puzzle_undo()">
    <i class="material-icons">undo</i><span>Undo</span>
  </button>
  <button id="puzzle-redo-btn" class="ab-btn" onclick="do_puzzle_redo()">
    <i class="material-icons">redo</i><span>Redo</span>
  </button>
</div>
<div class="ab-divider"></div>
${modeSpecific}`;
}

function renderPuzzleEditorRhs() {
    const mode      = _currentEditorMode();
    const activeTab = _getActiveTab(mode);
    const tabList   = mode === 'grid' ? ['grid', 'stats'] : ['clues', 'word', 'stats', 'fill-order'];
    let contentHtml;

    if (mode === 'grid') {
        contentHtml = activeTab === 'stats' && AppState._statsData
            ? renderStatsPanel(AppState._statsData)
            : renderGridModePanel();
    } else {
        switch (activeTab) {
            case 'word':
                contentHtml = AppState.editingWord
                    ? renderWordEditorPanel()
                    : `<div class="sidebar-empty">Select a word in the grid, then click <b>Edit word</b> to edit it here.</div>`;
                break;
            case 'stats':
                contentHtml = AppState._statsData
                    ? renderStatsPanel(AppState._statsData)
                    : `<div class="sidebar-empty">Loading stats…</div>`;
                break;
            case 'fill-order':
                contentHtml = AppState._fillOrderData
                    ? renderFillOrderPanel(AppState._fillOrderData)
                    : `<div class="sidebar-empty">Loading fill order…</div>`;
                break;
            default:
                contentHtml = renderClues();
        }
    }

    document.getElementById('rhs').innerHTML =
        renderSidebarTabs(activeTab, tabList) +
        `<div class="sidebar-content">${contentHtml}</div>`;
    _scrollCluesToFirstMissing();
}

function _getActiveTab(mode) {
    if (mode === 'grid') return AppState.sidebarTab === 'stats' ? 'stats' : 'grid';
    if (AppState.editingWord) return 'word';
    return AppState.sidebarTab || 'clues';
}

function renderSidebarTabs(activeTab, tabs) {
    const labels = { clues: 'Clues', word: 'Word', stats: 'Stats', 'fill-order': 'Fill Order', grid: 'Grid' };
    return `<div class="sidebar-tabs">${
        tabs.map(t =>
            `<button class="sidebar-tab${t === activeTab ? ' sidebar-tab-active' : ''}"
                     onclick="switchSidebarTab('${t}')">${labels[t]}</button>`
        ).join('')
    }</div>`;
}

async function switchSidebarTab(tab) {
    if (tab === 'stats' && !AppState._statsData) {
        await do_puzzle_stats(); return;
    }
    if (tab === 'fill-order' && !AppState._fillOrderData) {
        await do_puzzle_fill_order(); return;
    }
    if (tab === 'word' && !AppState.editingWord && AppState.selectedWord) {
        await openWordEditor(AppState.selectedWord.seq, AppState.selectedWord.direction); return;
    }
    AppState.sidebarTab     = tab;
    AppState.showingStats   = (tab === 'stats');
    AppState.showingFillOrder = (tab === 'fill-order');
    renderPuzzleEditorRhs();
}

function switchClueDirection(dir) {
    _clueDirection = dir;
    renderPuzzleEditorRhs();
}

function _scrollCluesToFirstMissing() {
    const list = document.getElementById('clue-list-active');
    if (!list) return;
    const first = list.querySelector('[data-noclue]');
    if (first) first.scrollIntoView({ block: 'nearest' });
}

function renderGridModePanel() {
    const pd   = AppState.puzzleData;
    const size = pd ? pd.grid.size : '—';
    const wc   = pd ? pd.puzzle.words.length : '—';
    const canGen = pd && pd.grid.size >= 9 && pd.grid.size % 2 === 1;
    return `
<div class="grid-panel-info">
  <p class="grid-instructions">Click any cell to toggle it between white and black. The grid maintains rotational symmetry automatically.</p>
  <div class="grid-info-card">
    <div class="grid-info-row"><span class="grid-info-label">Grid size</span><span class="grid-info-value">${size} × ${size}</span></div>
    <div class="grid-info-row"><span class="grid-info-label">Words</span><span class="grid-info-value">${wc}</span></div>
    <div class="grid-info-row"><span class="grid-info-label">Symmetry</span><span class="grid-info-value">180° rotational</span></div>
    <div class="grid-info-row"><span class="grid-info-label">Auto-generate</span><span class="grid-info-value">${canGen ? 'Available (odd size ≥ 9)' : 'Not available for this size'}</span></div>
  </div>
  <p class="grid-instructions" style="margin-top:0">Use <b>Rotate</b> to rotate the grid 90°. Use <b>Generate</b> to create a random valid grid pattern. Switch to <b>Puzzle Mode</b> when done.</p>
</div>`;
}

function renderClues() {
    if (!AppState.puzzleData) return '';
    const words    = AppState.puzzleData.puzzle.words;
    const across   = words.filter(w => w.direction === 'across').sort((a, b) => a.seq - b.seq);
    const down     = words.filter(w => w.direction === 'down').sort((a, b) => a.seq - b.seq);
    const selected = AppState.selectedWord;
    const dir      = _clueDirection;
    const list     = dir === 'across' ? across : down;

    const acrossClued = across.filter(w => w.clue).length;
    const downClued   = down.filter(w => w.clue).length;
    const countLabel  = dir === 'across'
        ? `${acrossClued}/${across.length} clued`
        : `${downClued}/${down.length} clued`;
    const countClass  = (dir === 'across' ? acrossClued === across.length : downClued === down.length)
        ? 'clue-count-ok' : 'clue-count-bad';

    const items = list.map(w => {
        const isSelected = selected && selected.seq === w.seq && selected.direction === dir;
        const hasMissing = !w.clue;
        return `<li class="clue-row${isSelected ? ' clue-row-selected' : ''}"${hasMissing ? ' data-noclue="1"' : ''}>` +
            `<a class="clue-row-link" onclick="selectWord(${w.seq},'${dir}');return false;">` +
            (hasMissing ? '<span class="clue-missing-dot"></span>' : '') +
            `<span class="clue-num">${w.seq}</span>` +
            `<span class="clue-text${hasMissing ? ' clue-text-missing' : ''}">${escapeHtml(w.clue || 'No clue')}</span>` +
            `</a>` +
            `<a class="clue-edit-link" onclick="do_puzzle_edit_word(${w.seq},'${dir}');return false;">edit</a>` +
            `</li>`;
    }).join('');

    return `
<div class="clue-toolbar">
  <div class="clue-dir-toggle">
    <button class="clue-dir-btn${dir === 'across' ? ' clue-dir-btn-active' : ''}" onclick="switchClueDirection('across')">Across</button>
    <button class="clue-dir-btn${dir === 'down'   ? ' clue-dir-btn-active' : ''}" onclick="switchClueDirection('down')">Down</button>
  </div>
  <span class="clue-count ${countClass}">${countLabel}</span>
</div>
<ul id="clue-list-active" class="clue-list-new">${items}</ul>`;
}

// ---------------------------------------------------------------------------
// Word editor panel
// ---------------------------------------------------------------------------

function renderWordEditorPanel() {
    const ew       = AppState.editingWord;
    const clue     = ew.clue || '';
    const dirLabel = ew.direction.charAt(0).toUpperCase() + ew.direction.slice(1);
    const len      = ew.cells.length;
    const text     = (ew.answer || '').padEnd(len).slice(0, len);
    const defsDisabled = /^[A-Za-z]+$/.test(text.trim()) && text.trim().length === len ? '' : 'disabled';

    return `
<div id="we-dialog" class="we-panel">
  <div class="we-header">
    <div class="we-header-info">
      <div class="we-header-title">${ew.seq} ${dirLabel}</div>
      <div class="we-header-sub">${len} letters</div>
    </div>
    <button class="we-header-close" onclick="closeWordEditor()" aria-label="Close">&times;</button>
  </div>

  <div class="we-body">
    <!-- Answer -->
    <div class="we-field">
      <label class="we-label">Answer</label>
      <input class="we-word-input" id="we-text" type="text"
             maxlength="${len}" value="${escapeHtml(text.replace(/ /g, '.'))}"
             oninput="weUpdateDefinitionsBtn()"/>
    </div>

    <!-- Clue -->
    <div class="we-field">
      <label class="we-label">Clue</label>
      <input class="we-clue-input" id="we-clue" type="text"
             value="${escapeHtml(clue)}"
             onfocus="_weClueBeforeEdit=this.value"
             onblur="_weOnClueBlur(this.value)"
             placeholder="Enter clue…"/>
    </div>

    <!-- Suggestions -->
    <div class="we-field">
      <div class="we-suggestions-toolbar">
        <label class="we-label" style="margin:0">Suggestions</label>
        <label style="cursor:pointer;font-size:0.78rem;color:var(--c-text-muted);display:flex;align-items:center;gap:4px">
          <input type="checkbox" id="we-constrained" checked> Constrained
        </label>
        <button class="ab-btn" type="button" onclick="doWordSuggestFetch()" style="height:26px;font-size:0.75rem">
          <i class="material-icons" style="font-size:13px">search</i> Suggest
        </button>
      </div>
      <div id="we-match" class="we-match-label" style="display:none"></div>
      <ul id="we-suggestion-list" class="we-suggestion-list" style="display:none"></ul>
      <div id="we-pagination" style="display:none;margin-top:4px;align-items:center;gap:8px">
        <button class="ab-btn" type="button" id="we-page-prev" onclick="wePagePrev()" style="height:24px;padding:0 8px">&#9664;</button>
        <span id="we-page-label" style="flex:1;text-align:center;font-size:0.78rem;color:var(--c-text-muted)"></span>
        <button class="ab-btn" type="button" id="we-page-next" onclick="wePageNext()" style="height:24px;padding:0 8px">&#9654;</button>
      </div>
    </div>

    <!-- Secondary tools -->
    <div class="we-secondary-tools">
      <button class="ab-btn" id="we-constraints-btn" type="button" onclick="doWordConstraints()" style="font-size:0.78rem">
        <i class="material-icons" style="font-size:13px">assignment</i> Constraints
      </button>
      <button class="ab-btn" id="we-definitions-btn" type="button" ${defsDisabled} onclick="doWordDefinitions()" style="font-size:0.78rem">
        <i class="material-icons" style="font-size:13px">menu_book</i> Definitions
      </button>
    </div>

    <!-- Action row -->
    <div class="we-action-row">
      <button class="btn btn-primary" type="button" onclick="doWordEditOK()">Apply</button>
      <button class="btn btn-secondary" type="button" onclick="closeWordEditor()">Cancel</button>
    </div>
  </div>
</div>`;
}

function weListItemClick(word) {
    const inp = document.getElementById('we-text');
    if (inp) inp.value = word;
    weUpdateDefinitionsBtn();
    // Highlight selected item
    document.querySelectorAll('#we-suggestion-list li').forEach(li => {
        li.style.background = li.dataset.word === word ? '#d0e8ff' : '';
    });
}

function weUpdateDefinitionsBtn() {
    const inp = document.getElementById('we-text');
    const btn = document.getElementById('we-definitions-btn');
    if (!inp || !btn) return;
    const len = AppState.editingWord ? AppState.editingWord.cells.length : 0;
    const val = inp.value;
    btn.disabled = !(val.length === len && /^[A-Za-z]+$/.test(val));
}

function _weOnClueBlur(newVal) {
    _weClueBeforeEdit = newVal;
    if (AppState.editingWord) AppState.editingWord.clue = newVal;
}

// ---------------------------------------------------------------------------
// Word editor — keyboard handler (Escape/Enter only; browser handles #we-text)
// ---------------------------------------------------------------------------

function _weKeydown(e) {
    if (!AppState.editingWord) return;
    const tag = e.target.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA') {
        if (e.key === 'Escape') { closeWordEditor();     e.preventDefault(); }
        if (e.key === 'Enter' && e.target.id === 'we-text') { doWordSuggestFetch(); e.preventDefault(); }
        if (e.key === 'Enter' && e.target.id !== 'we-text') { doWordEditOK();       e.preventDefault(); }
        return;
    }
    // For buttons/other elements: Escape closes, Enter lets the focused element
    // handle its own click (so Suggest button → search, OK button → save, etc.)
    if (e.key === 'Escape') { closeWordEditor(); e.preventDefault(); }
}

// ---------------------------------------------------------------------------
// Word editor — open / close
// ---------------------------------------------------------------------------

async function openWordEditor(seq, direction) {
    if (_currentEditorMode() !== 'puzzle') return;
    const wn = AppState.puzzleWorkingName;
    try {
        const data = await apiFetch('GET',
            `/api/puzzles/${encodeURIComponent(wn)}/words/${seq}/${direction}`);
        if (data.error) { alert(`Word not found: ${data.error}`); return; }
        AppState.editingWord = {
            seq:       data.seq,
            direction: data.direction,
            cells:     data.cells,
            answer:    data.answer,
            clue:      data.clue,
        };
        AppState.sidebarTab  = 'word';
        _weSuggestions = [];
        _wePage        = 0;
        document.removeEventListener('keydown', _peKeydown);
        document.addEventListener('keydown', _weKeydown);
        renderPuzzleEditorLhs();
        renderPuzzleEditorRhs();
        _updatePuzzleUndoRedo();
    } catch (e) {
        alert('Error opening word editor');
    }
}

function closeWordEditor() {
    document.removeEventListener('keydown', _weKeydown);
    document.addEventListener('keydown', _peKeydown);
    AppState.editingWord  = null;
    AppState.showingStats = false;
    AppState.sidebarTab   = 'clues';
    _weSuggestions = [];
    _wePage        = 0;
    renderPuzzleEditorLhs();
    renderPuzzleEditorRhs();
    _updatePuzzleUndoRedo();
}

// ---------------------------------------------------------------------------
// Word editor — suggestions (fetch + pagination)
// ---------------------------------------------------------------------------

async function doWordSuggestFetch() {
    const constrained = document.getElementById('we-constrained')?.checked ?? true;
    if (constrained) {
        await _fetchConstrainedSuggestions();
    } else {
        await _fetchPatternSuggestions();
    }
}

async function _fetchPatternSuggestions() {
    { const m = document.getElementById('we-match'); if (m) m.style.display = 'none'; }
    const inp     = document.getElementById('we-text');
    const rawText = inp ? inp.value : (AppState.editingWord.answer || '');
    const pattern = rawText.replace(/ /g, '.').toUpperCase();
    if (!pattern) return;
    try {
        const data = await apiFetch('GET',
            `/api/words/suggestions?pattern=${encodeURIComponent(pattern)}`);
        if (!AppState.editingWord) return;
        const matchEl = document.getElementById('we-match');
        if (!matchEl) return;
        if (!data.suggestions || data.suggestions.length === 0) {
            _weSuggestions = [];
            matchEl.innerHTML     = 'No matches found';
            matchEl.style.display = 'block';
        } else {
            _weSuggestions            = data.suggestions.map(w => w.toUpperCase());
            _weSuggestionsConstrained = false;
            _wePage                   = 0;
            _weRenderSuggestionList();
        }
    } catch (e) {
        if (!AppState.editingWord) return;
        const matchEl = document.getElementById('we-match');
        if (matchEl) { matchEl.innerHTML = 'Error fetching suggestions'; matchEl.style.display = 'block'; }
    }
}

async function _fetchConstrainedSuggestions() {
    const ew = AppState.editingWord;
    const wn = AppState.puzzleWorkingName;
    { const m = document.getElementById('we-match'); if (m) m.style.display = 'none'; }
    try {
        const inp = document.getElementById('we-text');
        const rawText = inp ? inp.value : (ew.answer || '');
        const pattern = rawText.replace(/ /g, '.').toUpperCase();
        const data = await apiFetch('GET',
            `/api/puzzles/${encodeURIComponent(wn)}/words/${ew.seq}/${ew.direction}/suggestions?pattern=${encodeURIComponent(pattern)}`);
        if (!AppState.editingWord) return;
        const matchEl = document.getElementById('we-match');
        if (!matchEl) return;
        if (!data.suggestions || data.suggestions.length === 0) {
            _weSuggestions = [];
            matchEl.innerHTML     = 'No matches found';
            matchEl.style.display = 'block';
        } else {
            _weSuggestions            = data.suggestions.map(
                item => typeof item === 'string'
                    ? { word: item.toUpperCase(), score: null }
                    : { word: item.word.toUpperCase(), score: item.score }
            );
            _weSuggestionsConstrained = true;
            _wePage                   = 0;
            _weRenderSuggestionList();
        }
    } catch (e) {
        if (!AppState.editingWord) return;
        const matchEl = document.getElementById('we-match');
        if (matchEl) { matchEl.innerHTML = 'Error fetching suggestions'; matchEl.style.display = 'block'; }
    }
}

function _weRenderSuggestionList() {
    const matchEl  = document.getElementById('we-match');
    const listEl   = document.getElementById('we-suggestion-list');
    const pageDiv  = document.getElementById('we-pagination');
    const prevBtn  = document.getElementById('we-page-prev');
    const nextBtn  = document.getElementById('we-page-next');
    const labelEl  = document.getElementById('we-page-label');

    const total     = _weSuggestions.length;
    const pageStart = _wePage * WE_PAGE_SIZE;
    const pageEnd   = Math.min(pageStart + WE_PAGE_SIZE, total);
    const pageItems = _weSuggestions.slice(pageStart, pageEnd);

    matchEl.innerHTML     = `${total} match${total === 1 ? '' : 'es'} found:`;
    matchEl.style.display = 'block';

    const maxScore = _weSuggestionsConstrained
        ? Math.max(1, ..._weSuggestions.map(s => s.score || 0))
        : 0;

    listEl.innerHTML = '';
    for (const item of pageItems) {
        const word  = _weSuggestionsConstrained ? item.word : item;
        const score = _weSuggestionsConstrained ? item.score : null;
        const li    = document.createElement('li');
        li.dataset.word  = word;
        li.style.cssText = 'padding:4px 8px;cursor:pointer;display:flex;align-items:center;gap:8px;border-bottom:1px solid #eee';
        li.onmouseover = () => { if (li.style.background !== 'rgb(208, 232, 255)') li.style.background = '#f5f5f5'; };
        li.onmouseout  = () => { if (li.style.background !== 'rgb(208, 232, 255)') li.style.background = ''; };
        li.onclick     = () => weListItemClick(word);

        let inner = `<span style="font-family:Courier;font-size:14px;min-width:${word.length * 9}px">${escapeHtml(word)}</span>`;
        if (score !== null) {
            const pct = Math.round((score / maxScore) * 100);
            inner += `<span style="display:inline-block;width:60px;height:8px;background:#ddd;border-radius:3px;flex-shrink:0">` +
                     `<span style="display:block;width:${pct}%;height:100%;background:#5b9bd5;border-radius:3px"></span></span>` +
                     `<span style="font-size:11px;color:#888">${score}</span>`;
        }
        li.innerHTML = inner;
        listEl.appendChild(li);
    }
    listEl.style.display = 'block';

    // Pagination controls
    if (total > WE_PAGE_SIZE) {
        labelEl.textContent    = `${pageStart + 1}–${pageEnd} of ${total}`;
        prevBtn.disabled       = _wePage === 0;
        nextBtn.disabled       = pageEnd >= total;
        pageDiv.style.display  = 'flex';
    } else {
        pageDiv.style.display  = 'none';
    }
}

function wePagePrev() {
    if (_wePage > 0) { _wePage--; _weRenderSuggestionList(); }
}

function wePageNext() {
    if ((_wePage + 1) * WE_PAGE_SIZE < _weSuggestions.length) { _wePage++; _weRenderSuggestionList(); }
}

// ---------------------------------------------------------------------------
// Word editor — Constraints tab
// ---------------------------------------------------------------------------

async function doWordConstraints() {
    const ew = AppState.editingWord;
    const wn = AppState.puzzleWorkingName;

    const titleEl = document.getElementById('constraints-popup-title');
    const bodyEl  = document.getElementById('constraints-popup-body');
    titleEl.textContent = `Constraints — ${ew.seq} ${ew.direction === 'A' ? 'Across' : 'Down'}`;
    bodyEl.innerHTML = 'Loading…';
    showElement('constraints-popup');

    try {
        const data = await apiFetch('GET',
            `/api/puzzles/${encodeURIComponent(wn)}/words/${ew.seq}/${ew.direction}/constraints`);
        if (data.error) { bodyEl.innerHTML = `Error: ${escapeHtml(data.error)}`; return; }

        const colNames    = ['Pos', 'Letter', 'Location', 'Text', 'Index', 'Regexp', 'Choices'];
        const crosserKeys = ['pos', 'letter', 'crossing_location', 'crossing_text',
                             'crossing_index', 'regexp', 'choices'];

        const headerRow = colNames.map(n => `<th>${n}</th>`).join('');
        const bodyRows  = data.crossers.map(cr =>
            `<tr>${crosserKeys.map(k => `<td>${escapeHtml(String(cr[k]))}</td>`).join('')}</tr>`
        ).join('');

        bodyEl.innerHTML = `
<div class="w3-padding w3-center">
  <b>Overall pattern:</b>
  <code style="margin:0 8px">${escapeHtml(data.pattern)}</code>
</div>
<table class="w3-table w3-small w3-bordered">
  <tr>${headerRow}</tr>
  ${bodyRows}
</table>`;
    } catch (e) {
        bodyEl.innerHTML = 'Error fetching constraints';
    }
}

// ---------------------------------------------------------------------------
// Word editor — Definitions tab
// ---------------------------------------------------------------------------

async function doWordDefinitions() {
    const inp  = document.getElementById('we-text');
    const word = inp ? inp.value.toUpperCase() : '';

    const titleEl = document.getElementById('defs-popup-title');
    const bodyEl  = document.getElementById('defs-popup-body');
    titleEl.textContent = word;
    bodyEl.innerHTML = 'Loading…';
    showElement('defs-popup');

    try {
        const data = await apiFetch('GET', `/api/words/${encodeURIComponent(word)}/definitions`);
        if (data.error) { bodyEl.innerHTML = `<p>${escapeHtml(data.error)}</p>`; return; }

        const entriesHtml = data.entries.map(entry => {
            const defsHtml = entry.definitions.map(d => {
                const ex = d.example ? `<div style="color:#666;font-style:italic;margin-top:2px">${escapeHtml(d.example)}</div>` : '';
                return `<li style="margin-bottom:4px">${escapeHtml(d.text)}${ex}</li>`;
            }).join('');
            return `<div style="margin-bottom:8px">
  <b style="text-transform:capitalize">${escapeHtml(entry.part_of_speech)}</b>
  <ol style="margin:4px 0 0 0;padding-left:18px">${defsHtml}</ol>
</div>`;
        }).join('');

        bodyEl.innerHTML = entriesHtml || '<p>No definitions found.</p>';
    } catch (e) {
        bodyEl.innerHTML = 'Error fetching definitions.';
    }
}

// ---------------------------------------------------------------------------
// Word editor — OK
// ---------------------------------------------------------------------------

async function doWordEditOK() {
    const ew   = AppState.editingWord;
    const wn   = AppState.puzzleWorkingName;
    const clue = document.getElementById('we-clue').value || '';
    const len  = ew.cells.length;
    const text = (document.getElementById('we-text').value || '').toUpperCase().replace(/\./g, ' ').padEnd(len).slice(0, len);

    try {
        const data = await apiFetch('PUT',
            `/api/puzzles/${encodeURIComponent(wn)}/words/${ew.seq}/${ew.direction}`,
            { text, clue });
        if (data.error) { alert(`Error saving word: ${data.error}`); return; }
        document.removeEventListener('keydown', _weKeydown);
        document.addEventListener('keydown', _peKeydown);
        AppState.puzzleData  = data;
        AppState.editingWord = null;
        _weSuggestions       = [];
        _wePage              = 0;
        // Sync selectedWord text from the response so the grid renders correctly
        if (AppState.selectedWord) {
            const sw = AppState.selectedWord;
            const updated = (data.puzzle.words || []).find(
                w => w.seq === sw.seq && w.direction === sw.direction);
            if (updated) {
                const newText = (updated.answer || '').padEnd(sw.cells.length).slice(0, sw.cells.length);
                sw.initialText = newText;
                sw.currentText = newText;
            }
        }
        renderPuzzleEditor();
    } catch (e) {
        alert('Error saving word');
    }
}

// ---------------------------------------------------------------------------
// Menu actions — Puzzle
// ---------------------------------------------------------------------------

async function _openPuzzleInEditor(name) {
    const openData = await apiFetch('POST', `/api/puzzles/${encodeURIComponent(name)}/open`);
    if (openData.error) {
        throw new Error(openData.error);
    }
    const wn = openData.working_name;
    const puzzleData = await apiFetch('GET', `/api/puzzles/${encodeURIComponent(wn)}`);
    if (puzzleData.error) {
        throw new Error(puzzleData.error);
    }
    AppState.puzzleName        = name;
    AppState.puzzleOriginalName = name;
    AppState.puzzleWorkingName = wn;
    AppState.puzzleData        = puzzleData;
    AppState.puzzleSavedHash   = _hash(puzzleData.puzzle);
    AppState.editingWord       = null;
    AppState.selectedWord      = null;
    AppState.showingStats      = false;
    AppState.showingFillOrder  = false;
    AppState.sidebarTab        = 'clues';
    AppState._statsData        = null;
    AppState._fillOrderData    = null;
    AppState.gridStructureChanged = false;
    showView('editor');
}

async function do_puzzle_open() {
    try {
        const listData = await apiFetch('GET', '/api/puzzles');
        if (listData.error) { alert(`Error: ${listData.error}`); return; }
        const puzzles = (listData.puzzles || []).filter(p => p && !p.startsWith('__wc__'));
        if (puzzles.length === 0) {
            showMessageLine('No saved puzzles found.', 'notice');
            return;
        }
        showPreviewChooser('Open puzzle', puzzles, '/api/puzzles', async (name) => {
            try {
                await _openPuzzleInEditor(name);
            } catch (e) { alert('Error opening puzzle'); }
        });
    } catch (e) {
        alert('Error listing puzzles');
    }
}

async function do_puzzle_import() {
    const fileInput = document.getElementById('acrosslite-file-input');
    // Reset so the same file can be selected again
    fileInput.value = '';
    fileInput.onchange = async (evt) => {
        const file = evt.target.files[0];
        if (!file) return;

        // Pre-populate name from filename (strip .txt extension)
        const defaultName = file.name.replace(/\.txt$/i, '');

        inputBox(
            'Import AcrossLite puzzle',
            '<b>Puzzle name:</b>',
            defaultName,
            async (name) => {
                name = name.trim();
                if (!name) { alert('Puzzle name is required'); return; }

                let content;
                try {
                    content = await file.text();
                } catch (e) {
                    alert('Could not read file');
                    return;
                }

                try {
                    const data = await apiFetch('POST', '/api/import/acrosslite', { name, content });
                    if (data.error) { alert(`Import failed: ${data.error}`); return; }
                    showMessageLine(`Imported "${name}" — opening…`, 'notice');
                    await _openPuzzleInEditor(name);
                } catch (e) {
                    alert(`Import error: ${e.message || e}`);
                }
            }
        );
    };
    fileInput.click();
}

async function do_puzzle_new() {
    inputBox(
        'New puzzle',
        '<b>Puzzle size:</b> <em>(an odd positive integer, e.g. 15)</em>',
        '',
        (sizeVal) => {
            const n = Number(sizeVal);
            if (!sizeVal || isNaN(n))  { alert(sizeVal + ' is not a number'); return; }
            if (n % 2 === 0)           { alert(n + ' is not an odd number'); return; }
            if (n < 1)                 { alert(n + ' is not a positive number'); return; }
            (async () => {
                try {
                    const internalName = '__new__' + Math.random().toString(36).slice(2, 10);
                    const data = await apiFetch('POST', '/api/puzzles', { name: internalName, size: n });
                    if (data.error) { alert(`Error creating puzzle: ${data.error}`); return; }
                    await _openPuzzleInEditor(internalName);
                    AppState.puzzleName         = null;        // no user-facing name yet
                    AppState.puzzleOriginalName = internalName;
                    renderPuzzleEditorLhs();
                } catch (e) { alert('Error creating puzzle'); }
            })();
        }
    );
}

async function do_puzzle_save() {
    const wn   = AppState.puzzleWorkingName;
    const name = AppState.puzzleName;
    if (!name) { do_puzzle_save_as(); return; }
    try {
        await _settlePuzzleEditingBeforeSave();
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(wn)}/copy`, { new_name: name });
        if (data.error) { alert(`Save failed: ${data.error}`); return; }
        AppState.puzzleSavedHash = _hash(AppState.puzzleData.puzzle);
        updateAppBarPuzzleInfo();
        showMessageLine(`Puzzle ${name} saved.`, 'notice');
    } catch (e) { alert('Error saving puzzle'); }
}

async function _listSavedPuzzleNames() {
    const listData = await apiFetch('GET', '/api/puzzles');
    if (listData.error) {
        throw new Error(listData.error);
    }
    return (listData.puzzles || []).filter(p => p && !p.startsWith('__'));
}

async function _savePuzzleAsName(newName) {
    const wn = AppState.puzzleWorkingName;
    const data = await apiFetch('POST',
        `/api/puzzles/${encodeURIComponent(wn)}/copy`, { new_name: newName });
    if (data.error) {
        throw new Error(data.error);
    }
    const oldOriginal = AppState.puzzleOriginalName;
    AppState.puzzleName         = newName;
    AppState.puzzleOriginalName = newName;
    AppState.puzzleSavedHash    = _hash(AppState.puzzleData.puzzle);
    renderPuzzleEditorLhs();
    showMessageLine(`Puzzle ${newName} saved.`, 'notice');
    if (oldOriginal && oldOriginal !== newName) {
        // Clean up the internal __new__ entry now that a real name exists
        try { await apiFetch('DELETE', `/api/puzzles/${encodeURIComponent(oldOriginal)}`); }
        catch (e) { /* ignore */ }
    }
}

async function do_puzzle_save_as() {
    inputBox('Save puzzle as', 'Puzzle name:', AppState.puzzleName || '', async (newName) => {
        if (!newName) return;
        if (!validateUserFacingName('puzzle', newName)) return;
        try {
            await _settlePuzzleEditingBeforeSave();
            await confirmOverwriteIfExists(
                'puzzle',
                newName,
                _listSavedPuzzleNames,
                () => _savePuzzleAsName(newName)
            );
        } catch (e) { alert('Error saving puzzle'); }
    });
}

async function do_puzzle_rename() {
    const currentName = AppState.puzzleName;
    if (!currentName) return;
    inputBox('Rename puzzle', 'New name:', currentName, async (newName) => {
        if (!newName || newName === currentName) return;
        if (!validateUserFacingName('puzzle', newName)) return;
        try {
            const existing = await _listSavedPuzzleNames();
            if (existing.includes(newName)) {
                const confirmed = await new Promise(resolve =>
                    messageBox(`A puzzle named "${newName}" already exists. Overwrite?`,
                        [{ label: 'Overwrite', value: true }, { label: 'Cancel', value: false }],
                        resolve)
                );
                if (!confirmed) return;
            }
            const data = await apiFetch('POST',
                `/api/puzzles/${encodeURIComponent(currentName)}/rename`, { new_name: newName });
            if (data.error) { alert(`Error renaming puzzle: ${data.error}`); return; }
            AppState.puzzleName         = newName;
            AppState.puzzleOriginalName = newName;
            renderPuzzleEditorLhs();
            updateMenu();
            showMessageLine(`Puzzle renamed to ${newName}.`, 'notice');
        } catch (e) { alert('Error renaming puzzle'); }
    });
}

async function _doPuzzleCloseConfirmed() {
    document.removeEventListener('keydown', _peKeydown);
    document.removeEventListener('keydown', _weKeydown);
    const wn           = AppState.puzzleWorkingName;
    const originalName = AppState.puzzleOriginalName;
    const savedName    = AppState.puzzleName;
    AppState.puzzleName         = null;
    AppState.puzzleOriginalName = null;
    AppState.puzzleWorkingName  = null;
    AppState.puzzleData         = null;
    AppState.puzzleSavedHash    = null;
    AppState.editingWord        = null;
    AppState.selectedWord       = null;
    AppState.showingStats       = false;
    AppState.showingFillOrder   = false;
    AppState.sidebarTab         = 'clues';
    AppState._statsData         = null;
    AppState._fillOrderData     = null;
    AppState.gridStructureChanged = false;
    if (wn) {
        try { await apiFetch('DELETE', `/api/puzzles/${encodeURIComponent(wn)}`); }
        catch (e) { /* ignore cleanup errors */ }
    }
    if (!savedName && originalName) {
        // Puzzle was never given a user name — delete the internal __new__ original too
        try { await apiFetch('DELETE', `/api/puzzles/${encodeURIComponent(originalName)}`); }
        catch (e) { /* ignore cleanup errors */ }
    }
    showView('home');
}

async function do_puzzle_close() {
    const isDirty = AppState.puzzleData &&
        _hash(AppState.puzzleData.puzzle) !== AppState.puzzleSavedHash;
    if (isDirty) {
        const name = AppState.puzzleName || '(No name)';
        messageBox(
            'Close puzzle',
            `Puzzle <b>${escapeHtml(name)}</b> has unsaved changes. Close without saving?`,
            null,
            () => _doPuzzleCloseConfirmed()
        );
    } else {
        await _doPuzzleCloseConfirmed();
    }
}

async function do_puzzle_title() {
    const wn = AppState.puzzleWorkingName;
    const current = AppState.puzzleData && AppState.puzzleData.puzzle.title || '';
    inputBox('Set puzzle title', '<b>Puzzle title:</b>', current, async (title) => {
        try {
            const data = await apiFetch('PUT',
                `/api/puzzles/${encodeURIComponent(wn)}/title`, { title });
            if (data.error) { alert(`Error: ${data.error}`); return; }
            const fresh = await apiFetch('GET', `/api/puzzles/${encodeURIComponent(wn)}`);
            if (!fresh.error) { AppState.puzzleData = fresh; renderPuzzleEditorLhs(); }
        } catch (e) { alert('Error setting title'); }
    });
}

async function do_puzzle_stats() {
    const wn = AppState.puzzleWorkingName;
    try {
        await _settlePuzzleEditingBeforeModeSwitch();
        const data = await apiFetch('GET', `/api/puzzles/${encodeURIComponent(wn)}/stats`);
        if (data.error) { alert(`Error: ${data.error}`); return; }
        AppState._statsData       = data;
        AppState.showingFillOrder = false;
        AppState.showingStats     = true;
        AppState.editingWord      = null;
        AppState.sidebarTab       = 'stats';
        renderPuzzleEditorRhs();
    } catch (e) { alert('Error fetching stats'); }
}

async function do_puzzle_fill_order() {
    const wn = AppState.puzzleWorkingName;
    try {
        const data = await apiFetch('GET', `/api/puzzles/${encodeURIComponent(wn)}/fill-order`);
        if (data.error) { alert(`Error: ${data.error}`); return; }
        AppState._fillOrderData   = data;
        AppState.showingStats     = false;
        AppState.showingFillOrder = true;
        AppState.editingWord      = null;
        AppState.sidebarTab       = 'fill-order';
        renderPuzzleEditorRhs();
    } catch (e) { alert('Error fetching fill order'); }
}

function renderStatsPanel(stats) {
    const validText  = stats.valid ? 'Valid' : 'Invalid';
    const validClass = stats.valid ? 'stat-valid' : 'stat-invalid';

    const allErrors = Object.values(stats.errors).flat();
    const errorsHtml = allErrors.length === 0 ? '' :
        `<div class="stat-error-box">${allErrors.map(e => escapeHtml(e)).join('<br>')}</div>`;

    const wlRows = Object.entries(stats.wordlengths)
        .sort((a, b) => Number(b[0]) - Number(a[0]))
        .map(([len, entry]) => {
            const across = (entry.alist || []).join(', ') || '—';
            const down   = (entry.dlist || []).join(', ') || '—';
            return `<tr>
  <td>${len}</td>
  <td style="word-break:break-word">${escapeHtml(across)}</td>
  <td style="word-break:break-word">${escapeHtml(down)}</td>
</tr>`;
        }).join('');

    return `
<div class="stat-cards">
  <div class="stat-card ${validClass}">
    <div class="stat-card-value">${validText}</div>
    <div class="stat-card-label">Validity</div>
  </div>
  <div class="stat-card">
    <div class="stat-card-value">${escapeHtml(stats.size)}</div>
    <div class="stat-card-label">Grid size</div>
  </div>
  <div class="stat-card">
    <div class="stat-card-value">${stats.wordcount}</div>
    <div class="stat-card-label">Words</div>
  </div>
  <div class="stat-card">
    <div class="stat-card-value">${stats.blockcount}</div>
    <div class="stat-card-label">Black cells</div>
  </div>
</div>
${errorsHtml}
<div class="stat-section-title">Word lengths</div>
<table class="stat-table">
  <tr><th>Length</th><th>Across</th><th>Down</th></tr>
  ${wlRows}
</table>`;
}

function renderFillOrderPanel(data) {
    const rows = (data.fill_priority || []).map(item => {
        const countLabel = `${item.candidate_count} candidate${item.candidate_count === 1 ? '' : 's'}`;
        return `<tr onclick="_openWordFromFillOrder(${item.seq},'${item.direction}')">
  <td style="white-space:nowrap"><a onclick="return false">${escapeHtml(item.label)}</a></td>
  <td style="font-family:var(--font-mono)">${escapeHtml(item.pattern || '')}</td>
  <td style="white-space:nowrap">${escapeHtml(countLabel)}</td>
  <td>${escapeHtml(item.reason || '')}</td>
</tr>`;
    }).join('');
    const body = rows
        ? `<table class="fill-table">
    <thead><tr><th>Slot</th><th>Pattern</th><th>Candidates</th><th>Reason</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`
        : `<div class="sidebar-empty">No fill-order data yet.</div>`;

    return `
<p class="fill-intro">Best slots to fill next, ranked by candidate count. Click a row to open the word editor for that slot.</p>
${body}`;
}

function closeStatsPanel() {
    AppState.showingStats = false;
    AppState.sidebarTab   = 'clues';
    renderPuzzleEditorRhs();
}

function _openWordFromFillOrder(seq, dir) {
    selectWord(seq, dir);
    openWordEditor(seq, dir);
}

function closeFillOrderPanel() {
    AppState.showingFillOrder = false;
    AppState.sidebarTab       = 'clues';
    renderPuzzleEditorRhs();
}

async function _refreshPuzzleStatsIfVisible() {
    if (AppState.sidebarTab !== 'stats' || !AppState.puzzleWorkingName) return;
    try {
        const data = await apiFetch('GET',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/stats`);
        if (data.error) return;
        AppState._statsData = data;
        renderPuzzleEditorRhs();
    } catch (e) {
        // Keep the current panel if the refresh fails.
    }
}

async function _refreshFillOrderIfVisible() {
    if (AppState.sidebarTab !== 'fill-order' || !AppState.puzzleWorkingName || _currentEditorMode() !== 'puzzle') return;
    try {
        const data = await apiFetch('GET',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/fill-order`);
        if (data.error) return;
        AppState._fillOrderData = data;
        renderPuzzleEditorRhs();
    } catch (e) {
        // Keep the current panel if the refresh fails.
    }
}

async function _applyGridModeUpdate(data) {
    AppState.puzzleData   = data;
    AppState.editingWord  = null;
    AppState.selectedWord = null;
    AppState.gridStructureChanged = true;
    renderPuzzleEditor();
    await _refreshPuzzleStatsIfVisible();
    await _refreshFillOrderIfVisible();
}

async function handleGridModeClick(event) {
    const svg = document.getElementById('puzzle-svg');
    const pd  = AppState.puzzleData;
    if (!svg || !pd || _currentEditorMode() !== 'grid') return;
    const rect = svg.getBoundingClientRect();
    const x    = event.clientX - rect.left;
    const y    = event.clientY - rect.top;
    const n    = pd.grid.size;
    const r    = Math.floor(y / BOXSIZE);
    const c    = Math.floor(x / BOXSIZE);
    if (r < 0 || r >= n || c < 0 || c >= n) return;
    try {
        const data = await apiFetch('PUT',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/grid/cells/${r}/${c}`);
        if (data.error) { alert(`Error updating grid: ${data.error}`); return; }
        await _applyGridModeUpdate(data);
    } catch (e) {
        alert('Error updating grid');
    }
}

function _updatePuzzleUndoRedo() {
    const pd      = AppState.puzzleData;
    const mode    = _currentEditorMode();
    const editing = !!AppState.editingWord;
    const ub      = document.getElementById('puzzle-undo-btn');
    const rb      = document.getElementById('puzzle-redo-btn');
    if (!ub || !rb) return;
    const canUndo = !pd ? false : (mode === 'grid' ? !!pd.grid_can_undo : !!pd.puzzle_can_undo);
    const canRedo = !pd ? false : (mode === 'grid' ? !!pd.grid_can_redo : !!pd.puzzle_can_redo);
    ub.classList.toggle('w3-disabled', editing || !canUndo);
    rb.classList.toggle('w3-disabled', editing || !canRedo);
    _updatePuzzleToolbar();
}

function _updatePuzzleToolbar() {
    const mode = _currentEditorMode();
    const eb = document.getElementById('puzzle-editword-btn');
    if (!eb) return;
    eb.classList.toggle('w3-disabled', mode !== 'puzzle' || !AppState.selectedWord || !!AppState.editingWord);
}

async function do_puzzle_undo() { await _puzzleUndoRedo('undo'); }
async function do_puzzle_redo() { await _puzzleUndoRedo('redo'); }

async function _puzzleUndoRedo(action) {
    if (_currentEditorMode() === 'puzzle') {
        await _peCommitWord();
    }
    const wn = AppState.puzzleWorkingName;
    const path = _currentEditorMode() === 'grid'
        ? `/api/puzzles/${encodeURIComponent(wn)}/grid/${action}`
        : `/api/puzzles/${encodeURIComponent(wn)}/${action}`;
    try {
        const data = await apiFetch('POST', path);
        if (data.error) { alert(`${action} failed: ${data.error}`); return; }
        AppState.puzzleData       = data;
        AppState.editingWord      = null;
        AppState.selectedWord     = null;
        AppState.showingStats     = false;
        AppState.showingFillOrder = false;
        AppState.sidebarTab       = 'clues';
        AppState._statsData       = null;
        AppState._fillOrderData   = null;
        renderPuzzleEditor();
    } catch (e) { alert(`Error during ${action}`); }
}

async function _settlePuzzleEditingBeforeModeSwitch() {
    if (AppState.editingWord) {
        await doWordEditOK();
        if (AppState.editingWord) {
            throw new Error('Could not save current word edit');
        }
        return;
    }
    if (AppState.selectedWord) {
        await _peCommitWord();
    }
}

async function _settlePuzzleEditingBeforeSave() {
    if (_currentEditorMode() !== 'puzzle') return;
    await _settlePuzzleEditingBeforeModeSwitch();
}

async function _switchToGridModeConfirmed() {
    try {
        await _settlePuzzleEditingBeforeModeSwitch();
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/mode/grid`);
        if (data.error) { alert(`Error switching modes: ${data.error}`); return; }
        AppState.puzzleData       = data;
        AppState.editingWord      = null;
        AppState.selectedWord     = null;
        AppState.showingStats     = false;
        AppState.showingFillOrder = false;
        AppState.sidebarTab       = 'grid';
        AppState._statsData       = null;
        AppState._fillOrderData   = null;
        renderPuzzleEditor();
    } catch (e) { alert('Error switching to Grid mode'); }
}

async function do_switch_to_grid_mode() {
    if (!AppState.puzzleWorkingName || _currentEditorMode() === 'grid') return;
    messageBox(
        'Modify grid',
        'Are you sure you want to modify the grid?',
        null,
        async () => _switchToGridModeConfirmed()
    );
}

async function do_switch_to_puzzle_mode() {
    if (!AppState.puzzleWorkingName || _currentEditorMode() === 'puzzle') return;
    try {
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/mode/puzzle`);
        if (data.error) { alert(`Error switching modes: ${data.error}`); return; }
        const hadGridStructureChange = AppState.gridStructureChanged;
        AppState.puzzleData   = data;
        AppState.editingWord  = null;
        AppState.selectedWord     = null;
        AppState.showingStats     = false;
        AppState.showingFillOrder = false;
        AppState.sidebarTab       = 'clues';
        AppState._statsData       = null;
        AppState._fillOrderData   = null;
        AppState.gridStructureChanged = false;
        renderPuzzleEditor();
        if (hadGridStructureChange) {
            showMessageLine(
                'Back in Puzzle mode. Review recomputed entries and any clues that were cleared.',
                'notice'
            );
        }
    } catch (e) { alert('Error switching to Puzzle mode'); }
}

async function do_puzzle_rotate_grid() {
    if (!AppState.puzzleWorkingName || _currentEditorMode() !== 'grid') return;
    try {
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/grid/rotate`);
        if (data.error) { alert(`Error rotating grid: ${data.error}`); return; }
        await _applyGridModeUpdate(data);
    } catch (e) { alert('Error rotating grid'); }
}

async function do_puzzle_generate_grid() {
    if (!AppState.puzzleWorkingName || _currentEditorMode() !== 'grid') return;
    const btn = document.getElementById('puzzle-generate-btn');
    if (btn) btn.classList.add('w3-disabled');
    try {
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/grid/generate`);
        if (data.notice) { showMessageLine(data.notice, 'notice'); return; }
        if (data.error) { showMessageLine(`Error generating grid: ${data.error}`, 'error'); return; }
        await _applyGridModeUpdate(data);
    } catch (e) { showMessageLine('Error generating grid', 'error'); }
    finally {
        if (btn) btn.classList.remove('w3-disabled');
    }
}

async function do_puzzle_delete() {
    try {
        const puzzles = await _listSavedPuzzleNames();
        if (puzzles.length === 0) {
            showMessageLine('No saved puzzles found.', 'notice');
            return;
        }
        showPreviewChooser('Delete puzzle', puzzles, '/api/puzzles', async (name) => {
            messageBox(
                'Delete puzzle',
                `Are you sure you want to delete puzzle <b>'${escapeHtml(name)}'</b>?`,
                null,
                async () => {
                    try {
                        const data = await apiFetch('DELETE', `/api/puzzles/${encodeURIComponent(name)}`);
                        if (data && data.error) { alert(`Error deleting puzzle: ${data.error}`); return; }
                        if (AppState.puzzleName === name) {
                            await _doPuzzleCloseConfirmed();
                            return;
                        }
                        showMessageLine(`Puzzle ${name} deleted.`, 'notice');
                    } catch (e) { alert('Error deleting puzzle'); }
                }
            );
        });
    } catch (e) {
        alert('Error listing puzzles');
    }
}

// ---------------------------------------------------------------------------
// Menu actions — Export
// ---------------------------------------------------------------------------

async function _downloadExport(name, format) {
    const endpointMap = { puz: 'acrosslite', xml: 'xml', nyt: 'nytimes', solver: 'solver-pdf' };
    const filenameMap = { puz: `acrosslite-${name}.txt`, xml: `${name}.xml`, nyt: `nytimes-${name}.pdf`, solver: `${name}-solver.pdf` };
    const labelMap  = { puz: 'Across Lite', xml: 'Crossword Compiler XML', nyt: 'New York Times', solver: 'Solver PDF' };
    const endpoint = endpointMap[format];
    const filename = filenameMap[format];
    try {
        const resp = await fetch(`/api/export/puzzles/${encodeURIComponent(name)}/${endpoint}`);
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            showMessageLine(err.error || `Export failed: HTTP ${resp.status}`, 'error');
            return;
        }
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showMessageLine(`Exported "${name}" as ${labelMap[format]}: ${filename}`, 'notice');
    } catch (e) {
        showMessageLine('Export request failed.', 'error');
    }
}

async function do_export(format) {
    if (AppState.view === 'editor' && AppState.puzzleName) {
        await _downloadExport(AppState.puzzleName, format);
    } else {
        try {
            const listData = await apiFetch('GET', '/api/puzzles');
            if (listData.error) { alert(`Error: ${listData.error}`); return; }
            const puzzles = (listData.puzzles || []).filter(p => p && !p.startsWith('__wc__'));
            if (puzzles.length === 0) {
                showMessageLine('No saved puzzles found.', 'notice');
                return;
            }
            showPreviewChooser('Choose a puzzle to export', puzzles, '/api/puzzles', async (name) => {
                await _downloadExport(name, format);
            });
        } catch (e) {
            alert('Error listing puzzles');
        }
    }
}

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const cfg = await (await fetch('/api/config')).json();
        if (cfg.message_line_timeout_ms != null) {
            MESSAGE_LINE_TIMEOUT_MS = cfg.message_line_timeout_ms;
        }
    } catch (e) { /* use default */ }

    positionMessageLine();
    window.addEventListener('scroll', positionMessageLine, { passive: true });
    window.addEventListener('resize', positionMessageLine);
    showView('home');
});
