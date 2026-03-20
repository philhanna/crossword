/**
 * Word editor - clue input and word suggestions.
 */

const WordEditor = {
    currentWord: null,

    /**
     * Render word editor with clue and suggestions
     */
    render: (word) => {
        if (!word) return;

        WordEditor.currentWord = word;
        const puzzleName = State.get('currentPuzzle');

        const clueEditor = document.getElementById('word-clue-editor');
        const suggestionsDiv = document.getElementById('word-suggestions');

        // Show clue editor
        clueEditor.style.display = 'block';
        const clueInput = document.getElementById('input-clue');
        clueInput.value = word.clue || '';
        clueInput.placeholder = `Clue for ${word.seq} ${word.direction}`;

        // Wire up save clue button
        document.getElementById('btn-save-clue').onclick = () => {
            WordEditor.saveClue(puzzleName, word.seq, word.direction);
        };

        // Show suggestions section
        const patternInput = document.getElementById('input-pattern');
        patternInput.value = word.pattern || '';
        patternInput.placeholder = `Pattern (e.g., ?HALE)`;

        // Wire up pattern input for live suggestions
        patternInput.addEventListener('input', () => {
            WordEditor.updateSuggestions(patternInput.value);
        });

        // Show initial suggestions if pattern exists
        if (word.pattern) {
            WordEditor.updateSuggestions(word.pattern);
        }
    },

    /**
     * Update suggestions based on pattern
     */
    updateSuggestions: async (pattern) => {
        if (!pattern || pattern.length < 2) {
            document.getElementById('suggestions-list').innerHTML = '';
            return;
        }

        try {
            const result = await CrosswordAPI.getSuggestions(pattern);
            const suggestions = result.suggestions || [];
            const container = document.getElementById('suggestions-list');
            container.innerHTML = '';

            if (suggestions.length === 0) {
                container.innerHTML = '<div style="padding: 0.5rem; color: #999;">No suggestions</div>';
                return;
            }

            suggestions.slice(0, 20).forEach(word => {
                const div = document.createElement('div');
                div.textContent = word;
                div.style.cssText = 'padding: 0.5rem; background: #ecf0f1; margin: 0.25rem 0; border-radius: 3px; cursor: pointer;';
                div.addEventListener('click', () => {
                    document.getElementById('input-clue').focus();
                    showStatus(`Selected: ${word}`);
                });
                div.addEventListener('mouseover', () => {
                    div.style.background = '#bdc3c7';
                });
                div.addEventListener('mouseout', () => {
                    div.style.background = '#ecf0f1';
                });
                container.appendChild(div);
            });
        } catch (err) {
            console.error('Failed to get suggestions:', err);
        }
    },

    /**
     * Save clue for current word
     */
    saveClue: async (puzzleName, seq, direction) => {
        try {
            const clue = document.getElementById('input-clue').value;
            showStatus(`Saving clue...`);
            await CrosswordAPI.setWordClue(puzzleName, seq, direction, clue);
            showStatus(`Clue saved`);
            WordEditor.currentWord.clue = clue;
        } catch (err) {
            showError(`Failed to save clue: ${err.message}`);
        }
    },
};
