"""
Tests za kina za KILA module ya ongezapro (orodha + baseline iko modules/ongezapro.json).

Kwa kila module (list page):
  page_loads      ukurasa unafunguka bila error, aina na heading ni zile zile
  columns         hakuna column iliyopotea
  records         idadi ya records inaonekana na table ina rows
  pagination      page 2 inafunguka na ina rows tofauti
  sort            sort kwa ID (au key ya kwanza) ASC na DESC, na ID zimepangwa
  filter_*        filter kwa thamani halisi inarudisha rows sahihi; thamani isiyokuwepo -> 0
  view            row ya kwanza inafunguka kwenye detail page
Hakuna kinachosaviwa.
"""

import pytest

from core import list_checks as lc


APP = "ongezapro"
pytestmark = pytest.mark.smoke


@pytest.mark.parametrize("module", lc.params(APP, lambda m: True))
def test_page_loads(driver, app, module):
    lc.check_page_matches_baseline(driver, app, module)


@pytest.mark.parametrize("module", lc.params(APP, lc.is_list, "hakuna list pages"))
def test_columns(driver, app, module):
    lc.check_columns(driver, app, module)


@pytest.mark.parametrize("module", lc.params(APP, lc.is_list, "hakuna list pages"))
def test_records(driver, app, module):
    lc.check_records(driver, app, module)


@pytest.mark.parametrize("module", lc.params(APP, lc.has_more_pages, "hakuna module yenye pages 2+"))
def test_pagination(driver, app, module):
    lc.check_pagination(driver, app, module)


@pytest.mark.parametrize("module", lc.params(APP, lc.has_sort, "hakuna module yenye sort"))
def test_sort(driver, app, module):
    lc.check_sort(driver, app, module)


@pytest.mark.parametrize("module", lc.params(APP, lc.has_text_filter, "hakuna module yenye filter"))
def test_filter_finds_row(driver, app, module):
    lc.check_filter_finds_row(driver, app, module)


@pytest.mark.parametrize("module", lc.params(APP, lc.has_text_filter, "hakuna module yenye filter"))
def test_filter_no_match(driver, app, module):
    lc.check_filter_no_match(driver, app, module)


@pytest.mark.parametrize("module", lc.params(APP, lc.has_view, "hakuna module yenye view"))
def test_view(driver, app, module):
    lc.check_view(driver, app, module)
