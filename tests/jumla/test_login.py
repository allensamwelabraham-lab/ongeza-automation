import time

import pytest

from core.config import get_credentials
from core.helpers import find_error_on_page, wait_page_ready
from core.session import fill_login_form, is_login_page, login


pytestmark = pytest.mark.smoke


def test_login_valid(fresh_driver, app):
    login(fresh_driver, app)
    assert not is_login_page(fresh_driver)
    assert find_error_on_page(fresh_driver) is None


def test_login_wrong_password(fresh_driver, app):
    username, _ = get_credentials(app["key"])
    fresh_driver.get(app["base_url"])

    fill_login_form(fresh_driver, username, "AUTO-wrong-password-123")
    time.sleep(5)

    assert is_login_page(fresh_driver), "Password mbaya imekubaliwa!"


def test_login_empty_fields(fresh_driver, app):
    fresh_driver.get(app["base_url"])

    fill_login_form(fresh_driver, "", "")
    time.sleep(3)

    assert is_login_page(fresh_driver), "Login bila username/password imekubaliwa!"


def test_dashboard_loads(driver, app):
    driver.get(app["base_url"])
    wait_page_ready(driver)

    assert not is_login_page(driver)
    assert find_error_on_page(driver) is None
