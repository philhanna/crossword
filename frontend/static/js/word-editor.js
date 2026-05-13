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
// Shared selected-word state
// ---------------------------------------------------------------------------

let _weClueBeforeEdit = '';  // clue value on focus, for detecting changes on blur
let _clueDirection  = 'across'; // active clue direction in Clues tab

function _normalizeWordText(text, len) {
    return (text || '').toUpperCase().replace(/\./g, ' ').padEnd(len).slice(0, len);
}

function _getPuzzleWord(seq, direction) {
    const pd = AppState.puzzleData;
    if (!pd || !pd.puzzle || !pd.puzzle.words) return null;
    return pd.puzzle.words.find(w => w.seq === seq && w.direction === direction) || null;
}

function _isWordEditorOpen() {
    return !!(AppState.selectedWord && AppState.selectedWord.editorMode === 'word');
}

function _getSelectedWordCursorIdx() {
    return AppState.selectedWord ? AppState.selectedWord.cursorIdx || 0 : 0;
}

function _setSelectedWordCursorIdx(value) {
    if (!AppState.selectedWord) return;
    const len = AppState.selectedWord.cells.length;
    AppState.selectedWord.cursorIdx = Math.max(0, Math.min(value, len - 1));
}

function _getDefaultCursorIdx(word, text, clickR, clickC) {
    if (clickR !== undefined && clickC !== undefined) {
        const clickedIdx = word.cells.findIndex(([r, c]) => r === clickR && c === clickC);
        if (clickedIdx >= 0) return clickedIdx;
    }
    const firstBlank = text.indexOf(' ');
    return firstBlank >= 0 ? firstBlank : 0;
}

function _syncSelectedWordFromInputs() {
    const sw = AppState.selectedWord;
    if (!sw || !_isWordEditorOpen()) return;
    const textEl = document.getElementById('we-text');
    const clueEl = document.getElementById('we-clue');
    if (textEl) sw.draftText = _normalizeWordText(textEl.value, sw.cells.length);
    if (clueEl) sw.draftClue = clueEl.value || '';
}

function _selectedWordHasChanges() {
    const sw = AppState.selectedWord;
    if (!sw) return false;
    return sw.draftText !== sw.originalText || sw.draftClue !== sw.originalClue;
}

function _hydrateSelectedWord(word, options = {}) {
    if (!word) return null;
    const len = word.cells.length;
    const text = _normalizeWordText(word.answer || '', len);
    return {
        seq: word.seq,
        direction: word.direction,
        cells: word.cells,
        originalText: text,
        draftText: options.draftText !== undefined ? _normalizeWordText(options.draftText, len) : text,
        originalClue: word.clue || '',
        draftClue: options.draftClue !== undefined ? options.draftClue : (word.clue || ''),
        cursorIdx: _getDefaultCursorIdx(word, text, options.clickR, options.clickC),
        editorMode: options.editorMode || 'puzzle',
    };
}

function _refreshSelectedWordFromPuzzleData(options = {}) {
    const current = AppState.selectedWord;
    if (!current) return null;
    const word = _getPuzzleWord(current.seq, current.direction);
    if (!word) {
        AppState.selectedWord = null;
        return null;
    }
    const next = _hydrateSelectedWord(word, {
        clickR: options.clickR,
        clickC: options.clickC,
        editorMode: options.editorMode !== undefined ? options.editorMode : current.editorMode,
    });
    next.cursorIdx = options.cursorIdx !== undefined
        ? Math.max(0, Math.min(options.cursorIdx, next.cells.length - 1))
        : Math.max(0, Math.min(current.cursorIdx || 0, next.cells.length - 1));
    AppState.selectedWord = next;
    return next;
}

