/* Functions that are called from edit-word.html */

//  ============================================================
//  NAME: do_suggest_word()
//  DESCRIPTION: Suggest a word that matches the pattern
//  ============================================================
function do_suggest_word() {

    // Get the pattern

    var elem_word = document.getElementById('ew-word');
    var pattern = elem_word.value;

    // Invoke an AJAX call to get the matching words
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
       if (this.readyState == 4 && this.status == 200) {
          jsonstr = this.responseText;
          words = JSON.parse(jsonstr);
          elem_select = document.getElementById('ew-select');
          elem_select.innerHTML = "";
          for (var i = 0; i < words.length; i++) {
            word = words[i];
            elem_option = document.createElement("option")
            elem_option.value = word
            elem_option.appendChild(document.createTextNode(word))
            elem_select.appendChild(elem_option)
          }
          openModalDialog('ew-wordlist');
          openModalDialog('ew-select')
       }
   }
   var url = '{{ url_for("wordlists")}}';
   url += "?pattern=" + pattern
   xhttp.open("GET", url, true);
   xhttp.send();
}

//  ============================================================
//  NAME: do_select_changed()
//  DESCRIPTION: Updates the text in the input field to match
//      the entry selected in the dropdown box
//  ============================================================
function do_select_changed() {
    elem_select = document.getElementById('ew-select')
    value = elem_select.value
    elem_word = document.getElementById('ew-word')
    elem_word.value = value
}

//  ============================================================
//  NAME: do_validate_word()
//  DESCRIPTION: Ensures that there are no regexes in the
//      input word. Raises an alert if so.
//  ============================================================
function do_validate_word() {
    var text = document.getElementById('ew-word').value;
    for (var i = 0; i < text.length; i++) {
        var ch = text.charAt(i).toUpperCase();
        var p = "ABCDEFGHIJKLMNOPQRSTUVWXYZ.".indexOf(ch);
        if (p < 0) {
            alert(text + " contains non-alphabetic characters");
            return false;
        }
    }
    return true;
}

//  ============================================================
//  NAME: do_reset_word()
//  DESCRIPTION: Clears the word in the puzzle except for the
//      letters that are part of a completed crossing word
//  ============================================================
function do_reset_word() {

    // Invoke an AJAX call to get the cleared text
    // for the input word
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
       if (this.readyState == 4 && this.status == 200) {
          jsonstr = this.responseText;
          new_text = JSON.parse(jsonstr);
          // Update the input field
          elem_word = document.getElementById('ew-word');
          elem_word.value = new_text
       }
   }
   var url = '{{ url_for("reset_word")}}';
   xhttp.open("GET", url, true);
   xhttp.send();
}
