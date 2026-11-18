"""Autofill: filling every blank from the word list, and undoing it."""

from playwright.sync_api import expect

from crossword.tests.frontend.helpers import grid_letters, open_from_dashboard


def open_empty(page, api):
    api.create_puzzle("five")
    page.reload()
    open_from_dashboard(page, "five")


def test_autofill_fills_the_grid_and_undo_empties_it(app_page, api):
    page = app_page
    open_empty(page, api)
    assert set("".join(grid_letters(page, 5))) == {"."}

    page.locator("#puzzle-autofill-btn").click()
    expect(page.locator("#ml-text")).to_contain_text("Autofill complete")
    assert "." not in "".join(grid_letters(page, 5))

    page.locator("#puzzle-undo-btn").click()
    expect(page.locator("#ml-text")).not_to_contain_text("Autofill complete")
    assert set("".join(grid_letters(page, 5))) == {"."}
