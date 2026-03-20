        function cancel_dialog() {
            window.location.href = "{{ url_for('uipuzzle.puzzle_screen') }}";
        }

        function do_select_changed() {
            const elem_select = document.getElementById("we-select");
            const elem_word = document.getElementById("we-word");
            elem_word.value = elem_select.value;
        }

        function open_word_edit_tab(tabname) {
            const elem_tabs = document.getElementsByClassName("we-tab");
            for (let i = 0; i < elem_tabs.length; i++) {
                elem_tabs[i].style.display = "none";
            }
            const elem_tab = document.getElementById(tabname);
            elem_tab.style.display = "block";
        }

        function do_word_suggest() {
            const elem_match = document.getElementById("we-match");
            const state = elem_match.style.display;
            if (state == "block") {
                hideElement("we-match");
                hideElement("we-select");
                return;
            }

            // Get the pattern
            const elem_word = document.getElementById("we-word");
            const pattern = elem_word.value;

            // Invoke an AJAX call to get the matching words
            const xhttp = new XMLHttpRequest();
            xhttp.onreadystatechange = function () {
                if (this.readyState == 4 && this.status == 200) {
                    const jsonstr = this.responseText;
                    const words = JSON.parse(jsonstr);

                    const elem_select = document.getElementById("we-select");
                    elem_select.innerHTML = "";

                    const elem_match = document.getElementById("we-match");
                    elem_match.innerHTML = "";

                    if (words.length == 0) {
                        elem_match.innerHTML = "No matches found";
                        showElement("we-match");
                        hideElement("we-select");
                    } else {
                        elem_match.innerHTML = words.length + " matches found:";
                        for (let i = 0; i < words.length; i++) {
                            const word = words[i];
                            const elem_option = document.createElement("option");
                            elem_option.value = word;
                            elem_option.appendChild(document.createTextNode(word))
                            elem_select.appendChild(elem_option);
                        }
                        showElement("we-match");
                        showElement("we-select")
                    }
                }
            }
            const url = "{{ url_for('uiwordlists.wordlists')}}" + "?pattern=" + pattern;
            xhttp.open("GET", url, true);
            xhttp.send();
        }
        function do_fastpath(text) {
            if (text != " ") {
                const elem_word = document.getElementById("we-word");
                elem_word.setAttribute("value", text);
                hideElement('we-select');
                hideElement('we-match');
                open_word_edit_tab("we-tab-suggest");
                do_word_suggest();
            }
        }
        function do_word_constraints() {
            // Invoke an AJAX call to get the cleared text
            // for the input word
            const xhttp = new XMLHttpRequest();
            xhttp.onreadystatechange = function () {
                if (this.readyState == 4 && this.status == 200) {

                    // Get the constraints data from the server
                    const jsonstr = this.responseText;
                    const constraints = JSON.parse(jsonstr);
                    // Start building the constraints UI section
                    const elem_ui = document.getElementById("we-constraints-table");
                    elem_ui.innerHTML = "";

                    // Heading shows overall pattern
                    const elem_div = document.createElement("div");
                    elem_ui.appendChild(elem_div);
                    elem_div.setAttribute("class", "w3-padding w3-center");

                    const elem_b = document.createElement("b");
                    elem_div.appendChild(elem_b);
                    elem_b.appendChild(document.createTextNode("Overall pattern:"));

                    const elem_input = document.createElement("input");
                    elem_div.appendChild(elem_input);
                    elem_input.setAttribute("class", "w3-border");
                    elem_input.setAttribute("value", constraints["pattern"]);

                    const elem_button = document.createElement("button");
                    elem_div.appendChild(elem_button);
                    elem_button.setAttribute("class", "w3-margin-left")
                    elem_button.setAttribute("type", "button");
                    elem_button.innerText = "Suggest";
                    const text = constraints["pattern"]
                    elem_button.setAttribute("onclick", `do_fastpath('${text}')`);

                    // Fill in the table

                    const elem_table = document.createElement("table");
                    elem_ui.appendChild(elem_table);
                    elem_table.setAttribute("class", "w3-table w3-small w3-bordered");
                    let elem_tr, elem_th, elem_td;

                    elem_tr = document.createElement("tr");
                    elem_table.appendChild(elem_tr);

                    let column_names = ["Pos", "Letter", "Location", "Text",
                                        "Index", "Regexp", "Choices"];
                    for (let i = 0; i < column_names.length; i++) {
                        const name = column_names[i];
                        elem_th = document.createElement("th");
                        elem_tr.appendChild(elem_th);
                        elem_th.appendChild(document.createTextNode(name));
                    }
                    const crossers = constraints["crossers"];
                    for (let i = 0; i < crossers.length; i++) {
                        const crosser = crossers[i];
                        const attrnames = ["pos", "letter", "location", "text",
                                            "index", "regexp", "choices"];
                        elem_tr = document.createElement("tr");
                        elem_table.appendChild(elem_tr);
                        for (let j = 0; j < attrnames.length; j++) {
                            elem_td = document.createElement("td");
                            elem_tr.appendChild(elem_td);
                            const attrName = attrnames[j];
                            const attrValue = crosser[attrName];
                            elem_td.appendChild(document.createTextNode(attrValue));
                        }
                    }


                    // Make the section visible
                    showElement("we-constraints-table");
                }
            }
            const url = "{{ url_for('uiword.word_constraints')}}";
            xhttp.open("GET", url, true);
            xhttp.send();
        }
        function do_word_reset() {

            // Invoke an AJAX call to get the cleared text
            // for the input word
            const xhttp = new XMLHttpRequest();
            xhttp.onreadystatechange = function () {
                if (this.readyState == 4 && this.status == 200) {
                    const jsonstr = this.responseText;
                    const new_text = JSON.parse(jsonstr);

                    // Update the input field
                    const elem_word = document.getElementById("we-word");
                    elem_word.value = new_text
                }
            }
            const url = "{{ url_for('uiword.word_reset')}}";
            xhttp.open("GET", url, true);
            xhttp.send();
        }

        function do_word_validate() {
            const text = document.getElementById("we-word").value;
            for (let i = 0; i < text.length; i++) {
                const ch = text.charAt(i).toUpperCase();
                const p = " ABCDEFGHIJKLMNOPQRSTUVWXYZ.".indexOf(ch);
                if (p < 0) {
                    alert(`${text} contains non-alphabetic characters`);
                    return false;
                }
            }
            return true;
        }


