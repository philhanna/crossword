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
function do_grid_open() {
    let function_list = [];

    function preview_anchor(gridname) {
        const elem_a = document.createElement("a");
        const elem_i = document.createElement("i");
        elem_i.setAttribute("class", "material-icons");
        elem_i.appendChild(document.createTextNode("preview"));
        elem_a.appendChild(elem_i);
        const onclick = "do_grid_preview('" + gridname + "')";
        elem_a.setAttribute("onclick", onclick);
        elem_a.style.textDecoration = "none"; // No underline
        return elem_a;
    }

    function_list.push(preview_anchor);

    function open_anchor(gridname) {
        const elem_a = document.createElement("a");
        elem_a.href = "{{ url_for('uigrid.grid_open') }}" + "?gridname=" + gridname;
        elem_a.style.textDecoration = "none"; // No underline
        elem_a.style.verticalAlign = "top"; // Align with icon
        elem_a.appendChild(document.createTextNode(gridname));
        return elem_a;
    }

    function_list.push(open_anchor);

    grid_chooser_ajax(function_list);
    showElement("gc-dialog");
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
function grid_chooser_ajax(function_list) {
    const xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {

            // Get the JSON array of grid names returned by the AJAX call
            const jsonstr = this.responseText;
            const grid_list = JSON.parse(jsonstr);

            // Clear out the <ul> that will contain the list items
            const elem_ul = document.getElementById("grid-list");
            elem_ul.innerHTML = "";

            // Populate the list
            for (let i = 0; i < grid_list.length; i++) {

                // Get the next file name in the list
                const gridname = grid_list[i];

                // Create a <li> to contain anchors for this grid
                const elem_li = document.createElement("li");

                // Add each anchor to the <li>
                for (let j = 0; j < function_list.length; j++) {
                    const fun = function_list[j];
                    const elem_anchor = fun(gridname);
                    elem_li.appendChild(elem_anchor);
                }

                // and append the list item to the <ul>
                elem_ul.appendChild(elem_li);
            }
        }
    };
    const url = "{{ url_for('uigrid.grids')}}";
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

    const xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            document.getElementById("grid-svg").innerHTML = this.responseText;
        }
    };
    const url = "{{ url_for('uigrid.grid_click')}}" + "?r=" + r + "&c=" + c;
    xhttp.open("GET", url, true);
    xhttp.send();
}
function do_grid_stats() {
    const url = "{{ url_for('uigrid.grid_statistics') }}";
    window.location.href = url;
}
