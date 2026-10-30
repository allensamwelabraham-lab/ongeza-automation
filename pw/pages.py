"""Kufungua kurasa na kusoma table kwa Playwright. JS ya kusoma ukurasa ni ileile ya core/pages.py."""

import json
import os
import re

from core.helpers import ERROR_MARKERS
from core.pages import ACTIVE_SORT_JS, PROFILE_JS, ROWS_JS, SORT_ITEMS, with_query
from pw import js
from pw.browser import is_login_page, wait_ready

LIST_WAIT = int(os.getenv("LIST_WAIT", "90"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "90"))  # sekunde za kusubiri jibu la sort/filter


class NotTested(Exception):
    """Test haikuweza kupima (staging haikujibu, ukurasa haukufika). Ripoti: ERROR = Not tested, si Fail."""


def profile(page):
    return js.run(page, PROFILE_JS)


def table_data(page, kind):
    return js.run(page, ROWS_JS, kind)


def page_error(page):
    """Marker ya error (500/404/SQL ...) kwenye ukurasa, au None."""
    try:
        text = page.title() + "\n" + page.inner_text("body", timeout=5000)
    except Exception:
        return None
    return next((m for m in ERROR_MARKERS if m in text), None)


def inertia_props(page):
    """Props za Inertia za ukurasa ulio wazi (data halisi ya server), au None kwa kurasa zisizo Inertia."""
    raw = page.get_attribute("[data-page]", "data-page", timeout=2000) if page.locator("[data-page]").count() else None
    try:
        return json.loads(raw)["props"] if raw else None
    except (ValueError, KeyError):
        return None


def open_page(page, app, path):
    """Fungua ukurasa. Inarudisha (status ya HTTP, marker ya error au None)."""
    url = path if path.startswith("http") else app["base_url"] + path
    try:
        response = page.goto(url, wait_until="domcontentloaded", timeout=REQUEST_TIMEOUT * 1000)
    except Exception as exc:
        raise NotTested(f"ukurasa {url} haukufunguka ndani ya sekunde {REQUEST_TIMEOUT}: "
                        f"{str(exc).splitlines()[0][:150]}") from None
    wait_ready(page)
    status = response.status if response else None
    if status in (502, 503, 504):
        raise NotTested(f"staging imejibu {status} kwa {url}")
    return status, page_error(page)


def open_module(page, app, module, path=None):
    status, error = open_page(page, app, path or module["path"])
    assert not is_login_page(page), f"{module['name']}: imerudisha login page (session imeisha?)"
    if module.get("ignore_error_text") and error and "timeout" not in error.lower():
        error = None
    assert error is None and (status or 200) < 400, (
        f"{module['name']}: error '{error or status}' kwenye {page.url}")
    if module.get("columns") and not path:
        # Table isipojitokeza kabisa, hatukuweza kupima: Not tested, si Fail
        try:
            page.wait_for_function("() => document.querySelector('table thead th, table tr th')",
                                   timeout=LIST_WAIT * 1000)
        except Exception:
            error = page_error(page)
            assert error is None, f"{module['name']}: error '{error}' kwenye {page.url}"
            raise NotTested(f"{module['name']}: table haikujitokeza ndani ya sekunde {LIST_WAIT}") from None
    return profile(page)


def _is_inertia(response):
    return response.request.headers.get("x-inertia") == "true"


