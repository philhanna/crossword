/* Gets a list of puzzle files from the server and prompts the user to choose one */
function do_open_puzzle() {

      function build_url(filename) {
         url = "{{ url_for('open_puzzle_screen') }}"
         url += "?puzzlename=" + filename
         return url
      };

      {% include 'puzzle-chooser-ajax.js' %}

  document.getElementById('puzzle-chooser-dialog').style.display='block';
}
