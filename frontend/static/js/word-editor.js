// Crossword Puzzle Editor — click handling, word selection, keyboard entry, word editor panel

// ---------------------------------------------------------------------------
// Puzzle editor — click handling state
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
const WE_PAGE_SIZE           = 5;

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

// ---------------------------------------------------------------------------
// Puzzle editor — click handling (single = select across, double = select down)
// ---------------------------------------------------------------------------

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

function _focusPuzzleSvg() {
    const svg = document.getElementById('puzzle-svg');
    if (!svg) return;
    try {
        svg.focus({ preventScroll: true });
    } catch (e) {
        svg.focus();
    }
}

async function handlePuzzleClick(event) {
    if (Date.now() < _ignorePuzzleClicksUntil) return;
    const wasEditingWord = !!AppState.editingWord;
    if (AppState.editingWord) {
        if (_clickTimeout) {
            clearTimeout(_clickTimeout);
            _clickTimeout = null;
        }
        _clickState = 0;
        _clickEvent = null;
        await _weApplyAndClose();
    }
    _focusPuzzleSvg();
    _clickEvent = event;
    if (_clickState === 0) {
        _clickState = 1;
        _clickTimeout = setTimeout(() => {
            _clickState = 0;
            _clickTimeout = null;
            puzzleClickAt(_clickEvent, 'across', !wasEditingWord);
        }, CLICK_DELAY);
    } else {
        _clickState = 0;
        clearTimeout(_clickTimeout);
        _clickTimeout = null;
        puzzleClickAt(event, 'down', !wasEditingWord);
    }
}

