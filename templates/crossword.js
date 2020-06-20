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
 *  FUNCTION NAME:   do_close_grid
 *  DESCRIPTION:     Closes the grid screen
 *       1. Asks the server whether the grid has changed
 *       2. If so, opens the grid changed confirmation dialog
 *       3. Otherwise, redirects to main screen
 ***************************************************************/
function do_close_grid() {
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
 *  FUNCTION NAME:   do_delete_grid
 *  DESCRIPTION:     Prompts the user for confirmation
 *                   of grid deletion
 ***************************************************************/
function do_delete_grid() {
  showElement('gd-dialog');
}

/***************************************************************
 *  FUNCTION NAME:   do_new_grid
 *  DESCRIPTION:     Prompts the user for a grid size
 ***************************************************************/
function do_new_grid() {
  showElement('ng-dialog');
}

/***************************************************************
 *  FUNCTION NAME:   do_open_grid
 *  DESCRIPTION:     Gets a list of grid files from the server
 *                   and prompts the user to choose one
 ***************************************************************/
function do_open_grid() {
   grid_chooser_ajax(
      function(filename) {
         return "{{ url_for('open_grid_screen') }}" + "?gridname=" + filename;
      }
   );
   showElement('gc-dialog');
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
function grid_chooser_ajax(build_url) {
   var xhttp = new XMLHttpRequest();
   xhttp.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200) {

         // Get the JSON array of grid names returned by the AJAX call
         var jsonstr = this.responseText;
         var grid_list = JSON.parse(jsonstr);

         // Clear out the <ul> that will contain the list items
         var elem_list = document.getElementById('grid-list');
         elem_list.innerHTML = ""

         // Populate the list
         for (var i = 0; i < grid_list.length; i++) {

            // Get the next file name in the list
            var gridname = grid_list[i];

            // Create an <a> element for the URL
            // with the full URL that will be used as the link
            var elem_anchor = document.createElement("a");
            elem_anchor.href = build_url(gridname);
            elem_anchor.style.textDecoration = "none"; // No underline
            elem_anchor.appendChild(document.createTextNode(gridname));

            // Create a <li> to contain the <a>
            var elem_list_item = document.createElement("li");
            elem_list_item.appendChild(elem_anchor);

            // and append the list item to the <ul>
            elem_list.appendChild(elem_list_item);
         }
      }
   };
   var url = '{{ url_for("grids")}}';
   xhttp.open("GET", url, true);
   xhttp.send();
}

/***************************************************************
 *  FUNCTION NAME:   do_save_grid
 *  DESCRIPTION:     Turns on the save grid modal dialog
 ***************************************************************/
function do_save_grid(gridname) {
    if (gridname == "") {
        showElement('gs-dialog');
    }
    else {
        window.location.href = "{{ url_for('grid_save') }}";
    }
}

/***************************************************************
 *  FUNCTION NAME:   do_save_grid_as
 *  DESCRIPTION:     Turns on the save grid modal dialog
 ***************************************************************/
