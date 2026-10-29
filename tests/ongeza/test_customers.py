"""
Customers (Customer > All Customers) - tests za kina. Hakuna kinachosaviwa.
"""

import pytest
from selenium.webdriver.common.by import By

from core.helpers import click, find_error_on_page, wait_until
from core.pages import column_index, open_page, profile, table_data, vue_filter_inputs


CUSTOMERS = "/crud/customer/index2"
pytestmark = pytest.mark.smoke


def open_customers(driver, app):
    error = open_page(driver, app, CUSTOMERS)
    assert error is None, f"Customers: {error}"
    info = profile(driver)
    assert info["rows"] > 0, "Customers: table iko tupu"
    return info


def test_customers_filter_by_phone(driver, app):
    info = open_customers(driver, app)
    col = column_index(info["columns"], "phone number")
    phones = [r[col] for r in table_data(driver, "vue") if r[col] not in ("", "--")]
    if not phones:
        pytest.skip("Hakuna customer mwenye phone kwenye page 1")
    phone = phones[0].split(",")[0].strip()

    vue_filter_inputs(driver, {"Phone": phone})
    rows = table_data(driver, "vue")
    assert rows, f"Filter Phone={phone} haikurudisha customer"
    wrong = [r[col] for r in rows if phone not in r[col]]
    assert not wrong, f"Filter Phone={phone} imerudisha customers wengine: {wrong[:5]}"


def test_customers_filter_by_date_range(driver, app):
    info = open_customers(driver, app)
    col = column_index(info["columns"], "created date")
    day = table_data(driver, "vue")[0][col][:10]

    vue_filter_inputs(driver, {"From": day, "To": day})
    rows = table_data(driver, "vue")
    assert rows, f"Filter From/To={day} haikurudisha customer"
    wrong = [r[col] for r in rows if not r[col].startswith(day)]
    assert not wrong, f"Filter From/To={day} imerudisha tarehe nyingine: {wrong[:5]}"
    total = profile(driver)["total"]
    assert total is not None and total < info["total"], (
        f"Filter ya tarehe haikupunguza records ({total} vs {info['total']})"
    )


def test_customer_view_shows_same_customer(driver, app):
    info = open_customers(driver, app)
    first = column_index(info["columns"], "first name")
    row = table_data(driver, "vue")[0]
    name = row[first]

    link = driver.find_element(By.CSS_SELECTOR, "table.ongeza-table tbody tr a[data-id]")
    before = driver.current_url
    click(driver, link)
    wait_until(driver, lambda d: d.current_url != before, timeout=30)
    wait_until(driver, lambda d: name.lower() in d.find_element(By.TAG_NAME, "body").text.lower(), timeout=30)

    assert find_error_on_page(driver) is None, f"Customer view: error kwenye {driver.current_url}"
    assert name.lower() in driver.find_element(By.TAG_NAME, "body").text.lower(), (
        f"Customer view haionyeshi jina '{name}' ({driver.current_url})"
    )
