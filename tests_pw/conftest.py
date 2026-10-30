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


class _ModulePages:
    """Ukurasa mmoja kwa kila module (kwa worker): tests za module hiyo zinaendeshwa mfululizo na kuushiriki,
    kwa hiyo ukurasa haupakiwi upya kwa kila test (open_module inautumia tena ukiwa bado safi)."""

    def __init__(self, browser, storage_state, app):
        self.browser, self.storage_state, self.app = browser, storage_state, app
        self.key = self.context = self.page = self.guard = None

    def get(self, key):
        if key != self.key or self.page is None or self.page.is_closed():
            self.close()
            self.guard = WriteGuard(self.app["base_url"])
            self.context = self.browser.new_context(storage_state=self.storage_state,
                                                    viewport={"width": 1920, "height": 1080}, accept_downloads=True)
            self.guard.install(self.context)
            self.context.tracing.start(screenshots=True, snapshots=True)
            self.page = self.context.new_page()
            self.page.set_default_timeout(PAGE_LOAD_TIMEOUT * 1000)
            self.key = key
        return self.page

    def close(self):
        if self.context is not None:
            try:
                self.context.tracing.stop()
                self.context.close()
            except Exception:
                pass
        self.key = self.context = self.page = None


@pytest.fixture(scope="session")
def module_pages(browser, storage_state, app):
    pages = _ModulePages(browser, storage_state, app)
    yield pages
    pages.close()


def _module_key(item):
    callspec = getattr(item, "callspec", None)
    module = callspec.params.get("module") if callspec else None
    return module["id"] if isinstance(module, dict) else item.nodeid


@pytest.fixture
def page(request, module_pages):
    page = module_pages.get(_module_key(request.node))
    module_pages.guard.take()
    module_pages.context.tracing.start_chunk()
    yield page
    failed = getattr(request.node, "rep_call", None) is not None and request.node.rep_call.failed
    if failed:
        page.clean_module = None  # test iliyoshindwa inaweza kuacha ukurasa katikati
        folder = REPORTS_DIR / "traces"
        folder.mkdir(parents=True, exist_ok=True)
        module_pages.context.tracing.stop_chunk(path=str(folder / f"{_name(request.node)}.zip"))
    else:
        module_pages.context.tracing.stop_chunk()


@pytest.fixture
def guard(page, module_pages):
    return module_pages.guard


# Mpangilio: module kwa module (page_loads kwanza), ili tests za module moja zifuatane na kushiriki ukurasa.
# Na --workers 2: kila module inaenda kwa worker mmoja (xdist_group + --dist loadgroup).
_ORDER = ["test_page_loads", "test_columns", "test_records", "test_view_matches_row", "test_pagination_data",
          "test_sort_all_columns", "test_per_page", "test_pagination", "test_sort", "test_filter_finds_row",
          "test_filter_no_match", "test_filters_all"]


def pytest_collection_modifyitems(config, items):
    def rank(item):
        name = item.originalname or item.name
        return (_module_key(item), _ORDER.index(name) if name in _ORDER else len(_ORDER))

    items.sort(key=rank)
    for item in items:
        item.add_marker(pytest.mark.xdist_group(_module_key(item)))


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
    pages = item.funcargs.get("module_pages")
    guard = pages.guard if pages else None
    if guard and guard.blocked:
        report.sections.append(("write guard", "Imezuiwa: " + ", ".join(guard.blocked[:5])))
