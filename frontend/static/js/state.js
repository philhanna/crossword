/**
 * Simple observable state management.
 */

const State = (() => {
    let state = {
        mode: 'list', // 'list', 'grid', 'puzzle'
        currentGrid: null,
        currentPuzzle: null,
        grids: [],
        puzzles: [],
    };

    const subscribers = [];

    return {
        get: (key) => (key ? state[key] : state),
        set: (patch) => {
            state = { ...state, ...patch };
            subscribers.forEach(fn => fn(state));
        },
        subscribe: (fn) => {
            subscribers.push(fn);
            return () => {
                subscribers.splice(subscribers.indexOf(fn), 1);
            };
        },
    };
})();
