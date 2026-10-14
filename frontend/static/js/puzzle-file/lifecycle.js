// Crossword Puzzle Editor — puzzle lifecycle: new, open, save, save as, rename, close, delete
//
// These talk to the server and then hand the result to the editor (or the
// dashboard) to draw. The open puzzle's names and saved checksum live in
// AppState.

import { registerActions } from '../core/actions.js';
import { apiFetch } from '../core/api.js';
import { escapeHtml } from '../core/dom.js';
import { _hash } from '../core/hash.js';
import { AppState } from '../core/state.js';
import { showPreviewChooser } from '../ui/chooser.js';
import { askConfirm, askFields, askText, showAlert } from '../ui/dialogs.js';
import { updateMenu } from '../ui/menu.js';
import { showMessageLine, showRequestError } from '../ui/message-line.js';
import { showView } from '../ui/view.js';
import {
    _settlePuzzleEditingBeforeSave, renderPuzzleEditor, renderPuzzleEditorLhs,
    resetEditor,
} from '../editor/editor.js';
import { _peOutsideMousedown } from '../editor/grid-clicks.js';
import { do_puzzle_generate_grid } from '../editor/grid-mode.js';
import { _peKeydown, _weKeydown } from '../editor/keyboard.js';
import { _isWordEditorOpen } from '../editor/selection.js';

registerActions({
    'puzzle-new':            () => do_puzzle_new(),
    'puzzle-open':           () => do_puzzle_open(),
    'puzzle-save':           () => do_puzzle_save(),
    'puzzle-save-as':        () => do_puzzle_save_as(),
    'puzzle-rename':         () => do_puzzle_rename(),
    'puzzle-close':          () => do_puzzle_close(),
    'puzzle-delete':         () => do_puzzle_delete(),
    'puzzle-delete-current': () => do_puzzle_delete_current(),
});

// ---------------------------------------------------------------------------
// New and open
// ---------------------------------------------------------------------------

async function do_puzzle_new() {
    const details = await askNewPuzzleDetails();
    if (!details) return;
    try {
        const internalName = '__new__' + Math.random().toString(36).slice(2, 10);
        await apiFetch('POST', '/api/puzzles', { name: internalName, size: details.size });
        await _openPuzzleInEditor(internalName);
        AppState.puzzleName         = null;
        AppState.puzzleOriginalName = internalName;
        AppState.puzzleThemeSpec    = details.spec;
        renderPuzzleEditorLhs();
        if (details.spec) {
            await do_puzzle_generate_grid();
        }
    } catch (e) { showRequestError('Error creating puzzle', e); }
}

// Ask for the new puzzle's size and optional theme word lengths, asking
// again (with what was typed) after each mistake. Resolves to
// { size, spec } with spec null when no theme was given, or null on Cancel.
async function askNewPuzzleDetails() {
    let entered = { size: '', spec: '' };
    for (;;) {
        const values = await askFields('New puzzle', [
            {
                name: 'size',
                label: '<b>Puzzle size:</b> <em>(an odd positive integer, e.g. 15)</em>',
                value: entered.size,
            },
            {
                name: 'spec',
                label: '<b>Theme word lengths</b> <em>(optional — palindromic integers with any delimiter, e.g. 7,5,5,7)</em>',
                value: entered.spec,
                required: false,
            },
        ]);
        if (!values) return null;
        entered = values;

        const problem = newPuzzleProblem(values);
        if (!problem) return { size: Number(values.size), spec: parseThemeSpec(values.spec) };

        // OK on the explanation asks again; Cancel gives up
        if (!await askConfirm(problem.title, problem.message)) return null;
    }
}

// What is wrong with the entered size and theme spec, or null if nothing
function newPuzzleProblem({ size, spec }) {
    const n = Number(size);
    if (!size || isNaN(n)) return { title: 'Invalid puzzle size', message: `${escapeHtml(size)} is not a number.` };
    if (n % 2 === 0) return { title: 'Invalid puzzle size', message: `${n} is not an odd number.` };
    if (n < 1) return { title: 'Invalid puzzle size', message: `${n} is not a positive number.` };

    const nums = parseThemeSpec(spec);
    if (nums === null) return null;
    if (nums.some(x => isNaN(x) || !Number.isInteger(x) || x < 1)) {
        return { title: 'Invalid theme spec', message: 'Each value must be a positive integer.' };
    }
    if (JSON.stringify(nums) !== JSON.stringify([...nums].reverse())) {
        return { title: 'Invalid theme spec', message: 'The list must be a palindrome (e.g. 7,5,5,7).' };
    }
    return null;
}

// The theme word lengths as numbers, split on anything that isn't a digit;
// null when none were given
function parseThemeSpec(spec) {
    const trimmed = spec.trim();
    if (!trimmed) return null;
    return trimmed.split(/[^0-9]+/).filter(s => s.length > 0).map(Number);
}

