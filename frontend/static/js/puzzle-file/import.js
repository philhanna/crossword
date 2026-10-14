// Crossword Puzzle Editor — the Import menu
//
// Every format imports the same way: pick a file, name the puzzle, post the
// file's contents to the format's endpoint, and open the result. The table
// below holds what differs between formats.

import { registerActions } from '../core/actions.js';
import { apiFetch } from '../core/api.js';
import { askText } from '../ui/dialogs.js';
import { showMessageLine, showRequestError } from '../ui/message-line.js';
import { _openPuzzleInEditor } from './lifecycle.js';

// read: 'text' posts { name, content }; 'base64' posts { name, content_b64 }
const IMPORT_FORMATS = {
    puz:        { title: 'Import .puz puzzle',               accept: '.puz',        read: 'base64', endpoint: '/api/import/puz' },
    acrosslite: { title: 'Import AcrossLite puzzle',         accept: '.txt',        read: 'text',   endpoint: '/api/import/acrosslite' },
    ipuz:       { title: 'Import ipuz puzzle',               accept: '.ipuz,.json', read: 'text',   endpoint: '/api/import/ipuz' },
    xd:         { title: 'Import xd puzzle',                 accept: '.xd',         read: 'text',   endpoint: '/api/import/xd' },
    ccxml:      { title: 'Import Crossword Compiler puzzle', accept: '.xml',        read: 'text',   endpoint: '/api/import/ccxml' },
};

registerActions({
    'import': (el) => importPuzzle(IMPORT_FORMATS[el.dataset.format]),
});

function importPuzzle(format) {
    const fileInput = document.getElementById('import-file-input');
    fileInput.accept = format.accept;

    // Reset so the same file can be picked again
    fileInput.value = '';
    fileInput.onchange = () => {
        const file = fileInput.files[0];
        if (file) askNameAndImport(format, file);
    };
    fileInput.click();
}

async function askNameAndImport(format, file) {
    let name = await askText(format.title, '<b>Puzzle name:</b>', defaultPuzzleName(file.name, format.accept));
    if (name === null) return;
    name = name.trim();
    if (!name) { showMessageLine('Puzzle name is required', 'error', 0); return; }

    let body;
    try {
        body = await readForUpload(file, format.read, name);
    } catch (e) {
        showMessageLine('Could not read file', 'error', 0);
        return;
    }

    try {
        await apiFetch('POST', format.endpoint, body);
        showMessageLine(`Imported "${name}" — opening…`, 'notice');
        await _openPuzzleInEditor(name);
    } catch (e) {
        showRequestError('Import failed', e);
    }
}

// The file name without whichever of the format's extensions it ends in
function defaultPuzzleName(filename, accept) {
    const extensions = accept.split(',').map(ext => ext.slice(1)).join('|');
    return filename.replace(new RegExp(`\\.(${extensions})$`, 'i'), '');
}

async function readForUpload(file, read, name) {
    if (read === 'base64') {
        const buf = await file.arrayBuffer();
        return { name, content_b64: btoa(String.fromCharCode(...new Uint8Array(buf))) };
    }
    return { name, content: await file.text() };
}
