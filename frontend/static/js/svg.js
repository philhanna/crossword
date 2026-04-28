// Crossword Puzzle Editor — client-side SVG renderers

// ---------------------------------------------------------------------------
// Grid SVG renderer
// ---------------------------------------------------------------------------

function computeGridNumbers(cells, n) {
    const nums = new Array(n * n).fill(null);
    let num = 1;
    for (let r = 1; r <= n; r++) {
        for (let c = 1; c <= n; c++) {
            const idx = (r - 1) * n + (c - 1);
            if (cells[idx]) continue; // black cell
            const startsAcross = (c === 1 || cells[(r - 1) * n + (c - 2)]) &&
                                  c < n && !cells[(r - 1) * n + c];
            const startsDown   = (r === 1 || cells[(r - 2) * n + (c - 1)]) &&
                                  r < n && !cells[r * n + (c - 1)];
            if (startsAcross || startsDown) nums[idx] = num++;
        }
    }
    return nums;
}

function buildGridSvg(cells, n) {
    const totalPx = n * BOXSIZE + 1;
    const nums    = computeGridNumbers(cells, n);
    const parts   = [
        `<svg xmlns="http://www.w3.org/2000/svg" id="grid-svg" class="svg-grid-mode" ` +
        `width="${totalPx}" height="${totalPx}" style="cursor:pointer;display:block">`,
    ];
    for (let r = 1; r <= n; r++) {
        for (let c = 1; c <= n; c++) {
            const idx   = (r - 1) * n + (c - 1);
            const x     = (c - 1) * BOXSIZE;
            const y     = (r - 1) * BOXSIZE;
            const black = cells[idx];
            parts.push(
                `<rect x="${x}" y="${y}" width="${BOXSIZE}" height="${BOXSIZE}" ` +
                `class="${black ? 'grid-cell-black' : 'grid-cell-white'}" ` +
                `fill="${black ? '#1a1a1a' : 'white'}" stroke="#c8c4bc" stroke-width="0.5"/>`
            );
            if (!black && nums[idx] !== null) {
                parts.push(
                    `<text x="${x + 2}" y="${y + 10}" ` +
                    `font-size="9" font-family="'IBM Plex Sans', sans-serif" fill="#555">${nums[idx]}</text>`
                );
            }
        }
    }
    parts.push(
        `<rect x="0" y="0" width="${totalPx - 1}" height="${totalPx - 1}" ` +
        `fill="none" stroke="#1a1a1a" stroke-width="2"/>`
    );
    parts.push('</svg>');
    return parts.join('');
}

// ---------------------------------------------------------------------------
// Puzzle SVG renderer
// ---------------------------------------------------------------------------

function buildPuzzleSvg(puzzleData, editState = null) {
    const n           = puzzleData.grid.size;
    const blackCells  = puzzleData.grid.cells;        // bool[], true = black
    const puzzleCells = puzzleData.puzzle.cells;      // {"idx": {number?, letter?}}
    const totalPx     = n * BOXSIZE + 1;

    // Build edit-mode lookup structures
    let wordCellSet   = null;  // Set of flat indices belonging to the word
    let cursorFlatIdx = -1;
    let wordLetterMap = {};    // flat index -> letter from editState.text

    if (editState) {
        wordCellSet = new Set();
        const text = editState.text || '';
        editState.cells.forEach(([r, c], i) => {
            const fi = (r - 1) * n + (c - 1);
            wordCellSet.add(fi);
            const ch = text[i];
            if (ch && ch !== ' ') wordLetterMap[fi] = ch;
        });
        const [cr, cc] = editState.cells[editState.cursorIdx];
        cursorFlatIdx = (cr - 1) * n + (cc - 1);
    }

    const parts = [
        `<svg xmlns="http://www.w3.org/2000/svg" id="puzzle-svg" class="svg-puzzle-mode" ` +
        `width="${totalPx}" height="${totalPx}" tabindex="0" style="cursor:pointer;display:block">`,
    ];

    for (let r = 1; r <= n; r++) {
        for (let c = 1; c <= n; c++) {
            const idx   = (r - 1) * n + (c - 1);
            const x     = (c - 1) * BOXSIZE;
            const y     = (r - 1) * BOXSIZE;
            const black = blackCells[idx];

            let fill, cellClass;
            if (black) {
                fill = '#1a1a1a'; cellClass = '';
            } else if (editState && wordCellSet.has(idx)) {
                if (idx === cursorFlatIdx) {
                    fill = '#f5cbcb'; cellClass = 'puzzle-cell-cursor'; // amber active cell
                } else {
                    fill = '#b8d4f5'; cellClass = 'puzzle-cell-word';   // selected word
                }
            } else {
                fill = 'white'; cellClass = 'puzzle-cell-plain';
            }

            parts.push(
                `<rect x="${x}" y="${y}" width="${BOXSIZE}" height="${BOXSIZE}" ` +
                `${cellClass ? `class="${cellClass}" ` : ''}` +
                `fill="${fill}" stroke="#c8c4bc" stroke-width="0.5"/>`
            );

            if (!black) {
                const cd = puzzleCells[String(idx)] || {};
                if (cd.number !== undefined) {
                    parts.push(
                        `<text x="${x + 2}" y="${y + 10}" ` +
                        `font-size="9" font-family="'IBM Plex Sans', sans-serif" fill="#555">${cd.number}</text>`
                    );
                }
                // In edit mode show weText letters for word cells; otherwise use puzzle data
                const letter = (editState && wordCellSet.has(idx))
                    ? (wordLetterMap[idx] || '')
                    : (cd.letter || '');
                if (letter) {
                    const letterFill = (idx === cursorFlatIdx) ? '#1a1a1a' : '#1a1a2e';
                    parts.push(
                        `<text x="${x + BOXSIZE / 2}" y="${y + BOXSIZE - 5}" ` +
                        `font-size="16" font-family="'IBM Plex Mono', monospace" font-weight="500" ` +
                        `fill="${letterFill}" text-anchor="middle">${escapeHtml(letter)}</text>`
                    );
                }
            }
        }
    }

    // Outer border
    parts.push(
        `<rect x="0" y="0" width="${totalPx - 1}" height="${totalPx - 1}" ` +
        `fill="none" stroke="#1a1a1a" stroke-width="2"/>`
    );

    parts.push('</svg>');
    return parts.join('');
}
