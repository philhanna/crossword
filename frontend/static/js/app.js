// Crossword Puzzle Editor — main application script

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const BOXSIZE = 32;
const MESSAGE_LINE_TIMEOUT_MS = 3000;

// ---------------------------------------------------------------------------
// Application state
// ---------------------------------------------------------------------------

const AppState = {
    view: 'home',            // 'home' | 'editor'
    puzzleName: null,        // name of currently-open puzzle (original)
    puzzleWorkingName: null, // working copy name (e.g. '__wc__a1b2c3d4')
    puzzleData: null,        // response from GET /api/puzzles/{workingName}
    puzzleSavedHash: null,   // checksum of puzzle at last open/save
    editingWord: null,       // null | {seq, direction, cells, answer, clue}
    selectedWord: null,      // null | {seq, direction, cells, initialText, currentText}
    showingStats: false,     // true = puzzle editor RHS shows stats panel
    _statsData: null,        // cached puzzle stats response
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
    } else {
        mbOk.onclick = null;
        mbOk.setAttribute('href', ok);
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
    'menu-puzzle-save', 'menu-puzzle-save-as', 'menu-puzzle-close', 'menu-puzzle-delete',
    'menu-publish-acrosslite', 'menu-publish-cwcompiler', 'menu-publish-nytimes',
];

function menuEnable(id)  { document.getElementById(id).classList.remove('w3-disabled'); }
function menuDisable(id) { document.getElementById(id).classList.add('w3-disabled'); }

function updateMenu() {
    const home   = AppState.view === 'home';
    const editor = AppState.view === 'editor';

    home   ? menuEnable('menu-puzzle-new')     : menuDisable('menu-puzzle-new');
    home   ? menuEnable('menu-puzzle-open')    : menuDisable('menu-puzzle-open');
    editor ? menuEnable('menu-puzzle-save')    : menuDisable('menu-puzzle-save');
    editor ? menuEnable('menu-puzzle-save-as') : menuDisable('menu-puzzle-save-as');
    editor ? menuEnable('menu-puzzle-close')   : menuDisable('menu-puzzle-close');
    editor ? menuEnable('menu-puzzle-delete')  : menuDisable('menu-puzzle-delete');

    menuEnable('menu-publish-acrosslite');
    menuEnable('menu-publish-cwcompiler');
    menuEnable('menu-publish-nytimes');
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
        case 'home':   renderHome();   break;
        case 'editor': renderPuzzleEditor(); break;
        default:
            document.getElementById('lhs').innerHTML =
                `<div class="w3-container"><p>Unknown view: ${view}</p></div>`;
    }
}

function renderHome() {
    document.getElementById('lhs').innerHTML =
        '<div class="w3-container"><p>Use the Puzzle menu to create or open a crossword for editing.</p></div>';
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
        `<svg xmlns="http://www.w3.org/2000/svg" id="grid-svg" ` +
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
                `fill="${black ? 'black' : 'white'}" stroke="#999" stroke-width="0.5"/>`
            );
            if (!black && nums[idx] !== null) {
                parts.push(
                    `<text x="${x + 2}" y="${y + 10}" ` +
                    `font-size="9" font-family="sans-serif">${nums[idx]}</text>`
                );
            }
        }
    }
    parts.push(
        `<rect x="0" y="0" width="${totalPx - 1}" height="${totalPx - 1}" ` +
        `fill="none" stroke="black" stroke-width="2"/>`
    );
    parts.push('</svg>');
    return parts.join('');
}

// ---------------------------------------------------------------------------
// Grid editor — rendering and click handling
// ---------------------------------------------------------------------------

function renderGridEditor() {
    const gd   = AppState.gridData;
    const name = AppState.gridOriginalName || '(untitled)';

    const toolbar = `
<div class="w3-container w3-margin-bottom" style="height:36px">
  <div class="w3-bar w3-border">
        <a class="w3-bar-item w3-button crosstb" onclick="do_grid_save()">
            <i class="material-icons crosstb-icon">save</i><span>Save</span></a>
        <a class="w3-bar-item w3-button crosstb" onclick="do_grid_save_as()">
            <i class="material-icons crosstb-icon">save_alt</i><span>Save As</span></a>
        <a class="w3-bar-item w3-button crosstb" onclick="do_grid_close()">
            <i class="material-icons crosstb-icon">close</i><span>Close</span></a>
    <a id="grid-undo-btn" class="w3-bar-item w3-button crosstb" onclick="do_grid_undo_action()">
      <i class="material-icons crosstb-icon">undo</i><span>Undo</span></a>
    <a id="grid-redo-btn" class="w3-bar-item w3-button crosstb" onclick="do_grid_redo_action()">
      <i class="material-icons crosstb-icon">redo</i><span>Redo</span></a>
    <a class="w3-bar-item w3-button crosstb" onclick="do_grid_info_action()">
      <i class="material-icons crosstb-icon">info</i><span>Info</span></a>
        <a class="w3-bar-item w3-button crosstb" onclick="do_grid_rotate_action()">
            <i class="material-icons crosstb-icon">rotate_right</i><span>Rotate</span></a>
  </div>
</div>`;

    document.getElementById('lhs').innerHTML = `
<div class="w3-container">
  <h3>Editing grid <b>${escapeHtml(name)}</b></h3>
</div>
${toolbar}
<div id="grid-svg-container" class="w3-container" style="padding-top:4px">
  ${gd ? buildGridSvg(gd.cells, gd.size) : ''}
</div>
<div class="w3-container w3-text-gray" style="margin-top:8px;font-style:italic">
  Click to toggle black cells
</div>`;

    renderGridEditorRhs();

    const svg = document.getElementById('grid-svg');
    if (svg) svg.addEventListener('click', handleGridClick);
    _updateGridUndoRedo();
}

