// Crossword Puzzle Editor — main application script

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const BOXSIZE = 32;

// ---------------------------------------------------------------------------
// Application state
// ---------------------------------------------------------------------------

const AppState = {
    view: 'home',            // 'home' | 'grid-editor' | 'puzzle-editor'
    gridOriginalName: null,  // name of currently-open grid (original)
    gridWorkingName: null,   // grid working copy name (e.g. '__wc__a1b2c3d4')
    gridData: null,          // { size, cells[] } from API
    gridSavedHash: null,     // checksum of cells[] at last open/save
    puzzleName: null,        // name of currently-open puzzle (original)
    puzzleWorkingName: null, // working copy name (e.g. '__wc__a1b2c3d4')
    puzzleData: null,        // response from GET /api/puzzles/{workingName}
    puzzleSavedHash: null,   // checksum of puzzle at last open/save
    editingWord: null,       // null | {seq, direction, cells, answer, clue}
    showingStats: false,     // true = puzzle editor RHS shows stats panel
    showingGridStats: false, // true = grid editor RHS shows stats panel
    _gridStatsData: null,    // cached grid stats response
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
    'menu-grid-new', 'menu-grid-new-from-puzzle', 'menu-grid-open',
    'menu-grid-save', 'menu-grid-save-as', 'menu-grid-close', 'menu-grid-delete',
    'menu-puzzle-new', 'menu-puzzle-open',
    'menu-puzzle-save', 'menu-puzzle-save-as', 'menu-puzzle-close', 'menu-puzzle-delete',
    'menu-publish-acrosslite', 'menu-publish-cwcompiler', 'menu-publish-nytimes',
];

function menuEnable(id)  { document.getElementById(id).classList.remove('w3-disabled'); }
function menuDisable(id) { document.getElementById(id).classList.add('w3-disabled'); }

function updateMenu() {
    const home   = AppState.view === 'home';
    const grid   = AppState.view === 'grid-editor';
    const puzzle = AppState.view === 'puzzle-editor';

    home  ? menuEnable('menu-grid-new')             : menuDisable('menu-grid-new');
    home  ? menuEnable('menu-grid-new-from-puzzle') : menuDisable('menu-grid-new-from-puzzle');
    home  ? menuEnable('menu-grid-open')            : menuDisable('menu-grid-open');
    grid  ? menuEnable('menu-grid-save')            : menuDisable('menu-grid-save');
    grid  ? menuEnable('menu-grid-save-as')         : menuDisable('menu-grid-save-as');
    grid  ? menuEnable('menu-grid-close')           : menuDisable('menu-grid-close');
    grid  ? menuEnable('menu-grid-delete')  : menuDisable('menu-grid-delete');

    home   ? menuEnable('menu-puzzle-new')          : menuDisable('menu-puzzle-new');
    home   ? menuEnable('menu-puzzle-open')         : menuDisable('menu-puzzle-open');
    puzzle ? menuEnable('menu-puzzle-save')         : menuDisable('menu-puzzle-save');
    puzzle ? menuEnable('menu-puzzle-save-as')      : menuDisable('menu-puzzle-save-as');
    puzzle ? menuEnable('menu-puzzle-close')        : menuDisable('menu-puzzle-close');
    puzzle ? menuEnable('menu-puzzle-delete')       : menuDisable('menu-puzzle-delete');

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
    <a class="w3-bar-item w3-button crosstb" onclick="do_grid_rotate_action()">
      <i class="material-icons crosstb-icon">rotate_right</i><span>Rotate</span></a>
    <a id="grid-undo-btn" class="w3-bar-item w3-button crosstb" onclick="do_grid_undo_action()">
      <i class="material-icons crosstb-icon">undo</i><span>Undo</span></a>
    <a id="grid-redo-btn" class="w3-bar-item w3-button crosstb" onclick="do_grid_redo_action()">
      <i class="material-icons crosstb-icon">redo</i><span>Redo</span></a>
    <a class="w3-bar-item w3-button crosstb" onclick="do_grid_info_action()">
      <i class="material-icons crosstb-icon">info</i><span>Info</span></a>
    <a class="w3-bar-item w3-button crosstb" onclick="do_grid_save()">
      <i class="material-icons crosstb-icon">save</i><span>Save</span></a>
    <a class="w3-bar-item w3-button crosstb" onclick="do_grid_close()">
      <i class="material-icons crosstb-icon">close</i><span>Close</span></a>
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

function buildPuzzleSvg(puzzleData) {
    const n           = puzzleData.grid.size;
    const blackCells  = puzzleData.grid.cells;        // bool[], true = black
    const puzzleCells = puzzleData.puzzle.cells;      // {"idx": {number?, letter?}}
    const totalPx     = n * BOXSIZE + 1;

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

            parts.push(
                `<rect x="${x}" y="${y}" width="${BOXSIZE}" height="${BOXSIZE}" ` +
                `fill="${black ? 'black' : 'white'}" stroke="#999" stroke-width="0.5"/>`
            );

            if (!black) {
                const cd = puzzleCells[String(idx)] || {};
                if (cd.number !== undefined) {
                    parts.push(
                        `<text x="${x + 2}" y="${y + 10}" ` +
                        `font-size="9" font-family="sans-serif">${cd.number}</text>`
                    );
                }
                if (cd.letter) {
                    parts.push(
                        `<text x="${x + BOXSIZE / 2}" y="${y + BOXSIZE - 6}" ` +
                        `font-size="15" font-family="sans-serif" ` +
                        `text-anchor="middle">${escapeHtml(cd.letter)}</text>`
                    );
                }
            }
        }
    }

    // Outer border drawn last
    parts.push(
        `<rect x="0" y="0" width="${totalPx - 1}" height="${totalPx - 1}" ` +
        `fill="none" stroke="black" stroke-width="2"/>`
    );
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