async function puzzleClickAt(event, direction, openEditor = true) {
    const svg = document.getElementById('puzzle-svg');
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const r = Math.floor(1 + y / BOXSIZE);
    const c = Math.floor(1 + x / BOXSIZE);
    const n = AppState.puzzleData.grid.size;
    if (r < 1 || r > n || c < 1 || c > n) { await _peCommitWord(); return; }
    if (AppState.puzzleData.grid.cells[(r - 1) * n + (c - 1)]) { await _peCommitWord(); return; } // black cell
    const word = findWordAtCell(r, c, direction);
    if (word) {
        await _peCommitWord();
        selectWord(word.seq, word.direction, r, c);
        if (openEditor) await openWordEditor(word.seq, word.direction);
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
    AppState.sidebarTab = 'word';
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
        if (data.error) { showMessageLine(`Error saving word: ${data.error}`, 'error', 0); return; }
        AppState.puzzleData      = data;
        sw.initialText           = sw.currentText;
        _updatePuzzleUndoRedo();
    } catch (e) { showMessageLine('Error saving word', 'error', 0); }
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

function _peOutsideMousedown(e) {
    if (!AppState.selectedWord || AppState.editingWord) return;
    const svg = document.getElementById('puzzle-svg');
    if (svg && svg.contains(e.target)) return; // SVG clicks handled by puzzleClickAt
    _peCommitWord(); // fire-and-forget
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
             oninput="weHandleTextInput(this.value)"/>
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
    _weSyncAnswerFromInput();
    weUpdateDefinitionsBtn();
    // Highlight selected item
    document.querySelectorAll('#we-suggestion-list li').forEach(li => {
        li.style.background = li.dataset.word === word ? '#d0e8ff' : '';
    });
}

async function weListItemDoubleClick(word) {
    weListItemClick(word);
    await doWordEditOK();
}

function _weGetRawInputText() {
    const inp = document.getElementById('we-text');
    if (inp) return inp.value;
    return AppState.editingWord ? (AppState.editingWord.answer || '') : '';
}

function _weSyncAnswerFromInput() {
    if (!AppState.editingWord) return '';
    const len = AppState.editingWord.cells.length;
    const rawText = _weGetRawInputText();
    const normalized = rawText.replace(/\./g, ' ').toUpperCase().padEnd(len).slice(0, len);
    AppState.editingWord.answer = normalized;
    return rawText;
}

function weHandleTextInput(value) {
    if (AppState.editingWord) {
        const len = AppState.editingWord.cells.length;
        AppState.editingWord.answer = value.replace(/\./g, ' ').toUpperCase().padEnd(len).slice(0, len);
    }
    weUpdateDefinitionsBtn();
}

function _weSyncTextInputFromAnswer() {
    const inp = document.getElementById('we-text');
    if (!inp || !AppState.editingWord) return;
    inp.value = (AppState.editingWord.answer || '').replace(/ /g, '.');
    weUpdateDefinitionsBtn();
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
// Word editor — change detection + apply-on-navigate
// ---------------------------------------------------------------------------

function _weHasChanges() {
    const ew = AppState.editingWord;
    if (!ew) return false;
    const len     = ew.cells.length;
    const textEl  = document.getElementById('we-text');
    const clueEl  = document.getElementById('we-clue');
    if (!textEl || !clueEl) return false;
    const curText = (textEl.value || '').toUpperCase().replace(/\./g, ' ').padEnd(len).slice(0, len);
    const origText = (ew._origAnswer || '').padEnd(len).slice(0, len);
    return curText !== origText || (clueEl.value || '') !== ew._origClue;
}

async function _weApplyAndClose() {
    if (_weHasChanges()) {
        await doWordEditOK();
    } else {
        closeWordEditor();
    }
}

// ---------------------------------------------------------------------------
// Word editor — keyboard handler
// ---------------------------------------------------------------------------

async function _weKeydown(e) {
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
    if (e.key === 'Escape') { closeWordEditor(); e.preventDefault(); return; }

    const ew = AppState.editingWord;
    const len = ew.cells.length;

    const isAcross    = ew.direction === 'across';
    const forwardKey  = isAcross ? 'ArrowRight' : 'ArrowDown';
    const backwardKey = isAcross ? 'ArrowLeft'  : 'ArrowUp';

    if (e.key === forwardKey && _weCursorIdx < len - 1) {
        _weCursorIdx++;
        renderPuzzleEditorLhs();
        e.preventDefault();
        return;
    }
    if (e.key === backwardKey && _weCursorIdx > 0) {
        _weCursorIdx--;
        renderPuzzleEditorLhs();
        e.preventDefault();
        return;
    }
    if ((isAcross && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) ||
        (!isAcross && (e.key === 'ArrowLeft' || e.key === 'ArrowRight'))) {
        const [curR, curC] = ew.cells[_weCursorIdx];
        const perpDir = isAcross ? 'down' : 'across';
        const neighbor = findWordAtCell(curR, curC, perpDir);
        await _weApplyAndClose();
        if (neighbor) selectWord(neighbor.seq, neighbor.direction, curR, curC);
        e.preventDefault();
        return;
    }

    if (e.key === 'Delete') {
        const t = ew.answer || ''.padEnd(len);
        ew.answer = t.slice(0, _weCursorIdx) + ' ' + t.slice(_weCursorIdx + 1);
        _weSyncTextInputFromAnswer();
        renderPuzzleEditorLhs();
        e.preventDefault();
        return;
    }

    if (e.key === 'Backspace') {
        const t = ew.answer || ''.padEnd(len);
        if (t[_weCursorIdx] !== ' ') {
            ew.answer = t.slice(0, _weCursorIdx) + ' ' + t.slice(_weCursorIdx + 1);
        } else if (_weCursorIdx > 0) {
            _weCursorIdx--;
            ew.answer = t.slice(0, _weCursorIdx) + ' ' + t.slice(_weCursorIdx + 1);
        }
        _weSyncTextInputFromAnswer();
        renderPuzzleEditorLhs();
        e.preventDefault();
        return;
    }

    if (e.key === ' ' || (e.key.length === 1 && /^[a-zA-Z]$/.test(e.key))) {
        const ch = e.key === ' ' ? ' ' : e.key.toUpperCase();
        const t = (ew.answer || '').padEnd(len).slice(0, len);
        ew.answer = t.slice(0, _weCursorIdx) + ch + t.slice(_weCursorIdx + 1);
        if (_weCursorIdx < len - 1) _weCursorIdx++;
        _weSyncTextInputFromAnswer();
        renderPuzzleEditorLhs();
        e.preventDefault();
    }
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
        if (data.error) { showMessageLine(`Word not found: ${data.error}`, 'error', 0); return; }
        const selectedWord = AppState.selectedWord;
        if (selectedWord && selectedWord.seq === seq && selectedWord.direction === direction) {
            _weCursorIdx = _peCursorIdx;
        } else {
            const text = (data.answer || '').padEnd(data.cells.length).slice(0, data.cells.length);
            const firstBlank = text.indexOf(' ');
            _weCursorIdx = firstBlank >= 0 ? firstBlank : 0;
        }
        AppState.editingWord = {
            seq:         data.seq,
            direction:   data.direction,
            cells:       data.cells,
            answer:      data.answer,
            clue:        data.clue,
            _origAnswer: data.answer || '',
            _origClue:   data.clue   || '',
        };
        AppState.sidebarTab  = 'word';
        _weSuggestions = [];
        _wePage        = 0;
        document.removeEventListener('keydown', _peKeydown);
        document.addEventListener('keydown', _weKeydown);
        updateMenu();
        renderPuzzleEditorLhs();
        renderPuzzleEditorRhs();
        _updatePuzzleUndoRedo();
    } catch (e) {
        showMessageLine('Error opening word editor', 'error', 0);
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
    updateMenu();
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
    const rawText = _weSyncAnswerFromInput();
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
        const rawText = _weSyncAnswerFromInput();
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
        li.ondblclick  = () => weListItemDoubleClick(word);

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
    titleEl.textContent = `Constraints — ${ew.seq} ${ew.direction === 'across' ? 'Across' : 'Down'}`;
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
        if (data.error) { showMessageLine(`Error saving word: ${data.error}`, 'error', 0); return; }
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
        showMessageLine('Error saving word', 'error', 0);
    }
}
