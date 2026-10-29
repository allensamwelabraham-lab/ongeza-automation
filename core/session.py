import json
import time

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from core.config import LOGIN_TIMEOUT, SESSIONS_DIR, TIMEOUT, get_credentials


# ============================================================
# LOGIN SELECTORS (kutoka login_once.py, pamoja na fallback)
# ============================================================

USERNAME_SELECTORS = [
    (By.CSS_SELECTOR, 'input[placeholder="Username"]'),
    (By.CSS_SELECTOR, 'input[name="username"]'),
    (By.CSS_SELECTOR, 'input#username'),
    (By.CSS_SELECTOR, 'input[placeholder="username" i]'),
    (By.CSS_SELECTOR, 'input[name="email"]'),
    (By.CSS_SELECTOR, 'input[type="email"]'),
]

PASSWORD_SELECTORS = [
    (By.CSS_SELECTOR, 'input[placeholder="Password"]'),
    (By.CSS_SELECTOR, 'input[type="password"]'),
]

LOGIN_BUTTON_SELECTORS = [
    (By.XPATH, '//button[.//span[normalize-space()="Login"]]'),
    (By.XPATH, '//button[normalize-space()="Login"]'),
    (By.CSS_SELECTOR, 'button[type="submit"]'),
    (By.CSS_SELECTOR, 'input[type="submit"]'),
]


def find_first(driver, selectors, timeout=TIMEOUT, condition=EC.visibility_of_element_located):
    end = time.time() + timeout
    while time.time() < end:
        for locator in selectors:
            try:
                return WebDriverWait(driver, 0.5).until(condition(locator))
            except TimeoutException:
                continue
    raise TimeoutException(f"Hakuna selector iliyopatikana: {selectors}")


def is_login_page(driver):
    for locator in PASSWORD_SELECTORS:
        for element in driver.find_elements(*locator):
            try:
                if element.is_displayed():
                    return True
            except Exception:
                pass
    return False


# ============================================================
# LOGIN KWA FORM
# ============================================================

def fill_login_form(driver, username, password):
    user_input = find_first(driver, USERNAME_SELECTORS)
    user_input.clear()
    user_input.send_keys(username)

    pass_input = find_first(driver, PASSWORD_SELECTORS)
    pass_input.clear()
    pass_input.send_keys(password)

    button = find_first(
        driver, LOGIN_BUTTON_SELECTORS, condition=EC.element_to_be_clickable
    )
    button.click()


def _open_light_page(driver, app):
    """Ukurasa mwepesi wa kuthibitisha session (si Dashboard nzito)."""
    try:
        driver.get(app["base_url"] + app.get("light_page", "/"))
    except TimeoutException:
        try:
            driver.execute_script("window.stop();")
        except Exception:
            pass


def login(driver, app):
    username, password = get_credentials(app["key"])

    print(f"\n[{app['name']}] Login kama '{username}'...")
    driver.get(app["base_url"])

    fill_login_form(driver, username, password)

    # Jibu la Login (POST) ndilo linaloleta Dashboard, ambayo ni nzito kwenye staging.
    # Hatusimamishi (window.stop) mapema: hiyo ingekata POST ya login yenyewe kabla
    # session haijaundwa. Tunasubiri LOGIN_TIMEOUT; ikishindikana, tunajaribu ukurasa
    # mwepesi (session inaweza kuwa imeshaundwa hata kama Dashboard bado inaload).
    try:
        WebDriverWait(driver, LOGIN_TIMEOUT).until(lambda d: not is_login_page(d))
    except TimeoutException:
        try:
            driver.execute_script("window.stop();")
        except Exception:
            pass
        _open_light_page(driver, app)
        WebDriverWait(driver, 30).until(lambda d: not is_login_page(d))
    time.sleep(2)

    print(f"[{app['name']}] LOGIN SUCCESSFUL -> {driver.current_url}")
    save_session(driver, app)


# ============================================================
# SAVE / RESTORE SESSION (cookies + localStorage)
# ============================================================

def _session_files(app):
    folder = SESSIONS_DIR / app["key"]
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "cookies.json", folder / "local_storage.json"


def save_session(driver, app):
    cookies_file, storage_file = _session_files(app)

    cookies_file.write_text(json.dumps(driver.get_cookies()))

    local_storage = driver.execute_script(
        "return Object.fromEntries(Object.entries(localStorage));"
    )
    storage_file.write_text(json.dumps(local_storage))

    print(f"[{app['name']}] Session imehifadhiwa kwenye {cookies_file.parent}")


def restore_session(driver, app):
    cookies_file, storage_file = _session_files(app)

    if not cookies_file.exists():
        return False

    driver.get(app["base_url"])
    time.sleep(1)

    cookies = json.loads(cookies_file.read_text())
    # Cookie ya session ya zamani (PHPSESSID, bila expiry) ikirudishwa, server ya Yii inapoteza flash
    # (validation errors hazirudi baada ya Save). Ikiwa kuna cookie ya kudumu ya login (_identity),
    # tunarudisha hiyo tu na server inatoa session mpya.
    if any(c.get("expiry") for c in cookies):
        cookies = [c for c in cookies if c.get("expiry")]
    for cookie in cookies:
        cookie.pop("sameSite", None)
        try:
            driver.add_cookie(cookie)
        except Exception:
            pass

    if storage_file.exists():
        for key, value in json.loads(storage_file.read_text()).items():
            driver.execute_script(
                "window.localStorage.setItem(arguments[0], arguments[1]);",
                key,
                value,
            )

    # SPA (k.m. ONGEZA PRO) husoma token ya localStorage wakati wa kuload.
    # Dashboard inaweza kuchelewa server ikiwa na mzigo, kwa hiyo tunasubiri.
    _open_light_page(driver, app)
    end = time.time() + LOGIN_TIMEOUT
    while time.time() < end:
        time.sleep(1)
        try:
            ready = driver.execute_script("return document.readyState") == "complete"
        except Exception:
            ready = False
        if ready:
            break
    time.sleep(2)
    restored = not is_login_page(driver)
    if not restored:
        time.sleep(5)
        restored = not is_login_page(driver)

    print(f"[{app['name']}] Session restore: {'OK' if restored else 'imeisha muda'}")
    return restored


def ensure_logged_in(driver, app):
    """Tumia session iliyohifadhiwa; ikishindikana, login upya."""
    if restore_session(driver, app):
        return
    # Server ikiwa na mzigo login inaweza kukwama (504); jaribu tena mara moja
    try:
        login(driver, app)
    except TimeoutException:
        print(f"[{app['name']}] Login imechelewa, tunajaribu tena...")
        login(driver, app)
