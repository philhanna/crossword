/* Updates the puzzle's grid */
function do_replace_puzzle_grid() {

      function build_url(filename) {
         url = "{{ url_for('puzzle_replace_grid_screen') }}"
         url += "?gridname=" + filename
         return url
      };

      {% include 'grid-chooser-ajax.js' %}

  openModalDialog('gc-dialog');
}
