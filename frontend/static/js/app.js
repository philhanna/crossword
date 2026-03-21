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
    gridName: null,          // name of currently-open grid (original)
    puzzleName: null,        // name of currently-open puzzle (original)
    puzzleWorkingName: null, // working copy name (e.g. '__wc__a1b2c3d4')
    puzzleData: null,        // response from GET /api/puzzles/{workingName}
    editingWord: null,       // null | {seq, direction, cells, answer, clue}
};

// ---------------------------------------------------------------------------
// Utility helpers
// ---------------------------------------------------------------------------

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
        a.className = 'w3-bar-item w3-button';
        a.textContent = item;
        a.onclick = () => { hideElement('ch'); onSelect(item); };
        listEl.appendChild(a);
    }
    showElement('ch');
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
    menuDisable('menu-grid-delete');

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

function renderGridEditor() { /* Phase 2 */ }

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
    <a class="w3-bar-item w3-button crosstb" onclick="do_puzzle_title()">
      <i class="material-icons crosstb-icon">title</i><span>Title</span></a>
    <a class="w3-bar-item w3-button crosstb" onclick="do_puzzle_undo()">
      <i class="material-icons crosstb-icon">undo</i><span>Undo</span></a>
    <a class="w3-bar-item w3-button crosstb" onclick="do_puzzle_redo()">
      <i class="material-icons crosstb-icon">redo</i><span>Redo</span></a>
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
}

function renderPuzzleEditorRhs() {
    document.getElementById('rhs').innerHTML =
        AppState.editingWord ? renderWordEditorPanel() : renderClues();
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
    AppState.editingWord = null;
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
        // Save each cell letter in parallel
        await Promise.all(
            ew.cells.map(([r, c], i) =>
                apiFetch('PUT',
                    `/api/puzzles/${encodeURIComponent(wn)}/cells/${r}/${c}`,
                    { letter: text[i] })
            )
        );

        // Save clue
        await apiFetch('PUT',
            `/api/puzzles/${encodeURIComponent(wn)}/words/${ew.seq}/${ew.direction}`,
            { clue });

        // Reload and re-render
        const fresh = await apiFetch('GET', `/api/puzzles/${encodeURIComponent(wn)}`);
        if (fresh.error) { alert(`Error reloading puzzle: ${fresh.error}`); return; }
        AppState.puzzleData  = fresh;
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
        const puzzles = (listData.puzzles || []).filter(p => !p.startsWith('__wc__'));
        if (puzzles.length === 0) {
            messageBox('Open puzzle', 'No saved puzzles found.', null, null);
            return;
        }
        showChooser('Open puzzle', puzzles, async (name) => {
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
                AppState.editingWord       = null;
                showView('puzzle-editor');
            } catch (e) { alert('Error opening puzzle'); }
        });
    } catch (e) {
        alert('Error listing puzzles');
    }
}

function do_puzzle_new() {
    alert('New puzzle — coming in Phase 3 (requires grid chooser)');
}

async function do_puzzle_save() {
    const wn   = AppState.puzzleWorkingName;
    const name = AppState.puzzleName;
    if (!name) { do_puzzle_save_as(); return; }
    try {
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(wn)}/copy`, { new_name: name });
        if (data.error) alert(`Save failed: ${data.error}`);
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
            AppState.puzzleName = newName;
            renderPuzzleEditorLhs();
        } catch (e) { alert('Error saving puzzle'); }
    });
}

async function do_puzzle_close() {
    const wn = AppState.puzzleWorkingName;
    AppState.puzzleName        = null;
    AppState.puzzleWorkingName = null;
    AppState.puzzleData        = null;
    AppState.editingWord       = null;
    if (wn) {
        try { await apiFetch('DELETE', `/api/puzzles/${encodeURIComponent(wn)}`); }
        catch (e) { /* ignore cleanup errors */ }
    }
    showView('home');
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

async function do_puzzle_undo() { await _puzzleUndoRedo('undo'); }
async function do_puzzle_redo() { await _puzzleUndoRedo('redo'); }

async function _puzzleUndoRedo(action) {
    const wn = AppState.puzzleWorkingName;
    try {
        const data = await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(wn)}/${action}`);
        if (data.error) { alert(`${action} failed: ${data.error}`); return; }
        AppState.puzzleData  = data;
        AppState.editingWord = null;
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
// Menu actions — Grid (Phase 2 stubs)
// ---------------------------------------------------------------------------

function do_grid_new() {
    inputBox(
        'New grid',
        '<b>Grid size:</b> <em>(a single odd positive integer)</em>',
        '',
        (value) => {
            const n = Number(value);
            if (!value || isNaN(n))  { alert(value + ' is not a number'); return; }
            if (n % 2 === 0)         { alert(n + ' is not an odd number'); return; }
            if (n < 1)               { alert(n + ' is not a positive number'); return; }
            alert(`Create ${n}×${n} grid — coming in Phase 2`);
        }
    );
}

function do_grid_new_from_puzzle() { alert('New grid from puzzle — coming in Phase 2'); }
function do_grid_open()            { alert('Open grid — coming in Phase 2'); }
function do_grid_save()            { alert('Save grid — coming in Phase 2'); }
function do_grid_save_as()         { alert('Save grid as — coming in Phase 2'); }
function do_grid_close()           { AppState.gridName = null; showView('home'); }
function do_grid_delete()          { alert('Delete grid — coming in Phase 2'); }

// ---------------------------------------------------------------------------
// Menu actions — Publish (Phase 5 stub)
// ---------------------------------------------------------------------------

function do_publish(format) {
    if (!AppState.puzzleName) return;
    alert(`Publish "${AppState.puzzleName}" as ${format} — coming in Phase 5`);
}

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------

document.addEventListener('DOMContentLoaded', () => {
    showView('home');
});
