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
 *  FUNCTION NAME:   do_puzzle_statistics
 *  DESCRIPTION:     Assembles puzzle statistics and shows results
 ***************************************************************/
function do_puzzle_stats() {
    const objType = "puzzle";
    const url = "{{ url_for('uipuzzle.puzzle_statistics') }}";
    do_statistics(objType, url);
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