async function handleGridClick(event) {
    const svg = document.getElementById('grid-svg');
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const x    = event.clientX - rect.left;
    const y    = event.clientY - rect.top;
    const n    = AppState.gridData.size;
    const r    = Math.floor(y / BOXSIZE);  // 0-indexed for API
    const c    = Math.floor(x / BOXSIZE);
    if (r < 0 || r >= n || c < 0 || c >= n) return;
    const wn   = AppState.gridWorkingName;
    try {
        const data = await apiFetch('PUT',
            `/api/grids/${encodeURIComponent(wn)}/cells/${r}/${c}`);
        if (data.error) { alert(`Error: ${data.error}`); return; }
        AppState.gridData = data;
        const container = document.getElementById('grid-svg-container');
        if (container) {
            container.innerHTML = buildGridSvg(data.cells, data.size);
            document.getElementById('grid-svg').addEventListener('click', handleGridClick);
        }
        _updateGridUndoRedo();
    } catch (e) {
        alert('Error toggling cell');
    }
}

async function _gridAction(method, path) {
    const wn = AppState.gridWorkingName;
    try {
        const data = await apiFetch(method, `/api/grids/${encodeURIComponent(wn)}${path}`);
        if (data.error) { alert(`Error: ${data.error}`); return; }
        AppState.gridData = data;
        const container = document.getElementById('grid-svg-container');
        if (container) {
            container.innerHTML = buildGridSvg(data.cells, data.size);
            document.getElementById('grid-svg').addEventListener('click', handleGridClick);
        }
        _updateGridUndoRedo();
    } catch (e) { alert('Error performing grid action'); }
}

function _updateGridUndoRedo() {
    const gd = AppState.gridData;
    const ub = document.getElementById('grid-undo-btn');
    const rb = document.getElementById('grid-redo-btn');
    if (!ub || !rb) return;
    ub.classList.toggle('w3-disabled', !gd || !gd.can_undo);
    rb.classList.toggle('w3-disabled', !gd || !gd.can_redo);
}

async function do_grid_rotate_action() { await _gridAction('POST', '/rotate'); }
async function do_grid_undo_action()   { await _gridAction('POST', '/undo'); }
async function do_grid_redo_action()   { await _gridAction('POST', '/redo'); }

function renderGridEditorRhs() {
    const html = AppState.showingGridStats && AppState._gridStatsData
        ? renderGridStatsPanel(AppState._gridStatsData)
        : '';
    document.getElementById('rhs').innerHTML = html;
}

async function do_grid_info_action() {
    const wn = AppState.gridWorkingName;
    if (!wn) return;
    try {
        const data = await apiFetch('GET', `/api/grids/${encodeURIComponent(wn)}/stats`);
        if (data.error) { alert(`Error: ${data.error}`); return; }
        AppState._gridStatsData   = data;
        AppState.showingGridStats = true;
        renderGridEditorRhs();
    } catch (e) { alert('Error fetching grid stats'); }
}

function renderGridStatsPanel(stats) {
    const validColor = stats.valid ? 'w3-text-green' : 'w3-text-red';
    const validText  = stats.valid ? 'Valid' : 'Invalid';

    let errorsHtml;
    const allErrors = Object.values(stats.errors).flat();
    if (allErrors.length === 0) {
        errorsHtml = 'None';
    } else {
        errorsHtml = '<ul style="list-style-type:none;margin:0;padding:0">' +
            allErrors.map(e => `<li style="color:#cc0000">${escapeHtml(e)}</li>`).join('') +
            '</ul>';
    }

    const wlRows = Object.entries(stats.wordlengths)
        .sort((a, b) => Number(b[0]) - Number(a[0]))
        .map(([len, entry]) => {
            const across = (entry.alist || []).join(', ') || '(none)';
            const down   = (entry.dlist || []).join(', ') || '(none)';
            return `<tr>
  <td style="border:1px solid #ccc;padding:3px 8px">${len}</td>
  <td style="border:1px solid #ccc;padding:3px 8px;word-break:break-word">${escapeHtml(across)}</td>
  <td style="border:1px solid #ccc;padding:3px 8px;word-break:break-word">${escapeHtml(down)}</td>
</tr>`;
        }).join('');

    function row(label, value) {
        return `<div class="w3-section w3-cell-row">
  <div class="w3-cell" style="width:30%"><b>${label}</b></div>
  <div class="w3-cell">${value}</div>
</div>`;
    }

    return `
<div class="w3-margin-right">
  <header class="w3-container w3-blue-gray" style="padding:7px;position:relative">
    <h3>Grid statistics</h3>
    <span class="w3-button w3-xlarge w3-hover-red"
          style="position:absolute;top:0;right:0"
          onclick="closeGridStatsPanel()">&times;</span>
  </header>
  <div class="w3-card-4">
    <div class="w3-container" style="padding-bottom:12px">
      ${row('Valid:', `<span class="${validColor}"><b>${validText}</b></span>`)}
      ${row('Errors:', errorsHtml)}
      ${row('Size:', escapeHtml(stats.size))}
      ${row('Word count:', stats.wordcount)}
      ${row('Black cells:', stats.blockcount)}
      <div class="w3-section">
        <table class="w3-table" style="border-collapse:collapse;width:auto">
          <tr>
            <th style="border:1px solid #ccc;padding:3px 8px">Word length</th>
            <th style="border:1px solid #ccc;padding:3px 8px">Across</th>
            <th style="border:1px solid #ccc;padding:3px 8px">Down</th>
          </tr>
          ${wlRows}
        </table>
      </div>
    </div>
  </div>
</div>`;
}

