"""Typing in the grid, the word editor panel, suggestions and clues."""

from playwright.sync_api import expect

from crossword.tests.frontend.helpers import (
    click_cell, double_click_cell, grid_letters, open_from_dashboard,
)


def open_five(page, api):
    api.create_puzzle("five")
    page.reload()
    open_from_dashboard(page, "five")


def test_single_click_opens_word_editor_and_typing_fills_grid(app_page, api):
    page = app_page
    open_five(page, api)

    click_cell(page, 0, 0)
    expect(page.locator(".we-header-title")).to_have_text("1 Across")
    page.keyboard.type("abcde")
    expect(page.locator("#we-text")).to_have_value("ABCDE")
    assert grid_letters(page, 5)[0] == "ABCDE"

    page.locator(".we-action-row .btn-primary").click()
    expect(page.locator("#we-dialog")).to_have_count(0)
    expect(page.locator(".clue-answer").first).to_have_text("ABCDE")
    expect(page.locator(".save-status")).to_have_text("● Unsaved")


def test_escape_cancels_word_editor(app_page, api):
    page = app_page
    open_five(page, api)

    click_cell(page, 0, 0)
    page.keyboard.type("xyz")
    page.keyboard.press("Escape")
    expect(page.locator("#we-dialog")).to_have_count(0)
    assert grid_letters(page, 5)[0] == "....."


def test_typing_after_word_editor_closes_is_handled_once(app_page, api):
    page = app_page
    open_five(page, api)

    # Open the word editor, apply, and then type straight into the grid:
    # each key must land exactly once.
    click_cell(page, 0, 0)
    page.locator(".we-action-row .btn-primary").click()
    expect(page.locator("#we-dialog")).to_have_count(0)

    page.keyboard.type("q")
    assert grid_letters(page, 5)[0] == "Q...."
    page.keyboard.type("r")
    assert grid_letters(page, 5)[0] == "QR..."

    # The cursor sits on an empty cell, so Backspace steps back and clears
    page.keyboard.press("Backspace")
    assert grid_letters(page, 5)[0] == "Q...."
    page.keyboard.press("Backspace")
    assert grid_letters(page, 5)[0] == "....."


def test_tab_moves_to_next_word_and_commits(app_page, api):
    page = app_page
    open_five(page, api)

    click_cell(page, 0, 0)
    page.locator(".we-action-row .btn-primary").click()
    page.keyboard.type("hello")
    page.keyboard.press("Tab")
    expect(page.locator(".clue-answer").first).to_have_text("HELLO")
    page.keyboard.type("w")
    assert grid_letters(page, 5)[1] == "W...."


def test_click_in_grid_while_editing_applies_and_selects(app_page, api):
    page = app_page
    open_five(page, api)

    click_cell(page, 0, 0)
    page.keyboard.type("abcde")
    click_cell(page, 2, 0)
    expect(page.locator("#we-dialog")).to_have_count(0)
    expect(page.locator(".clue-answer").first).to_have_text("ABCDE")
    page.keyboard.type("z")
    assert grid_letters(page, 5)[2] == "Z...."


def test_double_click_selects_down_word(app_page, api):
    page = app_page
    open_five(page, api)

    double_click_cell(page, 0, 2)
    expect(page.locator(".we-header-title")).to_have_text("3 Down")


def test_pick_suggestion_and_clue_in_word_editor(app_page, api):
    page = app_page
    open_five(page, api)

    click_cell(page, 0, 0)
    page.locator("#we-text").fill("ABAC.")
    page.locator("#we-constrained").uncheck()
    page.locator(".we-suggestions-toolbar .ab-btn").click()
    first = page.locator("#we-suggestion-list li").first
    expect(first).to_be_visible()
    word = first.get_attribute("data-word")
    assert word.startswith("ABAC") and len(word) == 5
    first.click()
    expect(page.locator("#we-text")).to_have_value(word)

    page.locator("#we-clue").fill("Counting frame")
    page.locator(".we-action-row .btn-primary").click()
    expect(page.locator("#we-dialog")).to_have_count(0)
    row = page.locator(".clue-row").first
    expect(row.locator(".clue-answer")).to_have_text(word)
    expect(row.locator(".clue-text")).to_have_text("Counting frame")


