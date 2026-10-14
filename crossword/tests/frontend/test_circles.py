"""Circling squares in Puzzle mode with Shift+click."""

from playwright.sync_api import expect

from crossword.tests.frontend.helpers import (
    cell_point, confirm_message_box, open_from_dashboard,
)


def open_five(page, api):
    api.create_puzzle("five")
    page.reload()
    open_from_dashboard(page, "five")


def shift_click_cell(page, row, col):
    x, y = cell_point(page, row, col)
    page.keyboard.down("Shift")
    page.mouse.click(x, y)
    page.keyboard.up("Shift")


def test_shift_click_toggles_circle_without_selecting(app_page, api):
    page = app_page
    open_five(page, api)

    shift_click_cell(page, 1, 2)
    expect(page.locator("#puzzle-svg circle")).to_have_count(1)
    expect(page.locator("#we-dialog")).to_have_count(0)
    expect(page.locator(".save-status")).to_have_text("● Unsaved")

    shift_click_cell(page, 1, 2)
    expect(page.locator("#puzzle-svg circle")).to_have_count(0)


def test_undo_removes_circle(app_page, api):
    page = app_page
    open_five(page, api)

    shift_click_cell(page, 0, 0)
    expect(page.locator("#puzzle-svg circle")).to_have_count(1)

    page.locator("#puzzle-undo-btn").click()
    expect(page.locator("#puzzle-svg circle")).to_have_count(0)


def test_grid_mode_shows_circles(app_page, api):
    page = app_page
    open_five(page, api)

    shift_click_cell(page, 2, 2)
    expect(page.locator("#puzzle-svg circle")).to_have_count(1)

    page.locator(".ab-mode-btn", has_text="Grid Mode").click()
    confirm_message_box(page)
    expect(page.locator(".mode-badge")).to_have_text("Grid Mode")
    expect(page.locator("#puzzle-svg circle")).to_have_count(1)
