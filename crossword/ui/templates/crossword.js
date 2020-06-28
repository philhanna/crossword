//  ============================================================
//  Global variables and functions
//  ============================================================

var BOXSIZE = 32;
var CLICK_EVENT;
var PUZZLE_CLICK_STATE = 0;
var TIMEOUT_VAR;

/***************************************************************
 * FUNCTION NAME:   showElement
 * DESCRIPTION:     Turns on the display of a dialog
 ***************************************************************/

function showElement(id) {
   document.getElementById(id).style.display = 'block';
}

/***************************************************************
 *  FUNCTION NAME:   hideElement
 *  DESCRIPTION:     Turns off the display of a dialog
 ***************************************************************/
function hideElement(id) {
   document.getElementById(id).style.display = 'none';
}

//  ============================================================
//  Grid functions
//  ============================================================

/***************************************************************
 *  FUNCTION NAME:   do_grid_close
 *  DESCRIPTION:     Closes the grid screen
 *       1. Asks the server whether the grid has changed
 *       2. If so, opens the grid changed confirmation dialog
 *       3. Otherwise, redirects to main screen
 ***************************************************************/
function do_grid_close() {
   var xhttp = new XMLHttpRequest();

   xhttp.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200) {

         // Get the server's answer about whether the grid has changed
         var jsonstr = this.responseText;
         var obj = JSON.parse(jsonstr);
         var changed = obj.changed;

         // If it has changed, open the grid changed dialog
         if (changed) {
            showElement('gx-dialog');
         }
         else {
            window.location.href = "{{ url_for('main_screen') }}";
         }
      }
   };

   // Ask the server if the grid has changed
   var url = '{{ url_for("grid_changed")}}';
   xhttp.open("GET", url, true);
   xhttp.send();
}

/***************************************************************
 *  FUNCTION NAME:   do_grid_delete
 *  DESCRIPTION:     Prompts the user for confirmation
 *                   of grid deletion
 ***************************************************************/
function do_grid_delete() {
  showElement('gd-dialog');
}

/***************************************************************
 *  FUNCTION NAME:   do_grid_new
 *  DESCRIPTION:     Prompts the user for a grid size
 ***************************************************************/
function do_grid_new() {
  showElement('gn-dialog');
}

/***************************************************************
 *  FUNCTION NAME:   do_grid_open
 *  DESCRIPTION:     Gets a list of grid files from the server
 *                   and prompts the user to choose one
 ***************************************************************/
function do_grid_open() {
    function_list = [];

    function preview_anchor(gridname) {
        var elem_a = document.createElement("a");
        var elem_i = document.createElement("i");
        elem_i.setAttribute("class", "material-icons");
        elem_i.appendChild(document.createTextNode("preview"));
        elem_a.appendChild(elem_i);
        var onclick = "do_grid_preview('" + gridname + "')";
        elem_a.setAttribute("onclick", onclick);
        elem_a.style.textDecoration = "none"; // No underline
        return elem_a;
    };
    function_list.push(preview_anchor);

    function open_anchor(gridname) {
        var elem_a = document.createElement("a");
        elem_a.href = "{{ url_for('grid_open') }}" + "?gridname=" + gridname;
        elem_a.style.textDecoration = "none"; // No underline
        elem_a.style.verticalAlign = "top"; // Align with icon
        elem_a.appendChild(document.createTextNode(gridname));
        return elem_a;
    };
    function_list.push(open_anchor);

    grid_chooser_ajax(function_list);
    showElement('gc-dialog');
}

/***************************************************************
 *  FUNCTION NAME:   do_grid_preview
 ***************************************************************/
function do_grid_preview(gridname) {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
     if (this.readyState == 4 && this.status == 200) {
        var jsonstr = this.responseText;
        obj = JSON.parse(jsonstr);
        document.getElementById("gv-gridname").innerHTML = obj.gridname;
        document.getElementById("gv-container").style.width = obj.width;
        document.getElementById("gv-wordcount").innerHTML = obj.wordcount;
        document.getElementById("gv-svgstr").innerHTML = obj.svgstr;
        showElement('gv-dialog');
     }
  };
  var url = '{{ url_for("grid_preview") }}' + "?gridname=" + gridname;
  xhttp.open("GET", url, true);
  xhttp.send();
}

