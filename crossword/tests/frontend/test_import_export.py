"""Import one file in each format, and export the open puzzle in each format."""

import pytest
from playwright.sync_api import expect

from crossword.tests.frontend.conftest import SAMPLE_PUZ
from crossword.tests.frontend.helpers import (
    answer_input_box, expect_editor_name, expect_message, menu, open_from_dashboard,
)

# (menu item, export endpoint that makes a file of that format, file suffix)
IMPORTS = [
    ("#menu-import-puz", None, ".puz"),
    ("#menu-import-acrosslite", "acrosslite", ".txt"),
    ("#menu-import-ipuz", "ipuz", ".ipuz"),
    ("#menu-import-xd", "xd", ".xd"),
    ("#menu-import-ccxml", "xml", ".xml"),
]

EXPORTS = [
    "#menu-export-puz",
    "#menu-export-acrosslite",
    "#menu-export-ipuz",
    "#menu-export-xd",
    "#menu-export-cwcompiler",
    "#menu-export-nytimes",
    "#menu-export-solver-pdf",
    "#menu-export-solved-pdf",
]


@pytest.mark.parametrize("item, endpoint, suffix", IMPORTS)
def test_import(app_page, api, tmp_path, item, endpoint, suffix):
    page = app_page
    sample = tmp_path / f"sample{suffix}"
    if endpoint is None:
        sample.write_bytes(SAMPLE_PUZ.read_bytes())
    else:
        api.import_sample("source")
        sample.write_bytes(api.export_text("source", endpoint))

    with page.expect_file_chooser() as chooser:
        menu(page, "Import", item)
    accept = page.locator("#import-file-input").get_attribute("accept")
    assert suffix in accept.split(",")
    chooser.value.set_files(str(sample))
    expect(page.locator("#ib-input")).to_have_value("sample")
    answer_input_box(page, "imported")
    expect_editor_name(page, "imported")
    expect(page.locator(".clue-row").first).to_be_visible()
    assert "imported" in api.puzzle_names()


def test_import_needs_a_name(app_page, tmp_path):
    page = app_page
    sample = tmp_path / "sample.puz"
    sample.write_bytes(SAMPLE_PUZ.read_bytes())

    with page.expect_file_chooser() as chooser:
        menu(page, "Import", "#menu-import-puz")
    chooser.value.set_files(str(sample))
    page.locator("#ib-input").fill("   ")
    page.locator("#ib-ok").click()
    expect_message(page, "Puzzle name is required")


@pytest.mark.parametrize("item", EXPORTS)
def test_export_open_puzzle(app_page, api, item):
    page = app_page
    api.import_sample("sample")
    page.reload()
    open_from_dashboard(page, "sample")

    with page.expect_download() as download:
        menu(page, "Export", item)
    assert download.value.suggested_filename
    expect_message(page, 'Exported "sample"')


def test_export_from_dashboard_uses_chooser(app_page, api):
    page = app_page
    api.import_sample("sample")
    page.reload()
    page.locator(".dash").wait_for()

    menu(page, "Export", "#menu-export-xd")
    expect(page.locator("#ch-title")).to_have_text("Choose a puzzle to export")
    with page.expect_download() as download:
        page.locator("#ch-list > div", has_text="sample").click()
    assert download.value.suggested_filename == "sample.xd"
