"""Dashboard: the puzzle list, its tabs and sorting, state changes and history."""

from playwright.sync_api import expect

from crossword.tests.frontend.helpers import expect_editor_name, open_from_dashboard


def seed(api, page):
    api.create_puzzle("bravo")
    api.create_puzzle("alpha")
    api.create_puzzle("charlie")
    api.set_state("charlie", "submitted", publisher="NYT", date_submitted="2026-01-02")
    page.reload()
    page.locator(".dash").wait_for()


def table_names(page):
    return page.locator(".dash-table tbody tr").evaluate_all(
        "rows => rows.map(r => r.getAttribute('data-dash-name'))")


def test_dashboard_lists_puzzles_in_cards_and_table(app_page, api):
    page = app_page
    seed(api, page)

    expect(page.locator(".dash-card")).to_have_count(4)
    expect(page.locator(".dash-card-1 .dash-card-title")).to_have_text("IN PROGRESS (2)")
    expect(page.locator(".dash-card-3 .dash-card-title")).to_have_text("SUBMITTED (1)")
    expect(page.locator(".dash-card-3")).to_contain_text("submitted to NYT")
    assert sorted(table_names(page)) == ["alpha", "bravo", "charlie"]


def test_filter_tabs(app_page, api):
    page = app_page
    seed(api, page)

    page.locator("[data-dash-tab='submitted']").click()
    expect(page.locator("[data-dash-tab='submitted']")).to_have_class("dash-tab dash-tab-active")
    assert table_names(page) == ["charlie"]

    page.locator("[data-dash-tab='archived']").click()
    expect(page.locator(".dash-empty")).to_have_text("No puzzles.")

    page.locator("[data-dash-tab='draft']").click()
    assert sorted(table_names(page)) == ["alpha", "bravo"]


def test_sorting_by_column(app_page, api):
    page = app_page
    seed(api, page)

    page.locator("[data-dash-sort='name']").click()
    expect(page.locator("[data-dash-sort='name']")).to_have_text("Name ▲")
    assert table_names(page) == ["alpha", "bravo", "charlie"]

    page.locator("[data-dash-sort='name']").click()
    expect(page.locator("[data-dash-sort='name']")).to_have_text("Name ▼")
    assert table_names(page) == ["charlie", "bravo", "alpha"]


def test_clicking_a_name_opens_the_puzzle(app_page, api):
    page = app_page
    seed(api, page)

    open_from_dashboard(page, "bravo")
    expect_editor_name(page, "bravo")


def test_change_state_from_dashboard(app_page, api):
    page = app_page
    seed(api, page)

    page.locator("[data-dash-state='alpha']").select_option("submitted")
    expect(page.locator("#state-dialog")).to_be_visible()
    expect(page.locator("#state-dialog-name")).to_have_text("alpha")
    expect(page.locator("#state-dialog-publisher-row")).to_be_visible()

    # Publisher is required for 'submitted'
    page.locator("#state-dialog-ok").click()
    expect(page.locator("#state-dialog-error")).to_have_text("Publisher is required when submitting.")

    page.locator("#state-dialog-publisher").fill("WSJ")
    page.locator("#state-dialog-ok").click()
    expect(page.locator("#state-dialog")).to_be_hidden()
    expect(page.locator(".dash-card-3 .dash-card-title")).to_have_text("SUBMITTED (2)")
    assert api.call("GET", "/api/puzzles/alpha/state")["publisher"] == "WSJ"


def test_cancelling_state_change_reverts_dropdown(app_page, api):
    page = app_page
    seed(api, page)

    select = page.locator("[data-dash-state='bravo']")
    select.select_option("archived")
    page.locator("#state-dialog-cancel").click()
    expect(page.locator("#state-dialog")).to_be_hidden()
    expect(select).to_have_value("draft")


def test_show_history(app_page, api):
    page = app_page
    seed(api, page)

    page.locator(".dash-table tbody tr[data-dash-name='charlie']").click(button="right")
    page.locator(".context-menu-item", has_text="Show history").click()
    popup = page.locator("#history-popup")
    expect(popup).to_be_visible()
    expect(page.locator("#history-popup-title")).to_have_text("History — charlie")
    expect(popup.locator("tbody tr").first).to_contain_text("submitted to NYT")

    page.locator("#history-popup .dialog-close-btn").click()
    expect(popup).to_be_hidden()


def test_restore_from_history(app_page, api):
    page = app_page
    api.create_puzzle("five")

    # Two saves leave an earlier version that can be restored
    for comment, letter in [("first", "A"), ("second", "B")]:
        wn = api.call("POST", "/api/puzzles/five/open")["working_name"]
        api.call("PUT", f"/api/puzzles/{wn}/words/1/across",
                 {"text": letter * 5, "clue": "", "locked": False})
        api.call("POST", f"/api/puzzles/{wn}/copy", {"new_name": "five", "comment": comment})
    page.reload()
    page.locator(".dash").wait_for()

    page.locator(".dash-row[data-dash-name='five']").click(button="right")
    page.locator(".context-menu-item", has_text="Show history").click()
    restore = page.locator("#history-popup .dash-history-restore").first
    expect(restore).to_be_visible()
    restore.click()
    expect(page.locator("#mb-ok")).to_have_text("Restore")
    page.locator("#mb-ok").click()
    expect_editor_name(page, "five")
    expect(page.locator(".clue-answer").first).to_have_text("AAAAA")
