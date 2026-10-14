// Crossword Puzzle Editor — data-action event delegation
//
// Elements say what they do in data attributes instead of inline handlers:
//
//   data-action="name"           run on a click on the element or inside it
//   data-backdrop-action="name"  run on a click on the element itself but not
//                                its content (the dimmed backdrop of a dialog)
//   data-input="name"            run on input
//   data-change="name"           run on change
//   data-submit="name"           run when a form is submitted
//   data-contextmenu="name"      run on a right-click
//
// Each module registers the handlers it owns with registerActions(). One
// listener per event type on the document finds the element and calls its
// handler as handler(element, event), so HTML built on the fly works without
// attaching anything. Any other data-* attributes on the element are the
// handler's arguments.

const handlers = new Map();

export function registerActions(table) {
    for (const [name, handler] of Object.entries(table)) {
        if (handlers.has(name)) throw new Error(`Action registered twice: ${name}`);
        handlers.set(name, handler);
    }
}

export function listenForActions(root = document) {
    root.addEventListener('click', onClick);
    root.addEventListener('input', (e) => runClosest(e, 'input'));
    root.addEventListener('change', (e) => runClosest(e, 'change'));
    root.addEventListener('submit', (e) => runClosest(e, 'submit'));
    root.addEventListener('contextmenu', (e) => runClosest(e, 'contextmenu'));
}

function onClick(e) {
    const target = e.target;
    if (!(target instanceof Element)) return;
    if (target.dataset.backdropAction) {
        run(target.dataset.backdropAction, target, e);
        return;
    }
    runClosest(e, 'action');
}

function runClosest(e, key) {
    if (!(e.target instanceof Element)) return;
    const attr = `data-${key}`;
    const el = e.target.closest(`[${attr}]`);
    if (el) run(el.getAttribute(attr), el, e);
}

function run(name, el, e) {
    const handler = handlers.get(name);
    if (!handler) throw new Error(`No handler registered for action: ${name}`);
    handler(el, e);
}
