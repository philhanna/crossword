/**
 * Dialog utilities - reusable modals and prompts.
 */

const Dialogs = {
    /**
     * Show new grid dialog
     */
    showNewGrid: () => {
        const dialog = document.getElementById('dialog-new-grid');
        dialog.style.display = 'flex';

        // Reset form
        document.getElementById('input-grid-name').value = '';
        document.getElementById('input-grid-size').value = '15';

        // Wire up buttons
        document.getElementById('btn-confirm-new-grid').onclick = () => {
            Dialogs.confirmNewGrid();
        };

        document.getElementById('btn-cancel-new-grid').onclick = () => {
            dialog.style.display = 'none';
        };

        // Focus name input
        document.getElementById('input-grid-name').focus();
    },

    /**
     * Confirm new grid creation
     */
    confirmNewGrid: async () => {
        const name = document.getElementById('input-grid-name').value.trim();
        const size = parseInt(document.getElementById('input-grid-size').value);

        if (!name) {
            showError('Please enter a grid name');
            return;
        }

        if (size < 1 || size > 25 || isNaN(size)) {
            showError('Grid size must be between 1 and 25');
            return;
        }

        try {
            showStatus('Creating grid...');
            await CrosswordAPI.createGrid(name, size);
            showStatus('Grid created');
            document.getElementById('dialog-new-grid').style.display = 'none';

            // Reload grids and puzzles
            await loadGridsAndPuzzles();
            await loadAndDisplayGrid(name);
        } catch (err) {
            showError(`Failed to create grid: ${err.message}`);
        }
    },

    /**
     * Show new puzzle dialog
     */
    showNewPuzzle: async () => {
        const dialog = document.getElementById('dialog-new-puzzle');
        dialog.style.display = 'flex';

        // Reset form
        document.getElementById('input-puzzle-name').value = '';

        // Populate grid dropdown
        const select = document.getElementById('select-grid-for-puzzle');
        select.innerHTML = '<option value="">-- Select a grid --</option>';

        try {
            const result = await CrosswordAPI.listGrids();
            const grids = result.grids || [];
            grids.forEach(gridName => {
                const option = document.createElement('option');
                option.value = gridName;
                option.textContent = gridName;
                select.appendChild(option);
            });
        } catch (err) {
            showError(`Failed to load grids: ${err.message}`);
            dialog.style.display = 'none';
            return;
        }

        // Wire up buttons
        document.getElementById('btn-confirm-new-puzzle').onclick = () => {
            Dialogs.confirmNewPuzzle();
        };

        document.getElementById('btn-cancel-new-puzzle').onclick = () => {
            dialog.style.display = 'none';
        };

        // Focus name input
        document.getElementById('input-puzzle-name').focus();
    },

    /**
     * Confirm new puzzle creation
     */
    confirmNewPuzzle: async () => {
        const name = document.getElementById('input-puzzle-name').value.trim();
        const gridName = document.getElementById('select-grid-for-puzzle').value;

        if (!name) {
            showError('Please enter a puzzle name');
            return;
        }

        if (!gridName) {
            showError('Please select a grid');
            return;
        }

        try {
            showStatus('Creating puzzle...');
            await CrosswordAPI.createPuzzle(name, gridName);
            showStatus('Puzzle created');
            document.getElementById('dialog-new-puzzle').style.display = 'none';

            // Reload grids and puzzles
            await loadGridsAndPuzzles();
            await loadAndDisplayPuzzle(name);
        } catch (err) {
            showError(`Failed to create puzzle: ${err.message}`);
        }
    },

    /**
     * Show error dialog (already handled in app.js but included for completeness)
     */
    showError: (message) => {
        showError(message);
    },

    /**
     * Show save grid as dialog
     */
    showSaveGridAs: (currentName) => {
        const newName = prompt(`Save grid "${currentName}" as:`, currentName);
        if (newName && newName !== currentName) {
            // API call would go here
            console.log(`Save grid as: ${newName}`);
        }
    },

    /**
     * Show save puzzle as dialog
     */
    showSavePuzzleAs: (currentName) => {
        const newName = prompt(`Save puzzle "${currentName}" as:`, currentName);
        if (newName && newName !== currentName) {
            // API call would go here
            console.log(`Save puzzle as: ${newName}`);
        }
    },
};