async function do_puzzle_open() {
    try {
        await showPreviewChooser('Open puzzle', [], '/api/puzzles', async (name) => {
            try {
                await _openPuzzleInEditor(name);
            } catch (e) { showRequestError('Error opening puzzle', e); }
        }, {
            stateFilterEnabled: true,
            initialStateFilter: 'all',
            emptyMessage: 'No saved puzzles found for that state.',
            loadItems: async (state) => {
                const path = `/api/puzzles?state=${encodeURIComponent(state || 'all')}`;
                const listData = await apiFetch('GET', path);
                return (listData.puzzles || []).filter(p => p && !p.startsWith('__wc__'));
            },
        });
    } catch (e) {
        showMessageLine(`Error listing puzzles: ${e.message}`, 'error', 0);
    }
}

export async function _openPuzzleInEditor(name) {
    const openData = await apiFetch('POST', `/api/puzzles/${encodeURIComponent(name)}/open`);
    await _openWorkingCopyInEditor(name, openData.working_name);
}

export async function _openWorkingCopyInEditor(name, wn) {
    const puzzleData = await apiFetch('GET', `/api/puzzles/${encodeURIComponent(wn)}`);
    let stateInfo = null;
    try {
        stateInfo = await apiFetch('GET', `/api/puzzles/${encodeURIComponent(name)}/state`);
    } catch (e) { /* state label is informational only — non-fatal */ }
    AppState.puzzleState       = stateInfo ? stateInfo.state : null;
    AppState.puzzleName        = name;
    AppState.puzzleOriginalName = name;
    AppState.puzzleWorkingName = wn;
    AppState.puzzleData        = puzzleData;
    AppState.puzzleSavedHash   = _hash(puzzleData.puzzle);
    resetEditor();
    showView('editor');
}

// ---------------------------------------------------------------------------
// Save, save as, rename
// ---------------------------------------------------------------------------

async function do_puzzle_save() {
    const wn   = AppState.puzzleWorkingName;
    const name = AppState.puzzleName;
    if (!name) { do_puzzle_save_as(); return; }
    const isDirty = AppState.puzzleSavedHash !== null &&
        _hash(AppState.puzzleData.puzzle) !== AppState.puzzleSavedHash;
    if (!isDirty) return;
    const comment = await askText('Save puzzle', 'What changed?');
    if (comment === null) return;
    await _doPuzzleSave(wn, name, comment);
}

