/**
 * API client - Promise-based wrapper around HTTP endpoints.
 * All methods return Promise<response> or throw on error.
 */

const API_BASE = '/api';

class CrosswordAPI {
    // =========================================================================
    // Grid operations
    // =========================================================================

    /**
     * List all grids for the current user.
     * GET /api/grids
     */
    static async listGrids() {
        const response = await fetch(`${API_BASE}/grids`);
        return this._handleResponse(response);
    }

    /**
     * Create a new grid.
     * POST /api/grids
     */
    static async createGrid(name, size) {
        const response = await fetch(`${API_BASE}/grids`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, size }),
        });
        return this._handleResponse(response);
    }

    /**
     * Load a grid by name.
     * GET /api/grids/<name>
     */
    static async loadGrid(name) {
        const response = await fetch(`${API_BASE}/grids/${encodeURIComponent(name)}`);
        return this._handleResponse(response);
    }

    /**
     * Delete a grid by name.
     * DELETE /api/grids/<name>
     */
    static async deleteGrid(name) {
        const response = await fetch(`${API_BASE}/grids/${encodeURIComponent(name)}`, {
            method: 'DELETE',
        });
        return this._handleResponse(response);
    }

    /**
     * Toggle a black cell in a grid.
     * PUT /api/grids/<name>/cells/<r>/<c>
     */
    static async toggleBlackCell(name, r, c) {
        const response = await fetch(
            `${API_BASE}/grids/${encodeURIComponent(name)}/cells/${r}/${c}`,
            { method: 'PUT' }
        );
        return this._handleResponse(response);
    }

    /**
     * Rotate a grid 90 degrees counterclockwise.
     * POST /api/grids/<name>/rotate
     */
    static async rotateGrid(name) {
        const response = await fetch(
            `${API_BASE}/grids/${encodeURIComponent(name)}/rotate`,
            { method: 'POST' }
        );
        return this._handleResponse(response);
    }

    /**
     * Undo the last operation on a grid.
     * POST /api/grids/<name>/undo
     */
    static async undoGrid(name) {
        const response = await fetch(
            `${API_BASE}/grids/${encodeURIComponent(name)}/undo`,
            { method: 'POST' }
        );
        return this._handleResponse(response);
    }

    /**
     * Redo the last undone operation on a grid.
     * POST /api/grids/<name>/redo
     */
    static async redoGrid(name) {
        const response = await fetch(
            `${API_BASE}/grids/${encodeURIComponent(name)}/redo`,
            { method: 'POST' }
        );
        return this._handleResponse(response);
    }

    // =========================================================================
    // Puzzle operations
    // =========================================================================

    /**
     * List all puzzles for the current user.
     * GET /api/puzzles
     */
    static async listPuzzles() {
        const response = await fetch(`${API_BASE}/puzzles`);
        return this._handleResponse(response);
    }

    /**
     * Create a new puzzle from a grid.
     * POST /api/puzzles
     */
    static async createPuzzle(name, gridName) {
        const response = await fetch(`${API_BASE}/puzzles`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, grid_name: gridName }),
        });
        return this._handleResponse(response);
    }

    /**
     * Load a puzzle by name.
     * GET /api/puzzles/<name>
     */
    static async loadPuzzle(name) {
        const response = await fetch(`${API_BASE}/puzzles/${encodeURIComponent(name)}`);
        return this._handleResponse(response);
    }

    /**
     * Delete a puzzle by name.
     * DELETE /api/puzzles/<name>
     */
    static async deletePuzzle(name) {
        const response = await fetch(`${API_BASE}/puzzles/${encodeURIComponent(name)}`, {
            method: 'DELETE',
        });
        return this._handleResponse(response);
    }

    /**
     * Set a letter in a puzzle cell.
     * PUT /api/puzzles/<name>/cells/<r>/<c>
     */
    static async setCellLetter(name, r, c, letter) {
        const response = await fetch(
            `${API_BASE}/puzzles/${encodeURIComponent(name)}/cells/${r}/${c}`,
            {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ letter }),
            }
        );
        return this._handleResponse(response);
    }

    /**
     * Get a word at a numbered cell.
     * GET /api/puzzles/<name>/words/<seq>/<direction>
     */
    static async getWordAt(name, seq, direction) {
        const response = await fetch(
            `${API_BASE}/puzzles/${encodeURIComponent(name)}/words/${seq}/${direction}`
        );
        return this._handleResponse(response);
    }

    /**
     * Set a clue for a word.
     * PUT /api/puzzles/<name>/words/<seq>/<direction>
     */
    static async setWordClue(name, seq, direction, clue) {
        const response = await fetch(
            `${API_BASE}/puzzles/${encodeURIComponent(name)}/words/${seq}/${direction}`,
            {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ clue }),
            }
        );
        return this._handleResponse(response);
    }

    /**
     * Undo the last operation on a puzzle.
     * POST /api/puzzles/<name>/undo
     */
    static async undoPuzzle(name) {
        const response = await fetch(
            `${API_BASE}/puzzles/${encodeURIComponent(name)}/undo`,
            { method: 'POST' }
        );
        return this._handleResponse(response);
    }

    /**
     * Redo the last undone operation on a puzzle.
     * POST /api/puzzles/<name>/redo
     */
    static async redoPuzzle(name) {
        const response = await fetch(
            `${API_BASE}/puzzles/${encodeURIComponent(name)}/redo`,
            { method: 'POST' }
        );
        return this._handleResponse(response);
    }

    /**
     * Replace the grid of a puzzle with a new grid.
     * PUT /api/puzzles/<name>/grid
     */
    static async replacePuzzleGrid(name, newGridName) {
        const response = await fetch(
            `${API_BASE}/puzzles/${encodeURIComponent(name)}/grid`,
            {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ new_grid_name: newGridName }),
            }
        );
        return this._handleResponse(response);
    }

    // =========================================================================
    // Word operations
    // =========================================================================

    /**
     * Get word suggestions matching a pattern.
     * GET /api/words/suggestions?pattern=<pattern>
     */
    static async getSuggestions(pattern) {
        const query = new URLSearchParams({ pattern });
        const response = await fetch(`${API_BASE}/words/suggestions?${query}`);
        return this._handleResponse(response);
    }

    /**
     * Get all words in the dictionary.
     * GET /api/words/all
     */
    static async getAllWords() {
        const response = await fetch(`${API_BASE}/words/all`);
        return this._handleResponse(response);
    }

    /**
     * Validate if a word is in the dictionary.
     * GET /api/words/validate?word=<word>
     */
    static async validateWord(word) {
        const query = new URLSearchParams({ word });
        const response = await fetch(`${API_BASE}/words/validate?${query}`);
        return this._handleResponse(response);
    }

    // =========================================================================
    // Export operations
    // =========================================================================

    /**
     * Export a grid to PDF.
     * GET /api/export/grids/<name>/pdf
     */
    static async exportGridPDF(name) {
        const response = await fetch(
            `${API_BASE}/export/grids/${encodeURIComponent(name)}/pdf`
        );
        if (!response.ok) {
            throw new Error(`Export failed: ${response.statusText}`);
        }
        return response.blob();
    }

    /**
     * Export a grid to PNG.
     * GET /api/export/grids/<name>/png
     */
    static async exportGridPNG(name) {
        const response = await fetch(
            `${API_BASE}/export/grids/${encodeURIComponent(name)}/png`
        );
        if (!response.ok) {
            throw new Error(`Export failed: ${response.statusText}`);
        }
        return response.blob();
    }

    /**
     * Export a puzzle to .puz format.
     * GET /api/export/puzzles/<name>/puz
     */
    static async exportPuzzlePUZ(name) {
        const response = await fetch(
            `${API_BASE}/export/puzzles/${encodeURIComponent(name)}/puz`
        );
        if (!response.ok) {
            throw new Error(`Export failed: ${response.statusText}`);
        }
        return response.blob();
    }

    /**
     * Export a puzzle to XML.
     * GET /api/export/puzzles/<name>/xml
     */
    static async exportPuzzleXML(name) {
        const response = await fetch(
            `${API_BASE}/export/puzzles/${encodeURIComponent(name)}/xml`
        );
        if (!response.ok) {
            throw new Error(`Export failed: ${response.statusText}`);
        }
        return response.text();
    }

    // =========================================================================
    // Helper methods
    // =========================================================================

    /**
     * Handle HTTP response - check status and parse JSON.
     * Throws an error if response is not OK or if JSON contains an error field.
     */
    static async _handleResponse(response) {
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        try {
            const data = await response.json();
            if (data.error) {
                throw new Error(data.error);
            }
            return data;
        } catch (err) {
            if (err instanceof SyntaxError) {
                throw new Error('Invalid JSON response from server');
            }
            throw err;
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CrosswordAPI;
}
