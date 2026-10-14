"""The settings panel: tabs, saving, and values surviving a reload."""

from playwright.sync_api import expect

from crossword.tests.frontend.helpers import expect_message


def open_settings(page):
    page.locator(".app-nav-icon[title=Settings]").click()
    expect(page.locator("#settings-panel")).to_be_visible()


def test_change_a_setting_and_reload(app_page):
    page = app_page

    open_settings(page)
    expect(page.locator(".settings-tab.active")).to_have_text("Server")
    page.locator("#settings-tab-message_line_timeout_ms").click()
    expect(page.locator("#settings-panel-message_line_timeout_ms")).to_be_visible()
    expect(page.locator("#settings-panel-server")).to_be_hidden()
    page.locator("#setting-message_line_timeout_ms").fill("4321")
    page.locator(".settings-footer .btn-primary").click()
    expect(page.locator("#settings-panel")).to_be_hidden()
    expect_message(page, "Settings saved.")

    page.reload()
    page.locator(".dash").wait_for()
    open_settings(page)
    expect(page.locator("#setting-message_line_timeout_ms")).to_have_value("4321")


def test_restart_required_notice(app_page):
    page = app_page

    open_settings(page)
    page.locator("#settings-tab-log_level").click()
    page.locator("#setting-log_level").select_option("DEBUG")
    page.locator(".settings-footer .btn-primary").click()
    expect_message(page, "Restart the server")


def test_cancel_settings(app_page):
    page = app_page

    open_settings(page)
    page.locator("#setting-host").fill("example.com")
    page.locator(".settings-footer .btn-secondary").click()
    expect(page.locator("#settings-panel")).to_be_hidden()

    open_settings(page)
    expect(page.locator("#setting-host")).to_have_value("127.0.0.1")


def test_message_line_close_button(app_page):
    page = app_page

    open_settings(page)
    page.locator(".settings-footer .btn-primary").click()
    expect(page.locator("#ml")).to_be_visible()
    page.locator("#ml-close").click()
    expect(page.locator("#ml")).to_be_hidden()