async function _doPuzzleSave(wn, name, comment) {
    try {
        await _settlePuzzleEditingBeforeSave();
        await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(wn)}/copy`, { new_name: name, comment });
        AppState.puzzleSavedHash = _hash(AppState.puzzleData.puzzle);
        renderPuzzleEditor();
        showMessageLine(`Puzzle ${name} saved.`, 'notice');
    } catch (e) { showRequestError('Error saving puzzle', e); }
}

async function do_puzzle_save_as() {
    const values = await askFields('Save puzzle as', [
        { name: 'newName', label: 'Puzzle name:', value: AppState.puzzleName || '' },
        { name: 'comment', label: 'What changed?', value: '' },
    ]);
    if (!values) return;
    const { newName, comment } = values;
    if (!newName) return;
    if (!await validateUserFacingName('puzzle', newName)) return;
    try {
        await _settlePuzzleEditingBeforeSave();
        if (!await confirmOverwriteIfExists('puzzle', newName)) return;
        await _savePuzzleAsName(newName, comment);
    } catch (e) { showRequestError('Error saving puzzle', e); }
}

async function _listSavedPuzzleNames() {
    const listData = await apiFetch('GET', '/api/puzzles');
    return (listData.puzzles || []).filter(p => p && !p.startsWith('__'));
}

async function _savePuzzleAsName(newName, comment) {
    const wn = AppState.puzzleWorkingName;
    await apiFetch('POST',
        `/api/puzzles/${encodeURIComponent(wn)}/copy`, { new_name: newName, comment });
    AppState.puzzleSavedHash = _hash(AppState.puzzleData.puzzle);
    if (!AppState.puzzleName) {
        // New (never-saved) puzzle: assign the name and clean up the __new__ entry
        const oldOriginal = AppState.puzzleOriginalName;
        AppState.puzzleName         = newName;
        AppState.puzzleOriginalName = newName;
        if (oldOriginal && oldOriginal !== newName) {
            try { await apiFetch('DELETE', `/api/puzzles/${encodeURIComponent(oldOriginal)}`); }
            catch (e) { /* ignore */ }
        }
    }
    renderPuzzleEditor();
    // For an existing named puzzle (true Save As), keep the editor on the original.
    showMessageLine(`Puzzle saved as "${newName}".`, 'notice');
}

async function do_puzzle_rename() {
    const currentName = AppState.puzzleName;
    if (!currentName) return;
    const newName = await askText('Rename puzzle', 'New name:', currentName);
    if (!newName || newName === currentName) return;
    if (!await validateUserFacingName('puzzle', newName)) return;
    try {
        // The server won't rename over another puzzle, so say so up front
        const existing = await _listSavedPuzzleNames();
        if (existing.includes(newName)) {
            await showAlert('Duplicate puzzle name',
                `Puzzle <b>${escapeHtml(newName)}</b> already exists. Choose a different name.`);
            return;
        }
        await apiFetch('POST',
            `/api/puzzles/${encodeURIComponent(currentName)}/rename`, { new_name: newName });
        AppState.puzzleName         = newName;
        AppState.puzzleOriginalName = newName;
        renderPuzzleEditorLhs();
        updateMenu();
        showMessageLine(`Puzzle renamed to ${newName}.`, 'notice');
    } catch (e) { showRequestError('Error renaming puzzle', e); }
}

// ---------------------------------------------------------------------------
// Close and delete
// ---------------------------------------------------------------------------

async function do_puzzle_close() {
    if (_isWordEditorOpen()) return;
    const isDirty = AppState.puzzleData &&
        _hash(AppState.puzzleData.puzzle) !== AppState.puzzleSavedHash;
    if (isDirty) {
        const name = AppState.puzzleName || '(No name)';
        const confirmed = await askConfirm('Close puzzle',
            `Puzzle <b>${escapeHtml(name)}</b> has unsaved changes. Close without saving?`);
        if (!confirmed) return;
    }
    await _doPuzzleCloseConfirmed();
}

async function _doPuzzleCloseConfirmed() {
    document.removeEventListener('keydown', _peKeydown);
    document.removeEventListener('keydown', _weKeydown);
    document.removeEventListener('mousedown', _peOutsideMousedown);
    const wn           = AppState.puzzleWorkingName;
    const originalName = AppState.puzzleOriginalName;
    const savedName    = AppState.puzzleName;
    AppState.puzzleName         = null;
    AppState.puzzleOriginalName = null;
    AppState.puzzleWorkingName  = null;
    AppState.puzzleState        = null;
    AppState.puzzleData         = null;
    AppState.puzzleSavedHash    = null;
    AppState.puzzleThemeSpec    = null;
    resetEditor();
    if (wn) {
        try { await apiFetch('DELETE', `/api/puzzles/${encodeURIComponent(wn)}`); }
        catch (e) { /* ignore cleanup errors */ }
    }
    if (!savedName && originalName) {
        // Puzzle was never given a user name — delete the internal __new__ original too
        try { await apiFetch('DELETE', `/api/puzzles/${encodeURIComponent(originalName)}`); }
        catch (e) { /* ignore cleanup errors */ }
    }
    showView('dashboard');
}

async function do_puzzle_delete() {
    try {
        const puzzles = await _listSavedPuzzleNames();
        if (puzzles.length === 0) {
            showMessageLine('No saved puzzles found.', 'notice');
            return;
        }
        showPreviewChooser('Delete puzzle', puzzles, '/api/puzzles', async (name) => {
            if (!await confirmDelete(name)) return;
            try {
                await apiFetch('DELETE', `/api/puzzles/${encodeURIComponent(name)}`);
                if (AppState.puzzleName === name) {
                    await _doPuzzleCloseConfirmed();
                    return;
                }
                showMessageLine(`Puzzle ${name} deleted.`, 'notice');
            } catch (e) { showRequestError('Error deleting puzzle', e); }
        });
    } catch (e) {
        showRequestError('Error listing puzzles', e);
    }
}

async function do_puzzle_delete_current() {
    // Delete the puzzle currently open in the editor, using the same
    // confirmation dialog as the Puzzle > Delete menu item.
    if (_isWordEditorOpen()) return;
    const name = AppState.puzzleName;
    if (!name) {
        showMessageLine('This puzzle has not been saved yet.', 'notice');
        return;
    }
    if (!await confirmDelete(name)) return;
    try {
        await apiFetch('DELETE', `/api/puzzles/${encodeURIComponent(name)}`);
        await _doPuzzleCloseConfirmed();
        showMessageLine(`Puzzle ${name} deleted.`, 'notice');
    } catch (e) { showRequestError('Error deleting puzzle', e); }
}

function confirmDelete(name) {
    return askConfirm('Delete puzzle',
        `Are you sure you want to delete puzzle <b>'${escapeHtml(name)}'</b>?`);
}

// ---------------------------------------------------------------------------
// Name checks
// ---------------------------------------------------------------------------

// Resolves false (after telling the user why) for a name the app keeps for itself
async function validateUserFacingName(kind, name) {
    if (!name.startsWith('__wc__')) return true;
    await showAlert(
        `Invalid ${kind} name`,
        `Names starting with <b>__wc__</b> are reserved for internal working copies used while editing a ${kind}. Please choose a different ${kind} name.`
    );
    return false;
}

// Resolves true when no saved puzzle has this name, or the user agrees to overwrite it
async function confirmOverwriteIfExists(kind, name) {
    const existingNames = await _listSavedPuzzleNames();
    if (!existingNames.includes(name)) return true;
    return askConfirm(
        `Overwrite ${kind}`,
        `${kind.charAt(0).toUpperCase() + kind.slice(1)} <b>${escapeHtml(name)}</b> already exists. Overwrite it?`,
        'Overwrite'
    );
}