function handlePuzzleClick(event) {
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

function puzzleClickAt(event, direction) {
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
    if (word) openWordEditor(word.seq, word.direction);
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
// Puzzle editor — rendering
// ---------------------------------------------------------------------------

function renderPuzzleEditor() {
    renderPuzzleEditorLhs();
    renderPuzzleEditorRhs();
}

function renderPuzzleEditorLhs() {
    const pd    = AppState.puzzleData;
    const name  = AppState.puzzleName || '(untitled)';
    const title = pd && pd.puzzle.title ? `: &ldquo;${escapeHtml(pd.puzzle.title)}&rdquo;` : '';

    const toolbar = `
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
        <a class="w3-bar-item w3-button crosstb" onclick="do_puzzle_stats()">
            <i class="material-icons crosstb-icon">info</i><span>Info</span></a>
        <a class="w3-bar-item w3-button crosstb" onclick="do_puzzle_title()">
            <i class="material-icons crosstb-icon">title</i><span>Title</span></a>
  </div>
</div>`;

    document.getElementById('lhs').innerHTML = `
<div class="w3-container">
  <h3>Editing puzzle <b>${escapeHtml(name)}</b>${title}</h3>
</div>
${toolbar}
<div id="puzzle-svg-container" class="w3-container" style="padding-top:4px">
  ${pd ? buildPuzzleSvg(pd) : ''}
</div>`;

    const svg = document.getElementById('puzzle-svg');
    if (svg) svg.addEventListener('click', handlePuzzleClick);
    _updatePuzzleUndoRedo();
}

function renderPuzzleEditorRhs() {
    let html;
    if (AppState.editingWord) {
        html = renderWordEditorPanel();
    } else if (AppState.showingStats) {
        html = AppState._statsData ? renderStatsPanel(AppState._statsData) : '';
    } else {
        html = renderClues();
    }
    document.getElementById('rhs').innerHTML = html;
}

function renderClues() {
    if (!AppState.puzzleData) return '';
    const words = AppState.puzzleData.puzzle.words;
    const across = words.filter(w => w.direction === 'across').sort((a, b) => a.seq - b.seq);
    const down   = words.filter(w => w.direction === 'down').sort((a, b) => a.seq - b.seq);

    function listHtml(wordList, direction, colorClass) {
        const items = wordList.map(w =>
            `<li><a onclick="openWordEditor(${w.seq}, '${direction}')">${w.seq}. ${escapeHtml(w.clue || '')}</a></li>`
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
    const text     = (ew.answer || '').replace(/ /g, '.');
    const clue     = ew.clue || '';
    const dirLabel = ew.direction.charAt(0).toUpperCase() + ew.direction.slice(1);
    const len      = ew.cells.length;

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

        <!-- Tab bar -->
        <div class="w3-bar w3-blue-gray">
          <button class="w3-bar-item w3-button" type="button"
                  onclick="openWordEditTab('we-tab-suggest')">Suggest</button>
          <button class="w3-bar-item w3-button" type="button"
                  onclick="openWordEditTab('we-tab-constraints')">Constraints</button>
          <button class="w3-bar-item w3-button" type="button"
                  onclick="openWordEditTab('we-tab-reset')">Reset</button>
        </div>

        <!-- Tab 1: Suggest -->
        <div id="we-tab-suggest" class="w3-bar w3-margin-top we-tab">
          <a class="w3-bar-item w3-button w3-small w3-round w3-light-gray crosstb"
             onclick="doWordSuggest()">
            <i class="material-icons crosstb-icon">search</i>
            <span>Suggest words that match pattern</span>
          </a>
          <div id="we-match" style="display:none;padding:4px 0" class="w3-bar-item"></div>
          <select id="we-select" class="w3-bar-item" style="display:none"
                  onchange="weSelectChanged()" onclick="weSelectChanged()"></select>
        </div>

        <!-- Tab 2: Constraints -->
        <div id="we-tab-constraints" class="we-tab" style="display:none">
          <div class="w3-bar w3-margin-top">
            <a class="w3-button w3-small w3-round w3-light-gray crosstb"
               onclick="doWordConstraints()">
              <i class="material-icons crosstb-icon">assignment</i>
              <span>Find constraints imposed by crossing words</span>
            </a>
          </div>
          <div id="we-constraints-table" style="overflow:auto;overflow-x:hidden;margin-top:4px"></div>
        </div>

        <!-- Tab 3: Reset -->
        <div id="we-tab-reset" class="w3-bar w3-margin-top we-tab" style="display:none">
          <a class="w3-bar-item w3-button w3-small w3-round w3-light-gray crosstb"
             onclick="doWordReset()">
            <i class="material-icons crosstb-icon">cached</i>
            <span>Clear letters not shared with full words</span>
          </a>
        </div>

        <!-- Word input -->
        <p style="width:55%;margin:12px 0 0 0">
          <label>Word:</label>
          <input class="w3-input w3-border" id="we-word" type="text"
                 style="font-family:Courier;font-size:large" value="${escapeHtml(text)}"/>
        </p>

        <!-- Clue input -->
        <p style="width:95%;margin:8px 0 0 0">
          <label>Clue:</label>
          <input class="w3-input w3-border" id="we-clue" type="text"
                 value="${escapeHtml(clue)}"/>
        </p>

        <!-- Buttons -->
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

function openWordEditTab(tabname) {
    document.querySelectorAll('.we-tab').forEach(t => t.style.display = 'none');
    document.getElementById(tabname).style.display = 'block';
}

function weSelectChanged() {
    const sel = document.getElementById('we-select');
    const inp = document.getElementById('we-word');
    if (sel && inp) inp.value = sel.value;
}

// ---------------------------------------------------------------------------
// Word editor — open / close
// ---------------------------------------------------------------------------

async function openWordEditor(seq, direction) {
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
        renderPuzzleEditorRhs();
    } catch (e) {
        alert('Error opening word editor');
    }
}

function closeWordEditor() {
    AppState.editingWord  = null;
    AppState.showingStats = false;
    renderPuzzleEditorRhs();
}

// ---------------------------------------------------------------------------
// Word editor — Suggest tab
// ---------------------------------------------------------------------------

async function doWordSuggest() {
    const matchEl  = document.getElementById('we-match');
    const selectEl = document.getElementById('we-select');
    const pattern  = (document.getElementById('we-word').value || '').trim();

    matchEl.style.display  = 'none';
    selectEl.style.display = 'none';
    if (!pattern) return;

    try {
        const data = await apiFetch('GET',
            `/api/words/suggestions?pattern=${encodeURIComponent(pattern)}`);
        selectEl.innerHTML = '';
        if (!data.suggestions || data.suggestions.length === 0) {
            matchEl.innerHTML      = 'No matches found';
            matchEl.style.display  = 'block';
        } else {
            matchEl.innerHTML     = `${data.suggestions.length} matches found:`;
            matchEl.style.display = 'block';
            for (const word of data.suggestions) {
                const opt       = document.createElement('option');
                opt.value       = word.toUpperCase();
                opt.textContent = word.toUpperCase();
                selectEl.appendChild(opt);
            }
            selectEl.style.display = 'block';
        }
    } catch (e) {
        matchEl.innerHTML     = 'Error fetching suggestions';
        matchEl.style.display = 'block';
    }
}

function doFastpath(pattern) {
    const inp = document.getElementById('we-word');
    if (inp && pattern) inp.value = pattern;
    openWordEditTab('we-tab-suggest');
    doWordSuggest();
}

// ---------------------------------------------------------------------------
// Word editor — Constraints tab
// ---------------------------------------------------------------------------

async function doWordConstraints() {
    const ew      = AppState.editingWord;
    const wn      = AppState.puzzleWorkingName;
    const tableEl = document.getElementById('we-constraints-table');
    tableEl.innerHTML = 'Loading…';

    try {
        const data = await apiFetch('GET',
            `/api/puzzles/${encodeURIComponent(wn)}/words/${ew.seq}/${ew.direction}/constraints`);
        if (data.error) { tableEl.innerHTML = `Error: ${escapeHtml(data.error)}`; return; }

        const colNames   = ['Pos', 'Letter', 'Location', 'Text', 'Index', 'Regexp', 'Choices'];
        const crosserKeys = ['pos', 'letter', 'crossing_location', 'crossing_text',
                             'crossing_index', 'regexp', 'choices'];

        const headerRow = colNames.map(n => `<th>${n}</th>`).join('');
        const bodyRows  = data.crossers.map(cr =>
            `<tr>${crosserKeys.map(k => `<td>${escapeHtml(String(cr[k]))}</td>`).join('')}</tr>`
        ).join('');

        tableEl.innerHTML = `
<div class="w3-padding w3-center">
  <b>Overall pattern:</b>
  <input class="w3-border" id="we-pattern-input"
         value="${escapeHtml(data.pattern)}" style="width:120px;margin:0 8px"/>
  <button type="button" class="w3-margin-left"
          onclick="doFastpath(document.getElementById('we-pattern-input').value)">
    Suggest &rsaquo;
  </button>
</div>
<table class="w3-table w3-small w3-bordered">
  <tr>${headerRow}</tr>
  ${bodyRows}
</table>`;
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

        // Update puzzle data and the word input with the cleared text
        AppState.puzzleData = data;
        const updated = (data.puzzle.words || []).find(
            w => w.seq === ew.seq && w.direction === ew.direction
        );
        if (updated) {
            AppState.editingWord = { ...ew, answer: updated.answer };
            const inp = document.getElementById('we-word');
            if (inp) inp.value = (updated.answer || '').replace(/ /g, '.');
        }
    } catch (e) {
        alert('Error resetting word');
    }
}

// ---------------------------------------------------------------------------
// Word editor — OK
// ---------------------------------------------------------------------------

async function doWordEditOK() {
    const ew  = AppState.editingWord;
    const wn  = AppState.puzzleWorkingName;
    let text  = (document.getElementById('we-word').value || '').toUpperCase();
    const clue = document.getElementById('we-clue').value || '';

    // Validate characters
    for (const ch of text) {
        if (!' ABCDEFGHIJKLMNOPQRSTUVWXYZ.'.includes(ch)) {
            alert(`"${text}" contains invalid characters`);
            return;
        }
    }

    // Pad/trim to word length; treat dot as blank
    const len = ew.cells.length;
    text = text.padEnd(len).slice(0, len).replace(/\./g, ' ');

    try {
        // Save text (undo-tracked) and clue in one request
        const data = await apiFetch('PUT',
            `/api/puzzles/${encodeURIComponent(wn)}/words/${ew.seq}/${ew.direction}`,
            { text, clue });
        if (data.error) { alert(`Error saving word: ${data.error}`); return; }
        AppState.puzzleData  = data;
        AppState.editingWord = null;
        renderPuzzleEditor();
    } catch (e) {
        alert('Error saving word');
    }
}

// ---------------------------------------------------------------------------
// Menu actions — Puzzle
// ---------------------------------------------------------------------------

async function do_puzzle_open() {
    try {
        const listData = await apiFetch('GET', '/api/puzzles');
        if (listData.error) { alert(`Error: ${listData.error}`); return; }
        const puzzles = (listData.puzzles || []).filter(p => p && !p.startsWith('__wc__'));
        if (puzzles.length === 0) {
            messageBox('Open puzzle', 'No saved puzzles found.', null, null);
            return;
        }
        showPreviewChooser('Open puzzle', puzzles, '/api/puzzles', async (name) => {
            try {
                const openData = await apiFetch('POST',
                    `/api/puzzles/${encodeURIComponent(name)}/open`);
                if (openData.error) { alert(`Error opening: ${openData.error}`); return; }
                const wn = openData.working_name;
                const puzzleData = await apiFetch('GET',
                    `/api/puzzles/${encodeURIComponent(wn)}`);
                if (puzzleData.error) { alert(`Error loading: ${puzzleData.error}`); return; }
                AppState.puzzleName        = name;
                AppState.puzzleWorkingName = wn;
                AppState.puzzleData        = puzzleData;
                AppState.puzzleSavedHash   = _hash(puzzleData.puzzle);
                AppState.editingWord       = null;
                showView('puzzle-editor');
            } catch (e) { alert('Error opening puzzle'); }
        });
    } catch (e) {
        alert('Error listing puzzles');
    }
}

async function do_puzzle_new() {
    try {
        const listData = await apiFetch('GET', '/api/grids');
        if (listData.error) { alert(`Error: ${listData.error}`); return; }
        const grids = (listData.grids || []).filter(g => g && !g.startsWith('__wc__'));
        if (grids.length === 0) {
            messageBox('New puzzle', 'No saved grids found. Create a grid first.', null, null);
            return;
        }
        showPreviewChooser('Choose a grid', grids, '/api/grids', (gridName) => {
            inputBox('New puzzle', '<b>Puzzle name:</b>', '', async (name) => {
                if (!name) return;
                try {
                    const data = await apiFetch('POST', '/api/puzzles',
                        { name, grid_name: gridName });
                    if (data.error) { alert(`Error creating puzzle: ${data.error}`); return; }
                    const openData = await apiFetch('POST',
                        `/api/puzzles/${encodeURIComponent(name)}/open`);
                    if (openData.error) { alert(`Error opening puzzle: ${openData.error}`); return; }
                    const wn = openData.working_name;
                    const puzzleData = await apiFetch('GET',
                        `/api/puzzles/${encodeURIComponent(wn)}`);
                    if (puzzleData.error) { alert(`Error loading puzzle: ${puzzleData.error}`); return; }
                    AppState.puzzleName        = name;
                    AppState.puzzleWorkingName = wn;
                    AppState.puzzleData        = puzzleData;
                    AppState.puzzleSavedHash   = _hash(puzzleData.puzzle);
                    AppState.editingWord       = null;
                    showView('puzzle-editor');
                } catch (e) { alert('Error creating puzzle'); }
            });
        });
    } catch (e) { alert('Error listing grids'); }
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
        messageBox('Save puzzle', `Puzzle <b>${escapeHtml(name)}</b> saved.`, null, () => {});
    } catch (e) { alert('Error saving puzzle'); }
}

async function do_puzzle_save_as() {
    inputBox('Save puzzle as', 'Puzzle name:', AppState.puzzleName || '', async (newName) => {
        if (!newName) return;
        const wn = AppState.puzzleWorkingName;
        try {
            const data = await apiFetch('POST',
                `/api/puzzles/${encodeURIComponent(wn)}/copy`, { new_name: newName });
            if (data.error) { alert(`Save failed: ${data.error}`); return; }
            AppState.puzzleName      = newName;
            AppState.puzzleSavedHash = _hash(AppState.puzzleData.puzzle);
            renderPuzzleEditorLhs();
        } catch (e) { alert('Error saving puzzle'); }
    });
}

async function _doPuzzleCloseConfirmed() {
    const wn = AppState.puzzleWorkingName;
    AppState.puzzleName        = null;
    AppState.puzzleWorkingName = null;
    AppState.puzzleData        = null;
    AppState.puzzleSavedHash   = null;
    AppState.editingWord       = null;
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

function _updatePuzzleUndoRedo() {
    const pd = AppState.puzzleData;
    const ub = document.getElementById('puzzle-undo-btn');
    const rb = document.getElementById('puzzle-redo-btn');
if (!ub || !rb) return;
    ub.classList.toggle('w3-disabled', !pd || !pd.can_undo);
    rb.classList.toggle('w3-disabled', !pd || !pd.can_redo);
}

async function do_puzzle_undo() { await _puzzleUndoRedo('undo'); }
async function do_puzzle_redo() { await _puzzleUndoRedo('redo'); }

async function _puzzleUndoRedo(action) {
    const wn = AppState.puzzleWorkingName;
    try {
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(wn)}/${action}`);
        if (data.error) { alert(`${action} failed: ${data.error}`); return; }
        AppState.puzzleData   = data;
        AppState.editingWord  = null;
        AppState.showingStats = false;
        renderPuzzleEditor();
    } catch (e) { alert(`Error during ${action}`); }
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
                try {
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
            messageBox('New grid from puzzle', 'No saved puzzles found.', null, null);
            return;
        }
        showPreviewChooser('Choose a puzzle', puzzles, '/api/puzzles', (puzzleName) => {
            inputBox('New grid from puzzle', '<b>New grid name:</b>', '', async (gridName) => {
                if (!gridName) return;
                try {
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
            messageBox('Open grid', 'No saved grids found.', null, null);
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
        messageBox('Save grid', `Grid <b>${escapeHtml(name)}</b> saved.`, null, () => {});
    } catch (e) { alert('Error saving grid'); }
}

async function do_grid_save_as() {
    inputBox('Save grid as', 'Grid name:', AppState.gridOriginalName || '', async (newName) => {
        if (!newName) return;
        const wn = AppState.gridWorkingName;
        try {
            const data = await apiFetch('POST',
                `/api/grids/${encodeURIComponent(wn)}/copy`, { new_name: newName });
            if (data.error) { alert(`Save failed: ${data.error}`); return; }
            AppState.gridOriginalName = newName;
            AppState.gridSavedHash    = _hash(AppState.gridData.cells);
            renderGridEditor();
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
            messageBox('Publish error', err.error || `HTTP ${resp.status}`, null, null);
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
        messageBox('Publish error', 'Export request failed.', null, null);
    }
}

async function do_publish(format) {
    if (AppState.view === 'puzzle-editor' && AppState.puzzleName) {
        await _downloadExport(AppState.puzzleName, format);
    } else {
        try {
            const listData = await apiFetch('GET', '/api/puzzles');
            if (listData.error) { alert(`Error: ${listData.error}`); return; }
            const puzzles = (listData.puzzles || []).filter(p => p && !p.startsWith('__wc__'));
            if (puzzles.length === 0) {
                messageBox('Publish', 'No saved puzzles found.', null, null);
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