async function completeSelectedWordEdit(options = {}) {
    const sw = AppState.selectedWord;
    if (!sw) {
        if (options.nextSelection) {
            const next = options.nextSelection;
            selectWord(next.seq, next.direction, next.clickR, next.clickC, next.editorMode || 'puzzle');
        }
        return { saved: false, changedSelection: !!options.nextSelection, error: false };
    }

    if (_isWordEditorOpen()) _syncSelectedWordFromInputs();

    const cursorIdx = sw.cursorIdx || 0;
    const editorMode = options.editorMode !== undefined ? options.editorMode : sw.editorMode;
    const dirty = _selectedWordHasChanges();

    if (dirty) {
        const wn = AppState.puzzleWorkingName;
        try {
            const data = await apiFetch('PUT',
                `/api/puzzles/${encodeURIComponent(wn)}/words/${sw.seq}/${sw.direction}`,
                { text: sw.draftText, clue: sw.draftClue });
            if (data.error) {
                showMessageLine(`Error saving word: ${data.error}`, 'error', 0);
                return { saved: false, changedSelection: false, error: true };
            }
            AppState.puzzleData = data;
        } catch (e) {
            showMessageLine('Error saving word', 'error', 0);
            return { saved: false, changedSelection: false, error: true };
        }
    }

    if (options.keepSelection === false) {
        AppState.selectedWord = null;
    } else if (options.nextSelection) {
        const next = options.nextSelection;
        selectWord(next.seq, next.direction, next.clickR, next.clickC, next.editorMode || 'puzzle');
    } else if (AppState.selectedWord) {
        _refreshSelectedWordFromPuzzleData({ cursorIdx, editorMode });
    }

    _updatePuzzleUndoRedo();
    return { saved: dirty, changedSelection: !!options.nextSelection, error: false };
}

// ---------------------------------------------------------------------------
// Puzzle editor — click handling (single = select across, double = select down)
// ---------------------------------------------------------------------------

