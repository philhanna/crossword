/* Suggest a word that matches the pattern */
function do_suggest_word() {
    // Get the pattern
    var elem_word = document.getElementById('edit-word-dialog-word');
    var pattern = elem_word.value;

    // Invoke an AJAX call to get the matching words
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
       if (this.readyState == 4 && this.status == 200) {
          jsonstr = this.responseText;
          words = JSON.parse(jsonstr);
          elem_select = document.getElementById('edit-word-wordlist-select')
          options = ""
          for (var i = 0; i < words.length; i++) {
            word = words[i]
            options += "<option value='" + word + "'>" + word + "</option>"
          }
          elem_select.innerHTML = options
          document.getElementById('edit-word-wordlist').style.display = 'block';
       }
   }
   var url = '{{ url_for("wordlists")}}';
   url += "?pattern=" + pattern
   xhttp.open("GET", url, true);
   xhttp.send();
}
