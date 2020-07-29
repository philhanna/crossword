// Global variables
let PUZZLE_CLICK_STATE = 0;
let CLICK_EVENT;
const BOXSIZE = 32;

function not_yet(fname) {
    alert(`${fname} is not yet implemented...`);
}
function showElement(id) {
    document.getElementById(id).style.display = "block";
}
function hideElement(id) {
    document.getElementById(id).style.display = "none";
}

function do_grid_new() {
    const title = "New grid";
    const label = "<b>Grid size:</b> <em>(a single odd positive integer)</em>";
    const value = "";
    const action = "javascript:validateNewGridFormAndSubmit()";
    const method = "";
    inputBox(title, label, value, action, method);
}
function validateNewGridFormAndSubmit() {
    let n = document.forms["ib-form"]["ib-input"].value;
    if (isNaN(n)) {
        alert(n + " is not a number");
        return false;
    }
    n = Number(n);
    if (n % 2 == 0) {
        alert(n + " is not an odd number");
        return false;
    }
    if (n < 0) {
        alert(n + " is not a positive number");
        return false;
    }
    hideElement("ib");
    let url = "{{ url_for('uigrid.grid_new') }}";
    url += `?n=${n}`;
    window.location.href=url;
}