function closeGridStatsPanel() {
    AppState.showingGridStats = false;
    renderGridEditorRhs();
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
        `<svg xmlns="http://www.w3.org/2000/svg" id="puzzle-svg" ` +
        `width="${totalPx}" height="${totalPx}" style="cursor:pointer;display:block">`,
    ];

    for (let r = 1; r <= n; r++) {
        for (let c = 1; c <= n; c++) {
            const idx   = (r - 1) * n + (c - 1);
            const x     = (c - 1) * BOXSIZE;
            const y     = (r - 1) * BOXSIZE;
            const black = blackCells[idx];

            let fill;
            if (black) {
                fill = 'black';
            } else if (editState) {
                if (idx === cursorFlatIdx)      fill = '#4fa3e0';  // cursor cell
                else if (wordCellSet.has(idx))  fill = '#c8e6fa';  // other word cells
                else                            fill = '#e8e8e8';  // dimmed
            } else {
                fill = 'white';
            }

            parts.push(
                `<rect x="${x}" y="${y}" width="${BOXSIZE}" height="${BOXSIZE}" ` +
                `fill="${fill}" stroke="#999" stroke-width="0.5"/>`
            );

            if (!black) {
                const cd = puzzleCells[String(idx)] || {};
                if (cd.number !== undefined) {
                    parts.push(
                        `<text x="${x + 2}" y="${y + 10}" ` +
                        `font-size="9" font-family="sans-serif">${cd.number}</text>`
                    );
                }
                // In edit mode show weText letters for word cells; otherwise use puzzle data
                const letter = (editState && wordCellSet.has(idx))
                    ? (wordLetterMap[idx] || '')
                    : (cd.letter || '');
                if (letter) {
                    parts.push(
                        `<text x="${x + BOXSIZE / 2}" y="${y + BOXSIZE - 6}" ` +
                        `font-size="15" font-family="sans-serif" ` +
                        `text-anchor="middle">${escapeHtml(letter)}</text>`
                    );
                }
            }
        }
    }

    // Outer border
    parts.push(
        `<rect x="0" y="0" width="${totalPx - 1}" height="${totalPx - 1}" ` +
        `fill="none" stroke="black" stroke-width="2"/>`
    );

    // Cursor indicator: bold inner border on cursor cell
    if (editState && cursorFlatIdx >= 0) {
        const cc_ = (cursorFlatIdx % n);
        const cr_ = Math.floor(cursorFlatIdx / n);
        parts.push(
            `<rect x="${cc_ * BOXSIZE + 2}" y="${cr_ * BOXSIZE + 2}" ` +
            `width="${BOXSIZE - 4}" height="${BOXSIZE - 4}" ` +
            `fill="none" stroke="#1565c0" stroke-width="2"/>`
        );
    }

    parts.push('</svg>');
    return parts.join('');
}

// ---------------------------------------------------------------------------
// Puzzle editor — click handling (single = across, double = down)
// ---------------------------------------------------------------------------

let _clickState   = 0;
let _clickTimeout = null;
let _clickEvent   = null;
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

