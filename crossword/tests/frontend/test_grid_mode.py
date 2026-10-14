"""New puzzle, Grid mode editing, undo/redo, and switching modes."""

from playwright.sync_api import expect

from crossword.tests.frontend.helpers import (
    answer_input_box, black_cell_count, cell_point, confirm_message_box,
    expect_dashboard, menu, open_from_dashboard,
)


def test_new_puzzle_grid_mode_round_trip(app_page):
    page = app_page

    menu(page, "Puzzle", "#menu-puzzle-new")
    answer_input_box(page, "5", "")
    expect(page.locator(".mode-badge")).to_have_text("Grid Mode")
    expect(page.locator(".puzzle-info-name")).to_have_text("(No name)")
    expect(page.locator(".sidebar-tab-active")).to_have_text("Grid")
    assert black_cell_count(page) == 0

    # A click blackens the cell and its rotational partner
    page.mouse.click(*cell_point(page, 0, 0))
    expect(page.locator('#puzzle-svg rect[width="32"][fill="#1a1a1a"]')).to_have_count(2)

    page.locator("#puzzle-undo-btn").click()
    expect(page.locator('#puzzle-svg rect[width="32"][fill="#1a1a1a"]')).to_have_count(0)
    page.locator("#puzzle-redo-btn").click()
    expect(page.locator('#puzzle-svg rect[width="32"][fill="#1a1a1a"]')).to_have_count(2)

    page.locator(".ab-mode-btn", has_text="Puzzle Mode").click()
    expect(page.locator(".mode-badge")).to_have_text("Puzzle Mode")
    expect(page.locator("#ml-text")).to_contain_text("Back in Puzzle mode")
    expect(page.locator(".sidebar-tab-active")).to_have_text("Clues")
    assert black_cell_count(page) == 2

    # Back to Grid mode, which asks first
    page.locator(".ab-mode-btn", has_text="Grid Mode").click()
    confirm_message_box(page)
    expect(page.locator(".mode-badge")).to_have_text("Grid Mode")


def test_new_puzzle_rejects_even_size(app_page):
    page = app_page

    menu(page, "Puzzle", "#menu-puzzle-new")
    answer_input_box(page, "4", "")
    expect(page.locator("#mb-prompt")).to_have_text("4 is not an odd number.")

    # OK on the error re-asks, keeping what was typed
    page.locator("#mb-ok").click()
    expect(page.locator("#ib")).to_be_visible()
    expect(page.locator("#ib-input-0")).to_have_value("4")
    page.locator("#ib-cancel").click()
    expect(page.locator("#ib")).to_be_hidden()
    expect_dashboard(page)


def test_rotate_and_stats_in_grid_mode(app_page, api):
    page = app_page
    api.create_puzzle("five")
    page.reload()
    open_from_dashboard(page, "five")

    page.locator(".ab-mode-btn", has_text="Grid Mode").click()
    confirm_message_box(page)
    expect(page.locator(".mode-badge")).to_have_text("Grid Mode")
    page.mouse.click(*cell_point(page, 0, 1))
    expect(page.locator('#puzzle-svg rect[width="32"][fill="#1a1a1a"]')).to_have_count(2)

    page.locator(".ab-btn", has_text="Rotate").click()
    expect(page.locator('#puzzle-svg rect[x="0"][y="96"][fill="#1a1a1a"]')).to_have_count(1)

    page.locator(".ab-btn", has_text="Stats").click()
    expect(page.locator(".sidebar-tab-active")).to_have_text("Stats")
    expect(page.locator(".stat-cards")).to_contain_text("Black cells")
    page.locator(".sidebar-tab", has_text="Grid").click()
    expect(page.locator(".grid-info-card")).to_contain_text("5 × 5")


def test_menu_items_follow_the_view(app_page, api):
    page = app_page
    api.create_puzzle("five")
    page.reload()
    page.locator(".dash").wait_for()

    def disabled(item_id):
        return page.locator(f"#{item_id}").get_attribute("aria-disabled") == "true"

    assert not disabled("menu-puzzle-new")
    assert disabled("menu-puzzle-save")
    assert disabled("menu-puzzle-close")

    open_from_dashboard(page, "five")
    assert disabled("menu-puzzle-new")
    assert not disabled("menu-puzzle-save")
    assert not disabled("menu-puzzle-close")
    assert not disabled("menu-puzzle-grid-mode")
    assert disabled("menu-puzzle-puzzle-mode")
