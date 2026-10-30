"""Browser, login moja (storage state) na write guard ya network."""

import os
import re
import time
from urllib.parse import urlparse

from core.config import HEADLESS, LOGIN_TIMEOUT, PAGE_LOAD_TIMEOUT, SESSIONS_DIR, get_credentials

# POST za KUSOMA (list/search/report) zinaruhusiwa; nyingine zote zinazuiwa na guard
READ_POST = re.compile(r"/(list|search|index\d*|data|datatable|filter|report\w*|view|show|details|options|lookup|"
                       r"autocomplete|count|summary|stats|preview-?list)/?$", re.I)
SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


def launch(playwright):
    """Chromium ya Playwright; CHROME_BINARY ikiwekwa, tumia browser hiyo."""
    options = {"headless": HEADLESS or os.getenv("CI") == "1"}
    binary = os.getenv("CHROME_BINARY")
    if binary:
        options["executable_path"] = binary
    return playwright.chromium.launch(**options)


def state_file(app):
    folder = SESSIONS_DIR / app["key"]
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "pw_state.json"


def is_login_page(page):
    try:
        return page.locator("input[type=password]:visible").count() > 0
    except Exception:
        return False


def login(browser, app):
    """Ingia kwa username/password na uhifadhi session (cookies + localStorage) kwa run nzima."""
    username, password = get_credentials(app["key"])
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()
    page.set_default_timeout(PAGE_LOAD_TIMEOUT * 1000)
    page.goto(app["base_url"], wait_until="domcontentloaded")
    page.fill("input[placeholder=Username]", username)
    page.fill("input[type=password]", password)
    # Jibu la Login ndilo linaunda session; Dashboard inayofuata ni nzito, haisubiriwi
    with page.expect_response(lambda r: r.request.method == "POST", timeout=LOGIN_TIMEOUT * 1000):
        page.click("button:has-text('Login')")
    page.goto(app["base_url"] + app.get("light_page", "/"), wait_until="domcontentloaded")
    if is_login_page(page):
        context.close()
        raise RuntimeError(f"{app['name']}: login imeshindwa (bado iko kwenye login page). Hakikisha password kwenye .env")
    context.storage_state(path=str(state_file(app)))
    context.close()
    print(f"[{app['name']}] LOGIN SUCCESSFUL, session imehifadhiwa {state_file(app)}")


def session_works(browser, app):
    path = state_file(app)
    if not path.exists():
        return False
    context = browser.new_context(storage_state=str(path))
    try:
        page = context.new_page()
        page.goto(app["base_url"] + app.get("light_page", "/"), wait_until="domcontentloaded",
                  timeout=PAGE_LOAD_TIMEOUT * 1000)
        return not is_login_page(page)
    except Exception:
        return False
    finally:
        context.close()


def ensure_session(browser, app):
    if not session_works(browser, app):
        login(browser, app)
    return str(state_file(app))


class WriteGuard:
    """Inazuia kila ombi la kubadilisha data (POST/PUT/PATCH/DELETE) kwenda kwenye app, kwenye network.
    Tofauti na guard ya JS, inashika pia forms, iframes, sendBeacon na redirects."""

    def __init__(self, base_url):
        self.host = urlparse(base_url).netloc
        self.enabled = True
        self.blocked = []

    def install(self, context):
        # Maombi ya app hii tu yanapita kwenye guard (CDN, fonts n.k. hayaguswi).
        # Tahadhari: kwenye sync API, handler inaendeshwa tu tukiwa ndani ya call ya Playwright, kwa hiyo
        # tumia page.wait_for_timeout(), kamwe time.sleep(), la sivyo maombi yanasimama.
        context.route(re.compile(r"^https?://" + re.escape(self.host) + r"(/|$)"), self._handle)

    def _handle(self, route):
        request = route.request
        url = urlparse(request.url)
        if (self.enabled and request.method not in SAFE_METHODS
                and not (request.method == "POST" and READ_POST.search(url.path))):
            self.blocked.append(f"{request.method} {url.path}")
            route.abort("blockedbyclient")
            return
        route.continue_()

    def take(self):
        out, self.blocked = self.blocked, []
        return out


def wait_ready(page, timeout=30):
    """Subiri ukurasa umalize kuload na table ya vue ijae. Hatusubiri "networkidle": kurasa zenye
    polling hazitulii kamwe, na hiyo ilikuwa inaongeza sekunde 15 kwa kila ukurasa."""
    try:
        page.wait_for_load_state("load", timeout=timeout * 1000)
    except Exception:
        pass
    try:
        page.wait_for_function(
            "() => !document.querySelector('.ongeza-toolbar') || "
            "!!document.querySelector('table.ongeza-table tbody tr, .ongeza-record-count b')",
            timeout=15000)
    except Exception:
        pass


def elapsed(start):
    return time.time() - start
