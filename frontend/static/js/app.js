/**
 * Main app - initialization, event wiring, and state management.
 */

// Initialize the app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('Crossword Editor initialized');

    // Load initial data
    loadGridsAndPuzzles();

    // Wire up button events
    setupEventListeners();

    // Subscribe to state changes
    State.subscribe((newState) => {
        console.log('State updated:', newState);
    });
});

/**
 * Load grids and puzzles from API and update UI
 */
async function loadGridsAndPuzzles() {
    try {
        showStatus('Loading grids and puzzles...');

        const gridsResult = await CrosswordAPI.listGrids();
        const puzzlesResult = await CrosswordAPI.listPuzzles();

        State.set({
            grids: gridsResult.grids || [],
            puzzles: puzzlesResult.puzzles || [],
        });

        renderGridsList(gridsResult.grids || []);
        renderPuzzlesList(puzzlesResult.puzzles || []);

        showStatus('Ready');
    } catch (err) {
        showError(`Failed to load data: ${err.message}`);
    }
}

/**
 * Render grids list in the UI
 */
function renderGridsList(grids) {
    const list = document.getElementById('grids-list');
    list.innerHTML = '';

    if (grids.length === 0) {
        list.innerHTML = '<li>No grids yet. Click "New Grid" to create one.</li>';
        return;
    }

    grids.forEach(name => {
        const li = document.createElement('li');
        li.textContent = name;
        li.onclick = () => loadAndDisplayGrid(name);
        list.appendChild(li);
    });
}

/**
 * Render puzzles list in the UI
 */
function renderPuzzlesList(puzzles) {
    const list = document.getElementById('puzzles-list');
    list.innerHTML = '';

    if (puzzles.length === 0) {
        list.innerHTML = '<li>No puzzles yet. Click "New Puzzle" to create one.</li>';
        return;
    }

    puzzles.forEach(name => {
        const li = document.createElement('li');
        li.textContent = name;
        li.onclick = () => loadAndDisplayPuzzle(name);
        list.appendChild(li);
    });
}

/**
 * Load a grid and display it
 */
async function loadAndDisplayGrid(name) {
    try {
        showStatus(`Loading grid "${name}"...`);

        const grid = await CrosswordAPI.loadGrid(name);

        State.set({
            currentGrid: name,
            mode: 'grid',
        });

        document.getElementById('list-section').style.display = 'none';
        document.getElementById('grid-section').style.display = 'block';
        document.getElementById('puzzle-section').style.display = 'none';

        GridEditor.render(grid);
        showStatus(`Loaded grid "${name}"`);
    } catch (err) {
        showError(`Failed to load grid: ${err.message}`);
    }
}

/**
 * Load a puzzle and display it
 */
async function loadAndDisplayPuzzle(name) {
    try {
        showStatus(`Loading puzzle "${name}"...`);

        const puzzle = await CrosswordAPI.loadPuzzle(name);

        State.set({
            currentPuzzle: name,
            mode: 'puzzle',
        });

        document.getElementById('list-section').style.display = 'none';
        document.getElementById('grid-section').style.display = 'none';
        document.getElementById('puzzle-section').style.display = 'block';

        PuzzleEditor.render(puzzle);
        showStatus(`Loaded puzzle "${name}"`);
    } catch (err) {
        showError(`Failed to load puzzle: ${err.message}`);
    }
}

/**
 * Return to list view
 */
function returnToList() {
    State.set({
        currentGrid: null,
        currentPuzzle: null,
        mode: 'list',
    });

    document.getElementById('list-section').style.display = 'block';
    document.getElementById('grid-section').style.display = 'none';
    document.getElementById('puzzle-section').style.display = 'none';
}

/**
 * Show status message
 */
function showStatus(message) {
    document.getElementById('status-message').textContent = message;
}

/**
 * Show error dialog
 */
function showError(message) {
    console.error('Error:', message);
    document.getElementById('error-message').textContent = message;
    document.getElementById('dialog-error').style.display = 'flex';
}

/**
 * Wire up event listeners
 */