/***************************************************************
 *  FUNCTION NAME:   do_grid_rotate
 *  DESCRIPTION:     Rotates the grid 90 degrees left
 ***************************************************************/
function do_grid_rotate() {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
     if (this.readyState == 4 && this.status == 200) {
        document.getElementById("grid-svg").innerHTML = this.responseText;
     }
  };
  var url = '{{ url_for("grid_rotate")}}';
  xhttp.open("GET", url, true);
  xhttp.send();
}

/***************************************************************
 *  FUNCTION NAME:   grid_chooser_ajax
 *  DESCRIPTION:     Gets a list of grid files from the server
 *                   and forms a list of links
 ***************************************************************/
function grid_chooser_ajax(function_list) {
   var xhttp = new XMLHttpRequest();
   xhttp.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200) {

         // Get the JSON array of grid names returned by the AJAX call
         var jsonstr = this.responseText;
         var grid_list = JSON.parse(jsonstr);

         // Clear out the <ul> that will contain the list items
         var elem_ul = document.getElementById('grid-list');
         elem_ul.innerHTML = ""

         // Populate the list
         for (var i = 0; i < grid_list.length; i++) {

            // Get the next file name in the list
            var gridname = grid_list[i];

            // Create a <li> to contain anchors for this grid
            var elem_li = document.createElement("li");

            // Add each anchor to the <li>
            for (var j = 0; j < function_list.length; j++) {
                fun = function_list[j];
                elem_anchor = fun(gridname);
                elem_li.appendChild(elem_anchor);
            }

            // and append the list item to the <ul>
            elem_ul.appendChild(elem_li);
         }
      }
   };
   var url = '{{ url_for("grids")}}';
   xhttp.open("GET", url, true);
   xhttp.send();
}

/***************************************************************
 *  FUNCTION NAME:   do_grid_save
 *  DESCRIPTION:     Turns on the save grid modal dialog
 ***************************************************************/
function do_grid_save(gridname) {
    if (gridname == "") {
        showElement('gs-dialog');
    }
    else {
        window.location.href = "{{ url_for('grid_save') }}";
    }
}

/***************************************************************
 *  FUNCTION NAME:   do_grid_save_as
 *  DESCRIPTION:     Turns on the save grid modal dialog
 ***************************************************************/
function do_grid_save_as() {
   showElement('gsa-dialog');
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
    var newgridname = document.forms["gsa-form"]["newgridname"].value;
    var url = "{{ url_for('grid_save_as') }}" + "?newgridname=" + newgridname;
    url = encodeURI(url);

    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {

            var jsonstr = this.responseText;
            var grid_list = JSON.parse(jsonstr);

            if (grid_list.includes(newgridname)) {
                // Duplicate name - prompt for OK
                document.getElementById('ge-gridname').innerHTML = newgridname;
                document.getElementById('ge-ok').setAttribute('href', url)
                hideElement('gsa-dialog');
                showElement('ge-dialog');
            }
            else {
                // No duplicate - proceed
                window.location.href = url;
            }
        }
    };

    // Send AJAX request for existing grid names
    var ajax_url = '{{ url_for("grids")}}';
    xhttp.open("GET", ajax_url, true);
    xhttp.send();
}

function do_cancel_grid_save_as() {
    hideElement('gsa-dialog');
    hideElement('ge-dialog');
}

/***************************************************************
 *  FUNCTION NAME:   grid_click
 *  DESCRIPTION:     Gets the x and y coordinates of a grid click
 *                   event and converts them to row and column.
 *                   Then invokes the grid click function on the
 *                   server and refreshes the grid SVG image.
 ***************************************************************/
function grid_click(event) {
  var x = event.offsetX;
  var y = event.offsetY;
  var r = Math.floor(1 + y/BOXSIZE); // Boxsize is a global var
  var c = Math.floor(1 + x/BOXSIZE);

  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
     if (this.readyState == 4 && this.status == 200) {
        document.getElementById("grid-svg").innerHTML = this.responseText;
     }
  };
  var url = '{{ url_for("grid_click")}}' + "?r=" + r + "&c=" + c;
  xhttp.open("GET", url, true);
  xhttp.send();
}

