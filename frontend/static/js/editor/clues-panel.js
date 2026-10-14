// Crossword Puzzle Editor — the Clues panel: the clue list and editing a clue in place

import { registerActions } from '../core/actions.js';
import { escapeHtml } from '../core/dom.js';
import { AppState } from '../core/state.js';
import { showMessageLine } from '../ui/message-line.js';
import { _currentEditorMode, renderPuzzleEditor, renderPuzzleEditorRhs } from './editor.js';
import { _getPuzzleWord, completeSelectedWordEdit, getSelectedWord } from './selection.js';

registerActions({
    'clue-direction': (el) => switchClueDirection(el.dataset.direction),
    'clue-edit':      (el) => startInlineClueEdit(Number(el.dataset.seq), el.dataset.direction),
});

// direction: which list the Clues tab shows. lastDirection: the one the
// previous redraw showed, to tell a flip from a refresh. pendingSave: the
// last in-place clue save, so the next one waits for it and saves reach the
// server in order.
const clues = { direction: 'across', lastDirection: null, pendingSave: Promise.resolve() };

// ---------------------------------------------------------------------------
// Clue list
// ---------------------------------------------------------------------------

export function renderClues() {
    if (!AppState.puzzleData) return '';
    const words    = AppState.puzzleData.puzzle.words;
    const across   = words.filter(w => w.direction === 'across').sort((a, b) => a.seq - b.seq);
    const down     = words.filter(w => w.direction === 'down').sort((a, b) => a.seq - b.seq);
    const selected = getSelectedWord();
    const dir      = clues.direction;
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
        const editWord = `data-action="edit-word" data-seq="${w.seq}" data-direction="${dir}"`;
        return `<tr class="clue-row${isSelected ? ' clue-row-selected' : ''}"${hasMissing ? ' data-noclue="1"' : ''}>` +
            `<td class="clue-num" ${editWord}>${w.seq}</td>` +
            `<td class="clue-answer" ${editWord}>${escapeHtml((w.answer || '').replace(/ /g, '.'))}</td>` +
            `<td class="clue-text${hasMissing ? ' clue-text-missing' : ''}" data-seq="${w.seq}"` +
            ` data-action="clue-edit" data-direction="${dir}">` +
            (hasMissing ? '<span class="clue-missing-dot"></span>' : '') +
            escapeHtml(w.clue || 'No clue') +
            `</td>` +
            `</tr>`;
    }).join('');

    return `
<div class="clue-toolbar">
  <div class="clue-dir-toggle">
    <button class="clue-dir-btn${dir === 'across' ? ' clue-dir-btn-active' : ''}" data-action="clue-direction" data-direction="across">Across</button>
    <button class="clue-dir-btn${dir === 'down'   ? ' clue-dir-btn-active' : ''}" data-action="clue-direction" data-direction="down">Down</button>
  </div>
  <span class="clue-count ${countClass}">${countLabel}</span>
</div>
<div id="clue-list-active" class="clue-list-new">
  <table class="clue-table"><tbody>${items}</tbody></table>
</div>`;
}

function switchClueDirection(dir) {
    clues.direction = dir;
    renderPuzzleEditorRhs();
}

// Remember where the clue list was scrolled, so a redraw of the sidebar
// doesn't lose it. Returns what restoreCluesScroll() needs afterwards.
export function saveCluesScroll() {
    const list = document.getElementById('clue-list-active');
    return list ? list.scrollTop : null;
}

// After a sidebar redraw: put the clue list back where it was, or, when it is
// new or shows the other direction now, scroll to the first missing clue.
export function restoreCluesScroll(oldScroll) {
    if (oldScroll !== null && clues.direction === clues.lastDirection) {
        _restoreCluesScroll(oldScroll);
    } else {
        _scrollCluesToFirstMissing();
    }
    clues.lastDirection = clues.direction;
}

function _restoreCluesScroll(scrollTop) {
    const list = document.getElementById('clue-list-active');
    if (!list) return;
    list.scrollTop = scrollTop;

    // Keep the selected row (e.g. the word just clued) in view
    const selected = list.querySelector('.clue-row-selected');
    if (selected) selected.scrollIntoView({ block: 'nearest' });
}

function _scrollCluesToFirstMissing() {
    const list = document.getElementById('clue-list-active');
    if (!list) return;
    const first = list.querySelector('[data-noclue]');
    if (!first) return;
    // Scroll so the first unclued row sits in the top third of the list
    const rowTop = first.getBoundingClientRect().top - list.getBoundingClientRect().top + list.scrollTop;
    list.scrollTop = Math.max(0, rowTop - list.clientHeight / 3);
}

// ---------------------------------------------------------------------------
// Editing a clue in place
// ---------------------------------------------------------------------------

async function startInlineClueEdit(seq, direction) {
    if (_currentEditorMode() !== 'puzzle') return;
    await clues.pendingSave;  // a blur-triggered save re-renders the list; let it finish first
    const word = _getPuzzleWord(seq, direction);
    if (!word) return;
    if (!word.answer || word.answer.includes(' ')) {
        showMessageLine('Fill in the word before giving it a clue', 'error');
        return;
    }
    const result = await completeSelectedWordEdit({ nextSelection: { seq, direction } });
    if (result.error) return;

    const cell = document.querySelector(`#clue-list-active .clue-text[data-seq="${seq}"]`);
    if (!cell) return;
    cell.classList.remove('clue-text-missing');

    // Clicks inside the text box must not start another edit
    cell.removeAttribute('data-action');
    cell.innerHTML = '';
    const input = document.createElement('input');
    input.type        = 'text';
    input.className   = 'clue-inline-input';
    input.value       = word.clue || '';
    input.placeholder = 'Enter clue…';
    cell.appendChild(input);
    input.focus();

    let finished = false;
    const finish = (save) => {
        if (finished) return;
        finished = true;
        if (save) {
            clues.pendingSave = _saveInlineClue(seq, direction, input.value.trim());
        } else {
            renderPuzzleEditorRhs();
        }
    };
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter')  { e.preventDefault(); finish(true); }
        if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); finish(false); }
    });
    input.addEventListener('blur', () => finish(true));
}

async function _saveInlineClue(seq, direction, clue) {
    const sw = getSelectedWord();
    if (!sw || sw.seq !== seq || sw.direction !== direction) {
        renderPuzzleEditorRhs();
        return;
    }
    sw.draftClue = clue;
    const result = await completeSelectedWordEdit();
    if (!result.error) renderPuzzleEditor();
}
