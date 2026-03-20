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
    document.getElementById('btn-rotate-grid').addEventListener('click', () => {
        console.log('Rotate grid');
    });

    document.getElementById('btn-undo-grid').addEventListener('click', () => {
        console.log('Undo grid');
    });

    document.getElementById('btn-redo-grid').addEventListener('click', () => {
        console.log('Redo grid');
    });

    document.getElementById('btn-delete-grid').addEventListener('click', () => {
        console.log('Delete grid');
    });

    // Puzzle toolbar buttons
    document.getElementById('btn-undo-puzzle').addEventListener('click', () => {
        console.log('Undo puzzle');
    });

    document.getElementById('btn-redo-puzzle').addEventListener('click', () => {
        console.log('Redo puzzle');
    });

    document.getElementById('btn-save-puzzle').addEventListener('click', () => {
        console.log('Save puzzle');
    });

    document.getElementById('btn-delete-puzzle').addEventListener('click', () => {
        console.log('Delete puzzle');
    });

    document.getElementById('btn-export-xml').addEventListener('click', () => {
        console.log('Export XML');
    });
}
