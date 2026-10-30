"""
Fixtures za Playwright. App inachaguliwa na PW_APP (tools.run_module --engine pw inaiweka).

Kila test inapata context mpya (session ileile ya login, cookies safi) yenye write guard ya network.
Test ikishindwa: screenshot ya wakati huo -> reports/screenshots/, trace -> reports/traces/
(fungua kwa:  python -m playwright show-trace reports/traces/<jina>.zip).
"""

import os

import pytest
from playwright.sync_api import sync_playwright

from core.config import PAGE_LOAD_TIMEOUT, REPORTS_DIR, get_app
from pw.browser import WriteGuard, ensure_session, launch, state_file

try:
    import fcntl
except ImportError:  # Windows: hakuna lock, workers wanaweza kulogin wote
    fcntl = None


def _name(item):
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in item.nodeid)


@pytest.fixture(scope="session")
def app():
    key = os.getenv("PW_APP")
    if not key:
        pytest.exit("Weka PW_APP (k.m. PW_APP=ongeza) au tumia: bash run.sh --app ongeza --engine pw ...")
    return get_app(key)


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as playwright:
        browser = launch(playwright)
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def storage_state(browser, app):
    # Workers wawili (--workers 2) wasilogin pamoja: wa pili anasubiri na kutumia session ya wa kwanza
    lock_path = state_file(app).with_suffix(".lock")
    with open(lock_path, "w") as lock:
        if fcntl:
            fcntl.flock(lock, fcntl.LOCK_EX)
        return ensure_session(browser, app)


@pytest.fixture
def guard(app):
    return WriteGuard(app["base_url"])


@pytest.fixture
def page(request, browser, storage_state, guard):
    context = browser.new_context(storage_state=storage_state, viewport={"width": 1920, "height": 1080},
                                  accept_downloads=True)
    guard.install(context)
    context.tracing.start(screenshots=True, snapshots=True)
    page = context.new_page()
    page.set_default_timeout(PAGE_LOAD_TIMEOUT * 1000)
    yield page
    failed = getattr(request.node, "rep_call", None) is not None and request.node.rep_call.failed
    if failed:
        folder = REPORTS_DIR / "traces"
        folder.mkdir(parents=True, exist_ok=True)
        context.tracing.stop(path=str(folder / f"{_name(request.node)}.zip"))
    else:
        context.tracing.stop()
    context.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return
    item.rep_call = report
    page = item.funcargs.get("page")
    if not report.failed or page is None:
        return
    # Screenshot sasa hivi, kabla context haijafungwa: inaonyesha ukurasa kama ulivyokuwa kosa lilipotokea
    folder = REPORTS_DIR / "screenshots"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{_name(item)}.png"
    try:
        page.screenshot(path=str(path), timeout=15000)
        report.sections.append(("screenshot", str(path)))
    except Exception as exc:
        report.sections.append(("screenshot", f"haikupigwa: {exc}"))
    guard = item.funcargs.get("guard")
    if guard and guard.blocked:
        report.sections.append(("write guard", "Imezuiwa: " + ", ".join(guard.blocked[:5])))
