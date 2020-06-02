/* Gets a list of puzzle files from the server and prompts the user to choose one */
function do_publish_nytimes() {

      function build_url(filename) {
         url = "{{ url_for('publish_nytimes_screen') }}"
         url += "?puzzlename=" + filename
         return url
      };

      {% include 'puzzle-chooser-ajax.js' %}

  openModalDialog('pc-dialog');
}
