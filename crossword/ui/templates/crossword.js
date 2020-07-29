/***************************************************************
 *  FUNCTION NAME:   do_grid_close
 *  DESCRIPTION:     Closes the grid screen
 *       1. Asks the server whether the grid has changed
 *       2. If so, opens the grid changed confirmation dialog
 *       3. Otherwise, redirects to main screen
 ***************************************************************/
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
                showElement("gx-dialog");
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

/***************************************************************
 *  FUNCTION NAME:   do_grid_delete
 *  DESCRIPTION:     Prompts the user for confirmation
 *                   of grid deletion
 ***************************************************************/
function do_grid_delete() {
    showElement("gd-dialog");
}

/***************************************************************
 *  FUNCTION NAME:   do_grid_open
 *  DESCRIPTION:     Gets a list of grid files from the server
 *                   and prompts the user to choose one
 ***************************************************************/
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

/***************************************************************
 *  FUNCTION NAME:   do_grid_preview
 ***************************************************************/
function do_grid_preview(gridname) {
    const xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            const jsonstr = this.responseText;
            const obj = JSON.parse(jsonstr);
            document.getElementById("gv-container").style.width = obj.width;
            document.getElementById("gv-heading").innerHTML = obj.heading;
            document.getElementById("gv-svgstr").innerHTML = obj.svgstr;
            showElement("gv-dialog");
        }
    };
    const url = "{{ url_for('uigrid.grid_preview') }}" + "?gridname=" + gridname;
    xhttp.open("GET", url, true);
    xhttp.send();
}

/***************************************************************
 *  FUNCTION NAME:   do_grid_rotate
 *  DESCRIPTION:     Rotates the grid 90 degrees left
 ***************************************************************/
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

/***************************************************************
 *  FUNCTION NAME:   grid_chooser_ajax
 *  DESCRIPTION:     Gets a list of grid files from the server
 *                   and forms a list of links
 ***************************************************************/
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

/***************************************************************
 *  FUNCTION NAME:   do_grid_save
 *  DESCRIPTION:     Turns on the save grid modal dialog
 ***************************************************************/
function do_grid_save(gridname) {
    if (gridname == "") {
        showElement("gs-dialog");
    } else {
        window.location.href = "{{ url_for('uigrid.grid_save') }}";
    }
}

/***************************************************************
 *  FUNCTION NAME:   do_grid_save_as
 *  DESCRIPTION:     Turns on the save grid modal dialog
 ***************************************************************/
function do_grid_save_as() {
    showElement("gsa-dialog");
}

/***************************************************************
 *  FUNCTION NAME:   validateGridNameForSaveAs
 *  DESCRIPTION:     Gets gridname from form. Gets a list of
 *                   grid names from webapp.grids() and sees
 *                   if gridname is in that list.
 *                   Yes - show grid-exists-dialog
 *                   No - proceed to grid_save_as_screen
 ***************************************************************/
function validateGridNameForSaveAs() {
    const newgridname = document.forms["gsa-form"]["newgridname"].value;
    let url = "{{ url_for('uigrid.grid_save_as') }}" + "?newgridname=" + newgridname;
    url = encodeURI(url);

    const xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {

            const jsonstr = this.responseText;
            const grid_list = JSON.parse(jsonstr);

            if (grid_list.includes(newgridname)) {
                // Duplicate name - prompt for OK
                document.getElementById("ge-gridname").innerHTML = newgridname;
                document.getElementById("ge-ok").setAttribute("href", url)
                hideElement("gsa-dialog");
                showElement("ge-dialog");
            } else {
                // No duplicate - proceed
                window.location.href = url;
            }
        }
    };

    // Send AJAX request for existing grid names
    const ajax_url = "{{ url_for('uigrid.grids')}}";
    xhttp.open("GET", ajax_url, true);
    xhttp.send();
}

function do_cancel_grid_save_as() {
    hideElement("gsa-dialog");
    hideElement("ge-dialog");
}

/***************************************************************
 *  FUNCTION NAME:   grid_click
 *  DESCRIPTION:     Gets the x and y coordinates of a grid click
 *                   event and converts them to row and column.
 *                   Then invokes the grid click function on the
 *                   server and refreshes the grid SVG image.
 ***************************************************************/
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

/***************************************************************
 *  FUNCTION NAME:   validateNewGridForm
 *  DESCRIPTION:     Validates the n parameter for a new grid
 ***************************************************************/
