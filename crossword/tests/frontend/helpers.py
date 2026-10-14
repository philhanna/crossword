"""
Small page actions shared by the frontend tests.

They do what a user does: hover a menu and click an item, click a grid cell,
answer a dialog. Keeping them here means a change to the page's structure is
fixed in one place rather than in every test.
"""

from playwright.sync_api import expect

BOXSIZE = 32

# The single-click handler waits this long to rule out a double click.
CLICK_DELAY_MS = 280


def menu(page, top_label, item_selector):
    """Open a top-bar dropdown by hovering it, then click one of its items."""
    page.locator(".app-nav-btn", has_text=top_label).hover()
    page.locator(item_selector).click()


def cell_point(page, row, col):
    """Page coordinates of the middle of a grid cell (rows and columns from 0)."""
    box = page.locator("#puzzle-svg").bounding_box()
    return (box["x"] + col * BOXSIZE + BOXSIZE / 2,
            box["y"] + row * BOXSIZE + BOXSIZE / 2)


def click_cell(page, row, col):
    """Single-click a grid cell and wait out the double-click delay."""
    x, y = cell_point(page, row, col)
    page.mouse.click(x, y)
    page.wait_for_timeout(CLICK_DELAY_MS + 120)


def double_click_cell(page, row, col):
    x, y = cell_point(page, row, col)
    page.mouse.dblclick(x, y)
    page.wait_for_timeout(150)


def grid_letters(page, size):
    """The letters showing in the grid, one string per row, '.' for empty."""
    cells = page.evaluate("""() => {
        const out = {};
        document.querySelectorAll('#puzzle-svg text[font-size="16"]').forEach(t => {
            out[t.getAttribute('x') + ',' + t.getAttribute('y')] = t.textContent;
        });
        return out;
    }""")
    rows = []
    for r in range(size):
        row = ""
        for c in range(size):
            key = f"{c * BOXSIZE + BOXSIZE // 2},{r * BOXSIZE + BOXSIZE / 2 + 7.5}"
            row += cells.get(key, ".")
        rows.append(row)
    return rows


def black_cell_count(page):
    return page.locator('#puzzle-svg rect[width="32"][fill="#1a1a1a"]').count()


def open_from_dashboard(page, name):
    """Click a puzzle's name in the dashboard table and wait for the editor."""
    page.locator(f".dash-table [data-dash-preview='{name}']").first.click()
    page.locator("#puzzle-svg").wait_for()


def answer_input_box(page, *values):
    """Fill the input dialog's fields in order and press OK."""
    dialog = page.locator("#ib")
    expect(dialog).to_be_visible()
    inputs = dialog.locator("input[type=text]")
    for i, value in enumerate(values):
        inputs.nth(i).fill(value)
    page.locator("#ib-ok").click()
    expect(dialog).to_be_hidden()


def confirm_message_box(page):
    expect(page.locator("#mb")).to_be_visible()
    page.locator("#mb-ok").click()
    expect(page.locator("#mb")).to_be_hidden()


def expect_message(page, text):
    expect(page.locator("#ml-text")).to_contain_text(text)


def expect_editor_name(page, name):
    expect(page.locator(".puzzle-info-name")).to_have_text(name)


def expect_dashboard(page):
    expect(page.locator(".dash")).to_be_visible()
    expect(page.locator("#action-bar")).to_be_hidden()
