"""Permute: swapping two locked words by drag and drop."""

from playwright.sync_api import expect

from crossword.tests.frontend.helpers import (
    cell_point, grid_letters, open_from_dashboard,
)

ROWS = ["ABCDE", "FGHIJ", "KLMNO", "PQRST", "UVWXY"]
ROW_SEQ = [1, 6, 7, 8, 9]


def open_filled(page, api, locked=(0, 1)):
    """A filled and clued 5x5 puzzle with the given rows locked, then open it"""
    api.create_puzzle("five")
    for i, (seq, row) in enumerate(zip(ROW_SEQ, ROWS)):
        api.call("PUT", f"/api/puzzles/five/words/{seq}/across",
                 {"text": row, "clue": f"clue {row}", "locked": i in locked})
    page.reload()
    open_from_dashboard(page, "five")


def drag(page, from_row, to_row, col=2):
    x1, y1 = cell_point(page, from_row, col)
    x2, y2 = cell_point(page, to_row, col)
    page.mouse.move(x1, y1)
    page.mouse.down()
    page.mouse.move(x1, (y1 + y2) / 2, steps=4)
    page.mouse.move(x2, y2, steps=4)
    page.mouse.up()


def permute_button(page):
    return page.locator("#puzzle-permute-btn")


def test_permute_is_disabled_without_a_swappable_pair(app_page, api):
    page = app_page
    open_filled(page, api, locked=(0,))
    expect(permute_button(page)).to_be_disabled()


def test_permute_button_is_left_of_clear(app_page, api):
    page = app_page
    open_filled(page, api)
    expect(permute_button(page)).to_be_enabled()
    permute_x = permute_button(page).bounding_box()["x"]
    assert permute_x < page.locator("#puzzle-clear-btn").bounding_box()["x"]


def test_button_reads_cancel_while_on_and_cancel_turns_it_off(app_page, api):
    page = app_page
    open_filled(page, api)
    expect(permute_button(page)).to_contain_text("Permute")

    permute_button(page).click()
    expect(permute_button(page)).to_contain_text("Cancel")

    permute_button(page).click()
    expect(permute_button(page)).to_contain_text("Permute")


def test_escape_turns_permute_off(app_page, api):
    page = app_page
    open_filled(page, api)
    permute_button(page).click()
    page.keyboard.press("Escape")
    expect(permute_button(page)).to_contain_text("Permute")


def test_drag_swaps_two_locked_words_and_turns_mode_off(app_page, api):
    page = app_page
    open_filled(page, api)
    permute_button(page).click()

    drag(page, 0, 1)

    expect(page.locator("#ml-text")).to_contain_text("Swapped 1-Across and 6-Across")
    assert grid_letters(page, 5)[:2] == ["FGHIJ", "ABCDE"]
    expect(permute_button(page)).to_contain_text("Permute")
    expect(permute_button(page)).to_be_enabled()
    expect(page.locator("#we-dialog")).to_have_count(0)


def test_undo_restores_the_swap(app_page, api):
    page = app_page
    open_filled(page, api)
    permute_button(page).click()
    drag(page, 0, 1)
    expect(page.locator("#ml-text")).to_contain_text("Swapped")

    page.locator("#puzzle-undo-btn").click()

    page.wait_for_function(
        "() => [...document.querySelectorAll('#puzzle-svg text[font-size=\"16\"]')]"
        ".slice(0, 5).map(t => t.textContent).join('') === 'ABCDE'")
    assert grid_letters(page, 5)[:2] == ["ABCDE", "FGHIJ"]


def test_drag_without_permute_does_nothing(app_page, api):
    page = app_page
    open_filled(page, api)
    drag(page, 0, 1)
    assert grid_letters(page, 5)[:2] == ["ABCDE", "FGHIJ"]


def test_drop_on_unlocked_word_changes_nothing_and_keeps_mode_on(app_page, api):
    page = app_page
    open_filled(page, api)
    permute_button(page).click()

    drag(page, 0, 2)

    assert grid_letters(page, 5)[:3] == ["ABCDE", "FGHIJ", "KLMNO"]
    expect(permute_button(page)).to_contain_text("Cancel")


def test_pressing_on_unlocked_word_does_not_start_a_drag(app_page, api):
    page = app_page
    open_filled(page, api)
    permute_button(page).click()

    drag(page, 2, 1)

    assert grid_letters(page, 5)[:3] == ["ABCDE", "FGHIJ", "KLMNO"]
