var xhttp = new XMLHttpRequest();
xhttp.onreadystatechange = function() {
   if (this.readyState == 4 && this.status == 200) {

      // Get the JSON array of grid names returned by the AJAX call
      jsonstr = this.responseText;
      grid_list = JSON.parse(jsonstr);

      // Clear out the <ul> that will contain the list items
      elem_list = document.getElementById('grid-list');
      elem_list.innerHTML = ""

      // Populate the list
      for (i = 0; i < grid_list.length; i++) {

         // Get the next file name in the list
         gridname = grid_list[i];

         // Create an <a> element for the URL
         // with the full URL that will be used as the link
         elem_anchor = document.createElement("a");
         elem_anchor.href = build_url(gridname);
         elem_anchor.style.textDecoration = "none"; // No underline
         elem_anchor.appendChild(document.createTextNode(gridname));

         // Create a <li> to contain the <a>
         elem_list_item = document.createElement("li");
         elem_list_item.appendChild(elem_anchor);

         // and append the list item to the <ul>
         elem_list.appendChild(elem_list_item);
      }
   }
};
var url = '{{ url_for("grids")}}';
xhttp.open("GET", url, true);
xhttp.send()