def inertia_call(page, action, what):
    """Fanya action (k.m. bofya Sort) na usubiri jibu la Inertia linalofuata. Inarudisha (url ya ombi, props mpya)."""
    try:
        with page.expect_response(_is_inertia, timeout=REQUEST_TIMEOUT * 1000) as info:
            action()
        response = info.value
    except Exception as exc:
        if "Timeout" in type(exc).__name__ or "Timeout" in str(exc):
            raise NotTested(f"{what}: server haikujibu ndani ya sekunde {REQUEST_TIMEOUT}") from None
        raise
    if response.status in (502, 503, 504):
        raise NotTested(f"{what}: staging imejibu {response.status}")
    assert response.status < 400, f"{what}: server imejibu {response.status} ({response.url})"
    # Vue inachora upya baada ya jibu: subiri frame mbili
    page.evaluate("() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
    try:
        return response.url, response.json().get("props")
    except Exception:
        return response.url, None


def wait_inertia(page, action, what):
    """Kama inertia_call, lakini inarudisha props tu."""
    return inertia_call(page, action, what)[1]


# ============================================================
# VUE: SORT / FILTER
# ============================================================

def _toolbar_button(page, label):
    button = page.locator(f"div.ongeza-toolbar button:has-text('{label}')").first
    try:
        button.wait_for(state="visible", timeout=10000)
    except Exception:
        heading = page.locator("h1, h2, h3, .card-header, .panel-heading").first
        seen = heading.inner_text(timeout=2000).strip() if heading.count() else ""
        raise AssertionError(f"Button '{label}' haipo kwenye toolbar ({page.url}); ukurasa unaonyesha "
                             f"'{seen[:60]}' bila table") from None
    return button


def _sort_is(page, key, direction=None):
    active = js.run(page, ACTIVE_SORT_JS, SORT_ITEMS) or []
    if direction is None:
        return any(sort.lstrip("-") == key for _, sort in active)
    want = ("-" if direction == "DESC" else "") + key
    return any(text == direction and sort == want for text, sort in active)


def _pick_sort_item(page, item, what):
    # Menu ikiwa tayari wazi usibofye Sort (ingeifunga)
    open_ = page.evaluate("s => [...document.querySelectorAll(s)].some(e => e.getClientRects().length && "
                          "getComputedStyle(e).visibility !== 'hidden')", SORT_ITEMS)
    if not open_:
        _toolbar_button(page, "Sort").click()
    assert item.count(), f"{what} haipo kwenye dropdown ya Sort"
    # Menu ndefu kuliko table: item ipo lakini imefichwa na mpaka wa table, bofya kwa JS
    wait_inertia(page, lambda: item.first.evaluate("e => e.click()"), what)


def vue_sort(page, key, direction):
    if not _sort_is(page, key):
        _pick_sort_item(page, page.locator(f"{SORT_ITEMS}[data-sort='{key}']"), f"Sort '{key}'")
    if not _sort_is(page, key, direction):
        item = page.locator(SORT_ITEMS).filter(has_text=re.compile(rf"^\s*{direction}\s*$", re.I))
        _pick_sort_item(page, item, f"Sort '{key}' {direction}")
    assert _sort_is(page, key, direction), (
        f"Sort '{key}' {direction} haikubaki: dropdown ya Sort haionyeshi uchaguzi huo (URL: {page.url})")


def vue_filter(page, label, value):
    """Jaza filter ya maandishi (kwa label au placeholder) kisha Apply Filter na subiri jibu la server."""
    panel = page.locator("[id$='-search-block']").first
    if "show" not in (panel.get_attribute("class") or ""):
        _toolbar_button(page, "Filter").click()
        page.wait_for_function("p => p.classList.contains('show')", arg=panel.element_handle(), timeout=5000)
    field = panel.locator(".col").filter(has=page.locator(f"label:text-is('{label}')")).locator(
        "input[type=text], input[type=date], input:not([type])").first
    if not field.count():
        field = panel.locator(f"input[placeholder='{label}' i], input[name='{label}' i], input[id='{label}' i]").first
    assert field.count(), f"Filter '{label}' haipo"
    field.fill(value)
    wait_inertia(page, lambda: panel.locator("button:has-text('Apply Filter')").click(), f"Filter '{label}'")


# ============================================================
# GRID (Yii2): SORT / FILTER ni links/URL
# ============================================================

def grid_sort_url(page, key, descending=False):
    href = page.evaluate("k => { const a = [...document.querySelectorAll('.grid-view thead a[data-sort]')]"
                         ".find(a => a.getAttribute('data-sort').replace(/^-/, '') === k); return a ? a.href : null; }",
                         key)
    return with_query(href, sort=("-" if descending else "") + key) if href else None


def grid_filter(page, name, value):
    field = page.locator(f".grid-view tr.filters [name='{name}']").first
    field.fill(value)
    try:
        with page.expect_navigation(timeout=REQUEST_TIMEOUT * 1000, wait_until="domcontentloaded"):
            field.press("Enter")
    except Exception:
        raise NotTested(f"Filter '{name}': ukurasa haukujipakia upya ndani ya sekunde {REQUEST_TIMEOUT}") from None
    wait_ready(page)
