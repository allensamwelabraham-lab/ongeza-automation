import os

import pytest

from core.config import RUN_BUTTONS, RUN_CRUD, get_app
from core.driver import create_driver
from core.session import ensure_logged_in


# ============================================================
# DRIVER MOJA ILIYO-LOGIN KWA KILA APP (inatumika na tests zote)
# ============================================================

@pytest.fixture(scope="session")
def _browsers():
    browsers = {}
    yield browsers
    for driver in browsers.values():
        driver.quit()


@pytest.fixture
def app(app_key):
    # app_key inatoka kwenye tests/<app>/conftest.py
    return get_app(app_key)


@pytest.fixture
def driver(_browsers, app):
    old = _browsers.get(app["key"])
    if old is not None:
        # Browser ikikwama au kufa (k.m. renderer imeganda), anzisha mpya ili
        # tests zinazofuata zisishindwe zote kwa sababu ya browser moja.
        try:
            old.set_script_timeout(20)
            old.execute_script("return 1")
        except Exception:
            print(f"[{app['name']}] browser imekwama -> naanzisha mpya")
            try:
                old.quit()
            except Exception:
                pass
            del _browsers[app["key"]]
    if app["key"] not in _browsers:
        browser = create_driver()
        ensure_logged_in(browser, app)
        _browsers[app["key"]] = browser
    return _browsers[app["key"]]


@pytest.fixture
def fresh_driver():
    """Browser mpya isiyo na session (kwa login tests)."""
    browser = create_driver()
    yield browser
    browser.quit()


# ============================================================
# CRUD TESTS ZINAENDESHWA TU RUN_CRUD=1
# ============================================================

def pytest_collection_modifyitems(config, items):
    skip_crud = pytest.mark.skip(reason="CRUD test: weka RUN_CRUD=1 kuiendesha")
    skip_buttons = pytest.mark.skip(reason="Test ya buttons: weka RUN_BUTTONS=1 (--buttons) kuiendesha")

    # tools.run_module inaweka MODULE_IDS: endesha modules hizo tu, kwa id kamili. "-k" peke yake
    # inalinganisha sehemu ya jina, kwa hiyo crud_ticket_index ingeendesha pia crud_ticket_indexall.
    wanted = {i for i in os.getenv("MODULE_IDS", "").split(",") if i}
    if wanted:
        keep, drop = [], []
        for item in items:
            module = getattr(item, "callspec", None) and item.callspec.params.get("module")
            if isinstance(module, dict) and module.get("id") not in wanted:
                drop.append(item)
            else:
                keep.append(item)
        if drop:
            config.hook.pytest_deselected(items=drop)
            items[:] = keep

    for item in items:
        if "crud" in item.keywords and not RUN_CRUD:
            item.add_marker(skip_crud)
        if "buttons" in item.keywords and not RUN_BUTTONS:
            item.add_marker(skip_buttons)


# ============================================================
# SCREENSHOT TEST IKISHINDWA -> reports/screenshots/
# ============================================================

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or not report.failed:
        return

    browser = item.funcargs.get("driver") or item.funcargs.get("fresh_driver")
    if browser is None:
        return

    from core.config import REPORTS_DIR

    folder = REPORTS_DIR / "screenshots"
    folder.mkdir(parents=True, exist_ok=True)
    name = "".join(c if c.isalnum() or c in "-_" else "_" for c in item.nodeid)
    path = folder / f"{name}.png"
    try:
        _wait_page_settled(browser)
        browser.save_screenshot(str(path))
        report.sections.append(("screenshot", str(path)))
    except Exception:
        pass


# Ukurasa ukiwa bado unapakia (progress bar, spinner, ukurasa umefifia), picha ingeonyesha
# ukurasa usiokamilika. Subiri (hadi SCREENSHOT_WAIT sekunde) utulie kabla ya kupiga picha.
SETTLED_JS = r"""
if (document.readyState !== 'complete') return false;
if (window.jQuery && jQuery.active > 0) return false;
const shown = e => { const s = getComputedStyle(e);
    return e.getClientRects().length && s.display !== 'none' && s.visibility !== 'hidden' && +s.opacity > 0.05; };
if ([...document.querySelectorAll('.pace-running, .pace-active, .nprogress-busy, #nprogress, ' +
        '.fa-spin, .spinner, .spinner-border, .loading, .loader, .preloader, .blockUI, .swal2-loading')]
        .some(shown)) return false;
for (const e of [document.documentElement, document.body, document.querySelector('main, #content, .content')])
    if (e && +getComputedStyle(e).opacity < 0.95) return false;
return true;
"""


def _wait_page_settled(driver):
    import os
    import time
    end = time.time() + float(os.getenv("SCREENSHOT_WAIT", "20"))
    calm = 0
    while time.time() < end:
        try:
            calm = calm + 1 if driver.execute_script(SETTLED_JS) else 0
        except Exception:
            calm = 0
        if calm >= 2:  # imetulia kwa ukaguzi 2 mfululizo
            return
        time.sleep(0.5)

