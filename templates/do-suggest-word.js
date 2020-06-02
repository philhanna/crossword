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
          elem_select = document.getElementById('edit-word-wordlist-select');
          elem_select.innerHTML = "";
          for (var i = 0; i < words.length; i++) {
            word = words[i];
            elem_option = document.createElement("option")
            elem_option.value = word
            elem_option.appendChild(document.createTextNode(word))
            elem_select.appendChild(elem_option)
          }
          document.getElementById('edit-word-wordlist').style.display = 'block';
       }
   }
   var url = '{{ url_for("wordlists")}}';
   url += "?pattern=" + pattern
   xhttp.open("GET", url, true);
   xhttp.send();
}