let _peCursorIdx = 0;  // cursor position within selectedWord.cells

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
    if (AppState.editingWord) return;  // word editor open — ignore grid clicks
    _clickEvent = event;
    if (_clickState === 0) {
        _clickState = 1;
        _clickTimeout = setTimeout(() => {
            _clickState = 0;
            puzzleClickAt(_clickEvent, 'across');
        }, CLICK_DELAY);
    } else {
        _clickState = 0;
        clearTimeout(_clickTimeout);
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
    AppState.showingStats = false;
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

function _modeButtonClass(mode) {
    return _currentEditorMode() === mode ? 'w3-blue-gray' : 'w3-light-gray';
}

function _gridChangeMessage() {
    return 'Grid updated. Entries were recomputed and affected clues were cleared.';
}

function renderPuzzleEditor() {
    document.removeEventListener('keydown', _peKeydown);
    if (_currentEditorMode() === 'puzzle') {
        document.addEventListener('keydown', _peKeydown);
    }
    renderPuzzleEditorLhs();
    renderPuzzleEditorRhs();
}

function renderPuzzleEditorLhs() {
    const pd    = AppState.puzzleData;
    const name  = AppState.puzzleName || '(untitled)';
    const title = pd && pd.puzzle.title ? `: &ldquo;${escapeHtml(pd.puzzle.title)}&rdquo;` : '';
    const mode  = _currentEditorMode();

    const modeToolbar = `
<div class="w3-container w3-margin-bottom" style="height:36px">
  <div class="w3-bar w3-border">
    <a class="w3-bar-item w3-button crosstb ${_modeButtonClass('grid')}" onclick="do_switch_to_grid_mode()">
      <i class="material-icons crosstb-icon">grid_on</i><span>Grid Mode</span></a>
    <a class="w3-bar-item w3-button crosstb ${_modeButtonClass('puzzle')}" onclick="do_switch_to_puzzle_mode()">
      <i class="material-icons crosstb-icon">edit_note</i><span>Puzzle Mode</span></a>
  </div>
</div>`;

    const toolbar = mode === 'grid' ? `
<div class="w3-container w3-margin-bottom" style="height:36px">
  <div class="w3-bar w3-border">
    <a class="w3-bar-item w3-button crosstb" onclick="do_puzzle_save()">
      <i class="material-icons crosstb-icon">save</i><span>Save</span></a>
    <a class="w3-bar-item w3-button crosstb" onclick="do_puzzle_save_as()">
      <i class="material-icons crosstb-icon">save_alt</i><span>Save As</span></a>
    <a class="w3-bar-item w3-button crosstb" onclick="do_puzzle_close()">
      <i class="material-icons crosstb-icon">close</i><span>Close</span></a>
    <a id="puzzle-undo-btn" class="w3-bar-item w3-button crosstb" onclick="do_puzzle_undo()">
      <i class="material-icons crosstb-icon">undo</i><span>Undo</span></a>
    <a id="puzzle-redo-btn" class="w3-bar-item w3-button crosstb" onclick="do_puzzle_redo()">
      <i class="material-icons crosstb-icon">redo</i><span>Redo</span></a>
    <a class="w3-bar-item w3-button crosstb" onclick="do_puzzle_rotate_grid()">
      <i class="material-icons crosstb-icon">rotate_right</i><span>Rotate</span></a>
    <a class="w3-bar-item w3-button crosstb" onclick="do_puzzle_stats()">
      <i class="material-icons crosstb-icon">info</i><span>Info</span></a>
  </div>
</div>` : `
<div class="w3-container w3-margin-bottom" style="height:36px">
  <div class="w3-bar w3-border">
    <a class="w3-bar-item w3-button crosstb" onclick="do_puzzle_save()">
      <i class="material-icons crosstb-icon">save</i><span>Save</span></a>
    <a class="w3-bar-item w3-button crosstb" onclick="do_puzzle_save_as()">
      <i class="material-icons crosstb-icon">save_alt</i><span>Save As</span></a>
    <a class="w3-bar-item w3-button crosstb" onclick="do_puzzle_close()">
      <i class="material-icons crosstb-icon">close</i><span>Close</span></a>
    <a id="puzzle-undo-btn" class="w3-bar-item w3-button crosstb" onclick="do_puzzle_undo()">
      <i class="material-icons crosstb-icon">undo</i><span>Undo</span></a>
    <a id="puzzle-redo-btn" class="w3-bar-item w3-button crosstb" onclick="do_puzzle_redo()">
      <i class="material-icons crosstb-icon">redo</i><span>Redo</span></a>
    <a id="puzzle-editword-btn" class="w3-bar-item w3-button crosstb" onclick="do_puzzle_edit_word()">
      <i class="material-icons crosstb-icon">edit</i><span>Edit word</span></a>
    <a class="w3-bar-item w3-button crosstb" onclick="do_puzzle_stats()">
      <i class="material-icons crosstb-icon">info</i><span>Info</span></a>
    <a class="w3-bar-item w3-button crosstb" onclick="do_puzzle_title()">
      <i class="material-icons crosstb-icon">title</i><span>Title</span></a>
  </div>
</div>`;

    const ew  = AppState.editingWord;
    const sw  = AppState.selectedWord;
    const editState = mode === 'puzzle' && ew
        ? { cells: ew.cells, cursorIdx: _weCursorIdx, text: ew.answer || '' }
        : mode === 'puzzle' && sw
        ? { cells: sw.cells, cursorIdx: _peCursorIdx, text: sw.currentText }
        : null;
    const clickHelp = mode === 'grid'
        ? '<div class="w3-container w3-text-gray" style="margin-top:8px;font-style:italic">Click cells to toggle black squares.</div>'
        : '';

    document.getElementById('lhs').innerHTML = `
<div class="w3-container">
  <h3>Editing puzzle <b>${escapeHtml(name)}</b>${title}</h3>
</div>
${modeToolbar}
${toolbar}
<div id="puzzle-svg-container" class="w3-container" style="padding-top:4px">
  ${pd ? buildPuzzleSvg(pd, editState) : ''}
</div>
${clickHelp}`;

    const svg = document.getElementById('puzzle-svg');
    if (svg && mode === 'puzzle') svg.addEventListener('click', handlePuzzleClick);
    if (svg && mode === 'grid') svg.addEventListener('click', handleGridModeClick);
    _updatePuzzleUndoRedo();
}

function renderPuzzleEditorRhs() {
    const mode = _currentEditorMode();
    let html;
    if (mode === 'grid') {
        html = AppState.showingStats && AppState._statsData
            ? renderStatsPanel(AppState._statsData)
            : renderGridModePanel();
    } else if (AppState.editingWord) {
        html = renderWordEditorPanel();
    } else if (AppState.showingStats) {
        html = AppState._statsData ? renderStatsPanel(AppState._statsData) : '';
    } else {
        html = renderClues();
    }
    document.getElementById('rhs').innerHTML = html;
}

function renderGridModePanel() {
    return `
<div class="w3-margin-right">
  <header class="w3-container w3-blue-gray" style="padding:7px">
    <h3>Grid Mode</h3>
  </header>
  <div class="w3-card-4">
    <div class="w3-container" style="padding-bottom:12px">
      <p>Click any cell in the grid to toggle it between white and black.</p>
      <p>Use <b>Rotate</b> from the toolbar if you want to rotate the grid.</p>
      <p>Affected entries are recomputed immediately, with affected clues cleared automatically.</p>
    </div>
  </div>
</div>`;
}

function renderClues() {
    if (!AppState.puzzleData) return '';
    const words = AppState.puzzleData.puzzle.words;
    const across = words.filter(w => w.direction === 'across').sort((a, b) => a.seq - b.seq);
    const down   = words.filter(w => w.direction === 'down').sort((a, b) => a.seq - b.seq);
    const selected = AppState.selectedWord;

    function listHtml(wordList, direction, colorClass) {
        const items = wordList.map(w =>
            `<li class="${selected && selected.seq === w.seq && selected.direction === direction ? 'w3-blue-gray' : ''}">` +
            `<a onclick="selectWord(${w.seq}, '${direction}');return false;">${w.seq}. ${escapeHtml(w.clue || '(no clue)')}</a> ` +
            `<span class="w3-small"><a onclick="do_puzzle_edit_word(${w.seq}, '${direction}');return false;">edit</a></span>` +
            `</li>`
        ).join('');
        return `<ul class="w3-ul w3-card w3-border w3-hoverable ${colorClass} clue-list">${items}</ul>`;
    }

    return `
<div class="w3-cell-row">
  <div class="w3-cell" style="width:50%">
    <div class="w3-center w3-margin-bottom"><b>Across</b></div>
    ${listHtml(across, 'across', 'w3-pale-yellow')}
  </div>
  <div class="w3-cell" style="width:50%">
    <div class="w3-center w3-margin-bottom"><b>Down</b></div>
    ${listHtml(down, 'down', 'w3-pale-green')}
  </div>
</div>`;
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

    return `
<div id="we-dialog" class="w3-margin-right">
  <div class="w3-section">
    <header class="w3-container w3-blue-gray" style="padding:7px;position:relative">
      <h3><span>${ew.seq} ${dirLabel} (${len} letters)</span></h3>
      <span class="w3-button w3-xlarge w3-hover-red"
            style="position:absolute;top:0;right:0"
            onclick="closeWordEditor()">&times;</span>
    </header>

    <div class="w3-card-4">
      <div class="w3-section" style="padding:0 8px 8px 8px">

        <!-- Word text input -->
        <p style="width:95%;margin:8px 0 0 0">
          <label>Word:</label>
          <input class="w3-input w3-border" id="we-text" type="text"
                 maxlength="${len}" value="${escapeHtml(text.replace(/ /g, '.'))}"
                 style="font-family:monospace;letter-spacing:0.2em;text-transform:uppercase"/>
        </p>

        <!-- Clue input -->
        <p style="width:95%;margin:8px 0 0 0">
          <label>Clue:</label>
          <input class="w3-input w3-border" id="we-clue" type="text"
                 value="${escapeHtml(clue)}"
                 onfocus="_weClueBeforeEdit=this.value"
                 onblur="_weOnClueBlur(this.value)"/>
        </p>

        <!-- Suggestions section -->
        <div style="margin-top:12px">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">
            <button class="w3-button w3-small w3-round w3-light-gray crosstb" type="button"
                    onclick="doWordSuggestFetch()">
              <i class="material-icons crosstb-icon">search</i>
              <span>Suggest</span>
            </button>
            <label style="margin:0;cursor:pointer;font-size:small">
              <input type="checkbox" id="we-constrained" checked> Use constraints
            </label>
          </div>
          <div id="we-match" style="display:none;font-size:small;color:#666;margin-bottom:4px"></div>
          <ul id="we-suggestion-list"
              style="list-style:none;margin:0;padding:0;max-height:220px;overflow-y:auto;
                     border:1px solid #ddd;display:none"></ul>
          <div id="we-pagination"
               style="display:none;margin-top:4px;font-size:small;
                      align-items:center;gap:8px">
            <button class="w3-button w3-small w3-border" type="button"
                    id="we-page-prev" onclick="wePagePrev()">&#9664;</button>
            <span id="we-page-label" style="flex:1;text-align:center"></span>
            <button class="w3-button w3-small w3-border" type="button"
                    id="we-page-next" onclick="wePageNext()">&#9654;</button>
          </div>
        </div>

        <!-- Show constraints / Reset row -->
        <div style="margin-top:14px;display:flex;gap:6px">
          <button class="w3-button w3-border w3-round w3-small w3-light-gray"
                  id="we-constraints-btn" type="button" onclick="doWordConstraints()">
            <i class="material-icons" style="font-size:14px;vertical-align:middle">assignment</i> Show constraints
          </button>
          <button class="w3-button w3-border w3-round w3-small w3-light-gray"
                  type="button" onclick="doWordReset()">
            <i class="material-icons" style="font-size:14px;vertical-align:middle">cached</i> Reset
          </button>
        </div>
        <div id="we-constraints-table"
             style="overflow:auto;overflow-x:hidden;margin-top:8px"></div>

        <!-- OK / Cancel -->
        <div style="margin-top:12px">
          <button class="w3-button w3-border w3-round w3-gray" style="width:100px"
                  onclick="doWordEditOK()">OK</button>
          <button class="w3-button w3-border w3-round w3-gray" style="width:100px"
                  onclick="closeWordEditor()">Cancel</button>
        </div>

      </div>
    </div>
  </div>
</div>`;
}

function weListItemClick(word) {
    const inp = document.getElementById('we-text');
    if (inp) inp.value = word;
    // Highlight selected item
    document.querySelectorAll('#we-suggestion-list li').forEach(li => {
        li.style.background = li.dataset.word === word ? '#d0e8ff' : '';
    });
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
        if (e.key === 'Escape') { closeWordEditor(); e.preventDefault(); }
        if (e.key === 'Enter')  { doWordEditOK();    e.preventDefault(); }
        return;
    }
    if (e.key === 'Escape') { closeWordEditor(); e.preventDefault(); }
    if (e.key === 'Enter')  { doWordEditOK();    e.preventDefault(); }
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
    const matchEl = document.getElementById('we-match');
    matchEl.style.display = 'none';
    const inp     = document.getElementById('we-text');
    const rawText = inp ? inp.value : (AppState.editingWord.answer || '');
    const pattern = rawText.replace(/ /g, '.').toUpperCase();
    if (!pattern) return;
    try {
        const data = await apiFetch('GET',
            `/api/words/suggestions?pattern=${encodeURIComponent(pattern)}`);
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
        matchEl.innerHTML     = 'Error fetching suggestions';
        matchEl.style.display = 'block';
    }
}

