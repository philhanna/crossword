/**
 * Grid editor - renders SVG grid and handles cell toggling.
 */

const GridEditor = {
    cellSize: 30,
    currentGridName: null,

    /**
     * Render grid as SVG with clickable cells
     */
    render: (gridData) => {
        const container = document.getElementById('grid-editor');
        const gridName = State.get('currentGrid');
        GridEditor.currentGridName = gridName;

        const { cells, size } = gridData;
        container.innerHTML = '';

        // Create SVG container
        const svgSize = size * GridEditor.cellSize;
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', svgSize);
        svg.setAttribute('height', svgSize);
        svg.setAttribute('style', 'border: 1px solid #ccc;');

        // Render each cell
        for (let r = 0; r < size; r++) {
            for (let c = 0; c < size; c++) {
                const cellIndex = r * size + c;
                const isBlack = cells[cellIndex];

                const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
                rect.setAttribute('x', c * GridEditor.cellSize);
                rect.setAttribute('y', r * GridEditor.cellSize);
                rect.setAttribute('width', GridEditor.cellSize);
                rect.setAttribute('height', GridEditor.cellSize);
                rect.setAttribute('fill', isBlack ? '#000' : '#fff');
                rect.setAttribute('stroke', '#999');
                rect.setAttribute('stroke-width', '1');
                rect.setAttribute('data-r', r);
                rect.setAttribute('data-c', c);

                if (!isBlack) {
                    rect.style.cursor = 'pointer';
                    rect.addEventListener('click', () => GridEditor.toggleCell(gridName, r, c));
                }

                svg.appendChild(rect);
            }
        }

        container.appendChild(svg);
    },

    /**
     * Toggle a black cell and refresh the display
     */
    toggleCell: async (gridName, r, c) => {
        try {
            showStatus(`Toggling cell (${r}, ${c})...`);
            const updatedGrid = await CrosswordAPI.toggleBlackCell(gridName, r, c);
            GridEditor.render(updatedGrid);
            showStatus('Cell toggled');
        } catch (err) {
            showError(`Failed to toggle cell: ${err.message}`);
        }
    },
};
