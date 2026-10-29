import time

from selenium.common.exceptions import (
    JavascriptException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from core.config import TIMEOUT


# ============================================================
# PAGE READY / ERROR PAGE
# ============================================================

ERROR_MARKERS = [
    "Server Error",
    "Integrity constraint violation",
    "An internal server error occurred",
    "504 Gateway Time-out",
    "Page Not Found",
    "502 Bad Gateway",
    "503 Service",
    "500 | ",
    "404 | Not Found",
    "403 | Forbidden",
    "419 | Page Expired",
    "Whoops, looks like something went wrong",
    "Internal Server Error",
    "Undefined variable",
    "Undefined index",
    "SQLSTATE[",
    "Call to undefined",
    "ErrorException",
    "Stack trace:",
    "This page isn’t working",
    "This site can’t be reached",
]

LOADING_SELECTORS = ".loading, .spinner, .el-loading-mask, .v-progress-circular, .dataTables_processing"


def wait_page_ready(driver, timeout=TIMEOUT):
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

    # Subiri loaders/spinners zipotee (kama zipo)
    end = time.time() + timeout
    while time.time() < end:
        visible = [
            el for el in driver.find_elements(By.CSS_SELECTOR, LOADING_SELECTORS)
            if _safe_displayed(el)
        ]
        if not visible:
            break
        time.sleep(0.5)

    time.sleep(0.5)


def _safe_displayed(element):
    try:
        return element.is_displayed()
    except Exception:
        return False


def find_error_on_page(driver):
    """Rudisha marker ya error ikiwa ukurasa ni error page, la sivyo None."""
    try:
        title = driver.title or ""
        body = driver.find_element(By.TAG_NAME, "body").text
    except Exception:  # ukurasa unabadilika wakati huu
        title, body = "", ""

    for marker in ERROR_MARKERS:
        if marker in title or marker in body:
            return marker

    return None


def browser_errors(driver):
    """Errors kali za JS kwenye console (Chrome peke yake)."""
    try:
        logs = driver.get_log("browser")
    except Exception:
        return []
    return [entry["message"] for entry in logs if entry.get("level") == "SEVERE"]


# ============================================================
# BUTTONS / TABLES / SEARCH
# ============================================================

ADD_BUTTON_XPATHS = [
    "//button[normalize-space()='Add']",
    "//a[normalize-space()='Add']",
    "//button[contains(normalize-space(),'Add ')]",
    "//a[contains(normalize-space(),'Add ')]",
    "//button[normalize-space()='Create' or normalize-space()='New']",
    "//a[normalize-space()='Create' or normalize-space()='New']",
    "//*[contains(@class,'btn')][contains(normalize-space(),'Ongeza')]",
]


def find_add_button(driver):
    for xpath in ADD_BUTTON_XPATHS:
        for element in driver.find_elements(By.XPATH, xpath):
            if _safe_displayed(element):
                return element
    return None


def table_rows(driver):
    rows = driver.find_elements(
        By.CSS_SELECTOR,
        "table tbody tr, .el-table__body tr, .v-data-table tbody tr",
    )
    return [r for r in rows if _safe_displayed(r)]


def has_table(driver):
    return bool(
        driver.find_elements(By.CSS_SELECTOR, "table, .el-table, .v-data-table")
    )


def find_search_input(driver):
    selectors = [
        "input[type='search']",
        "input[placeholder*='Search' i]",
        "input[placeholder*='Tafuta' i]",
        ".dataTables_filter input",
    ]
    for css in selectors:
        for element in driver.find_elements(By.CSS_SELECTOR, css):
            if _safe_displayed(element):
                return element
    return None


def page_heading(driver):
    for css in ["h1", "h2", "h3", ".page-title", ".card-title", ".breadcrumb"]:
        for element in driver.find_elements(By.CSS_SELECTOR, css):
            text = element.text.strip() if _safe_displayed(element) else ""
            if text:
                return text
    return ""


def click(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)


# ============================================================
# SELECT2 HELPERS (kutoka test_agent.py)
# ============================================================

def _open_select2(driver, wait, select_id):
    container = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, f"#{select_id} + span.select2")
        )
    )
    container.click()
    time.sleep(1)

    return wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "li.select2-results__option")
        )
    )


