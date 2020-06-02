/* Gets a list of grid files from the server and prompts the user to choose one */
function do_new_puzzle() {

      function build_url(filename) {
         url = "{{ url_for('new_puzzle_screen') }}"
         url += "?gridname=" + filename
         return url
      };

      {% include 'grid-chooser-ajax.js' %}

  openModalDialog('gc-dialog');
}
