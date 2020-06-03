function do_close_puzzle() {
    alert("DEBUG: About to close window");
    window.location.href = "{{ url_for('main_screen') }}"
}