def select2_option(driver, wait, select_id, option_text):
    print(f"Selecting {select_id} -> {option_text}")

    for option in _open_select2(driver, wait, select_id):
        if option.text.strip() == option_text:
            click(driver, option)
            time.sleep(1)
            return option_text

    raise AssertionError(f"Option '{option_text}' haipo kwenye Select2 '{select_id}'")


def select2_first_option(driver, wait, select_id):
    for option in _open_select2(driver, wait, select_id):
        text = option.text.strip()
        if (
            text
            and not text.startswith("--")
            and "Searching" not in text
            and "No results" not in text
            and "Loading" not in text
        ):
            click(driver, option)
            time.sleep(1)
            print(f"Selected: {select_id} = {text}")
            return text

    raise AssertionError(f"Hakuna option halisi kwenye {select_id}")


def wait_for_real_option(driver, wait, element_id):
    def check_options(d):
        try:
            select = Select(d.find_element(By.ID, element_id))
            return any(
                o.text.strip() and not o.text.strip().startswith("--")
                for o in select.options
            )
        except Exception:
            return False

    wait.until(check_options)


# ============================================================
# FORM INSPECTION (toleo la inspect_form linalorudisha data)
# ============================================================

def describe_form(driver, scope_css="#content, .app-content, main"):
    fields = []

    scopes = driver.find_elements(By.CSS_SELECTOR, scope_css) if scope_css else []
    root = scopes[0] if scopes else driver
    for element in root.find_elements(By.CSS_SELECTOR, "input, select, textarea"):
        try:
            field_type = element.get_attribute("type") or element.tag_name
            if field_type in ("hidden", "submit", "button"):
                continue
            # select2 huficha <select> halisi; bado tunaihesabu
            if not element.is_displayed() and element.tag_name != "select":
                continue
            fields.append({
                "tag": element.tag_name,
                "type": field_type,
                "id": element.get_attribute("id") or "",
                "name": element.get_attribute("name") or "",
                "placeholder": element.get_attribute("placeholder") or "",
                "required": element.get_attribute("required") is not None,
            })
        except Exception:
            pass

    return fields


SUBMIT_XPATHS = [
    "//button[@type='submit']",
    "//button[normalize-space()='Save' or normalize-space()='Submit' or normalize-space()='Create']",
    "//button[.//span[normalize-space()='Save' or normalize-space()='Submit']]",
    "//input[@type='submit']",
]


def find_submit_button(driver, scope_css="#content, .app-content, main"):
    scopes = driver.find_elements(By.CSS_SELECTOR, scope_css) if scope_css else []
    root = scopes[0] if scopes else driver
    for xpath in SUBMIT_XPATHS:
        for element in root.find_elements(By.XPATH, "." + xpath):
            if _safe_displayed(element):
                return element
    return None


VALIDATION_SELECTORS = (
    ".invalid-feedback, .is-invalid, .text-danger, .error, .help-block, "
    ".el-form-item__error, .v-messages__message, .alert-danger, .parsley-error, "
    "label.error, .toast-error, .swal2-popup"
)


def validation_shown(driver):
    """True ikiwa form imeonyesha validation (HTML5 au ujumbe wa error)."""
    invalid_html5 = driver.execute_script(
        "return Array.from(document.querySelectorAll('input,select,textarea'))"
        ".some(e => e.willValidate && !e.checkValidity());"
    )
    if invalid_html5:
        return True

    if any(_safe_displayed(e) for e in driver.find_elements(
            By.CSS_SELECTOR, ".is-invalid, .has-error, [aria-invalid='true']")):
        return True

    # Ujumbe wa error lazima uwe na maandishi (divs tupu za .text-danger hazihesabiwi)
    def shown_text(e):
        try:
            return _safe_displayed(e) and e.text.strip()
        except Exception:  # element imeondoka (ukurasa/Vue imechora upya)
            return ""

    return any(shown_text(e) for e in driver.find_elements(By.CSS_SELECTOR, VALIDATION_SELECTORS))


def wait_until(driver, condition, timeout=TIMEOUT):
    # Element "stale" (ukurasa umebadilika katikati ya kusoma) = jaribu tena, si error
    try:
        return WebDriverWait(driver, timeout, ignored_exceptions=(
            NoSuchElementException, StaleElementReferenceException, JavascriptException)).until(condition)
    except TimeoutException:
        return False
