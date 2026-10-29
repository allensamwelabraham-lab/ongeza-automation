"""
Agents (ONGEZA staging) - imetokana na test_agent.py yako.

- test_agents_list_opens / test_create_agent_form_fields: hazisavi chochote.
- test_create_agent: inaunda agent wa AUTO (inaendeshwa tu RUN_CRUD=1).
"""

import time
from datetime import datetime

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.guard import describe_server_responses, record_server_responses
from core.pages import open_page, table_data, vue_filter_inputs
from core.config import PAGE_LOAD_TIMEOUT, TIMEOUT
from core.helpers import (
    click,
    describe_form,
    find_error_on_page,
    find_submit_button,
    validation_shown,
    select2_first_option,
    select2_option,
    wait_for_real_option,
    wait_page_ready,
)


AGENTS_PATH = "/crud/worker/agents"
CREATE_AGENT_PATH = "/crud/worker/create-agent"


def open_create_agent(driver, app):
    wait = WebDriverWait(driver, TIMEOUT)

    driver.get(app["base_url"] + AGENTS_PATH)
    wait_page_ready(driver)

    add_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Add']"))
    )
    add_button.click()

    # Server ya staging ni nzito; kurasa zinaweza kuchukua zaidi ya TIMEOUT
    WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(EC.url_contains(CREATE_AGENT_PATH))
    wait_page_ready(driver)
    return wait


def page_messages(driver):
    """Ujumbe wa validation / toast unaoonekana kwenye ukurasa."""
    texts = [e.text.strip() for e in driver.find_elements(
        By.CSS_SELECTOR, ".text-danger, .invalid-feedback, .toast, .toast-message, .swal2-popup, .alert, [class*='notif']")
        if e.text.strip()]
    return " | ".join(dict.fromkeys(texts)) or "hakuna"


def set_date(driver, css, value):
    """Weka tarehe (YYYY-MM-DD) kwenye input[type=date] bila kutegemea locale ya browser."""
    element = driver.find_element(By.CSS_SELECTOR, css)
    driver.execute_script(
        "arguments[0].value = arguments[1];"
        "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
        "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
        element, value,
    )


def fill(driver, wait, locator, value):
    element = wait.until(EC.visibility_of_element_located(locator))
    element.clear()
    element.send_keys(value)
    return element


# ============================================================
# NON-DESTRUCTIVE
# ============================================================

@pytest.mark.smoke
def test_agents_list_opens(driver, app):
    driver.get(app["base_url"] + AGENTS_PATH)
    wait_page_ready(driver)

    assert find_error_on_page(driver) is None
    assert driver.find_elements(By.XPATH, "//button[normalize-space()='Add']"), (
        "Button ya Add haipo kwenye Agents"
    )


@pytest.mark.forms
def test_create_agent_form_fields(driver, app):
    open_create_agent(driver, app)

    expected = [
        (By.CSS_SELECTOR, "input[placeholder='first name']"),
        (By.CSS_SELECTOR, "input[placeholder='last name']"),
        (By.CSS_SELECTOR, "input[placeholder='username']"),
        (By.CSS_SELECTOR, "input[placeholder='apk version']"),
        (By.CSS_SELECTOR, "input[placeholder='phone no']"),
        (By.CSS_SELECTOR, "input[placeholder='nida number']"),
        (By.CSS_SELECTOR, "input[type='date'][placeholder='DOB']"),
        (By.CSS_SELECTOR, "input[type='date'][placeholder='Hire Date']"),
        (By.ID, "district_id"),
        (By.ID, "ward_id"),
        (By.ID, "org_key"),
        (By.ID, "department_id"),
        (By.ID, "org_position_id"),
    ]

    missing = [loc for loc in expected if not driver.find_elements(*loc)]
    assert not missing, f"Fields hazipo kwenye Create Agent: {missing}"


@pytest.mark.forms
def test_ward_loads_after_district(driver, app):
    wait = open_create_agent(driver, app)

    select2_option(driver, wait, "district_id", "Arusha")
    wait_for_real_option(driver, wait, "ward_id")


# ============================================================
# CRUD - INAUNDA AGENT WA AUTO
# ============================================================

@pytest.mark.crud
def test_create_agent(driver, app):
    stamp = datetime.now().strftime("%m%d%H%M%S")
    first_name = "Automation"
    last_name = f"Tester{stamp}"

    wait = open_create_agent(driver, app)

    fill(driver, wait, (By.CSS_SELECTOR, "input[placeholder='first name']"), first_name)
    fill(driver, wait, (By.CSS_SELECTOR, "input[placeholder='last name']"), last_name)
    fill(driver, wait, (By.CSS_SELECTOR, "input[placeholder='apk version']"), "1.0.0")
    fill(driver, wait, (By.CSS_SELECTOR, "input[placeholder='phone no']"), "07" + stamp[-8:])
    fill(driver, wait, (By.CSS_SELECTOR, "input[placeholder='nida number']"), "1995010112" + stamp)

    set_date(driver, "input[type='date'][placeholder='DOB']", "1995-01-01")
    set_date(driver, "input[type='date'][placeholder='Hire Date']", "2026-01-01")

    select2_option(driver, wait, "district_id", "Arusha")
    wait_for_real_option(driver, wait, "ward_id")
    select2_first_option(driver, wait, "ward_id")
    select2_option(driver, wait, "org_key", "ONGEZA")
    select2_option(driver, wait, "department_id", "Retail Sales")

    # Org Position inaload baada ya Department (ni lazima)
    wait_for_real_option(driver, wait, "org_position_id")
    position = select2_first_option(driver, wait, "org_position_id")

    # Fields zinazojitokeza baada ya Department (k.m. designation)
    time.sleep(3)
    if driver.find_elements(By.ID, "designation_id"):
        wait_for_real_option(driver, wait, "designation_id")
        select2_first_option(driver, wait, "designation_id")

    print("Form baada ya kujaza:", describe_form(driver))

    submit = find_submit_button(driver)
    assert submit is not None, "Button ya Save haikupatikana"
    record_server_responses(driver)
    click(driver, submit)

    # Ikisave, tunatoka kwenye create-agent
    WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
        lambda d: CREATE_AGENT_PATH not in d.current_url or validation_shown(d)
    )
    wait_page_ready(driver)
    error = find_error_on_page(driver)
    assert error is None, f"Kusave agent kumeleta server error '{error}'"
    assert CREATE_AGENT_PATH not in driver.current_url, (
        "Agent hakusaviwa. Ujumbe: " + page_messages(driver)
        + ". Jibu la server: " + describe_server_responses(driver)
    )
    print(f"ACTUAL: Agent {first_name} {last_name} ({position}) amesaviwa -> {driver.current_url}")

    # Thibitisha agent yupo kwenye list (filter kwa Name)
    assert open_page(driver, app, AGENTS_PATH) is None
    vue_filter_inputs(driver, {"Name": last_name})
    rows = table_data(driver, "vue")
    names = [r[1] for r in rows]
    assert any(last_name in n for n in names), f"Agent {last_name} hakuonekana kwenye list: {names[:5]}"
    print(f"ACTUAL: Agent anaonekana kwenye list: {[n for n in names if last_name in n][0]}")
