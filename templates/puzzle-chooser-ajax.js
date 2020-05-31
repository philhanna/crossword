var xhttp = new XMLHttpRequest();
xhttp.onreadystatechange = function() {
 if (this.readyState == 4 && this.status == 200) {
    jsonstr = this.responseText
    puzzle_list = JSON.parse(jsonstr);
    links = "";
    for (i = 0; i < puzzle_list.length; i++) {
        filename = puzzle_list[i]
        href = build_url(filename)
        quoted_href = "'" + href + "'"
        anchor = "<a href=" + quoted_href + ">" + filename + "</a>"
        listitem = "<li>" + anchor + "</li>"
        links += listitem + "\n"
    }
    document.getElementById("puzzle-list").innerHTML = links
 }
};
var url = '{{ url_for("puzzles")}}';
xhttp.open("GET", url, true);
xhttp.send()
