"""
Tests za kila list page (JUMLA na ONGEZA zinatumia tests hizi hizi; app = PW_APP):
page_loads, columns, records, pagination, sort, filter_finds_row, filter_no_match, view.
Hakuna kinachosaviwa: write guard ya network inazuia POST/PUT/DELETE.
"""

import os

import pytest

from core import list_checks as lc
from pw import checks

APP = os.getenv("PW_APP", "ongeza")
pytestmark = pytest.mark.smoke


@pytest.mark.parametrize("module", lc.params(APP, lambda m: True))
def test_page_loads(page, app, module):
    checks.check_page_loads(page, app, module)


@pytest.mark.parametrize("module", lc.params(APP, lc.is_list, "hakuna list pages"))
def test_columns(page, app, module):
    checks.check_columns(page, app, module)


@pytest.mark.parametrize("module", lc.params(APP, lc.is_list, "hakuna list pages"))
def test_records(page, app, module):
    checks.check_records(page, app, module)


@pytest.mark.parametrize("module", lc.params(APP, lc.has_more_pages, "hakuna module yenye pages 2+"))
def test_pagination(page, app, module):
    checks.check_pagination(page, app, module)


@pytest.mark.parametrize("module", lc.params(APP, lc.has_sort, "hakuna module yenye sort"))
def test_sort(page, app, module):
    checks.check_sort(page, app, module)


@pytest.mark.parametrize("module", lc.params(APP, lc.has_text_filter, "hakuna module yenye filter"))
def test_filter_finds_row(page, app, module):
    checks.check_filter_finds_row(page, app, module)


@pytest.mark.parametrize("module", lc.params(APP, lc.has_text_filter, "hakuna module yenye filter"))
def test_filter_no_match(page, app, module):
    checks.check_filter_no_match(page, app, module)


@pytest.mark.parametrize("module", lc.params(APP, lc.has_view, "hakuna module yenye view"))
def test_view(page, app, module):
    checks.check_view(page, app, module)
