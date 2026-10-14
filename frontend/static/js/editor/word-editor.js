// Crossword Puzzle Editor — the word editor panel: answer, clue, lock, suggestions

import { registerActions } from '../core/actions.js';
import {
    _currentEditorMode, renderPuzzleEditor, renderPuzzleEditorLhs,
    renderPuzzleEditorRhs,
} from './editor.js';
import { _peKeydown, _weKeydown } from './keyboard.js';
import {
    _isWordEditorOpen, _normalizeWordText, completeSelectedWordEdit, selectWord,
} from './selection.js';
import { AppState } from '../state.js';
import { ApiError, apiFetch, escapeHtml, showElement, updateMenu } from '../ui.js';

registerActions({
    // From a clue row the word is named; from the toolbar it's the selected one
    'edit-word': (el) => (el.dataset.seq
        ? do_puzzle_edit_word(Number(el.dataset.seq), el.dataset.direction)
        : do_puzzle_edit_word()),
    'open-word': (el) => _openWordFromPanel(Number(el.dataset.seq), el.dataset.direction),

    'word-editor-cancel':   () => closeWordEditor(),
    'word-lock':            (el) => weHandleLockToggle(el.checked),
    'word-answer':          (el) => weHandleTextInput(el.value),
    'word-clue':            (el) => weHandleClueInput(el.value),
    'word-suggest':         () => doWordSuggestFetch(),
    'word-suggestion-page': (el) => (el.dataset.page === 'prev' ? wePagePrev() : wePageNext()),
    'word-constraints':     () => doWordConstraints(),
    'word-definitions':     () => doWordDefinitions(),
    'word-apply':           () => doWordEditOK(),
});

let _weSuggestions           = [];    // full list from last fetch: string[] or {word,score}[]
let _weSuggestionsConstrained = false; // true when last fetch was constrained (has scores)
let _wePage                  = 0;     // current page (0-indexed)
const WE_PAGE_SIZE           = 5;

// ---------------------------------------------------------------------------
// Open, apply, close
// ---------------------------------------------------------------------------

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

// Open the word editor on a word picked from the stats or fill-order panel
async function _openWordFromPanel(seq, dir) {
    const result = await completeSelectedWordEdit({
        nextSelection: { seq, direction: dir }
    });
    if (result.error) return;
    await openWordEditor(seq, dir);
}

