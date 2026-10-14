// Crossword Puzzle Editor — checksum used to tell whether a puzzle has unsaved changes

export function _hash(obj) {
    // This is the djb2 hash function
    const s = JSON.stringify(obj);
    let h = 5381;
    for (let i = 0; i < s.length; i++)
        h = (h * 33 ^ s.charCodeAt(i)) >>> 0;
    return h;
}
