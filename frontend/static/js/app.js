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
    setupMenuEventListeners();

    // Subscribe to state changes
    State.subscribe((newState) => {
        console.log('State updated:', newState);
        updateMenuState();
    });

    // Initial menu state update
    updateMenuState();
});

/**
 * Menu state management
 */
const MenuState = {
    grid_new: true,
    grid_from_puzzle: true,
    grid_open: true,
    grid_save: false,
    grid_save_as: false,
    grid_close: false,
    grid_delete: false,
    puzzle_new: false,
    puzzle_open: true,
    puzzle_save: false,
    puzzle_save_as: false,
    puzzle_close: false,
    puzzle_delete: false,
    export_acrosslite: true,
    export_compiler: true,
    export_nytimes: true,

    update() {
        const state = State.get();
        this.grid_save = state.currentGrid && state.isDirty;
        this.grid_save_as = !!state.currentGrid;
        this.grid_close = !!state.currentGrid;
        this.grid_delete = !!state.currentGrid;

        this.puzzle_new = state.grids && state.grids.length > 0;
        this.puzzle_save = state.currentPuzzle && state.isDirty;
        this.puzzle_save_as = !!state.currentPuzzle;
        this.puzzle_close = !!state.currentPuzzle;
        this.puzzle_delete = !!state.currentPuzzle;

        this.renderMenuItems();
    },

    renderMenuItems() {
        Object.entries(this).forEach(([key, enabled]) => {
            if (key === 'update' || key === 'renderMenuItems') return;
            const btn = document.getElementById(`menu-${key}`);
            if (btn) {
                btn.classList.toggle('w3-disabled', !enabled);
                if (!enabled) {
                    btn.style.pointerEvents = 'none';
                    btn.style.opacity = '0.5';
                } else {
                    btn.style.pointerEvents = 'auto';
                    btn.style.opacity = '1';
                }
            }
        });
    }
};

function updateMenuState() {
    MenuState.update();
}

/**
 * Wire up menu event listeners
 */
function setupMenuEventListeners() {
    // Grid menu
    document.getElementById('menu-grid-new').addEventListener('click', () => {
        Dialogs.showNewGrid();
    });

    document.getElementById('menu-grid-from-puzzle').addEventListener('click', () => {
        showPuzzleChooserForGridCreation();
    });

    document.getElementById('menu-grid-open').addEventListener('click', () => {
        returnToList();
    });

    document.getElementById('menu-grid-save').addEventListener('click', async () => {
        const gridName = State.get('currentGrid');
        if (gridName) {
            try {
                showStatus('Saving grid...');
                await CrosswordAPI.saveGrid(gridName);
                State.set({ isDirty: false });
                showStatus('Grid saved');
            } catch (err) {
                showError(`Failed to save: ${err.message}`);
            }
        }
    });

    document.getElementById('menu-grid-save-as').addEventListener('click', () => {
        const gridName = State.get('currentGrid');
        if (gridName) {
            Dialogs.showSaveGridAs(gridName);
        }
    });

    document.getElementById('menu-grid-close').addEventListener('click', () => {
        returnToList();
    });

    document.getElementById('menu-grid-delete').addEventListener('click', async () => {
        const gridName = State.get('currentGrid');
        if (gridName) {
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
        }
    });

    // Puzzle menu
    document.getElementById('menu-puzzle-new').addEventListener('click', () => {
        Dialogs.showNewPuzzle();
    });

    document.getElementById('menu-puzzle-open').addEventListener('click', () => {
        returnToList();
    });

    document.getElementById('menu-puzzle-save').addEventListener('click', async () => {
        const puzzleName = State.get('currentPuzzle');
        if (puzzleName) {
            try {
                showStatus('Saving puzzle...');
                await CrosswordAPI.savePuzzle(puzzleName);
                State.set({ isDirty: false });
                showStatus('Puzzle saved');
            } catch (err) {
                showError(`Failed to save: ${err.message}`);
            }
        }
    });

    document.getElementById('menu-puzzle-save-as').addEventListener('click', () => {
        const puzzleName = State.get('currentPuzzle');
        if (puzzleName) {
            Dialogs.showSavePuzzleAs(puzzleName);
        }
    });

    document.getElementById('menu-puzzle-close').addEventListener('click', () => {
        returnToList();
    });

    document.getElementById('menu-puzzle-delete').addEventListener('click', async () => {
        const puzzleName = State.get('currentPuzzle');
        if (puzzleName) {
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
        }
    });

    // Export menu
    document.getElementById('menu-export-acrosslite').addEventListener('click', async () => {
        const puzzleName = State.get('currentPuzzle');
        if (puzzleName) {
            try {
                showStatus('Exporting Across Lite format...');
                const xml = await CrosswordAPI.exportPuzzleXML(puzzleName);
                downloadFile(xml, `${puzzleName}.puz`, 'application/octet-stream');
                showStatus('Exported as Across Lite format');
            } catch (err) {
                showError(`Failed to export: ${err.message}`);
            }
        }
    });

    document.getElementById('menu-export-compiler').addEventListener('click', async () => {
        const puzzleName = State.get('currentPuzzle');
        if (puzzleName) {
            try {
                showStatus('Exporting Crossword Compiler format...');
                const xml = await CrosswordAPI.exportPuzzleXML(puzzleName);
                downloadFile(xml, `${puzzleName}.ccxml`, 'application/xml');
                showStatus('Exported as Crossword Compiler format');
            } catch (err) {
                showError(`Failed to export: ${err.message}`);
            }
        }
    });

    document.getElementById('menu-export-nytimes').addEventListener('click', async () => {
        const puzzleName = State.get('currentPuzzle');
        if (puzzleName) {
            try {
                showStatus('Exporting New York Times format...');
                const xml = await CrosswordAPI.exportPuzzleXML(puzzleName);
                downloadFile(xml, `${puzzleName}.xml`, 'application/xml');
                showStatus('Exported as New York Times format');
            } catch (err) {
                showError(`Failed to export: ${err.message}`);
            }
        }
    });
}

function downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

function showPuzzleChooserForGridCreation() {
    // Show a puzzle chooser dialog
    // This would need to be implemented in dialogs.js
    console.log('Show puzzle chooser for grid creation');
}

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
        document.getElementById('right-panel').style.display = 'block';

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
    document.getElementById('right-panel').style.display = 'none';
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
}