async function _fetchConstrainedSuggestions() {
    const ew      = AppState.editingWord;
    const wn      = AppState.puzzleWorkingName;
    const matchEl = document.getElementById('we-match');
    matchEl.style.display = 'none';
    try {
        const data = await apiFetch('GET',
            `/api/puzzles/${encodeURIComponent(wn)}/words/${ew.seq}/${ew.direction}/suggestions`);
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
        matchEl.innerHTML     = 'Error fetching suggestions';
        matchEl.style.display = 'block';
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
    const tableEl = document.getElementById('we-constraints-table');
    const btn     = document.getElementById('we-constraints-btn');

    // Toggle: if already showing, hide
    if (tableEl.innerHTML.trim() !== '') {
        tableEl.innerHTML = '';
        if (btn) btn.innerHTML = '<i class="material-icons" style="font-size:14px;vertical-align:middle">assignment</i> Show constraints';
        return;
    }

    const ew = AppState.editingWord;
    const wn = AppState.puzzleWorkingName;
    tableEl.innerHTML = 'Loading…';

    try {
        const data = await apiFetch('GET',
            `/api/puzzles/${encodeURIComponent(wn)}/words/${ew.seq}/${ew.direction}/constraints`);
        if (data.error) { tableEl.innerHTML = `Error: ${escapeHtml(data.error)}`; return; }

        const colNames    = ['Pos', 'Letter', 'Location', 'Text', 'Index', 'Regexp', 'Choices'];
        const crosserKeys = ['pos', 'letter', 'crossing_location', 'crossing_text',
                             'crossing_index', 'regexp', 'choices'];

        const headerRow = colNames.map(n => `<th>${n}</th>`).join('');
        const bodyRows  = data.crossers.map(cr =>
            `<tr>${crosserKeys.map(k => `<td>${escapeHtml(String(cr[k]))}</td>`).join('')}</tr>`
        ).join('');

        tableEl.innerHTML = `
<div class="w3-padding w3-center">
  <b>Overall pattern:</b>
  <code style="margin:0 8px">${escapeHtml(data.pattern)}</code>
</div>
<table class="w3-table w3-small w3-bordered">
  <tr>${headerRow}</tr>
  ${bodyRows}
</table>`;
        if (btn) btn.innerHTML = '<i class="material-icons" style="font-size:14px;vertical-align:middle">assignment</i> Hide constraints';
    } catch (e) {
        tableEl.innerHTML = 'Error fetching constraints';
    }
}

// ---------------------------------------------------------------------------
// Word editor — Reset tab
// ---------------------------------------------------------------------------

async function doWordReset() {
    const ew = AppState.editingWord;
    const wn = AppState.puzzleWorkingName;
    try {
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(wn)}/words/${ew.seq}/${ew.direction}/reset`);
        if (data.error) { alert(`Reset failed: ${data.error}`); return; }

        const updated = (data.puzzle.words || []).find(
            w => w.seq === ew.seq && w.direction === ew.direction
        );
        if (updated) {
            const len     = ew.cells.length;
            const newText = (updated.answer || '').padEnd(len).slice(0, len);
            const inp = document.getElementById('we-text');
            if (inp) inp.value = newText.trimEnd();
        }
    } catch (e) {
        alert('Error resetting word');
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
    AppState.puzzleWorkingName = wn;
    AppState.puzzleData        = puzzleData;
    AppState.puzzleSavedHash   = _hash(puzzleData.puzzle);
    AppState.editingWord       = null;
    AppState.selectedWord      = null;
    AppState.showingStats      = false;
    AppState._statsData        = null;
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
            inputBox('New puzzle', '<b>Puzzle name:</b>', '', async (name) => {
                if (!name) return;
                if (!validateUserFacingName('puzzle', name)) return;
                try {
                    if (await rejectIfNameExists('puzzle', name, _listSavedPuzzleNames)) return;
                    const data = await apiFetch('POST', '/api/puzzles', { name, size: n });
                    if (data.error) { alert(`Error creating puzzle: ${data.error}`); return; }
                    await _openPuzzleInEditor(name);
                } catch (e) { alert('Error creating puzzle'); }
            });
        }
    );
}

async function do_puzzle_save() {
    const wn   = AppState.puzzleWorkingName;
    const name = AppState.puzzleName;
    if (!name) { do_puzzle_save_as(); return; }
    try {
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(wn)}/copy`, { new_name: name });
        if (data.error) { alert(`Save failed: ${data.error}`); return; }
        AppState.puzzleSavedHash = _hash(AppState.puzzleData.puzzle);
        showMessageLine(`Puzzle ${name} saved.`, 'notice');
    } catch (e) { alert('Error saving puzzle'); }
}

