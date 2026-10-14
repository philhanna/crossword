"""Puzzle menu: Save, Save as, Rename, Close, Delete, Open, Edit title."""

from playwright.sync_api import expect

from crossword.tests.frontend.helpers import (
    answer_input_box, click_cell, confirm_message_box, expect_dashboard,
    expect_editor_name, expect_message, menu, open_from_dashboard,
)


def open_five_with_a_change(page, api):
    api.create_puzzle("five")
    page.reload()
    open_from_dashboard(page, "five")
    click_cell(page, 0, 0)
    page.keyboard.type("abcde")
    page.locator(".we-action-row .btn-primary").click()
    expect(page.locator(".save-status")).to_have_text("● Unsaved")


def test_save_with_comment(app_page, api):
    page = app_page
    open_five_with_a_change(page, api)

    menu(page, "Puzzle", "#menu-puzzle-save")
    expect(page.locator("#ib-label")).to_have_text("What changed?")
    answer_input_box(page, "Filled 1 Across")
    expect_message(page, "Puzzle five saved.")
    expect(page.locator(".save-status")).to_have_text("✓ Saved")

    history = api.call("GET", "/api/puzzles/five/state/history")["history"]
    assert any(h["comment"] == "Filled 1 Across" for h in history)


def test_save_with_no_changes_does_nothing(app_page, api):
    page = app_page
    api.create_puzzle("five")
    page.reload()
    open_from_dashboard(page, "five")

    page.locator(".ab-btn", has_text="Save").click()
    page.wait_for_timeout(200)
    expect(page.locator("#ib")).to_be_hidden()


def test_save_as(app_page, api):
    page = app_page
    open_five_with_a_change(page, api)

    menu(page, "Puzzle", "#menu-puzzle-save-as")
    answer_input_box(page, "six", "Copied")
    expect_message(page, 'Puzzle saved as "six".')
    assert "six" in api.puzzle_names()
    expect_editor_name(page, "five")


def test_save_as_rejects_reserved_name(app_page, api):
    page = app_page
    open_five_with_a_change(page, api)

    menu(page, "Puzzle", "#menu-puzzle-save-as")
    answer_input_box(page, "__wc__x", "c")
    expect(page.locator("#mb-title")).to_have_text("Invalid puzzle name")


def test_save_as_asks_before_overwriting(app_page, api):
    page = app_page
    api.create_puzzle("other")
    open_five_with_a_change(page, api)

    menu(page, "Puzzle", "#menu-puzzle-save-as")
    answer_input_box(page, "other", "Overwrite it")
    expect(page.locator("#mb-ok")).to_have_text("Overwrite")
    confirm_message_box(page)
    expect_message(page, 'Puzzle saved as "other".')


def test_unnamed_puzzle_save_goes_to_save_as(app_page, api):
    page = app_page
    menu(page, "Puzzle", "#menu-puzzle-new")
    answer_input_box(page, "5", "")
    expect(page.locator(".puzzle-info-name")).to_have_text("(No name)")

    page.locator(".ab-btn", has_text="Save").click()
    answer_input_box(page, "fresh", "First save")
    expect_editor_name(page, "fresh")
    assert api.puzzle_names() == ["fresh"]


def test_rename(app_page, api):
    page = app_page
    api.create_puzzle("five")
    page.reload()
    open_from_dashboard(page, "five")

    menu(page, "Puzzle", "#menu-puzzle-rename")
    expect(page.locator("#ib-input")).to_have_value("five")
    answer_input_box(page, "seven")
    expect_message(page, "Puzzle renamed to seven.")
    expect_editor_name(page, "seven")
    assert api.puzzle_names() == ["seven"]


def test_close_clean_puzzle(app_page, api):
    page = app_page
    api.create_puzzle("five")
    page.reload()
    open_from_dashboard(page, "five")

    menu(page, "Puzzle", "#menu-puzzle-close")
    expect_dashboard(page)
    assert api.call("GET", "/api/puzzles")["puzzles"] == ["five"]


def test_close_dirty_puzzle_asks_first(app_page, api):
    page = app_page
    open_five_with_a_change(page, api)

    page.locator("#puzzle-close-btn").click()
    expect(page.locator("#mb-prompt")).to_contain_text("has unsaved changes")
    confirm_message_box(page)
    expect_dashboard(page)


def test_delete_from_menu(app_page, api):
    page = app_page
    api.create_puzzle("five")
    api.create_puzzle("six")
    page.reload()
    page.locator(".dash").wait_for()

    menu(page, "Puzzle", "#menu-puzzle-delete")
    expect(page.locator("#ch")).to_be_visible()
    page.locator("#ch-list > div", has_text="six").click()
    expect(page.locator("#mb-prompt")).to_contain_text("six")
    confirm_message_box(page)
    expect_message(page, "Puzzle six deleted.")
    assert api.puzzle_names() == ["five"]


def test_delete_open_puzzle_from_action_bar(app_page, api):
    page = app_page
    api.create_puzzle("five")
    page.reload()
    open_from_dashboard(page, "five")

    page.locator("#puzzle-delete-btn").click()
    confirm_message_box(page)
    expect_dashboard(page)
    expect_message(page, "Puzzle five deleted.")
    assert api.puzzle_names() == []


def test_open_from_chooser(app_page, api):
    page = app_page
    for name in ["p1", "p2", "p3", "p4", "p5", "p6"]:
        api.create_puzzle(name)
    api.set_state("p6", "archived")
    page.reload()
    page.locator(".dash").wait_for()

    menu(page, "Puzzle", "#menu-puzzle-open")
    chooser = page.locator("#ch")
    expect(chooser).to_be_visible()
    expect(page.locator("#ch-list > div")).to_have_count(5)
    expect(page.locator("#ch-page-label")).to_have_text("1–5 of 6")
    page.locator("#ch-page-next").click()
    expect(page.locator("#ch-list > div")).to_have_count(1)

    page.locator("#ch-state-filter").select_option("archived")
    expect(page.locator("#ch-list > div")).to_have_count(1)
    expect(page.locator("#ch-list")).to_contain_text("p6")

    page.locator("#ch-state-filter").select_option("all")
    expect(page.locator("#ch-list > div")).to_have_count(5)
    page.locator("input[name=ch-sort][value=alpha]").check()
    expect(page.locator("#ch-list > div").first).to_contain_text("p1")
    page.locator("#ch-list > div", has_text="p2").click()
    expect(chooser).to_be_hidden()
    expect_editor_name(page, "p2")


def test_edit_title(app_page, api):
    page = app_page
    api.create_puzzle("five")
    page.reload()
    open_from_dashboard(page, "five")

    menu(page, "Puzzle", "#menu-puzzle-title")
    answer_input_box(page, "My Title")
    expect(page.locator(".puzzle-title-display")).to_have_text("My Title")

    # Clicking the title opens the same dialog
    page.locator(".puzzle-title-display").click()
    expect(page.locator("#ib-input")).to_have_value("My Title")
    page.locator("#ib-cancel").click()


def test_dashboard_menu_returns_from_editor(app_page, api):
    page = app_page
    api.create_puzzle("five")
    page.reload()
    open_from_dashboard(page, "five")

    page.locator("#menu-dashboard").click()
    expect_dashboard(page)
