"""
Create/Add forms za modules za ongeza: zinafunguka, fields zote zipo, na form tupu
inakataliwa. Kabla ya kubofya Save tunaweka write guard (core/guard.py), kwa hiyo
hakuna kinachosaviwa hata form ikikosa validation.
"""

import pytest

from core import list_checks as lc


APP = "ongeza"
pytestmark = pytest.mark.forms


@pytest.mark.parametrize("module", lc.params(APP, lc.has_create, "hakuna module yenye Create/Add"))
def test_create_form_fields(driver, app, module):
    lc.check_create_form_fields(driver, app, module)


@pytest.mark.parametrize("module", lc.params(APP, lc.has_create, "hakuna module yenye Create/Add"))
def test_create_form_rejects_empty(driver, app, module):
    lc.check_create_form_rejects_empty(driver, app, module)


@pytest.mark.crud
@pytest.mark.parametrize("module", lc.params(APP, lc.can_save, "hakuna module ya kusave"))
def test_create_form_saves(driver, app, module):
    """RUN_CRUD=1 / --crud tu: jaza fomu kwa data ya AUTO, Save, hakikisha imesave."""
    lc.check_create_form_saves(driver, app, module)


@pytest.mark.crud
@pytest.mark.parametrize("module", lc.params(APP, lc.can_save, "hakuna module ya kusave"))
def test_edit_form_saves(driver, app, module):
    """RUN_CRUD=1 / --crud tu: fungua Edit ya record ya AUTO, badilisha field, Save, hakikisha imebadilika."""
    lc.check_edit_form_saves(driver, app, module)
