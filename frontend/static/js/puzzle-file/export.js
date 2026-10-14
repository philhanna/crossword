// Crossword Puzzle Editor — the Export menu

import { registerActions } from '../core/actions.js';
import { AppState } from '../state.js';
import { apiFetch, showMessageLine, showPreviewChooser, showRequestError } from '../ui.js';

registerActions({
    'export': (el) => do_export(el.dataset.format),
});

async function do_export(format) {
    if (AppState.view === 'editor' && AppState.puzzleName) {
        await _downloadExport(AppState.puzzleName, format);
    } else {
        try {
            const listData = await apiFetch('GET', '/api/puzzles');
            const puzzles = (listData.puzzles || []).filter(p => p && !p.startsWith('__wc__'));
            if (puzzles.length === 0) {
                showMessageLine('No saved puzzles found.', 'notice');
                return;
            }
            showPreviewChooser('Choose a puzzle to export', puzzles, '/api/puzzles', async (name) => {
                await _downloadExport(name, format);
            });
        } catch (e) {
            showRequestError('Error listing puzzles', e);
        }
    }
}

async function _downloadExport(name, format) {
    const endpointMap = { puz: 'acrosslite', puzbin: 'puz', xd: 'xd', ipuz: 'ipuz', xml: 'xml', nyt: 'nytimes', solver: 'solver-pdf', solved: 'solved-pdf' };
    const filenameMap = { puz: `${name}.txt`, puzbin: `${name}.puz`, xd: `${name}.xd`, ipuz: `${name}.ipuz`, xml: `${name}.xml`, nyt: `nytimes_${name}.pdf`, solver: `${name}.pdf`, solved: `${name}-solution.pdf` };
    const labelMap  = { puz: 'Across Lite', puzbin: '.puz Binary', xd: 'xword xd', ipuz: 'ipuz', xml: 'Crossword Compiler XML', nyt: 'New York Times', solver: 'Solver PDF', solved: 'Solution PDF' };
    const endpoint = endpointMap[format];
    const filename = filenameMap[format];
    try {
        const resp = await fetch(`/api/export/puzzles/${encodeURIComponent(name)}/${endpoint}`);
        if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            showMessageLine(err.error || `Export failed: HTTP ${resp.status}`, 'error');
            return;
        }
        const disposition = resp.headers.get('Content-Disposition') || '';
        const match = disposition.match(/filename="?([^";]+)"?/);
        const downloadFilename = match ? match[1] : filename;
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = downloadFilename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showMessageLine(`Exported "${name}" as ${labelMap[format]}: ${downloadFilename}`, 'notice');
    } catch (e) {
        showMessageLine('Export request failed.', 'error');
    }
}
