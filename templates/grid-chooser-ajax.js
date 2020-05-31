var xhttp = new XMLHttpRequest();
xhttp.onreadystatechange = function() {
 if (this.readyState == 4 && this.status == 200) {
    jsonstr = this.responseText
    grid_list = JSON.parse(jsonstr);
    links = "";
    for (i = 0; i < grid_list.length; i++) {
        filename = grid_list[i]
        href = build_url(filename)
        quoted_href = "'" + href + "'"
        anchor = "<a href=" + quoted_href + ">" + filename + "</a>"
        listitem = "<li>" + anchor + "</li>"
        links += listitem + "\n"
    }
    document.getElementById("grid-list").innerHTML = links
 }
};
var url = '{{ url_for("grids")}}';
xhttp.open("GET", url, true);
xhttp.send()
