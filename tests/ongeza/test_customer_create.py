"""
Kuunda mteja (Customer > All Customers > Add), kujaza fomu yote, kusave, na
kuhakikisha mteja amehifadhiwa.

Test hii INASAVE data kwenye staging, kwa hiyo inaendeshwa tu RUN_CRUD=1:

    RUN_CRUD=1 pytest tests/ongeza/test_customer_create.py -v

Mteja anapewa jina la AUTO (k.m. "Auto Tester1008061530") ili iwe rahisi kumtafuta
na kumfuta baadaye.
"""

import time
from datetime import datetime

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from core.config import PAGE_LOAD_TIMEOUT, TIMEOUT
from core.helpers import (
    click,
    describe_form,
    find_error_on_page,
    find_submit_button,
    select2_first_option,
    validation_shown,
)
from core.pages import column_index, open_page, profile, table_data, vue_filter_inputs


CUSTOMERS = "/crud/customer/index2"
CREATE_CUSTOMER = "/crud/customer/create"


def fill(driver, element_id, value):
    element = WebDriverWait(driver, TIMEOUT).until(
        EC.visibility_of_element_located((By.ID, element_id))
    )
    element.clear()
    element.send_keys(value)
    print(f"Filled {element_id} = {value}")


def choose_first(driver, select_id):
    """Chagua option ya kwanza halisi (select2 au <select> ya kawaida)."""
    wait = WebDriverWait(driver, TIMEOUT)
    if driver.find_elements(By.CSS_SELECTOR, f"#{select_id} + span.select2"):
        return select2_first_option(driver, wait, select_id)

    select = Select(driver.find_element(By.ID, select_id))
    for option in select.options:
        text = option.text.strip()
        if option.get_attribute("value") and text and not text.startswith("--"):
            select.select_by_visible_text(option.text)
            print(f"Selected: {select_id} = {text}")
            return text
    raise AssertionError(f"Hakuna option halisi kwenye {select_id}")


@pytest.mark.crud
def test_create_customer(driver, app):
    stamp = datetime.now().strftime("%m%d%H%M%S")
    first_name = "Auto"
    last_name = f"Tester{stamp}"

    # 1. Fungua fomu kupitia button ya Add kwenye Customers
    assert open_page(driver, app, CUSTOMERS) is None, "Customers haikufunguka"
    add = WebDriverWait(driver, TIMEOUT).until(
        EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Add']"))
    )
    click(driver, add)
    WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(EC.url_contains(CREATE_CUSTOMER))
    assert find_error_on_page(driver) is None, "Fomu ya Create Customer imeleta error"

    # 2. Jaza fomu
    fill(driver, "customer-first_name", first_name)
    fill(driver, "customer-last_name", last_name)
    ward = choose_first(driver, "customer-ward")
    fill(driver, "customer-village", "AUTO Village")
    fill(driver, "customer-sub_village", "AUTO Sub Village")
    fill(driver, "customer-land_mark", "AUTO Landmark")
    fill(driver, "customer-description", f"Automation test customer {stamp}")

    # Fields za ziada zikiwepo (k.m. phone)
    for field in describe_form(driver):
        if "phone" in (field["name"] + field["id"]).lower() and field["id"]:
            fill(driver, field["id"], "07" + stamp[-8:])

    # 3. Submit
    submit = find_submit_button(driver)
    assert submit is not None, "Button ya Save haikupatikana"
    click(driver, submit)

    WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
        lambda d: CREATE_CUSTOMER not in d.current_url or validation_shown(d)
    )
    time.sleep(2)
    error = find_error_on_page(driver)
    assert error is None, f"Kusave kumeleta server error '{error}' ({driver.current_url})"
    assert CREATE_CUSTOMER not in driver.current_url, (
        "Fomu haikusave (bado iko kwenye create). Validation: "
        + driver.find_element(By.TAG_NAME, "body").text[:300]
    )
    print(f"Saved -> {driver.current_url}")

    # 4. Ukurasa baada ya kusave unaonyesha mteja mpya
    body = driver.find_element(By.TAG_NAME, "body").text
    assert last_name in body, f"Ukurasa baada ya kusave hauonyeshi '{last_name}'"

    # 5. Mteja anaonekana kwenye list akitafutwa kwa last name
    assert open_page(driver, app, CUSTOMERS) is None
    vue_filter_inputs(driver, {"last name": last_name})
    info = profile(driver)
    rows = table_data(driver, "vue")
    col_last = column_index(info["columns"], "last name")
    col_ward = column_index(info["columns"], "ward")

    assert len(rows) == 1, f"Tulitarajia mteja 1 '{last_name}', tumepata {len(rows)}"
    assert rows[0][col_last] == last_name
    if col_ward is not None:
        assert rows[0][col_ward] == ward, f"Ward ni '{rows[0][col_ward]}', tulichagua '{ward}'"