function do_save_grid_as() {
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
 *  FUNCTION NAME:   do_close_puzzle
 *  DESCRIPTION:     Closes the puzzle screen
 *       1. Asks the server whether the puzzle has changed
 *       2. If so, opens the puzzle changed confirmation dialog
 *       3. Otherwise, redirects to main screen
 ***************************************************************/
function do_close_puzzle() {
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
 *  FUNCTION NAME:   do_delete_puzzle
 *  DESCRIPTION:     Opens the puzzle delete dialog
 ***************************************************************/
function do_delete_puzzle() {
   showElement('pd-dialog');
}

/***************************************************************
 *  FUNCTION NAME:   do_new_puzzle
 *  DESCRIPTION:     Gets a list of grid files from the server
 *                   and prompts the user to choose one
 ***************************************************************/
function do_new_puzzle() {
   grid_chooser_ajax(
      function(filename) {
         return "{{ url_for('new_puzzle_screen') }}" + "?gridname=" + filename;
      }
   );
   showElement('gc-dialog');
}

/***************************************************************
 *  FUNCTION NAME:   do_open_puzzle
 *  DESCRIPTION:     Gets a list of puzzle files from the server
 *                   and prompts the user to choose one
 ***************************************************************/
function do_open_puzzle() {
   puzzle_chooser_ajax(
      function(filename) {
         return "{{ url_for('open_puzzle_screen') }}" + "?puzzlename=" + filename;
      }
   );
   showElement('pc-dialog');
}

/***************************************************************
 *  FUNCTION NAME:   do_save_puzzle
 *  DESCRIPTION:     Turns on the save puzzle modal dialog
 ***************************************************************/
function do_save_puzzle(puzzlename) {
    if (puzzlename == "") {
        showElement('ps-dialog');
    }
    else {
        window.location.href = "{{ url_for('puzzle_save') }}";
    }
}

/***************************************************************
 *  FUNCTION NAME:   do_save_puzzle_as
 *  DESCRIPTION:     Turns on the save puzzle as modal dialog
 ***************************************************************/
function do_save_puzzle_as() {
   showElement('psa-dialog');
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
         var elem_h3 = document.getElementById('ew-heading');
         var heading = parms.seq + " " + parms.direction + " (" + parms.length + " letters)";
         elem_h3.innerHTML = heading;

         // Set the word maxlength and value
         var elem_word = document.getElementById('ew-word');
         elem_word.maxlength = parms.length;
         elem_word.value = parms.text;

         // Set the clue
         var elem_clue = document.getElementById('ew-clue');
         elem_clue.value = parms.clue;

         // Clear any previous select for "suggest" and turn it off
         var elem_select = document.getElementById('ew-select');
         elem_select.innerHTML = "";
         hideElement('ew-select');
         hideElement('ew-match');

         // Make the modal dialog visible
         showElement('ew-dialog');
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

         // Clear the <ul> that will contain the list items
         var elem_list = document.getElementById("puzzle-list");
         elem_list.innerHTML = ""

         // Populate the list
         for (var i = 0; i < puzzle_list.length; i++) {

            // Get the next puzzle name in the list
            var puzzlename = puzzle_list[i];

            // Create an <a> element for the URL
            // with the full URL that will be used as the link
            var elem_anchor = document.createElement("a");
            elem_anchor.href = build_url(puzzlename);
            elem_anchor.style.textDecoration = "none"; // No underline
            elem_anchor.appendChild(document.createTextNode(puzzlename));

            // Create a <li> to contain the <a>
            var elem_list_item = document.createElement("li");
            elem_list_item.appendChild(elem_anchor);

            // and append the list item to the <ul>
            elem_list.appendChild(elem_list_item);
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
 *  FUNCTION NAME:   do_publish_nytimes
 *  DESCRIPTION:     Gets a list of puzzle files from the server
 *                   and prompts the user to choose one, building
 *                   from it a list of links to the publish
 *                   function for that puzzle
 ***************************************************************/
function do_publish_nytimes() {
   puzzle_chooser_ajax(
      function(filename) {
         return "{{ url_for('publish_nytimes_screen') }}" + "?puzzlename=" + filename;
      }
   );
   showElement('pc-dialog');
}

/***************************************************************
 *  FUNCTION NAME:   do_publish_acrosslite
 *  DESCRIPTION:     Gets a list of puzzle files from the server
 *                   and prompts the user to choose one, building
 *                   from it a list of links to the publish
 *                   function for that puzzle
 ***************************************************************/
function do_publish_acrosslite() {
   puzzle_chooser_ajax(
      function(filename) {
         return "{{ url_for('publish_acrosslite_screen') }}" + "?puzzlename=" + filename;
      }
   );
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
   var elem_word = document.getElementById('ew-word');
   var pattern = elem_word.value;

   // Invoke an AJAX call to get the matching words
   var xhttp = new XMLHttpRequest();
   xhttp.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200) {
         var jsonstr = this.responseText;
         var words = JSON.parse(jsonstr);

         var elem_select = document.getElementById('ew-select');
         elem_select.innerHTML = "";

         var elem_match = document.getElementById('ew-match');
         elem_match.innerHTML = "";

         if (words.length == 0) {
            elem_match.innerHTML = "No matches found";
            showElement('ew-match');
            hideElement('ew-select');
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
            showElement('ew-match');
            showElement('ew-select')
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
    elem_select = document.getElementById('ew-select')
    value = elem_select.value
    elem_word = document.getElementById('ew-word')
    elem_word.value = value
}

/***************************************************************
 *  NAME: do_validate_word()
 *  DESCRIPTION: Ensures that there are no regexes in the
 *      input word. Raises an alert if so.
 ***************************************************************/
function do_validate_word() {
    var text = document.getElementById('ew-word').value;
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
 *  NAME: do_reset_word()
 *  DESCRIPTION: Clears the word in the puzzle except for the
 *      letters that are part of a completed crossing word
 ***************************************************************/
function do_reset_word() {

    // Invoke an AJAX call to get the cleared text
    // for the input word
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
       if (this.readyState == 4 && this.status == 200) {
          var jsonstr = this.responseText;
          var new_text = JSON.parse(jsonstr);

          // Update the input field
          var elem_word = document.getElementById('ew-word');
          elem_word.value = new_text
       }
   }
   var url = '{{ url_for("reset_word")}}';
   xhttp.open("GET", url, true);
   xhttp.send();
}

/***************************************************************
 *  FUNCTION NAME:   do_undo
 *  DESCRIPTION:     Undoes the last change
 ***************************************************************/
function do_undo() {
    window.location.href = "{{ url_for('undo') }}";
}

/***************************************************************
 *  FUNCTION NAME:   do_redo
 *  DESCRIPTION:     Redoes the last change
 ***************************************************************/
function do_redo() {
    window.location.href = "{{ url_for('redo') }}";
}
