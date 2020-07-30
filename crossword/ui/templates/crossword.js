
/***************************************************************
 *  FUNCTION NAME:   do_puzzle_preview
 ***************************************************************/
function do_puzzle_preview(puzzlename) {
    const xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            const jsonstr = this.responseText;
            const obj = JSON.parse(jsonstr);
            document.getElementById("pv-container").style.width = obj.width;
            document.getElementById("pv-heading").innerHTML = obj.heading;
            document.getElementById("pv-svgstr").innerHTML = obj.svgstr;
            showElement("pv-dialog");
        }
    };
    const url = "{{ url_for('uipuzzle.puzzle_preview') }}" + "?puzzlename=" + puzzlename;
    xhttp.open("GET", url, true);
    xhttp.send();
}
/***************************************************************
 *  FUNCTION NAME:   do_puzzle_undo
 *  DESCRIPTION:     Undoes the last change
 ***************************************************************/
function do_puzzle_undo() {
    window.location.href = "{{ url_for('uipuzzle.puzzle_undo') }}";
}

/***************************************************************
 *  FUNCTION NAME:   do_puzzle_redo
 *  DESCRIPTION:     Redoes the last change
 ***************************************************************/
function do_puzzle_redo() {
    window.location.href = "{{ url_for('uipuzzle.puzzle_redo') }}";
}
