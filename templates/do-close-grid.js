function do_close_grid() {
   var xhttp = new XMLHttpRequest();

   xhttp.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200) {

         // Get the server's answer about whether the grid has changed
         jsonstr = this.responseText;
         obj = JSON.parse(jsonstr);
         changed = obj.changed;

         // If it has changed, open the grid changed dialog
         if (changed) {
            openModalDialog('gx-dialog');
         }
         else {
            window.location.href = "{{ url_for('main_screen') }}"
         }
      }
   };

   // Ask the server if the grid has changed
   var url = '{{ url_for("grid_changed")}}';
   xhttp.open("GET", url, true);
   xhttp.send()
}
