// Crossword Puzzle Editor — right-click context menu

let _ctxMenuDismiss = null;

// items: [{ label, onClick }, ...]
export function showContextMenu(x, y, items) {
    hideContextMenu();

    const menu = document.createElement('div');
    menu.id = 'context-menu';
    menu.className = 'context-menu';
    items.forEach(item => {
        const entry = document.createElement('div');
        entry.className = 'context-menu-item';
        entry.textContent = item.label;
        entry.onclick = () => { hideContextMenu(); item.onClick(); };
        menu.appendChild(entry);
    });
    document.body.appendChild(menu);

    // Clamp to viewport so the menu never renders off-screen.
    const rect = menu.getBoundingClientRect();
    const left = Math.min(x, window.innerWidth - rect.width - 4);
    const top = Math.min(y, window.innerHeight - rect.height - 4);
    menu.style.left = `${Math.max(0, left)}px`;
    menu.style.top = `${Math.max(0, top)}px`;

    _ctxMenuDismiss = (e) => {
        if (e.type === 'mousedown' && menu.contains(e.target)) return;
        if (e.type === 'keydown' && e.key !== 'Escape') return;
        hideContextMenu();
    };
    document.addEventListener('mousedown', _ctxMenuDismiss, true);
    document.addEventListener('keydown', _ctxMenuDismiss, true);
    window.addEventListener('scroll', _ctxMenuDismiss, true);
}

function hideContextMenu() {
    const el = document.getElementById('context-menu');
    if (el) el.remove();
    if (_ctxMenuDismiss) {
        document.removeEventListener('mousedown', _ctxMenuDismiss, true);
        document.removeEventListener('keydown', _ctxMenuDismiss, true);
        window.removeEventListener('scroll', _ctxMenuDismiss, true);
        _ctxMenuDismiss = null;
    }
}