function validateNewGridForm() {
    let n = document.forms["gn-form"]["n"].value;
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
    return true;
}

/***************************************************************
 *  FUNCTION NAME:   do_grid_statistics
 *  DESCRIPTION:     Assembles grid statistics and shows results
 ***************************************************************/
function do_grid_stats() {
    const objType = "grid";
    const url = "{{ url_for('uigrid.grid_statistics') }}";
    do_statistics(objType, url);
}

/***************************************************************
 *  FUNCTION NAME:   do_statistics(objType, url)
 *                   objType must be 'grid' or 'puzzle'
 *                   url is '/grid-statistics'
 *                   or     '/puzzle-statistics'
 *
 *  DESCRIPTION:     Common function to grids and puzzles.
 *                   Assembles grid statistics and shows results.
 ***************************************************************/
function do_statistics(objType, url) {
    const xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            // Get the statistics back from the REST call
            const jsonstr = this.responseText;
            const stats = JSON.parse(jsonstr);

            // Fill in the "valid" cell
            const elem_valid = document.getElementById("st-valid");
            elem_valid.innerHTML = stats["valid"];

            // Fill in the "errors" cell
            const elem_errors = document.getElementById("st-errors");
            elem_errors.innerHTML = ""
            const errors = stats["errors"];
            if (stats["valid"] == true) {
                elem_errors.appendChild(document.createTextNode("None"))
            } else {

                // For each error type:
                const descriptions = {
                    "interlock": "Cell interlock errors",
                    "unchecked": "Cell unchecked errors",
                    "wordlength": "Minimum word length errors",
                    "dupwords": "Duplicate word errors",
                };
                for (const error_type in errors) {

                    const error_list = errors[error_type];
                    if (error_list.length == 0) {
                        continue;
                    }

                    const elem_div = document.createElement("div");
                    elem_errors.appendChild(elem_div);

                    const elem_header = document.createElement("header");
                    const description = descriptions[error_type] + ":";
                    const text_node = document.createTextNode(description);
                    elem_header.appendChild(text_node);
                    elem_header.style.fontWeight = "bold";
                    elem_div.appendChild(elem_header);

                    const elem_ul = document.createElement("ul");
                    elem_ul.style.listStyleType = "none";
                    elem_ul.style.lineHeight = "30%";
                    elem_div.appendChild(elem_ul);

                    for (const j in error_list) {
                        const errmsg = error_list[j];
                        const elem_li = document.createElement("li");
                        let elem_p = document.createElement("p");
                        elem_p.style.color = "red";
                        let node_text = document.createTextNode(errmsg);
                        elem_p.appendChild(node_text);
                        elem_li.appendChild(elem_p);
                        elem_ul.appendChild(elem_li);
                    }
                }
            }

            // Fill in the "size" cell
            const elem_size = document.getElementById("st-size");
            elem_size.innerHTML = ""
            elem_size.appendChild(document.createTextNode(stats["size"]));

            // Fill in the "wordcount" cell
            const elem_wordcount = document.getElementById("st-wordcount");
            elem_wordcount.innerHTML = ""
            elem_wordcount.appendChild(document.createTextNode(stats["wordcount"]));

            // Fill in the "wordlengths" table
            const elem_wordlengths = document.getElementById("st-wordlengths");
            elem_wordlengths.innerHTML = ""

            // Declare variables
            let elem_table, elem_tr, elem_th, elem_td, node_text, elem_p;

            // Create the table element and assign its classes
            elem_table = document.createElement("table");
            elem_table.setAttribute("class", "w3-table");
            elem_table.style.borderWidth = "thin";
            elem_table.style.borderStyle = "solid";
            elem_table.style.borderColor = "black";
            elem_table.style.borderCollapse = "collapse";

            // Table header
            elem_tr = document.createElement("tr");

            // Word length
            elem_th = document.createElement("th");
            elem_th.style.width = "15%";
            elem_th.appendChild(document.createTextNode("Word length"));
            elem_tr.appendChild(elem_th);

            // Across words of that length
            elem_th = document.createElement("th");
            elem_th.style.width = "40%";
            elem_th.appendChild(document.createTextNode("Across"));
            elem_tr.appendChild(elem_th);

            // Down words of that length
            elem_th = document.createElement("th");
            elem_th.style.width = "40%";
            elem_th.appendChild(document.createTextNode("Down"));
            elem_tr.appendChild(elem_th);

            // Done with table header
            elem_table.appendChild(elem_tr);

            // Now loop through the "wordlengths" list and create rows
            const wlens = stats["wordlengths"];
            for (const length in wlens) {
                const wlen = wlens[length];
                const alist = wlen["alist"];
                const dlist = wlen["dlist"];

                // Create the table row
                elem_tr = document.createElement("tr");
                elem_table.appendChild(elem_tr);

                // Length
                elem_td = document.createElement("td");
                elem_td.style.border = "1px solid black";
                elem_td.style.textAlign = "center";
                elem_td.appendChild(document.createTextNode(length));
                elem_tr.appendChild(elem_td);

                // Across words
                elem_td = document.createElement("td");
                elem_td.style.border = "1px solid black"
                elem_p = document.createElement("p");
                elem_td.appendChild(elem_p);
                elem_p.style.wordBreak = "break-word";
                node_text = "";
                for (let i = 0; i < alist.length; i++) {
                    if (i > 0) {
                        node_text += ",";
                    }
                    node_text += alist[i];
                }
                elem_td.innerHTML = node_text
                elem_tr.appendChild(elem_td);

                // Down words
                elem_td = document.createElement("td");
                elem_td.style.border = "1px solid black"
                elem_p.style.wordBreak = "break-word";
                node_text = "";
                for (let i = 0; i < dlist.length; i++) {
                    if (i > 0) {
                        node_text += ",";
                    }
                    node_text += dlist[i];
                }
                elem_td.innerHTML = node_text;
                elem_tr.appendChild(elem_td);
            }
            elem_wordlengths.appendChild(elem_table);

            // Show the stats screen
            document.getElementById("st-title").innerHTML = objType + " statistics"
            showElement("st-dialog");
        }
    }

    // Ask the server for grid or puzzle statistics
    xhttp.open("GET", url, true);
    xhttp.send();
}

