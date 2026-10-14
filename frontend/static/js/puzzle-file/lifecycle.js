// Crossword Puzzle Editor — puzzle lifecycle: new, open, save, save as, rename, close, delete
//
// These talk to the server and then hand the result to the editor (or the
// dashboard) to draw. The open puzzle's names and saved checksum live in
// AppState.

import { registerActions } from '../core/actions.js';
import {
    _settlePuzzleEditingBeforeSave, do_puzzle_generate_grid, renderPuzzleEditor,
    renderPuzzleEditorLhs,
} from '../puzzle-editor.js';
import { AppState } from '../state.js';
import {
    _hash, apiFetch, confirmOverwriteIfExists, escapeHtml, inputBox, messageBox,
    multiInputBox, showMessageLine, showPreviewChooser, showRequestError,
    showView, updateMenu, validateUserFacingName,
} from '../ui.js';
import { _isWordEditorOpen, _peKeydown, _peOutsideMousedown, _weKeydown } from '../word-editor.js';

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
    function promptForPuzzleDetails(sizeVal = '', specVal = '') {
        multiInputBox(
            'New puzzle',
            [
                {
                    name: 'size',
                    label: '<b>Puzzle size:</b> <em>(an odd positive integer, e.g. 15)</em>',
                    value: sizeVal,
                },
                {
                    name: 'spec',
                    label: '<b>Theme word lengths</b> <em>(optional — palindromic integers with any delimiter, e.g. 7,5,5,7)</em>',
                    value: specVal,
                    required: false,
                },
            ],
            ({ size: enteredSize, spec: enteredSpec }) => {
                const n = Number(enteredSize);
                if (!enteredSize || isNaN(n)) {
                    messageBox(
                        'Invalid puzzle size',
                        `${escapeHtml(enteredSize)} is not a number.`,
                        null,
                        () => promptForPuzzleDetails(enteredSize, enteredSpec)
                    );
                    return;
                }
                if (n % 2 === 0) {
                    messageBox(
                        'Invalid puzzle size',
                        `${n} is not an odd number.`,
                        null,
                        () => promptForPuzzleDetails(enteredSize, enteredSpec)
                    );
                    return;
                }
                if (n < 1) {
                    messageBox(
                        'Invalid puzzle size',
                        `${n} is not a positive number.`,
                        null,
                        () => promptForPuzzleDetails(enteredSize, enteredSpec)
                    );
                    return;
                }

                const trimmedSpec = enteredSpec.trim();
                let spec = null;
                if (trimmedSpec) {
                    const parts = trimmedSpec.split(/[^0-9]+/).filter(s => s.length > 0);
                    const nums = parts.map(Number);
                    if (nums.some(x => isNaN(x) || !Number.isInteger(x) || x < 1)) {
                        messageBox(
                            'Invalid theme spec',
                            'Each value must be a positive integer.',
                            null,
                            () => promptForPuzzleDetails(enteredSize, enteredSpec)
                        );
                        return;
                    }
                    if (JSON.stringify(nums) !== JSON.stringify([...nums].reverse())) {
                        messageBox(
                            'Invalid theme spec',
                            'The list must be a palindrome (e.g. 7,5,5,7).',
                            null,
                            () => promptForPuzzleDetails(enteredSize, enteredSpec)
                        );
                        return;
                    }
                    spec = nums;
                }

                createPuzzle(n, spec);
            },
            { onCancel: () => createPuzzle(null, null) }
        );
    }

    async function createPuzzle(size, spec) {
        if (size === null) return;
        try {
            const internalName = '__new__' + Math.random().toString(36).slice(2, 10);
            await apiFetch('POST', '/api/puzzles', { name: internalName, size });
            await _openPuzzleInEditor(internalName);
            AppState.puzzleName         = null;
            AppState.puzzleOriginalName = internalName;
            AppState.puzzleThemeSpec    = spec;
            renderPuzzleEditorLhs();
            if (spec) {
                await do_puzzle_generate_grid();
            }
        } catch (e) { showRequestError('Error creating puzzle', e); }
    }

    promptForPuzzleDetails();
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
    AppState.selectedWord      = null;
    AppState.showingStats      = false;
    AppState.showingFillOrder  = false;
    AppState.sidebarTab         = 'clues';
    AppState._statsData         = null;
    AppState._fillOrderCache    = new Map();
    AppState.gridStructureChanged = false;
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
    inputBox('Save puzzle', 'What changed?', '', async (comment) => {
        await _doPuzzleSave(wn, name, comment);
    });
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
    multiInputBox('Save puzzle as', [
        { name: 'newName', label: 'Puzzle name:', value: AppState.puzzleName || '' },
        { name: 'comment', label: 'What changed?', value: '' },
    ], async ({ newName, comment }) => {
        if (!newName) return;
        if (!validateUserFacingName('puzzle', newName)) return;
        try {
            await _settlePuzzleEditingBeforeSave();
            await confirmOverwriteIfExists(
                'puzzle',
                newName,
                _listSavedPuzzleNames,
                () => _savePuzzleAsName(newName, comment)
            );
        } catch (e) { showRequestError('Error saving puzzle', e); }
    });
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
            await apiFetch('POST',
                `/api/puzzles/${encodeURIComponent(currentName)}/rename`, { new_name: newName });
            AppState.puzzleName         = newName;
            AppState.puzzleOriginalName = newName;
            renderPuzzleEditorLhs();
            updateMenu();
            showMessageLine(`Puzzle renamed to ${newName}.`, 'notice');
        } catch (e) { showRequestError('Error renaming puzzle', e); }
    });
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
    AppState.selectedWord       = null;
    AppState.showingStats       = false;
    AppState.showingFillOrder   = false;
    AppState.sidebarTab         = 'clues';
    AppState._statsData         = null;
    AppState._fillOrderCache    = null;
    AppState.gridStructureChanged = false;
    AppState.puzzleThemeSpec      = null;
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
                        await apiFetch('DELETE', `/api/puzzles/${encodeURIComponent(name)}`);
                        if (AppState.puzzleName === name) {
                            await _doPuzzleCloseConfirmed();
                            return;
                        }
                        showMessageLine(`Puzzle ${name} deleted.`, 'notice');
                    } catch (e) { showRequestError('Error deleting puzzle', e); }
                }
            );
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
    messageBox(
        'Delete puzzle',
        `Are you sure you want to delete puzzle <b>'${escapeHtml(name)}'</b>?`,
        null,
        async () => {
            try {
                await apiFetch('DELETE', `/api/puzzles/${encodeURIComponent(name)}`);
                await _doPuzzleCloseConfirmed();
                showMessageLine(`Puzzle ${name} deleted.`, 'notice');
            } catch (e) { showRequestError('Error deleting puzzle', e); }
        }
    );
}