/***************************************************************
 *  FUNCTION NAME:   validateNewGridForm
 *  DESCRIPTION:     Validates the n parameter for a new grid
 ***************************************************************/
function validateNewGridForm() {
   var n = document.forms["ng-form"]["n"].value;
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
   var objType = "grid"
   var url = "{{ url_for('grid_statistics') }}";
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
   var xhttp = new XMLHttpRequest();
   xhttp.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200) {
         // Get the statistics back from the REST call
         var jsonstr = this.responseText;
         var stats = JSON.parse(jsonstr);

         // Fill in the "valid" cell
         var elem_valid = document.getElementById('st-valid');
         elem_valid.innerHTML = stats['valid'];

         // Fill in the "errors" cell
         var elem_errors = document.getElementById('st-errors');
         elem_errors.innerHTML = ""
         var errors = stats['errors']
         if (stats['valid'] == true) {
            elem_errors.appendChild(document.createTextNode("None"))
         }
         else {

            // For each error type:
            var descriptions = {
               "interlock": "Cell interlock errors",
               "unchecked": "Cell unchecked errors",
               "wordlength": "Minimum word length errors",
               "dupwords": "Duplicate word errors",
            };
            for (var error_type in errors) {

               var error_list = errors[error_type];
               if (error_list.length == 0) {
                  continue;
               }

               var elem_div = document.createElement('div');
               elem_errors.appendChild(elem_div);

               var elem_header = document.createElement('header');
               var description = descriptions[error_type] + ":";
               var text_node = document.createTextNode(description);
               elem_header.appendChild(text_node);
               elem_header.style.fontWeight = "bold";
               elem_div.appendChild(elem_header);

               var elem_ul = document.createElement("ul");
               elem_ul.style.listStyleType = "none";
               elem_ul.style.lineHeight = "30%";
               elem_div.appendChild(elem_ul);

               for (var j in error_list) {
                  errmsg = error_list[j];
                  var elem_li = document.createElement("li");
                  var elem_p = document.createElement("p");
                  elem_p.style.color = "red";
                  var node_text = document.createTextNode(errmsg);
                  elem_p.appendChild(node_text);
                  elem_li.appendChild(elem_p);
                  elem_ul.appendChild(elem_li);
               }
            }
         }

         // Fill in the "size" cell
         var elem_size = document.getElementById('st-size');
         elem_size.innerHTML = ""
         elem_size.appendChild(document.createTextNode(stats['size']));

         // Fill in the "wordcount" cell
         var elem_wordcount = document.getElementById('st-wordcount');
         elem_wordcount.innerHTML = ""
         elem_wordcount.appendChild(document.createTextNode(stats['wordcount']));

         // Fill in the "wordlengths" table
         var elem_wordlengths = document.getElementById('st-wordlengths');
         elem_wordlengths.innerHTML = ""

         // Declare variables
         var elem_table, elem_tr, elem_th, elem_td, node_text, elem_p;

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
         var wlens = stats['wordlengths'];
         for (var length in wlens) {
            var wlen = wlens[length];
            var alist = wlen['alist'];
            var dlist = wlen['dlist'];

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
            for (var i = 0; i < alist.length; i++) {
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
            for (var i = 0; i < dlist.length; i++) {
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
         document.getElementById('st-title').innerHTML = objType + " statistics"
         showElement('st-dialog');
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
 *  FUNCTION NAME:   do_puzzle_close
 *  DESCRIPTION:     Closes the puzzle screen
 *       1. Asks the server whether the puzzle has changed
 *       2. If so, opens the puzzle changed confirmation dialog
 *       3. Otherwise, redirects to main screen
 ***************************************************************/
function do_puzzle_close() {
   var xhttp = new XMLHttpRequest();
   xhttp.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200) {
         // Get the server's answer about whether the puzzle has changed
         var jsonstr = this.responseText;
         var obj = JSON.parse(jsonstr);
         var changed = obj.changed;
         // If it has changed, open the puzzle changed dialog
         if (changed) {
            showElement('px-dialog');
         }
         else {
            window.location.href = "{{ url_for('main_screen') }}";
         }
      }
   }
   // Ask the server if the puzzle has changed
   var url = '{{ url_for("puzzle_changed")}}';
   xhttp.open("GET", url, true);
   xhttp.send();
}

/***************************************************************
 *  FUNCTION NAME:   do_puzzle_delete
 *  DESCRIPTION:     Opens the puzzle delete dialog
 ***************************************************************/
function do_puzzle_delete() {
   showElement('pd-dialog');
}

/***************************************************************
 *  FUNCTION NAME:   do_puzzle_new
 *  DESCRIPTION:     Gets a list of grid files from the server
 *                   and prompts the user to choose one
 ***************************************************************/
function do_puzzle_new() {
    function_list = [];

    function open_anchor(gridname) {
        var elem_a = document.createElement("a");
        elem_a.href = "{{ url_for('puzzle_new') }}" + "?gridname=" + gridname;
        elem_a.style.textDecoration = "none"; // No underline
        elem_a.appendChild(document.createTextNode(gridname));
        return elem_a;
    };
    function_list.push(open_anchor);

    grid_chooser_ajax(function_list);
    showElement('gc-dialog');
}

/***************************************************************
 *  FUNCTION NAME:   do_puzzle_open
 *  DESCRIPTION:     Gets a list of puzzle files from the server
 *                   and prompts the user to choose one
 ***************************************************************/
function do_puzzle_open() {
    function_list = [];

    function preview_anchor(puzzlename) {
        var elem_a = document.createElement("a");
        var elem_i = document.createElement("i");
        elem_i.setAttribute("class", "material-icons");
        elem_i.appendChild(document.createTextNode("preview"));
        elem_a.appendChild(elem_i);
        var onclick = "do_puzzle_preview('" + puzzlename + "')";
        elem_a.setAttribute("onclick", onclick);
        elem_a.style.textDecoration = "none"; // No underline
        return elem_a;
    };
    function_list.push(preview_anchor);

    function open_anchor(puzzlename) {
        var elem_a = document.createElement("a");
        elem_a.href = "{{ url_for('puzzle_open') }}" + "?puzzlename=" + puzzlename;
        elem_a.style.textDecoration = "none"; // No underline
        elem_a.style.verticalAlign = "top"; // Align with icon
        elem_a.appendChild(document.createTextNode(puzzlename));
        return elem_a;
    };
    function_list.push(open_anchor);

    puzzle_chooser_ajax(function_list);
    showElement('pc-dialog');
}

/***************************************************************
 *  FUNCTION NAME:   do_puzzle_preview
 ***************************************************************/
function do_puzzle_preview(puzzlename) {
  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
     if (this.readyState == 4 && this.status == 200) {
        var jsonstr = this.responseText;
        obj = JSON.parse(jsonstr);
        document.getElementById("pv-puzzlename").innerHTML = obj.puzzlename;
        document.getElementById("pv-container").style.width = obj.width;
        document.getElementById("pv-wordcount").innerHTML = obj.wordcount;
        document.getElementById("pv-svgstr").innerHTML = obj.svgstr;
        showElement('pv-dialog');
     }
  };
  var url = '{{ url_for("puzzle_preview") }}' + "?puzzlename=" + puzzlename;
  xhttp.open("GET", url, true);
  xhttp.send();
}

/***************************************************************
 *  FUNCTION NAME:   do_puzzle_save
 *  DESCRIPTION:     Turns on the save puzzle modal dialog
 ***************************************************************/
function do_puzzle_save(puzzlename) {
    if (puzzlename == "") {
        showElement('ps-dialog');
    }
    else {
        window.location.href = "{{ url_for('puzzle_save') }}";
    }
}

/***************************************************************
 *  FUNCTION NAME:   do_puzzle_save_as
 *  DESCRIPTION:     Turns on the save puzzle as modal dialog
 ***************************************************************/
function do_puzzle_save_as() {
   showElement('psa-dialog');
}

/***************************************************************
 *  FUNCTION NAME:   validatePuzzleNameForSaveAs
 *  DESCRIPTION:     Gets puzzlename from form. Gets a list of
 *                   puzzle names from webapp.puzzles() and sees
 *                   if puzzlename is in that list.
 *                   Yes - show puzzle-exists-dialog
 *                   No - proceed to puzzle_save_as_screen
 ***************************************************************/
function validatePuzzleNameForSaveAs() {
    var newpuzzlename = document.forms["psa-form"]["newpuzzlename"].value;
    var url = "{{ url_for('puzzle_save_as') }}" + "?newpuzzlename=" + newpuzzlename;
    url = encodeURI(url);

    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {

            var jsonstr = this.responseText;
            var puzzle_list = JSON.parse(jsonstr);

            if (puzzle_list.includes(newpuzzlename)) {
                // Duplicate name - prompt for OK
                document.getElementById('pe-puzzlename').innerHTML = newpuzzlename;
                document.getElementById('pe-ok').setAttribute('href', url)
                hideElement('psa-dialog');
                showElement('pe-dialog');
            }
            else {
                // No duplicate - proceed
                window.location.href = url;
            }
        }
    };

    // Send AJAX request for existing puzzle names
    var ajax_url = '{{ url_for("puzzles")}}';
    xhttp.open("GET", ajax_url, true);
    xhttp.send();
}

