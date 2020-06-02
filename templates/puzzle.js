function getRC(event) {
  var x = event.offsetX;
  var y = event.offsetY;
  var boxsize = {{ boxsize }}
  var r = Math.floor(1 + y/boxsize);
  var c = Math.floor(1 + x/boxsize);
  return [r, c]
}

function do_word(event, url) {
  [r, c] = getRC(event)

  var xhttp = new XMLHttpRequest();
  xhttp.onreadystatechange = function() {
     if (this.readyState == 4 && this.status == 200) {
        parmstr = this.responseText;
        parms = JSON.parse(this.responseText);

        // Set the <h3>17 Across</h3> text
        elem_h3 = document.getElementById('ew-heading');
        heading = parms.seq + " " + parms.direction + " (" + parms.length + " letters)"
        elem_h3.innerHTML = heading;

        // Set the length in the tooltip
        elem_length = document.getElementById('ew-length');
        elem_length.innerHTML=parms.length;

        // Set the word maxlength and value
        elem_word = document.getElementById('ew-word');
        elem_word.maxlength = parms.length;
        elem_word.value = parms.text;

        // Set the clue
        elem_clue = document.getElementById('ew-clue');
        elem_clue.value = parms.clue;

        // Make the modal dialog visible
        document.getElementById('ew-dialog').style.display='block';
        elem_word.focus()
     }
  };
  url += "?r=" + r
  url += "&c=" + c
  xhttp.open("GET", url, true);
  xhttp.send()
}

/*  The purpose of this function is to distinguish between single and double clicks */
var puzzle_click_state = 0;
var TIMEOUT_VAR;
var CLICK_EVENT;

function puzzle_click(event) {

  var TIMEOUT_MS = 300;
  CLICK_EVENT = event;

  function single_click() {
    puzzle_click_state = 0;
    do_word(CLICK_EVENT, "{{ url_for('puzzle_click_across') }}");
  }

  function double_click() {
    puzzle_click_state = 0;
    do_word(event, "{{ url_for('puzzle_click_down') }}");
  }

  if (puzzle_click_state == 0) {
      puzzle_click_state = 1;
      TIMEOUT_VAR = setTimeout(single_click, TIMEOUT_MS);
  }
  else if (puzzle_click_state == 1) {
      puzzle_click_state = 0;
      clearTimeout(TIMEOUT_VAR);
      double_click(CLICK_EVENT);
  }
}
