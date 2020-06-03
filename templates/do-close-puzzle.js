function do_close_puzzle() {
   var xhttp = new XMLHttpRequest();

   xhttp.onreadystatechange = function() {
      if (this.readyState == 4 && this.status == 200) {

         // Get the server's answer about whether the puzzle has changed
         jsonstr = this.responseText;
         obj = JSON.parse(jsonstr);
         changed = obj.changed;

         // If it has changed, open the puzzle changed dialog
         if (changed) {
            openModalDialog('px-dialog');
         }
         else {
            window.location.href = "{{ url_for('main_screen') }}"
         }
      }
   };

   // Ask the server if the puzzle has changed
   var url = '{{ url_for("puzzle_changed")}}';
   xhttp.open("GET", url, true);
   xhttp.send()
}