async function _listSavedPuzzleNames() {
    const listData = await apiFetch('GET', '/api/puzzles');
    if (listData.error) {
        throw new Error(listData.error);
    }
    return (listData.puzzles || []).filter(p => p && !p.startsWith('__wc__'));
}

async function _savePuzzleAsName(newName) {
    const wn = AppState.puzzleWorkingName;
    const data = await apiFetch('POST',
        `/api/puzzles/${encodeURIComponent(wn)}/copy`, { new_name: newName });
    if (data.error) {
        throw new Error(data.error);
    }
    AppState.puzzleName      = newName;
    AppState.puzzleSavedHash = _hash(AppState.puzzleData.puzzle);
    renderPuzzleEditorLhs();
    showMessageLine(`Puzzle ${newName} saved.`, 'notice');
}

async function do_puzzle_save_as() {
    inputBox('Save puzzle as', 'Puzzle name:', AppState.puzzleName || '', async (newName) => {
        if (!newName) return;
        if (!validateUserFacingName('puzzle', newName)) return;
        try {
            await confirmOverwriteIfExists(
                'puzzle',
                newName,
                _listSavedPuzzleNames,
                () => _savePuzzleAsName(newName)
            );
        } catch (e) { alert('Error saving puzzle'); }
    });
}

async function _doPuzzleCloseConfirmed() {
    document.removeEventListener('keydown', _peKeydown);
    document.removeEventListener('keydown', _weKeydown);
    const wn = AppState.puzzleWorkingName;
    AppState.puzzleName        = null;
    AppState.puzzleWorkingName = null;
    AppState.puzzleData        = null;
    AppState.puzzleSavedHash   = null;
    AppState.editingWord       = null;
    AppState.selectedWord      = null;
    AppState.showingStats      = false;
    AppState._statsData        = null;
    AppState.gridStructureChanged = false;
    if (wn) {
        try { await apiFetch('DELETE', `/api/puzzles/${encodeURIComponent(wn)}`); }
        catch (e) { /* ignore cleanup errors */ }
    }
    showView('home');
}

async function do_puzzle_close() {
    const isDirty = AppState.puzzleData &&
        _hash(AppState.puzzleData.puzzle) !== AppState.puzzleSavedHash;
    if (isDirty) {
        const name = AppState.puzzleName || '(untitled)';
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
        const data = await apiFetch('GET', `/api/puzzles/${encodeURIComponent(wn)}/stats`);
        if (data.error) { alert(`Error: ${data.error}`); return; }
        AppState._statsData   = data;
        AppState.showingStats = true;
        AppState.editingWord  = null;
        renderPuzzleEditorRhs();
    } catch (e) { alert('Error fetching stats'); }
}