function do_cancel_puzzle_save_as() {
    hideElement('psa-dialog');
    hideElement('pe-dialog');
}

/***************************************************************
 *  FUNCTION NAME:   getRC
 *  DESCRIPTION:     Given a mouse click, returns row and column
 ***************************************************************/
function getRC(event) {
  var x = event.offsetX;
  var y = event.offsetY;
  var r = Math.floor(1 + y/BOXSIZE);
  var c = Math.floor(1 + x/BOXSIZE);
  return [r, c]
}

/***************************************************************
 *  FUNCTION NAME:   do_word
 *  DESCRIPTION:     Given a mouse click, returns row and column
 ***************************************************************/
function do_word(event, url) {
   var r;
   var c;
   [r, c] = getRC(event);
   var xhttp = new XMLHttpRequest();
   xhttp.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200) {
         var parmstr = this.responseText;
         var parms = JSON.parse(this.responseText);

         // Set the <h3>17 Across</h3> text
         var elem_h3 = document.getElementById('we-heading');
         var heading = parms.seq + " " + parms.direction + " (" + parms.length + " letters)";
         elem_h3.innerHTML = heading;

         // Set the word maxlength and value
         var elem_word = document.getElementById('we-word');
         elem_word.maxlength = parms.length;
         elem_word.value = parms.text;

         // Set the clue
         var elem_clue = document.getElementById('we-clue');
         elem_clue.value = parms.clue;

         // Clear any previous select for "suggest" and turn it off
         var elem_select = document.getElementById('we-select');
         elem_select.innerHTML = "";
         hideElement('we-select');
         hideElement('we-match');

         // Make the modal dialog visible
         showElement('we-dialog');
         elem_word.focus();
      }
   };
   url = url + "?r=" + r + "&c=" + c;
   xhttp.open("GET", url, true);
   xhttp.send();
}