function setupEventListeners() {
    // New grid button
    document.getElementById('btn-new-grid').addEventListener('click', () => {
        Dialogs.showNewGrid();
    });

    // New puzzle button
    document.getElementById('btn-new-puzzle').addEventListener('click', () => {
        Dialogs.showNewPuzzle();
    });

    // Close error dialog
    document.getElementById('btn-close-error').addEventListener('click', () => {
        document.getElementById('dialog-error').style.display = 'none';
    });

    // Grid toolbar buttons
    document.getElementById('btn-rotate-grid').addEventListener('click', async () => {
        const gridName = State.get('currentGrid');
        if (!gridName) return;
        try {
            showStatus('Rotating grid...');
            const rotated = await CrosswordAPI.rotateGrid(gridName);
            GridEditor.render(rotated);
            showStatus('Grid rotated');
        } catch (err) {
            showError(`Failed to rotate grid: ${err.message}`);
        }
    });

    document.getElementById('btn-undo-grid').addEventListener('click', async () => {
        const gridName = State.get('currentGrid');
        if (!gridName) return;
        try {
            showStatus('Undoing...');
            const undone = await CrosswordAPI.undoGrid(gridName);
            GridEditor.render(undone);
            showStatus('Undo complete');
        } catch (err) {
            showError(`Failed to undo: ${err.message}`);
        }
    });

    document.getElementById('btn-redo-grid').addEventListener('click', async () => {
        const gridName = State.get('currentGrid');
        if (!gridName) return;
        try {
            showStatus('Redoing...');
            const redone = await CrosswordAPI.redoGrid(gridName);
            GridEditor.render(redone);
            showStatus('Redo complete');
        } catch (err) {
            showError(`Failed to redo: ${err.message}`);
        }
    });

    document.getElementById('btn-delete-grid').addEventListener('click', async () => {
        const gridName = State.get('currentGrid');
        if (!gridName) return;
        if (!confirm(`Delete grid "${gridName}"? This cannot be undone.`)) return;
        try {
            showStatus('Deleting grid...');
            await CrosswordAPI.deleteGrid(gridName);
            showStatus('Grid deleted');
            returnToList();
            await loadGridsAndPuzzles();
        } catch (err) {
            showError(`Failed to delete grid: ${err.message}`);
        }
    });

    // Puzzle toolbar buttons
    document.getElementById('btn-undo-puzzle').addEventListener('click', async () => {
        const puzzleName = State.get('currentPuzzle');
        if (!puzzleName) return;
        try {
            showStatus('Undoing...');
            const undone = await CrosswordAPI.undoPuzzle(puzzleName);
            PuzzleEditor.render(undone);
            showStatus('Undo complete');
        } catch (err) {
            showError(`Failed to undo: ${err.message}`);
        }
    });

    document.getElementById('btn-redo-puzzle').addEventListener('click', async () => {
        const puzzleName = State.get('currentPuzzle');
        if (!puzzleName) return;
        try {
            showStatus('Redoing...');
            const redone = await CrosswordAPI.redoPuzzle(puzzleName);
            PuzzleEditor.render(redone);
            showStatus('Redo complete');
        } catch (err) {
            showError(`Failed to redo: ${err.message}`);
        }
    });

    document.getElementById('btn-save-puzzle').addEventListener('click', async () => {
        const puzzleName = State.get('currentPuzzle');
        if (!puzzleName) return;
        try {
            showStatus('Puzzle saved');
            // Changes are auto-saved via API calls, but show confirmation
        } catch (err) {
            showError(`Failed to save: ${err.message}`);
        }
    });

    document.getElementById('btn-delete-puzzle').addEventListener('click', async () => {
        const puzzleName = State.get('currentPuzzle');
        if (!puzzleName) return;
        if (!confirm(`Delete puzzle "${puzzleName}"? This cannot be undone.`)) return;
        try {
            showStatus('Deleting puzzle...');
            await CrosswordAPI.deletePuzzle(puzzleName);
            showStatus('Puzzle deleted');
            returnToList();
            await loadGridsAndPuzzles();
        } catch (err) {
            showError(`Failed to delete puzzle: ${err.message}`);
        }
    });

    document.getElementById('btn-export-xml').addEventListener('click', async () => {
        const puzzleName = State.get('currentPuzzle');
        if (!puzzleName) return;
        try {
            showStatus('Exporting XML...');
            const xml = await CrosswordAPI.exportPuzzleXML(puzzleName);
            // Create a download link
            const blob = new Blob([xml], { type: 'application/xml' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${puzzleName}.xml`;
            a.click();
            URL.revokeObjectURL(url);
            showStatus('XML exported');
        } catch (err) {
            showError(`Failed to export: ${err.message}`);
        }
    });
}