export async function openWordEditor(seq, direction) {
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

export function closeWordEditor() {
    document.removeEventListener('keydown', _weKeydown);
    document.addEventListener('keydown', _peKeydown);
    if (AppState.selectedWord) {
        AppState.selectedWord.draftText = AppState.selectedWord.originalText;
        AppState.selectedWord.draftClue = AppState.selectedWord.originalClue;
        AppState.selectedWord.draftLocked = AppState.selectedWord.originalLocked;
        AppState.selectedWord.editorMode = 'puzzle';
    }
    AppState.showingStats = false;
    AppState.sidebarTab   = 'clues';
    _weSuggestions = [];
    _wePage        = 0;
    updateMenu();
    renderPuzzleEditor();
}

export async function doWordEditOK() {
    // A lone suggestion is the only possible answer, so take it — unless
    // the user has already typed a complete answer of their own
    if (_weSuggestions.length === 1 && !_weInputIsCompleteAnswer()) {
        const only = _weSuggestions[0];
        weListItemClick(_weSuggestionsConstrained ? only.word : only);
    }
    const result = await completeSelectedWordEdit({ editorMode: 'puzzle' });
    if (!result.error) closeWordEditor();
}

function _weInputIsCompleteAnswer() {
    const sw = AppState.selectedWord;
    if (!sw) return false;
    const raw = _weGetRawInputText();
    return raw.length === sw.cells.length && /^[A-Za-z]+$/.test(raw);
}

export async function _weApplyAndClose() {
    const result = await completeSelectedWordEdit({ editorMode: 'puzzle' });
    if (!result.error) closeWordEditor();
}

// ---------------------------------------------------------------------------
// Panel
// ---------------------------------------------------------------------------

export function renderWordEditorPanel() {
    const sw       = AppState.selectedWord;
    const clue     = sw.draftClue || '';
    const dirLabel = sw.direction.charAt(0).toUpperCase() + sw.direction.slice(1);
    const len      = sw.cells.length;
    const text     = (sw.draftText || '').padEnd(len).slice(0, len);
    const locked   = !!sw.draftLocked;
    const lockDisabled = locked ? 'disabled' : '';
    const defsDisabled = (!locked && /^[A-Za-z]+$/.test(text.trim()) && text.trim().length === len) ? '' : 'disabled';

    return `
<div id="we-dialog" class="we-panel">
  <div class="we-header">
    <div class="we-header-info">
      <div class="we-header-title">${sw.seq} ${dirLabel}</div>
      <div class="we-header-sub">${len} letters</div>
    </div>
    <button class="we-header-close" data-action="word-editor-cancel" aria-label="Close">&times;</button>
  </div>

  <div class="we-body">
    <!-- Lock -->
    <div class="we-field we-lock-row">
      <label style="cursor:pointer;display:flex;align-items:center;gap:6px">
        <input type="checkbox" id="we-locked" ${locked ? 'checked' : ''} data-change="word-lock"> Lock word
      </label>
    </div>

    <!-- Answer -->
    <div class="we-field">
      <label class="we-label">Answer</label>
      <div style="position:relative">
        <input class="we-word-input" id="we-text" type="text" ${lockDisabled}
               value="${escapeHtml(text.replace(/ /g, '.'))}"
               data-input="word-answer"/>
        ${locked ? '<i class="material-icons" style="position:absolute;right:8px;top:50%;transform:translateY(-50%);font-size:16px;color:var(--c-text-muted)">lock</i>' : ''}
      </div>
    </div>

    <!-- Clue -->
    <div class="we-field">
      <label class="we-label">Clue</label>
      <input class="we-clue-input" id="we-clue" type="text"
             value="${escapeHtml(clue)}"
             data-input="word-clue"
             placeholder="Enter clue…"/>
    </div>

    <!-- Suggestions -->
    <div class="we-field">
      <div class="we-suggestions-toolbar">
        <label class="we-label" style="margin:0">Suggestions</label>
        <label style="cursor:pointer;font-size:0.78rem;color:var(--c-text-muted);display:flex;align-items:center;gap:4px">
          <input type="checkbox" id="we-constrained" checked> Constrained
        </label>
        <button class="ab-btn" type="button" ${lockDisabled} data-action="word-suggest" style="height:26px;font-size:0.75rem">
          <i class="material-icons" style="font-size:13px">search</i> Suggest
        </button>
      </div>
      <div id="we-match" class="we-match-label" style="display:none"></div>
      <ul id="we-suggestion-list" class="we-suggestion-list" style="display:none"></ul>
      <div id="we-pagination" style="display:none;margin-top:4px;align-items:center;gap:8px">
        <button class="ab-btn" type="button" id="we-page-prev" data-action="word-suggestion-page" data-page="prev" style="height:24px;padding:0 8px">&#9664;</button>
        <span id="we-page-label" style="flex:1;text-align:center;font-size:0.78rem;color:var(--c-text-muted)"></span>
        <button class="ab-btn" type="button" id="we-page-next" data-action="word-suggestion-page" data-page="next" style="height:24px;padding:0 8px">&#9654;</button>
      </div>
    </div>

    <!-- Secondary tools -->
    <div class="we-secondary-tools">
      <button class="ab-btn" id="we-constraints-btn" type="button" ${lockDisabled} data-action="word-constraints" style="font-size:0.78rem">
        <i class="material-icons" style="font-size:13px">assignment</i> Constraints
      </button>
      <button class="ab-btn" id="we-definitions-btn" type="button" ${defsDisabled} data-action="word-definitions" style="font-size:0.78rem">
        <i class="material-icons" style="font-size:13px">menu_book</i> Definitions
      </button>
    </div>

    <!-- Action row -->
    <div class="we-action-row">
      <button class="btn btn-primary" type="button" data-action="word-apply">Apply</button>
      <button class="btn btn-secondary" type="button" data-action="word-editor-cancel">Cancel</button>
    </div>
  </div>
</div>`;
}

export function _syncSelectedWordFromInputs() {
    const sw = AppState.selectedWord;
    if (!sw || !_isWordEditorOpen()) return;
    const textEl = document.getElementById('we-text');
    const clueEl = document.getElementById('we-clue');
    if (textEl) sw.draftText = _normalizeWordText(textEl.value, sw.cells.length);
    if (clueEl) sw.draftClue = clueEl.value || '';
}

function weHandleTextInput(value) {
    const sw = AppState.selectedWord;
    if (!sw) return;
    weUpdateDefinitionsBtn();
    // The field doubles as a search pattern box (in either Constrained
    // state) and a direct draft-answer box. Only treat it as a draft
    // answer — updating draftText and the live grid preview — when its
    // contents could plausibly be one; a longer or regex-flavored value is
    // a search pattern, and shouldn't flash into the grid while typed.
    if (!_weLooksLikeDraftAnswer(value, sw.cells.length)) return;
    sw.draftText = _normalizeWordText(value, sw.cells.length);
    renderPuzzleEditorLhs();
}

function _weLooksLikeDraftAnswer(value, len) {
    return value.length <= len && /^[A-Za-z. ]*$/.test(value);
}

function weHandleClueInput(value) {
    if (AppState.selectedWord) AppState.selectedWord.draftClue = value;
}

function weHandleLockToggle(checked) {
    const sw = AppState.selectedWord;
    if (!sw) return;
    sw.draftLocked = checked;
    renderPuzzleEditorRhs();
}

export function _weSyncTextInputFromAnswer() {
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

// ---------------------------------------------------------------------------
// Suggestions
// ---------------------------------------------------------------------------

export async function doWordSuggestFetch() {
    const constrained = _weIsConstrained();
    if (constrained) {
        await _fetchConstrainedSuggestions();
    } else {
        await _fetchPatternSuggestions();
    }
}

function _weIsConstrained() {
    return document.getElementById('we-constrained')?.checked ?? true;
}

async function _fetchPatternSuggestions() {
    { const m = document.getElementById('we-match'); if (m) m.style.display = 'none'; }
    const rawText = _weSyncAnswerFromInput();
    const pattern = rawText.replace(/ /g, '.').toUpperCase();
    if (!pattern) return;
    try {
        const sw = AppState.selectedWord;
        const wn = AppState.puzzleWorkingName;
        const puzzleParams = (sw && wn)
            ? `&puzzle=${encodeURIComponent(wn)}&seq=${sw.seq}&direction=${sw.direction}`
            : '';
        const data = await apiFetch('GET',
            `/api/words/suggestions?pattern=${encodeURIComponent(pattern)}${puzzleParams}`);
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

        // A pattern the server can't search with simply matches nothing
        const matchEl = document.getElementById('we-match');
        const text = e instanceof ApiError ? 'No matches found' : 'Error fetching suggestions';
        if (matchEl) { matchEl.innerHTML = text; matchEl.style.display = 'block'; }
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

        // A pattern the server can't search with simply matches nothing
        const matchEl = document.getElementById('we-match');
        const text = e instanceof ApiError ? 'No matches found' : 'Error fetching suggestions';
        if (matchEl) { matchEl.innerHTML = text; matchEl.style.display = 'block'; }
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

        let inner = `<span style="font-family:var(--font-mono);font-size:14px;min-width:${word.length * 9}px">${escapeHtml(word)}</span>`;
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

function wePagePrev() {
    if (_wePage > 0) { _wePage--; _weRenderSuggestionList(); }
}

function wePageNext() {
    if ((_wePage + 1) * WE_PAGE_SIZE < _weSuggestions.length) { _wePage++; _weRenderSuggestionList(); }
}

// ---------------------------------------------------------------------------
// Constraints and definitions
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
        bodyEl.innerHTML = e instanceof ApiError
            ? `Error: ${escapeHtml(e.message)}`
            : 'Error fetching constraints';
    }
}

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
        bodyEl.innerHTML = e instanceof ApiError
            ? `<p>${escapeHtml(e.message)}</p>`
            : 'Error fetching definitions.';
    }
}
