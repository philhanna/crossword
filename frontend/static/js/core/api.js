// Crossword Puzzle Editor — talking to the server

// A request the server answered with an error status. `message` is the
// server's own explanation from its {"error": ...} body when it sent one.
export class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
    }
}

// Send a JSON request and return the parsed response body. Throws ApiError
// when the server answers with an error status, and lets network failures
// propagate as they are.
export async function apiFetch(method, path, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body !== undefined) opts.body = JSON.stringify(body);
    const resp = await fetch(path, opts);
    const data = await resp.json().catch(() => null);
    if (!resp.ok) {
        throw new ApiError((data && data.error) || `HTTP ${resp.status}`, resp.status);
    }
    return data;
}