//  ============================================================
//  Puzzle functions
//  ============================================================

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
 *  FUNCTION NAME:   getRC
 *  DESCRIPTION:     Given a mouse click, returns row and column
 ***************************************************************/
function getRC(event) {
    const x = event.offsetX;
    const y = event.offsetY;
    const r = Math.floor(1 + y / BOXSIZE);
    const c = Math.floor(1 + x / BOXSIZE);
    return [r, c]
}

/***************************************************************
 *  FUNCTION NAME:   do_word
 *  DESCRIPTION:     Given a mouse click, returns row and column
 ***************************************************************/
function do_word(event, url) {
    let r;
    let c;
    [r, c] = getRC(event);
    const xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            const parmstr = this.responseText;
            const parms = JSON.parse(this.responseText);

            // Set the <h3>17 Across</h3> text
            const elem_h3 = document.getElementById("we-heading");
            const heading = `${parms.seq} ${parms.direction} (${parms.length} letters)`;
            elem_h3.innerHTML = heading;

            // Set the word maxlength and value
            const elem_word = document.getElementById("we-word");
            elem_word.maxlength = parms.length;
            elem_word.value = parms.text;

            // Set the clue
            const elem_clue = document.getElementById("we-clue");
            elem_clue.value = parms.clue;

            // Clear any previous select for "suggest" and turn it off
            const elem_select = document.getElementById("we-select");
            elem_select.innerHTML = "";
            hideElement("we-select");
            hideElement("we-match");

            // Make the modal dialog visible
            showElement("we-dialog");
            elem_word.focus();
        }
    };
    url = `${url}?r=${r}&c=${c}`;
    xhttp.open("GET", url, true);
    xhttp.send();
}

/***************************************************************
 *  FUNCTION NAME:   do_puzzle_statistics
 *  DESCRIPTION:     Assembles puzzle statistics and shows results
 ***************************************************************/
function do_puzzle_stats() {
    const objType = "puzzle";
    const url = "{{ url_for('uipuzzle.puzzle_statistics') }}";
    do_statistics(objType, url);
}

//  ============================================================
//  Edit word functions
//  ============================================================
/***************************************************************
 *  NAME: do_word_validate()
 *  DESCRIPTION: Ensures that there are no regexes in the
 *      input word. Raises an alert if so.
 ***************************************************************/
function do_word_validate() {
    const text = document.getElementById("we-word").value;
    for (let i = 0; i < text.length; i++) {
        const ch = text.charAt(i).toUpperCase();
        const p = " ABCDEFGHIJKLMNOPQRSTUVWXYZ.".indexOf(ch);
        if (p < 0) {
            alert(text + " contains non-alphabetic characters");
            return false;
        }
    }
    return true;
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
