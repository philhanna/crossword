function do_grid_close() {
    const xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {

            // Get the server's answer about whether the grid has changed
            const jsonstr = this.responseText;
            const obj = JSON.parse(jsonstr);
            const changed = obj.changed;

            // If it has changed, open the grid changed dialog
            if (changed) {
                const title = "Close grid";
                const prompt = "Close grid without saving?";
                const ok = "{{ url_for('uimain.main_screen') }}";
                messageBox(title, prompt, ok);
            } else {
                window.location.href = "{{ url_for('uimain.main_screen') }}";
            }
        }
    };

    // Ask the server if the grid has changed
    const url = "{{ url_for('uigrid.grid_changed')}}";
    xhttp.open("GET", url, true);
    xhttp.send();
}
function do_grid_delete(gridname) {
    const title = "Delete grid";
    const prompt = `Are you sure you want to delete grid <b>'${gridname}'</b>?`;
    const ok = "{{ url_for('uigrid.grid_delete') }}";
    messageBox(title, prompt, ok);
}
function do_grid_rotate() {
    const xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            document.getElementById("grid-svg").innerHTML = this.responseText;
        }
    };
    const url = "{{ url_for('uigrid.grid_rotate')}}";
    xhttp.open("GET", url, true);
    xhttp.send();
}
function do_grid_save(gridname) {
    if (gridname != "") {
        window.location.href = "{{ url_for('uigrid.grid_save') }}";
    }
    else {
        const title = "Save grid";
        const label = "Grid name:";
        const value = "";
        const action = "javascript:do_grid_save_with_name()";
        const method = "";
        inputBox(title, label, value, action, method);
    }
}
function do_grid_save_with_name() {
    const name = encodeURIComponent(document.getElementById("ib-input").value);
    const url = "{{ url_for('uigrid.grid_save') }}" + "?gridname=" + name;
    window.location.href = url;
}
function do_grid_save_as() {
    const title = "Save grid as";
    const label = "Grid name:";
    const value = "";
    const action = "javascript:validateGridNameForSaveAs()";
    const method = "";
    inputBox(title, label, value, action, method);
}
function validateGridNameForSaveAs() {
    const newgridname = document.forms["ib-form"]["ib-input"].value;
    const xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {

            const jsonstr = this.responseText;
            const grid_list = JSON.parse(jsonstr);
            let url = "{{ url_for('uigrid.grid_save_as') }}" + "?newgridname=" + newgridname;
            url = encodeURI(url);

            if (grid_list.includes(newgridname)) {
                const title = "Overwrite grid";
                const prompt = `<p>Grid "${newgridname}" already exists.  Overwrite it?</p>`;
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

    // Send AJAX request for existing grid names
    const ajax_url = "{{ url_for('uigrid.grids')}}";
    xhttp.open("GET", ajax_url, true);
    xhttp.send();
}
function grid_click(event) {
    const x = event.offsetX;
    const y = event.offsetY;
    const r = Math.floor(1 + y / BOXSIZE); // Boxsize is a global var
    const c = Math.floor(1 + x / BOXSIZE);
    const url = "{{ url_for('uigrid.grid_click')}}" + "?r=" + r + "&c=" + c;
    window.location.href = url;
}
function do_grid_stats() {
    const url = "{{ url_for('uigrid.grid_statistics') }}";
    window.location.href = url;
}
function do_grid_undo() {
    window.location.href = "{{ url_for('uigrid.grid_undo') }}";
}
function do_grid_redo() {
    window.location.href = "{{ url_for('uigrid.grid_redo') }}";
}
