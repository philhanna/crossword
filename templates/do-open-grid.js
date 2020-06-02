/* Gets a list of grid files from the server and prompts the user to choose one */
function do_open_grid() {

      function build_url(filename) {
         url = "{{ url_for('open_grid_screen') }}"
         url += "?gridname=" + filename
         return url
      };

      {% include 'grid-chooser-ajax.js' %}

  openModalDialog('gc-dialog');
}