function renderStatsPanel(stats) {
    const validColor = stats.valid ? 'w3-text-green' : 'w3-text-red';
    const validText  = stats.valid ? 'Valid' : 'Invalid';

    // Errors section
    let errorsHtml;
    const allErrors = Object.values(stats.errors).flat();
    if (allErrors.length === 0) {
        errorsHtml = 'None';
    } else {
        errorsHtml = '<ul style="list-style-type:none;margin:0;padding:0">' +
            allErrors.map(e => `<li style="color:#cc0000">${escapeHtml(e)}</li>`).join('') +
            '</ul>';
    }

    // Word lengths table
    const wlRows = Object.entries(stats.wordlengths)
        .sort((a, b) => Number(b[0]) - Number(a[0]))
        .map(([len, entry]) => {
            const across = (entry.alist || []).join(', ') || '(none)';
            const down   = (entry.dlist || []).join(', ') || '(none)';
            return `<tr>
  <td style="border:1px solid #ccc;padding:3px 8px">${len}</td>
  <td style="border:1px solid #ccc;padding:3px 8px;word-break:break-word">${escapeHtml(across)}</td>
  <td style="border:1px solid #ccc;padding:3px 8px;word-break:break-word">${escapeHtml(down)}</td>
</tr>`;
        }).join('');

    function row(label, value) {
        return `<div class="w3-section w3-cell-row">
  <div class="w3-cell" style="width:30%"><b>${label}</b></div>
  <div class="w3-cell">${value}</div>
</div>`;
    }

    return `
<div class="w3-margin-right">
  <header class="w3-container w3-blue-gray" style="padding:7px;position:relative">
    <h3>Puzzle statistics</h3>
    <span class="w3-button w3-xlarge w3-hover-red"
          style="position:absolute;top:0;right:0"
          onclick="closeStatsPanel()">&times;</span>
  </header>
  <div class="w3-card-4">
    <div class="w3-container" style="padding-bottom:12px">
      ${row('Valid:', `<span class="${validColor}"><b>${validText}</b></span>`)}
      ${row('Errors:', errorsHtml)}
      ${row('Size:', escapeHtml(stats.size))}
      ${row('Word count:', stats.wordcount)}
      ${row('Black cells:', stats.blockcount)}
      <div class="w3-section">
        <table class="w3-table" style="border-collapse:collapse;width:auto">
          <tr>
            <th style="border:1px solid #ccc;padding:3px 8px">Word length</th>
            <th style="border:1px solid #ccc;padding:3px 8px">Across</th>
            <th style="border:1px solid #ccc;padding:3px 8px">Down</th>
          </tr>
          ${wlRows}
        </table>
      </div>
    </div>
  </div>
</div>`;
}

function closeStatsPanel() {
    AppState.showingStats = false;
    renderPuzzleEditorRhs();
}