/***************************************************************
 *  FUNCTION NAME:   puzzle_click
 *  DESCRIPTION:     Distinguishes between single and double clicks
 ***************************************************************/
function puzzle_click(event) {

   var TIMEOUT_MS = 300;
   CLICK_EVENT = event;

   function single_click() {
      PUZZLE_CLICK_STATE = 0;
      do_word(CLICK_EVENT, "{{ url_for('puzzle_click_across') }}");
   }

   function double_click() {
      PUZZLE_CLICK_STATE = 0;
      do_word(event, "{{ url_for('puzzle_click_down') }}");
   }

   if (PUZZLE_CLICK_STATE == 0) {
      PUZZLE_CLICK_STATE = 1;
      TIMEOUT_VAR = setTimeout(single_click, TIMEOUT_MS);
   }
   else if (PUZZLE_CLICK_STATE == 1) {
      PUZZLE_CLICK_STATE = 0;
      clearTimeout(TIMEOUT_VAR);
      double_click(CLICK_EVENT);
   }
}

/***************************************************************
 *  FUNCTION NAME:   puzzle_chooser_ajax
 *  DESCRIPTION:     Gets a list of puzzle files from the server
 *                   and forms a list of links
 ***************************************************************/
function puzzle_chooser_ajax(build_url) {
   var xhttp = new XMLHttpRequest();
   xhttp.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200) {

         // Get the JSON array of puzzle names returned by the AJAX call
         var jsonstr = this.responseText;
         var puzzle_list = JSON.parse(jsonstr);

         // Clear out the <ul> that will contain the list items
         var elem_ul = document.getElementById('puzzle-list');
         elem_ul.innerHTML = ""

         // Populate the list
         for (var i = 0; i < puzzle_list.length; i++) {

            // Get the next file name in the list
            var puzzlename = puzzle_list[i];

            // Create a <li> to contain anchors for this puzzle
            var elem_li = document.createElement("li");

            // Add each anchor to the <li>
            for (var j = 0; j < function_list.length; j++) {
                fun = function_list[j];
                elem_anchor = fun(puzzlename);
                elem_li.appendChild(elem_anchor);
            }

            // and append the list item to the <ul>
            elem_ul.appendChild(elem_li);
         }
      }
   };
   var url = '{{ url_for("puzzles")}}';
   xhttp.open("GET", url, true);
   xhttp.send();
}

