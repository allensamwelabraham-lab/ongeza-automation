"""
Hatua ya 2: tests zinazolinganisha na data halisi ya server (Inertia) kwa JUMLA na ONGEZA:
sort kwa kila column, filters zote, Per Page, pagination kwa data, View = row.
Hakuna kinachosaviwa: write guard ya network inazuia POST/PUT/DELETE.
"""

import os

import pytest

from core import list_checks as lc
from pw import data_checks

APP = os.getenv("PW_APP", "ongeza")
pytestmark = pytest.mark.data


def is_vue_list(m):
    return lc.has_rows(m) and m.get("kind") == "vue"


@pytest.mark.parametrize("module", lc.params(APP, lambda m: lc.has_rows(m) and lc.is_paged_list(m),
                                             "hakuna list pages"))
def test_sort_all_columns(page, app, module):
    data_checks.check_sort_all_columns(page, app, module)


@pytest.mark.parametrize("module", lc.params(APP, is_vue_list, "hakuna list za Vue"))
def test_filters_all(page, app, module):
    data_checks.check_filters_all(page, app, module)


@pytest.mark.parametrize("module", lc.params(APP, is_vue_list, "hakuna list za Vue"))
def test_per_page(page, app, module):
    data_checks.check_per_page(page, app, module)


@pytest.mark.parametrize("module", lc.params(APP, is_vue_list, "hakuna list za Vue"))
def test_pagination_data(page, app, module):
    data_checks.check_pagination_data(page, app, module)


@pytest.mark.parametrize("module", lc.params(APP, lc.has_view, "hakuna module yenye view"))
def test_view_matches_row(page, app, module):
    data_checks.check_view_matches_row(page, app, module)
