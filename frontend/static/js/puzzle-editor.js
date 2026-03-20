/**
 * Puzzle editor - renders puzzle grid with word list and cell interaction.
 */

const PuzzleEditor = {
    cellSize: 30,
    currentPuzzleName: null,
    selectedWord: null,

    /**
     * Render puzzle as SVG with letters and word numbers
     */
    render: (puzzleData) => {
        const container = document.getElementById('puzzle-editor');
        const puzzleName = State.get('currentPuzzle');
        PuzzleEditor.currentPuzzleName = puzzleName;

        const { grid, puzzle } = puzzleData;
        const { cells: gridCells, size } = grid;
        const { cells: puzzleCells, words } = puzzle;

        container.innerHTML = '';

        // Create SVG container
        const svgSize = size * PuzzleEditor.cellSize;
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', svgSize);
        svg.setAttribute('height', svgSize);
        svg.setAttribute('style', 'border: 1px solid #ccc;');

        // Build word map for quick lookup
        const wordMap = {};
        words.forEach(word => {
            wordMap[`${word.seq},${word.direction}`] = word;
        });

        // Render each cell
        for (let r = 0; r < size; r++) {
            for (let c = 0; c < size; c++) {
                const cellIndex = r * size + c;
                const isBlack = gridCells[cellIndex];

                const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');

                // Background rect
                const bgRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                bgRect.setAttribute('x', c * PuzzleEditor.cellSize);
                bgRect.setAttribute('y', r * PuzzleEditor.cellSize);
                bgRect.setAttribute('width', PuzzleEditor.cellSize);
                bgRect.setAttribute('height', PuzzleEditor.cellSize);
                bgRect.setAttribute('fill', isBlack ? '#000' : '#fff');
                bgRect.setAttribute('stroke', '#999');
                bgRect.setAttribute('stroke-width', '1');
                g.appendChild(bgRect);

                if (!isBlack && puzzleCells && puzzleCells[cellIndex]) {
                    const cell = puzzleCells[cellIndex];

                    // Word number (if this is the start of a word)
                    if (cell.number) {
                        const number = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                        number.setAttribute('x', c * PuzzleEditor.cellSize + 2);
                        number.setAttribute('y', r * PuzzleEditor.cellSize + 10);
                        number.setAttribute('font-size', '10px');
                        number.setAttribute('font-weight', 'bold');
                        number.setAttribute('fill', '#000');
                        number.textContent = cell.number;
                        g.appendChild(number);
                    }

                    // Cell letter
                    if (cell.letter) {
                        const letter = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                        letter.setAttribute('x', c * PuzzleEditor.cellSize + PuzzleEditor.cellSize / 2);
                        letter.setAttribute('y', r * PuzzleEditor.cellSize + PuzzleEditor.cellSize * 0.7);
                        letter.setAttribute('text-anchor', 'middle');
                        letter.setAttribute('font-size', '20px');
                        letter.setAttribute('font-weight', 'bold');
                        letter.setAttribute('fill', '#000');
                        letter.textContent = cell.letter;
                        g.appendChild(letter);
                    }

                    // Click handler for selecting cells
                    bgRect.style.cursor = 'pointer';
                    bgRect.addEventListener('click', () => {
                        PuzzleEditor.selectCell(puzzleName, r, c, cell);
                    });
                }

                svg.appendChild(g);
            }
        }

        container.appendChild(svg);
        PuzzleEditor.renderWordList(words);
    },

    /**
     * Render word list in the sidebar
     */
    renderWordList: (words) => {
        const sidebar = document.getElementById('word-editor');
        let html = '<h3>Words</h3><div style="max-height: 300px; overflow-y: auto;">';

        // Group by direction
        const across = words.filter(w => w.direction === 'across');
        const down = words.filter(w => w.direction === 'down');

        if (across.length > 0) {
            html += '<strong>Across</strong><div>';
            across.forEach(word => {
                html += `<div class="word-item" data-seq="${word.seq}" data-dir="across" style="padding: 0.25rem; cursor: pointer; background: #f0f0f0; margin: 0.25rem 0; border-radius: 3px;">`;
                html += `${word.seq}. (${word.answer?.length || 0} letters)`;
                if (word.clue) html += ` - ${word.clue}`;
                html += '</div>';
            });
            html += '</div>';
        }

        if (down.length > 0) {
            html += '<strong style="margin-top: 0.5rem; display: block;">Down</strong><div>';
            down.forEach(word => {
                html += `<div class="word-item" data-seq="${word.seq}" data-dir="down" style="padding: 0.25rem; cursor: pointer; background: #f0f0f0; margin: 0.25rem 0; border-radius: 3px;">`;
                html += `${word.seq}. (${word.answer?.length || 0} letters)`;
                if (word.clue) html += ` - ${word.clue}`;
                html += '</div>';
            });
            html += '</div>';
        }

        html += '</div>';
        sidebar.innerHTML = html;

        // Wire up word item clicks
        document.querySelectorAll('.word-item').forEach(item => {
            item.addEventListener('click', () => {
                const seq = item.getAttribute('data-seq');
                const dir = item.getAttribute('data-dir');
                PuzzleEditor.selectedWord = { seq: parseInt(seq), direction: dir };
                WordEditor.render(words.find(w => w.seq == seq && w.direction === dir));
            });
        });
    },

    /**
     * Select a cell in the puzzle
     */
    selectCell: async (puzzleName, r, c, cell) => {
        try {
            // Attempt to get the word at this cell
            // For now, just show which cell is selected
            showStatus(`Selected cell (${r}, ${c})`);
        } catch (err) {
            showError(`Failed to select cell: ${err.message}`);
        }
    },
};