/***************************************************************
 *  FUNCTION NAME:   do_puzzle_statistics
 *  DESCRIPTION:     Assembles puzzle statistics and shows results
 ***************************************************************/
function do_puzzle_stats() {
   var objType = "puzzle"
   var url = "{{ url_for('puzzle_statistics') }}";
   do_statistics(objType, url);
}

/***************************************************************
 *  FUNCTION NAME:   do_puzzle_title
 *  DESCRIPTION:     Lets user set the puzzle title
 ***************************************************************/
function do_puzzle_title() {
   showElement('pt-dialog')
}

/***************************************************************
 *  FUNCTION NAME:   do_puzzle_publish_nytimes
 *  DESCRIPTION:     Gets a list of puzzle files from the server
 *                   and prompts the user to choose one, building
 *                   from it a list of links to the publish
 *                   function for that puzzle
 ***************************************************************/
function do_puzzle_publish_nytimes() {
    function_list = [];

    function preview_anchor(puzzlename) {
        var elem_a = document.createElement("a");
        var elem_i = document.createElement("i");
        elem_i.setAttribute("class", "material-icons");
        elem_i.appendChild(document.createTextNode("preview"));
        elem_a.appendChild(elem_i);
        var onclick = "do_puzzle_preview('" + puzzlename + "')";
        elem_a.setAttribute("onclick", onclick);
        elem_a.style.textDecoration = "none"; // No underline
        return elem_a;
    };
    function_list.push(preview_anchor);

    function publish_anchor(puzzlename) {
        var elem_a = document.createElement("a");
        elem_a.href = "{{ url_for('puzzle_publish_nytimes') }}" + "?puzzlename=" + puzzlename;
        elem_a.style.textDecoration = "none"; // No underline
        elem_a.style.verticalAlign = "top"; // Align with icon
        elem_a.appendChild(document.createTextNode(puzzlename));
        return elem_a;
    };
    function_list.push(publish_anchor);

    puzzle_chooser_ajax(function_list);
    showElement('pc-dialog');
}

/***************************************************************
 *  FUNCTION NAME:   do_puzzle_publish_acrosslite
 *  DESCRIPTION:     Gets a list of puzzle files from the server
 *                   and prompts the user to choose one, building
 *                   from it a list of links to the publish
 *                   function for that puzzle
 ***************************************************************/