async function _refreshPuzzleStatsIfVisible() {
    if (!AppState.showingStats || !AppState.puzzleWorkingName) return;
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

async function _applyGridModeUpdate(data, noticeText = _gridChangeMessage()) {
    AppState.puzzleData   = data;
    AppState.editingWord  = null;
    AppState.selectedWord = null;
    AppState.gridStructureChanged = true;
    renderPuzzleEditor();
    await _refreshPuzzleStatsIfVisible();
    showMessageLine(noticeText, 'notice');
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
        AppState.puzzleData   = data;
        AppState.editingWord  = null;
        AppState.selectedWord = null;
        AppState.showingStats = false;
        AppState._statsData   = null;
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

async function _switchToGridModeConfirmed() {
    try {
        await _settlePuzzleEditingBeforeModeSwitch();
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(AppState.puzzleWorkingName)}/mode/grid`);
        if (data.error) { alert(`Error switching modes: ${data.error}`); return; }
        AppState.puzzleData   = data;
        AppState.editingWord  = null;
        AppState.selectedWord = null;
        AppState.showingStats = false;
        AppState._statsData   = null;
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
        AppState.selectedWord = null;
        AppState.showingStats = false;
        AppState._statsData   = null;
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

async function do_puzzle_delete() {
    const name = AppState.puzzleName;
    if (!name) return;
    messageBox(
        'Delete puzzle',
        `Are you sure you want to delete puzzle <b>'${escapeHtml(name)}'</b>?`,
        null,
        async () => {
            try {
                await apiFetch('DELETE', `/api/puzzles/${encodeURIComponent(name)}`);
                await do_puzzle_close();
            } catch (e) { alert('Error deleting puzzle'); }
        }
    );
}

// ---------------------------------------------------------------------------
// Menu actions — Grid
// ---------------------------------------------------------------------------

async function _openGridInEditor(name) {
    try {
        const openData = await apiFetch('POST', `/api/grids/${encodeURIComponent(name)}/open`);
        if (openData.error) { alert(`Error opening grid: ${openData.error}`); return; }
        const wn       = openData.working_name;
        const gridData = await apiFetch('GET', `/api/grids/${encodeURIComponent(wn)}`);
        if (gridData.error) { alert(`Error loading grid: ${gridData.error}`); return; }
        AppState.gridOriginalName = name;
        AppState.gridWorkingName  = wn;
        AppState.gridData         = gridData;
        AppState.gridSavedHash    = _hash(gridData.cells);
        showView('grid-editor');
    } catch (e) { alert('Error opening grid'); }
}

function do_grid_new() {
    inputBox(
        'New grid',
        '<b>Grid size:</b> <em>(an odd positive integer, e.g. 15)</em>',
        '',
        (sizeVal) => {
            const n = Number(sizeVal);
            if (!sizeVal || isNaN(n))  { alert(sizeVal + ' is not a number'); return; }
            if (n % 2 === 0)           { alert(n + ' is not an odd number'); return; }
            if (n < 1)                 { alert(n + ' is not a positive number'); return; }
            inputBox('New grid', '<b>Grid name:</b>', '', async (name) => {
                if (!name) return;
                if (!validateUserFacingName('grid', name)) return;
                try {
                    if (await rejectIfNameExists('grid', name, _listSavedGridNames)) return;
                    const data = await apiFetch('POST', '/api/grids', { name, size: n });
                    if (data.error) { alert(`Error creating grid: ${data.error}`); return; }
                    await _openGridInEditor(name);
                } catch (e) { alert('Error creating grid'); }
            });
        }
    );
}

async function do_grid_new_from_puzzle() {
    try {
        const listData = await apiFetch('GET', '/api/puzzles');
        if (listData.error) { alert(`Error: ${listData.error}`); return; }
        const puzzles = (listData.puzzles || []).filter(p => p && !p.startsWith('__wc__'));
        if (puzzles.length === 0) {
            showMessageLine('No saved puzzles found.', 'notice');
            return;
        }
        showPreviewChooser('Choose a puzzle', puzzles, '/api/puzzles', (puzzleName) => {
            inputBox('New grid from puzzle', '<b>New grid name:</b>', '', async (gridName) => {
                if (!gridName) return;
                if (!validateUserFacingName('grid', gridName)) return;
                try {
                    if (await rejectIfNameExists('grid', gridName, _listSavedGridNames)) return;
                    const data = await apiFetch('POST', '/api/grids/from-puzzle',
                        { grid_name: gridName, puzzle_name: puzzleName });
                    if (data.error) { alert(`Error: ${data.error}`); return; }
                    await _openGridInEditor(gridName);
                } catch (e) { alert('Error creating grid from puzzle'); }
            });
        });
    } catch (e) { alert('Error listing puzzles'); }
}

async function do_grid_open() {
    try {
        const listData = await apiFetch('GET', '/api/grids');
        if (listData.error) { alert(`Error: ${listData.error}`); return; }
        const grids = (listData.grids || []).filter(g => g && !g.startsWith('__wc__'));
        if (grids.length === 0) {
            showMessageLine('No saved grids found.', 'notice');
            return;
        }
        showPreviewChooser('Open grid', grids, '/api/grids', async (name) => {
            await _openGridInEditor(name);
        });
    } catch (e) { alert('Error listing grids'); }
}

async function do_grid_save() {
    const wn   = AppState.gridWorkingName;
    const name = AppState.gridOriginalName;
    if (!name) { do_grid_save_as(); return; }
    try {
        const data = await apiFetch('POST',
            `/api/grids/${encodeURIComponent(wn)}/copy`, { new_name: name });
        if (data.error) { alert(`Save failed: ${data.error}`); return; }
        AppState.gridSavedHash = _hash(AppState.gridData.cells);
        showMessageLine(`Grid ${name} saved.`, 'notice');
    } catch (e) { alert('Error saving grid'); }
}

async function _listSavedGridNames() {
    const listData = await apiFetch('GET', '/api/grids');
    if (listData.error) {
        throw new Error(listData.error);
    }
    return (listData.grids || []).filter(g => g && !g.startsWith('__wc__'));
}

async function _saveGridAsName(newName) {
    const wn = AppState.gridWorkingName;
    const data = await apiFetch('POST',
        `/api/grids/${encodeURIComponent(wn)}/copy`, { new_name: newName });
    if (data.error) {
        throw new Error(data.error);
    }
    AppState.gridOriginalName = newName;
    AppState.gridSavedHash    = _hash(AppState.gridData.cells);
    renderGridEditor();
    showMessageLine(`Grid ${newName} saved.`, 'notice');
}

async function do_grid_save_as() {
    inputBox('Save grid as', 'Grid name:', AppState.gridOriginalName || '', async (newName) => {
        if (!newName) return;
        if (!validateUserFacingName('grid', newName)) return;
        try {
            await confirmOverwriteIfExists(
                'grid',
                newName,
                _listSavedGridNames,
                () => _saveGridAsName(newName)
            );
        } catch (e) { alert('Error saving grid'); }
    });
}

async function _doGridCloseConfirmed() {
    const wn = AppState.gridWorkingName;
    AppState.gridOriginalName = null;
    AppState.gridWorkingName  = null;
    AppState.gridData         = null;
    AppState.gridSavedHash    = null;
    AppState.showingGridStats = false;
    AppState._gridStatsData   = null;
    if (wn) {
        try { await apiFetch('DELETE', `/api/grids/${encodeURIComponent(wn)}`); }
        catch (e) { /* ignore cleanup errors */ }
    }
    showView('home');
}

async function do_grid_close() {
    const isDirty = AppState.gridData &&
        _hash(AppState.gridData.cells) !== AppState.gridSavedHash;
    if (isDirty) {
        const name = AppState.gridOriginalName || '(untitled)';
        messageBox(
            'Close grid',
            `Grid <b>${escapeHtml(name)}</b> has unsaved changes. Close without saving?`,
            null,
            () => _doGridCloseConfirmed()
        );
    } else {
        await _doGridCloseConfirmed();
    }
}

async function do_grid_delete() {
    const name = AppState.gridOriginalName;
    if (!name) return;
    messageBox(
        'Delete grid',
        `Are you sure you want to delete grid <b>'${escapeHtml(name)}'</b>?`,
        null,
        async () => {
            try {
                await apiFetch('DELETE', `/api/grids/${encodeURIComponent(name)}`);
                await do_grid_close();
            } catch (e) { alert('Error deleting grid'); }
        }
    );
}

// ---------------------------------------------------------------------------
// Menu actions — Publish
// ---------------------------------------------------------------------------

async function _downloadExport(name, format) {
    const endpointMap = { puz: 'acrosslite', xml: 'xml', nyt: 'nytimes' };
    const filenameMap = { puz: `acrosslite-${name}.zip`, xml: `${name}.xml`, nyt: `nytimes-${name}.zip` };
    const endpoint = endpointMap[format];
    const filename = filenameMap[format];
    try {
        const resp = await fetch(`/api/export/puzzles/${encodeURIComponent(name)}/${endpoint}`);
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            showMessageLine(err.error || `Publish failed: HTTP ${resp.status}`, 'error');
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
    } catch (e) {
        showMessageLine('Export request failed.', 'error');
    }
}

async function do_publish(format) {
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
            showPreviewChooser('Choose a puzzle to publish', puzzles, '/api/puzzles', async (name) => {
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

document.addEventListener('DOMContentLoaded', () => {
    showView('home');
});
