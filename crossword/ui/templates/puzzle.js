// Global variables
let PUZZLE_CLICK_STATE = 0;
let CLICK_EVENT;
const BOXSIZE = 32;

function puzzle_click(event) {

    const TIMEOUT_MS = 300;
    CLICK_EVENT = event;

    function single_click() {
        PUZZLE_CLICK_STATE = 0;
        do_word(CLICK_EVENT, "{{ url_for('uipuzzle.puzzle_click_across') }}");
    }

    function double_click() {
        PUZZLE_CLICK_STATE = 0;
        do_word(event, "{{ url_for('uipuzzle.puzzle_click_down') }}");
    }

    if (PUZZLE_CLICK_STATE == 0) {
        PUZZLE_CLICK_STATE = 1;
        TIMEOUT_VAR = setTimeout(single_click, TIMEOUT_MS);
    } else if (PUZZLE_CLICK_STATE == 1) {
        PUZZLE_CLICK_STATE = 0;
        clearTimeout(TIMEOUT_VAR);
        double_click(CLICK_EVENT);
    }
}
function do_click_across_clue(seq) {
    const elem_ul = document.getElementById("puzzle-across-clues");
    const v = elem_ul.scrollTop;
    const url = "{{ url_for('uipuzzle.puzzle_click_across') }}?seq=" + seq + "&scrollTop=" + v;
    window.location.href = url;
}
function do_click_down_clue(seq) {
    const elem_ul = document.getElementById("puzzle-down-clues");
    const v = elem_ul.scrollTop;
    const url = "{{ url_for('uipuzzle.puzzle_click_down') }}?seq=" + seq + "&scrollTop=" + v;
    window.location.href = url;
}
function do_puzzle_close() {
    const xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            // Get the server's answer about whether the puzzle has changed
            const jsonstr = this.responseText;
            const obj = JSON.parse(jsonstr);
            const changed = obj.changed;
            // If it has changed, open the puzzle changed dialog
            if (changed) {
                const title = "Close puzzle";
                const prompt = "Close puzzle without saving?";
                const ok = "{{ url_for('uimain.main_screen') }}";
                messageBox(title, prompt, ok);
            } else {
                window.location.href = "{{ url_for('uimain.main_screen') }}";
            }
        }
    };
    // Ask the server if the puzzle has changed
    const url = "{{ url_for('uipuzzle.puzzle_changed')}}";
    xhttp.open("GET", url, true);
    xhttp.send();
}
function do_puzzle_delete(puzzlename) {
    const title = "Delete puzzle";
    const prompt = `Are you sure you want to delete puzzle <b>'${puzzlename}'</b>?`;
    const ok = "{{ url_for('uipuzzle.puzzle_delete') }}";
    messageBox(title, prompt, ok);
}
function do_puzzle_save(puzzlename) {
    if (puzzlename != "") {
        window.location.href = "{{ url_for('uipuzzle.puzzle_save') }}";
    }
    else {
        const title = "Save puzzle";
        const label = "Puzzle name:";
        const value = "";
        const action = "javascript:do_puzzle_save_with_name()";
        const method = "";
        inputBox(title, label, value, action, method);
    }
}
function do_puzzle_save_with_name() {
    const name = encodeURIComponent(document.getElementById("ib-input").value);
    const url = "{{ url_for('uipuzzle.puzzle_save') }}" + "?puzzlename=" + name;
    window.location.href = url;
}
function do_puzzle_save_as() {
    const title = "Save puzzle as";
    const label = "Puzzle name:";
    const value = "";
    const action = "javascript:validatePuzzleNameForSaveAs()";
    const method = "";
    inputBox(title, label, value, action, method);
}
function validatePuzzleNameForSaveAs() {
    const newpuzzlename = document.forms["ib-form"]["ib-input"].value;
    const xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {

            const jsonstr = this.responseText;
            const puzzle_list = JSON.parse(jsonstr);
            let url = "{{ url_for('uipuzzle.puzzle_save_as') }}" + "?newpuzzlename=" + newpuzzlename;
            url = encodeURI(url);

            if (puzzle_list.includes(newpuzzlename)) {
                const title = "Overwrite puzzle";
                const prompt = `<p>Puzzle "${newpuzzlename}" already exists.  Overwrite it?</p>`;
                const ok = url;
                hideElement("ib");
                messageBox(title, prompt, ok);
            } else {
                // No duplicate - proceed
                window.location.href = url;
            }
            return true;
        }
    };

    // Send AJAX request for existing puzzle names
    const ajax_url = "{{ url_for('uipuzzle.puzzles')}}";
    xhttp.open("GET", ajax_url, true);
    xhttp.send();
}
function do_puzzle_title() {
    const title = "Puzzle title";
    const label = "<b>Puzzle title:</b>";
    const value = "{{ puzzletitle }}";
    const action = "{{ url_for('uipuzzle.puzzle_title') }}";
    const method = "POST";
    inputBox(title, label, value, action, method);
}
function do_word(event, url) {
    const x = event.offsetX;
    const y = event.offsetY;
    const r = Math.floor(1 + y / BOXSIZE);
    const c = Math.floor(1 + x / BOXSIZE);
    url = `${url}?r=${r}&c=${c}`;
    window.location.href = url;
}