function do_puzzle_publish_acrosslite() {
    function_list = [];

    function preview_anchor(puzzlename) {
        var elem_a = document.createElement("a");
        var elem_i = document.createElement("i");
        elem_i.setAttribute("class", "material-icons");
        elem_i.appendChild(document.createTextNode("preview"));
        elem_a.appendChild(elem_i);
        var onclick = "do_puzzle_preview('" + puzzlename + "')";
        elem_a.setAttribute("onclick", onclick);
        elem_a.style.textDecoration = "none"; // No underline
        return elem_a;
    };
    function_list.push(preview_anchor);

    function publish_anchor(puzzlename) {
        var elem_a = document.createElement("a");
        elem_a.href = "{{ url_for('puzzle_publish_acrosslite') }}" + "?puzzlename=" + puzzlename;
        elem_a.style.textDecoration = "none"; // No underline
        elem_a.style.verticalAlign = "top"; // Align with icon
        elem_a.appendChild(document.createTextNode(puzzlename));
        return elem_a;
    };
    function_list.push(publish_anchor);

    puzzle_chooser_ajax(function_list);
    showElement('pc-dialog');
}

//  ============================================================
//  Edit word functions
//  ============================================================

/***************************************************************
 *  NAME: do_suggest_word()
 *  DESCRIPTION: Suggest a word that matches the pattern
 ***************************************************************/
function do_suggest_word() {

   // Get the pattern
   var elem_word = document.getElementById('we-word');
   var pattern = elem_word.value;

   // Invoke an AJAX call to get the matching words
   var xhttp = new XMLHttpRequest();
   xhttp.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200) {
         var jsonstr = this.responseText;
         var words = JSON.parse(jsonstr);

         var elem_select = document.getElementById('we-select');
         elem_select.innerHTML = "";

         var elem_match = document.getElementById('we-match');
         elem_match.innerHTML = "";

         if (words.length == 0) {
            elem_match.innerHTML = "No matches found";
            showElement('we-match');
            hideElement('we-select');
         }
         else {
            elem_match.innerHTML = words.length + " matches found:";
            for (var i = 0; i < words.length; i++) {
               var word = words[i];
               var elem_option = document.createElement("option")
               elem_option.value = word;
               elem_option.appendChild(document.createTextNode(word))
               elem_select.appendChild(elem_option);
            }
            showElement('we-match');
            showElement('we-select')
         }
      }
   }
   var url = '{{ url_for("wordlists")}}';
   url += "?pattern=" + pattern
   xhttp.open("GET", url, true);
   xhttp.send();
}

/***************************************************************
 *  NAME: do_select_changed()
 *  DESCRIPTION: Updates the text in the input field to match
 *      the entry selected in the dropdown box
 ***************************************************************/
function do_select_changed() {
    elem_select = document.getElementById('we-select')
    value = elem_select.value
    elem_word = document.getElementById('we-word')
    elem_word.value = value
}

/***************************************************************
 *  NAME: do_word_validate()
 *  DESCRIPTION: Ensures that there are no regexes in the
 *      input word. Raises an alert if so.
 ***************************************************************/
function do_word_validate() {
    var text = document.getElementById('we-word').value;
    for (var i = 0; i < text.length; i++) {
        var ch = text.charAt(i).toUpperCase();
        var p = " ABCDEFGHIJKLMNOPQRSTUVWXYZ.".indexOf(ch);
        if (p < 0) {
            alert(text + " contains non-alphabetic characters");
            return false;
        }
    }
    return true;
}

/***************************************************************
 *  NAME: do_word_reset()
 *  DESCRIPTION: Clears the word in the puzzle except for the
 *      letters that are part of a completed crossing word
 ***************************************************************/
function do_word_reset() {

    // Invoke an AJAX call to get the cleared text
    // for the input word
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
       if (this.readyState == 4 && this.status == 200) {
          var jsonstr = this.responseText;
          var new_text = JSON.parse(jsonstr);

          // Update the input field
          var elem_word = document.getElementById('we-word');
          elem_word.value = new_text
       }
   }
   var url = '{{ url_for("word_reset")}}';
   xhttp.open("GET", url, true);
   xhttp.send();
}

/***************************************************************
 *  FUNCTION NAME:   do_puzzle_undo
 *  DESCRIPTION:     Undoes the last change
 ***************************************************************/
function do_puzzle_undo() {
    window.location.href = "{{ url_for('puzzle_undo') }}";
}

/***************************************************************
 *  FUNCTION NAME:   do_puzzle_redo
 *  DESCRIPTION:     Redoes the last change
 ***************************************************************/
function do_puzzle_redo() {
    window.location.href = "{{ url_for('puzzle_redo') }}";
}
