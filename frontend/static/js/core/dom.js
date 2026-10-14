// Crossword Puzzle Editor — small DOM helpers

export function showElement(id) { document.getElementById(id).style.display = 'block'; }

export function hideElement(id) { document.getElementById(id).style.display = 'none'; }

export function escapeHtml(s) {
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
