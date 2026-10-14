// Crossword Puzzle Editor — the Import menu

import { registerActions } from '../core/actions.js';
import { _openPuzzleInEditor } from './lifecycle.js';
import { apiFetch, inputBox, showMessageLine, showRequestError } from '../ui.js';

const IMPORTERS = {
    puz:        () => do_puzzle_import_puz(),
    acrosslite: () => do_puzzle_import(),
    ipuz:       () => do_puzzle_import_ipuz(),
    xd:         () => do_puzzle_import_xd(),
    ccxml:      () => do_puzzle_import_ccxml(),
};

registerActions({
    'import': (el) => IMPORTERS[el.dataset.format](),
});

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
                if (!name) { showMessageLine('Puzzle name is required', 'error', 0); return; }

                let content;
                try {
                    content = await file.text();
                } catch (e) {
                    showMessageLine('Could not read file', 'error', 0);
                    return;
                }

                try {
                    await apiFetch('POST', '/api/import/acrosslite', { name, content });
                    showMessageLine(`Imported "${name}" — opening…`, 'notice');
                    await _openPuzzleInEditor(name);
                } catch (e) {
                    showRequestError('Import failed', e);
                }
            }
        );
    };
    fileInput.click();
}

async function do_puzzle_import_xd() {
    const fileInput = document.getElementById('xd-file-input');
    fileInput.value = '';
    fileInput.onchange = async (evt) => {
        const file = evt.target.files[0];
        if (!file) return;

        const defaultName = file.name.replace(/\.xd$/i, '');

        inputBox(
            'Import xd puzzle',
            '<b>Puzzle name:</b>',
            defaultName,
            async (name) => {
                name = name.trim();
                if (!name) { showMessageLine('Puzzle name is required', 'error', 0); return; }

                let content;
                try {
                    content = await file.text();
                } catch (e) {
                    showMessageLine('Could not read file', 'error', 0);
                    return;
                }

                try {
                    await apiFetch('POST', '/api/import/xd', { name, content });
                    showMessageLine(`Imported "${name}" — opening…`, 'notice');
                    await _openPuzzleInEditor(name);
                } catch (e) {
                    showRequestError('Import failed', e);
                }
            }
        );
    };
    fileInput.click();
}

async function do_puzzle_import_ipuz() {
    const fileInput = document.getElementById('ipuz-file-input');
    fileInput.value = '';
    fileInput.onchange = async (evt) => {
        const file = evt.target.files[0];
        if (!file) return;

        const defaultName = file.name.replace(/\.(ipuz|json)$/i, '');

        inputBox(
            'Import ipuz puzzle',
            '<b>Puzzle name:</b>',
            defaultName,
            async (name) => {
                name = name.trim();
                if (!name) { showMessageLine('Puzzle name is required', 'error', 0); return; }

                let content;
                try {
                    content = await file.text();
                } catch (e) {
                    showMessageLine('Could not read file', 'error', 0);
                    return;
                }

                try {
                    await apiFetch('POST', '/api/import/ipuz', { name, content });
                    showMessageLine(`Imported "${name}" — opening…`, 'notice');
                    await _openPuzzleInEditor(name);
                } catch (e) {
                    showRequestError('Import failed', e);
                }
            }
        );
    };
    fileInput.click();
}

async function do_puzzle_import_ccxml() {
    const fileInput = document.getElementById('ccxml-file-input');
    fileInput.value = '';
    fileInput.onchange = async (evt) => {
        const file = evt.target.files[0];
        if (!file) return;

        const defaultName = file.name.replace(/\.xml$/i, '');

        inputBox(
            'Import Crossword Compiler puzzle',
            '<b>Puzzle name:</b>',
            defaultName,
            async (name) => {
                name = name.trim();
                if (!name) { showMessageLine('Puzzle name is required', 'error', 0); return; }

                let content;
                try {
                    content = await file.text();
                } catch (e) {
                    showMessageLine('Could not read file', 'error', 0);
                    return;
                }

                try {
                    await apiFetch('POST', '/api/import/ccxml', { name, content });
                    showMessageLine(`Imported "${name}" — opening…`, 'notice');
                    await _openPuzzleInEditor(name);
                } catch (e) {
                    showRequestError('Import failed', e);
                }
            }
        );
    };
    fileInput.click();
}

async function do_puzzle_import_puz() {
    const fileInput = document.getElementById('puz-file-input');
    fileInput.value = '';
    fileInput.onchange = async (evt) => {
        const file = evt.target.files[0];
        if (!file) return;

        const defaultName = file.name.replace(/\.puz$/i, '');

        inputBox(
            'Import .puz puzzle',
            '<b>Puzzle name:</b>',
            defaultName,
            async (name) => {
                name = name.trim();
                if (!name) { showMessageLine('Puzzle name is required', 'error', 0); return; }

                let content_b64;
                try {
                    const buf = await file.arrayBuffer();
                    content_b64 = btoa(String.fromCharCode(...new Uint8Array(buf)));
                } catch (e) {
                    showMessageLine('Could not read file', 'error', 0);
                    return;
                }

                try {
                    await apiFetch('POST', '/api/import/puz', { name, content_b64 });
                    showMessageLine(`Imported "${name}" — opening…`, 'notice');
                    await _openPuzzleInEditor(name);
                } catch (e) {
                    showRequestError('Import failed', e);
                }
            }
        );
    };
    fileInput.click();
}