function _weRenderLhs() {
    const container = document.getElementById('puzzle-svg-container');
    if (!container || !AppState.puzzleData) return;
    const sw        = AppState.selectedWord;
    const editState = _isWordEditorOpen() && sw
        ? { cells: sw.cells, cursorIdx: _getSelectedWordCursorIdx(), text: sw.draftText || '' }
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
    const wasEditingWord = _isWordEditorOpen();
    if (wasEditingWord) {
        if (_clickTimeout) {
            clearTimeout(_clickTimeout);
            _clickTimeout = null;
        }
        _clickState = 0;
        _clickEvent = null;
        await _weApplyAndClose();
        if (_isWordEditorOpen()) return;
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
    if (r < 1 || r > n || c < 1 || c > n) {
        await completeSelectedWordEdit();
        renderPuzzleEditor();
        return;
    }
    if (AppState.puzzleData.grid.cells[(r - 1) * n + (c - 1)]) {
        await completeSelectedWordEdit();
        renderPuzzleEditor();
        return;
    } // black cell
    const word = findWordAtCell(r, c, direction);
    if (word) {
        const current = AppState.selectedWord;
        const inCurrentWord = current && current.seq === word.seq && current.direction === word.direction &&
            current.cells.some(([wr, wc]) => wr === r && wc === c);
        if (!inCurrentWord) {
            const result = await completeSelectedWordEdit({
                nextSelection: { seq: word.seq, direction: word.direction, clickR: r, clickC: c }
            });
            if (result.error) return;
        } else {
            const clickedIdx = current.cells.findIndex(([wr, wc]) => wr === r && wc === c);
            if (clickedIdx >= 0) _setSelectedWordCursorIdx(clickedIdx);
            if (openEditor) {
                await openWordEditor(word.seq, word.direction);
                return;
            }
        }
        if (openEditor && !_isWordEditorOpen()) await openWordEditor(word.seq, word.direction);
        else renderPuzzleEditor();
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

function selectWord(seq, direction, clickR, clickC, editorMode = 'puzzle') {
    const word = _getPuzzleWord(seq, direction);
    if (!word) return;
    AppState.selectedWord = _hydrateSelectedWord(word, { clickR, clickC, editorMode });
    _closeSidePanels();
    AppState.sidebarTab = editorMode === 'word' ? 'word' : 'clues';
    _updatePuzzleToolbar();
    renderPuzzleEditorLhs();
    renderPuzzleEditorRhs();
}

async function _peCommitWord() {
    return completeSelectedWordEdit();
}

function _peKeydown(e) {
    if (!AppState.selectedWord || _isWordEditorOpen()) return;
    // Don't capture keystrokes going to modal inputs
    const tag = e.target.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

    const sw  = AppState.selectedWord;
    const len = sw.cells.length;
    const isAcross = sw.direction === 'across';

    if (e.key === 'Escape') {
        completeSelectedWordEdit({ keepSelection: false }).then((result) => {
            if (result.error) return;
            AppState.selectedWord = null;
            _updatePuzzleToolbar();
            renderPuzzleEditor();
        });
        e.preventDefault(); return;
    }

    if ((isAcross && e.key === 'ArrowRight') || (!isAcross && e.key === 'ArrowDown')) {
        _setSelectedWordCursorIdx(_getSelectedWordCursorIdx() + 1);
        renderPuzzleEditorLhs(); e.preventDefault(); return;
    }
    if ((isAcross && e.key === 'ArrowLeft') || (!isAcross && e.key === 'ArrowUp')) {
        _setSelectedWordCursorIdx(_getSelectedWordCursorIdx() - 1);
        renderPuzzleEditorLhs(); e.preventDefault(); return;
    }

    // Cross-direction navigation: switch to perpendicular word at the same cell
    const [curR, curC] = sw.cells[_getSelectedWordCursorIdx()];
    if (!isAcross && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
        const neighbor = findWordAtCell(curR, curC, 'across');
        if (neighbor) {
            completeSelectedWordEdit({
                nextSelection: { seq: neighbor.seq, direction: neighbor.direction, clickR: curR, clickC: curC }
            }).then((result) => {
                if (!result.error) renderPuzzleEditor();
            });
        }
        e.preventDefault(); return;
    }
    if (isAcross && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
        const neighbor = findWordAtCell(curR, curC, 'down');
        if (neighbor) {
            completeSelectedWordEdit({
                nextSelection: { seq: neighbor.seq, direction: neighbor.direction, clickR: curR, clickC: curC }
            }).then((result) => {
                if (!result.error) renderPuzzleEditor();
            });
        }
        e.preventDefault(); return;
    }

    if (e.key === 'Delete') {
        const idx = _getSelectedWordCursorIdx();
        const t = sw.draftText;
        sw.draftText = t.slice(0, idx) + ' ' + t.slice(idx + 1);
        renderPuzzleEditorLhs(); e.preventDefault(); return;
    }

    if (e.key === 'Backspace') {
        let idx = _getSelectedWordCursorIdx();
        const t = sw.draftText;
        if (t[idx] !== ' ') {
            sw.draftText = t.slice(0, idx) + ' ' + t.slice(idx + 1);
        } else if (idx > 0) {
            idx--;
            _setSelectedWordCursorIdx(idx);
            sw.draftText = sw.draftText.slice(0, idx) + ' ' + sw.draftText.slice(idx + 1);
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
        completeSelectedWordEdit({
            nextSelection: { seq: next.seq, direction: next.direction }
        }).then((result) => {
            if (!result.error) renderPuzzleEditor();
        });
        return;
    }

    if (e.key === ' ' || (e.key.length === 1 && /^[a-zA-Z]$/.test(e.key))) {
        const ch = e.key === ' ' ? ' ' : e.key.toUpperCase();
        const idx = _getSelectedWordCursorIdx();
        const t = sw.draftText;
        sw.draftText = t.slice(0, idx) + ch + t.slice(idx + 1);
        // Advance cursor one step forward
        if (idx < len - 1) _setSelectedWordCursorIdx(idx + 1);
        renderPuzzleEditorLhs(); e.preventDefault();
    }
}

function _peOutsideMousedown(e) {
    if (!AppState.selectedWord || _isWordEditorOpen()) return;
    const svg = document.getElementById('puzzle-svg');
    if (svg && svg.contains(e.target)) return; // SVG clicks handled by puzzleClickAt
    if (e.target.closest && (
        e.target.closest('#action-bar') ||
        e.target.closest('#rhs') ||
        e.target.closest('.app-bar') ||
        e.target.closest('#mb') ||
        e.target.closest('#ib') ||
        e.target.closest('#ch') ||
        e.target.closest('#constraints-popup') ||
        e.target.closest('#defs-popup') ||
        e.target.closest('button') ||
        e.target.closest('a') ||
        e.target.closest('input') ||
        e.target.closest('textarea') ||
        e.target.closest('select') ||
        e.target.closest('label')
    )) {
        return;
    }
    completeSelectedWordEdit().then((result) => {
        if (!result.error) renderPuzzleEditor();
    });
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
    const result = await completeSelectedWordEdit();
    if (result.error) return;
    openWordEditor(targetSeq, targetDir);
}

// ---------------------------------------------------------------------------
// Word editor panel
// ---------------------------------------------------------------------------

function renderWordEditorPanel() {
    const sw       = AppState.selectedWord;
    const clue     = sw.draftClue || '';
    const dirLabel = sw.direction.charAt(0).toUpperCase() + sw.direction.slice(1);
    const len      = sw.cells.length;
    const text     = (sw.draftText || '').padEnd(len).slice(0, len);
    const defsDisabled = /^[A-Za-z]+$/.test(text.trim()) && text.trim().length === len ? '' : 'disabled';

    return `
<div id="we-dialog" class="we-panel">
  <div class="we-header">
    <div class="we-header-info">
      <div class="we-header-title">${sw.seq} ${dirLabel}</div>
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
             oninput="weHandleClueInput(this.value)"
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
    return AppState.selectedWord ? (AppState.selectedWord.draftText || '') : '';
}

function _weSyncAnswerFromInput() {
    const sw = AppState.selectedWord;
    if (!sw) return '';
    const len = sw.cells.length;
    const rawText = _weGetRawInputText();
    sw.draftText = _normalizeWordText(rawText, len);
    return rawText;
}

function weHandleTextInput(value) {
    const sw = AppState.selectedWord;
    if (sw) sw.draftText = _normalizeWordText(value, sw.cells.length);
    weUpdateDefinitionsBtn();
    renderPuzzleEditorLhs();
}

function weHandleClueInput(value) {
    if (AppState.selectedWord) AppState.selectedWord.draftClue = value;
}

function _weSyncTextInputFromAnswer() {
    const inp = document.getElementById('we-text');
    if (!inp || !AppState.selectedWord) return;
    inp.value = (AppState.selectedWord.draftText || '').replace(/ /g, '.');
    weUpdateDefinitionsBtn();
}

function weUpdateDefinitionsBtn() {
    const inp = document.getElementById('we-text');
    const btn = document.getElementById('we-definitions-btn');
    if (!inp || !btn) return;
    const len = AppState.selectedWord ? AppState.selectedWord.cells.length : 0;
    const val = inp.value;
    btn.disabled = !(val.length === len && /^[A-Za-z]+$/.test(val));
}

function _weOnClueBlur(newVal) {
    _weClueBeforeEdit = newVal;
    if (AppState.selectedWord) AppState.selectedWord.draftClue = newVal;
}

// ---------------------------------------------------------------------------
// Word editor — change detection + apply-on-navigate
// ---------------------------------------------------------------------------

function _weHasChanges() {
    _syncSelectedWordFromInputs();
    return _selectedWordHasChanges();
}

async function _weApplyAndClose() {
    const result = await completeSelectedWordEdit({ editorMode: 'puzzle' });
    if (!result.error) closeWordEditor();
}

// ---------------------------------------------------------------------------
// Word editor — keyboard handler
// ---------------------------------------------------------------------------

async function _weKeydown(e) {
    if (!_isWordEditorOpen()) return;
    const tag = e.target.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA') {
        if (e.key === 'Escape') { closeWordEditor();     e.preventDefault(); }
        if (e.key === 'Enter' && e.target.id === 'we-text') { doWordSuggestFetch(); e.preventDefault(); }
        if (e.key === 'Enter' && e.target.id !== 'we-text') { doWordEditOK();       e.preventDefault(); }
        return;
    }
    // For buttons and other controls, keep native Enter behavior. When focus is
    // on the grid SVG itself, Enter should mirror the Apply button.
    if (e.key === 'Escape') { closeWordEditor(); e.preventDefault(); return; }
    if (e.key === 'Enter' && e.target.closest && e.target.closest('#puzzle-svg')) {
        doWordEditOK();
        e.preventDefault();
        return;
    }

    const sw = AppState.selectedWord;
    const len = sw.cells.length;

    const isAcross    = sw.direction === 'across';
    const forwardKey  = isAcross ? 'ArrowRight' : 'ArrowDown';
    const backwardKey = isAcross ? 'ArrowLeft'  : 'ArrowUp';

    if (e.key === forwardKey && _getSelectedWordCursorIdx() < len - 1) {
        _setSelectedWordCursorIdx(_getSelectedWordCursorIdx() + 1);
        renderPuzzleEditorLhs();
        e.preventDefault();
        return;
    }
    if (e.key === backwardKey && _getSelectedWordCursorIdx() > 0) {
        _setSelectedWordCursorIdx(_getSelectedWordCursorIdx() - 1);
        renderPuzzleEditorLhs();
        e.preventDefault();
        return;
    }
    if ((isAcross && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) ||
        (!isAcross && (e.key === 'ArrowLeft' || e.key === 'ArrowRight'))) {
        const [curR, curC] = sw.cells[_getSelectedWordCursorIdx()];
        const perpDir = isAcross ? 'down' : 'across';
        const neighbor = findWordAtCell(curR, curC, perpDir);
        const result = await completeSelectedWordEdit({
            nextSelection: neighbor ? {
                seq: neighbor.seq,
                direction: neighbor.direction,
                clickR: curR,
                clickC: curC,
            } : null
        });
        if (result.error) return;
        if (!neighbor) closeWordEditor();
        else await openWordEditor(neighbor.seq, neighbor.direction);
        e.preventDefault();
        return;
    }

    if (e.key === 'Delete') {
        const idx = _getSelectedWordCursorIdx();
        const t = sw.draftText || ''.padEnd(len);
        sw.draftText = t.slice(0, idx) + ' ' + t.slice(idx + 1);
        _weSyncTextInputFromAnswer();
        renderPuzzleEditorLhs();
        e.preventDefault();
        return;
    }

    if (e.key === 'Backspace') {
        let idx = _getSelectedWordCursorIdx();
        const t = sw.draftText || ''.padEnd(len);
        if (t[idx] !== ' ') {
            sw.draftText = t.slice(0, idx) + ' ' + t.slice(idx + 1);
        } else if (idx > 0) {
            idx--;
            _setSelectedWordCursorIdx(idx);
            sw.draftText = t.slice(0, idx) + ' ' + t.slice(idx + 1);
        }
        _weSyncTextInputFromAnswer();
        renderPuzzleEditorLhs();
        e.preventDefault();
        return;
    }

    if (e.key === ' ' || (e.key.length === 1 && /^[a-zA-Z]$/.test(e.key))) {
        const ch = e.key === ' ' ? ' ' : e.key.toUpperCase();
        const idx = _getSelectedWordCursorIdx();
        const t = (sw.draftText || '').padEnd(len).slice(0, len);
        sw.draftText = t.slice(0, idx) + ch + t.slice(idx + 1);
        if (idx < len - 1) _setSelectedWordCursorIdx(idx + 1);
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
    const selectedWord = AppState.selectedWord;
    if (selectedWord && selectedWord.seq === seq && selectedWord.direction === direction) {
        selectedWord.editorMode = 'word';
    } else {
        selectWord(seq, direction, undefined, undefined, 'word');
    }
    AppState.sidebarTab  = 'word';
    _weSuggestions = [];
    _wePage        = 0;
    document.removeEventListener('keydown', _peKeydown);
    document.addEventListener('keydown', _weKeydown);
    updateMenu();
    renderPuzzleEditor();
}

function closeWordEditor() {
    document.removeEventListener('keydown', _weKeydown);
    document.addEventListener('keydown', _peKeydown);
    if (AppState.selectedWord) {
        AppState.selectedWord.draftText = AppState.selectedWord.originalText;
        AppState.selectedWord.draftClue = AppState.selectedWord.originalClue;
        AppState.selectedWord.editorMode = 'puzzle';
    }
    AppState.showingStats = false;
    AppState.sidebarTab   = 'clues';
    _weSuggestions = [];
    _wePage        = 0;
    updateMenu();
    renderPuzzleEditor();
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
        if (!_isWordEditorOpen()) return;
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
        if (!_isWordEditorOpen()) return;
        const matchEl = document.getElementById('we-match');
        if (matchEl) { matchEl.innerHTML = 'Error fetching suggestions'; matchEl.style.display = 'block'; }
    }
}

async function _fetchConstrainedSuggestions() {
    const sw = AppState.selectedWord;
    const wn = AppState.puzzleWorkingName;
    { const m = document.getElementById('we-match'); if (m) m.style.display = 'none'; }
    try {
        const rawText = _weSyncAnswerFromInput();
        const pattern = rawText.replace(/ /g, '.').toUpperCase();
        const data = await apiFetch('GET',
            `/api/puzzles/${encodeURIComponent(wn)}/words/${sw.seq}/${sw.direction}/suggestions?pattern=${encodeURIComponent(pattern)}`);
        if (!_isWordEditorOpen()) return;
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
        if (!_isWordEditorOpen()) return;
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
    const sw = AppState.selectedWord;
    const wn = AppState.puzzleWorkingName;

    const titleEl = document.getElementById('constraints-popup-title');
    const bodyEl  = document.getElementById('constraints-popup-body');
    titleEl.textContent = `Constraints — ${sw.seq} ${sw.direction === 'across' ? 'Across' : 'Down'}`;
    bodyEl.innerHTML = 'Loading…';
    showElement('constraints-popup');

    try {
        const data = await apiFetch('GET',
            `/api/puzzles/${encodeURIComponent(wn)}/words/${sw.seq}/${sw.direction}/constraints`);
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
    const result = await completeSelectedWordEdit({ editorMode: 'puzzle' });
    if (!result.error) closeWordEditor();
}
