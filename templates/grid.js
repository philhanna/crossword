function grid_click(event) {
  var x = event.offsetX;
  var y = event.offsetY;
  var boxsize = {{ boxsize }}
  var r = Math.floor(1 + y/boxsize);
  var c = Math.floor(1 + x/boxsize);

  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
     if (this.readyState == 4 && this.status == 200) {
        document.getElementById("grid-svg").innerHTML = this.responseText;
     }
  };
  var url = '{{ url_for("grid_click")}}';
  url += "?r=" + r
  url += "&c=" + c
  xhttp.open("GET", url, true);
  xhttp.send()
}