def test_double_click_suggestion_applies_it(app_page, api):
    page = app_page
    open_five(page, api)

    click_cell(page, 0, 0)
    page.locator("#we-text").fill("ABAC.")
    page.keyboard.press("Enter")
    first = page.locator("#we-suggestion-list li").first
    expect(first).to_be_visible()
    word = first.get_attribute("data-word")
    first.dblclick()
    expect(page.locator("#we-dialog")).to_have_count(0)
    assert grid_letters(page, 5)[0] == word


def test_inline_clue_edit(app_page, api):
    page = app_page
    open_five(page, api)

    click_cell(page, 0, 0)
    page.keyboard.type("abcde")
    page.locator(".we-action-row .btn-primary").click()

    page.locator(".clue-text").first.click()
    clue_input = page.locator(".clue-inline-input")
    expect(clue_input).to_be_focused()
    clue_input.fill("First letters")
    clue_input.press("Enter")
    expect(page.locator(".clue-text").first).to_have_text("First letters")
    expect(page.locator(".clue-count")).to_have_text("1/5 clued")

    page.locator(".clue-dir-btn", has_text="Down").click()
    expect(page.locator(".clue-count")).to_have_text("0/5 clued")


def test_inline_clue_needs_a_filled_word(app_page, api):
    page = app_page
    open_five(page, api)

    page.locator(".clue-text").first.click()
    expect(page.locator("#ml-text")).to_have_text("Fill in the word before giving it a clue")


def test_lock_word_blocks_typing(app_page, api):
    page = app_page
    open_five(page, api)

    click_cell(page, 0, 0)
    page.keyboard.type("abcde")
    page.locator("#we-locked").check()
    page.locator(".we-action-row .btn-primary").click()
    expect(page.locator("#we-dialog")).to_have_count(0)

    page.keyboard.type("z")
    assert grid_letters(page, 5)[0] == "ABCDE"
    expect(page.locator(".ab-mode-btn", has_text="Grid Mode")).to_be_disabled()


def test_stats_and_fill_order_panels(app_page, api):
    page = app_page
    open_five(page, api)


    # Puzzle mode has no Stats tab button; the panel just replaces the clues
    page.locator(".ab-btn", has_text="Stats").click()
    expect(page.locator(".stat-cards")).to_be_visible()
    page.locator(".stats-subtab", has_text="Words").click()
    expect(page.locator(".stats-subtab-active")).to_have_text("Words")

    page.locator("#puzzle-fill-order-btn").click()
    expect(page.locator(".fill-intro")).to_be_visible()
    page.locator(".fill-table tbody tr").first.click()
    expect(page.locator("#we-dialog")).to_be_visible()


def test_undo_redo_in_puzzle_mode(app_page, api):
    page = app_page
    open_five(page, api)

    click_cell(page, 0, 0)
    page.keyboard.type("abcde")
    page.locator(".we-action-row .btn-primary").click()
    expect(page.locator(".clue-answer").first).to_have_text("ABCDE")

    page.locator("#puzzle-undo-btn").click()
    expect(page.locator(".clue-answer").first).to_have_text(".....")
    page.locator("#puzzle-redo-btn").click()
    expect(page.locator(".clue-answer").first).to_have_text("ABCDE")


def test_constraints_popup(app_page, api):
    page = app_page
    open_five(page, api)

    click_cell(page, 0, 0)
    page.locator("#we-constraints-btn").click()
    popup = page.locator("#constraints-popup")
    expect(popup).to_be_visible()
    expect(page.locator("#constraints-popup-title")).to_have_text("Constraints — 1 Across")
    expect(popup).to_contain_text("Overall pattern:")

    # Clicking the backdrop closes it
    page.mouse.click(5, 300)
    expect(popup).to_be_hidden()
    expect(page.locator("#we-dialog")).to_be_visible()


def test_escape_discards_clue_typed_in_word_editor(app_page, api):
    page = app_page
    open_five(page, api)

    click_cell(page, 0, 0)
    page.keyboard.type("abcde")
    page.locator(".we-action-row .btn-primary").click()
    expect(page.locator("#we-dialog")).to_have_count(0)

    click_cell(page, 0, 0)
    page.locator("#we-clue").fill("cancelled clue")
    page.locator("#we-clue").press("Escape")
    expect(page.locator("#we-dialog")).to_have_count(0)

    # Moving on commits the selected word; the cancelled clue must not go with it
    click_cell(page, 2, 0)
    page.keyboard.press("Escape")
    expect(page.locator(".clue-text").first).to_have_text("No clue")
