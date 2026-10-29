"""
Page objects za kurasa za ONGEZA/JUMLA/ONGEZA PRO.

Apps hizi zina mitindo miwili ya kurasa za orodha (list pages):

* "vue"  - mtindo mpya (System Version 2.0): toolbar ya Filter / Sort / Per Page /
           Export / + Add, "<b>646</b> records", table.ongeza-table,
           filter panel yenye "Apply Filter".
* "grid" - Yii2 / Kartik GridView: "Showing 1-20 of 152 items.", vichwa vya
           table ni links za sort, mstari wa filter (input name="XSearch[name]"),
           "Create X" link, icons za view / update / delete kwenye kila row.

Kurasa nyingine ni "table" (table ya kawaida, mara nyingi report) au "page"
(form, dashboard, map, n.k.).

Hakuna function hapa inayobofya delete, export, au save.
"""

import re
import time
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from selenium.common.exceptions import (
    InvalidElementStateException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By

from core.config import PAGE_LOAD_TIMEOUT
from selenium.webdriver.common.keys import Keys

from core.helpers import (
    _safe_displayed,
    click,
    find_error_on_page,
    wait_page_ready,
    wait_until,
)


# ============================================================
# PROFILE YA UKURASA (JS moja -> haraka)
# ============================================================

PROFILE_JS = r"""
const vis = el => !!(el && (el.offsetWidth || el.offsetHeight || el.getClientRects().length));
const txt = el => el ? (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim() : '';
const main = document.querySelector('#content, .content, main') || document.body;

let kind = 'page';
const spa = document.querySelector('[data-slot="sidebar-inset"]');
const vueTable = main.querySelector('table.ongeza-table');
const grid = main.querySelector('.grid-view');
if (main.querySelector('.ongeza-toolbar') || vueTable) kind = 'vue';
else if (grid) kind = 'grid';
else if (spa && Array.from(main.querySelectorAll('table')).some(vis)) kind = 'spa';
else if (Array.from(main.querySelectorAll('table')).some(vis)) kind = 'table';

let table = null;
if (kind === 'vue') table = vueTable;
else if (kind === 'grid') table = grid.querySelector('table');
else table = Array.from(main.querySelectorAll('table')).find(vis) || null;

let columns = [];
if (table) {
  const head = table.querySelector('thead tr') || table.querySelector('tr');
  if (head) columns = Array.from(head.querySelectorAll('th,td')).map(txt).filter(t => t);
}

let rows = 0, emptyText = '';
if (table) {
  const trs = Array.from(table.querySelectorAll('tbody tr')).filter(vis);
  const empty = trs.filter(tr => tr.querySelector('.empty') || /no results|no data|no records/i.test(txt(tr)) && tr.children.length === 1);
  // ONGEZA PRO: header ina checkbox column tupu
  if (kind === 'spa') columns = columns.filter(c => c);
  emptyText = empty.length ? txt(empty[0]) : '';
  rows = trs.length - empty.length;
}

let total = null;
const rc = main.querySelector('.ongeza-record-count b');
if (rc) total = parseInt(txt(rc).replace(/[^0-9]/g, ''), 10);
const summary = main.querySelector('.grid-view .summary');
if (summary) {
  const bs = summary.querySelectorAll('b');
  if (bs.length) total = parseInt(txt(bs[bs.length - 1]).replace(/[^0-9]/g, ''), 10);
}

let heading = '';
for (const sel of ['main main h1', '.panel-title', '.card-title', '.panel-heading h4', 'h2', 'h3', 'h4']) {
  const el = Array.from(main.querySelectorAll(sel)).find(e => vis(e) && txt(e));
  if (el) { heading = txt(el); break; }
}

// Sort
let sortKeys = [];
if (kind === 'grid' && table) sortKeys = Array.from(table.querySelectorAll('thead a[data-sort]')).map(a => a.getAttribute('data-sort').replace(/^-/, ''));
if (kind === 'vue') sortKeys = Array.from(main.querySelectorAll('li[data-sort]')).map(li => li.getAttribute('data-sort'));

// Filters
let filters = [];
if (kind === 'grid') filters = Array.from(main.querySelectorAll('.grid-view tr.filters [name]')).map(e => ({name: e.getAttribute('name'), tag: e.tagName.toLowerCase(), type: e.type || ''}));
if (kind === 'vue') filters = Array.from(main.querySelectorAll('[id$="-search-block"] input, [id$="-search-block"] select')).map(e => ({name: e.id || e.getAttribute('placeholder') || '', tag: e.tagName.toLowerCase(), type: e.type || '', label: txt(e.closest('.col') && e.closest('.col').querySelector('label'))}));

// Create
let createHref = null, addButton = null;
const createA = Array.from(main.querySelectorAll('a[href]')).find(a => vis(a) && /\/create[a-z-]*(\?|$)/i.test(a.getAttribute('href')) && !/\/view|update/i.test(a.getAttribute('href')));
if (createA) { createHref = createA.getAttribute('href'); addButton = txt(createA); }
if (!addButton) {
  const b = Array.from(main.querySelectorAll('.ongeza-toolbar-actions button, .ongeza-toolbar-actions a')).find(e => vis(e) && /add|create|new/i.test(txt(e)));
  if (b) addButton = txt(b);
}

// View links
let viewHref = null, vueView = false;
if (table) {
  const v = table.querySelector('tbody a[href*="/view"], tbody a[href$="/details"]');
  if (v) viewHref = v.getAttribute('href');
  if (table.querySelector('tbody a[class*="-view"][data-id]')) vueView = true;
}

const pag = Array.from(main.querySelectorAll('ul.pagination a.page-link[href*="page="]')).map(a => a.getAttribute('href'));
let pageCount = null;
if (kind === 'vue' && total !== null && rows) pageCount = Math.ceil(total / rows);

return {
  kind, heading, columns, rows, total, emptyText,
  sortKeys, filters, createHref, addButton, viewHref, vueView,
  hasPagination: pag.length > 0, pageCount,
  title: document.title,
};
"""


def profile(driver):
    """Rudisha dict yenye muundo wa ukurasa wa sasa (aina, columns, total ...)."""
    return driver.execute_script(PROFILE_JS)


# ============================================================
# KUFUNGUA UKURASA
# ============================================================

def open_page(driver, app, path, timeout=60):
    url = path if path.startswith("http") else app["base_url"] + path
    try:
        driver.get(url)
    except TimeoutException:
        try:
            driver.execute_script("window.stop();")
        except Exception:
            pass
        return f"Page load timeout (>{PAGE_LOAD_TIMEOUT}s)"
    try:
        wait_page_ready(driver, timeout=timeout)
    except Exception:
        pass
    # SPA (ONGEZA PRO): subiri maudhui ya <main> yatulie (data inaletwa kwa API)
    if driver.execute_script("return !!document.querySelector('[data-slot=\"sidebar-inset\"]')"):
        _wait_content_stable(driver)

    # Vue pages hujaza table baada ya readyState
    wait_until(
        driver,
        lambda d: d.execute_script(
            "return !document.querySelector('.ongeza-toolbar') || "
            "!!document.querySelector('table.ongeza-table tbody tr, .ongeza-record-count b')"
        ),
        timeout=15,
    )
    return find_error_on_page(driver)


def _wait_content_stable(driver, timeout=20, quiet=1.5):
    end = time.time() + timeout
    last, since = None, time.time()
    while time.time() < end:
        try:
            size = driver.execute_script(
                "const m = document.querySelector('main main') || document.body;"
                "return m.innerText.length + ':' + m.querySelectorAll('tr').length;"
            )
        except Exception:
            size = None
        if size != last:
            last, since = size, time.time()
        elif time.time() - since >= quiet:
            return
        time.sleep(0.3)


def with_query(url, **params):
    """Ongeza/badilisha query params kwenye URL."""
    parts = urlparse(url)
    query = parse_qs(parts.query, keep_blank_values=True)
    for key, value in params.items():
        query[key] = [str(value)]
    return urlunparse(parts._replace(query=urlencode(query, doseq=True)))


# ============================================================
# TABLE
# ============================================================

ROWS_JS = r"""
const kind = arguments[0];
const main = document.querySelector('#content, .content, main') || document.body;
let table = kind === 'vue' ? main.querySelector('table.ongeza-table')
          : kind === 'spa' ? Array.from(main.querySelectorAll('table')).find(t => t.offsetWidth)
          : kind === 'grid' ? main.querySelector('.grid-view table')
          : Array.from(main.querySelectorAll('table')).find(t => t.offsetWidth);
if (!table) return [];
return Array.from(table.querySelectorAll('tbody tr'))
  .filter(tr => tr.offsetWidth && !tr.querySelector('.empty') && tr.children.length > 1)
  .map(tr => Array.from(tr.children).map(td => (td.innerText || '').replace(/\s+/g, ' ').trim()));
"""


def table_data(driver, kind):
    """Rows za table kama list ya lists za maandishi."""
    return driver.execute_script(ROWS_JS, kind)


def column_values(driver, kind, column_index):
    return [r[column_index] for r in table_data(driver, kind) if len(r) > column_index]


def column_index(columns, *names):
    lowered = [c.strip().lower() for c in columns]
    for name in names:
        if name.lower() in lowered:
            return lowered.index(name.lower())
    return None


# ============================================================
# GRID (Yii2) - SORT / FILTER
# ============================================================

def grid_sort_url(driver, key, descending=False):
    for a in driver.find_elements(By.CSS_SELECTOR, ".grid-view thead a[data-sort]"):
        if a.get_attribute("data-sort").lstrip("-") == key:
            return with_query(a.get_attribute("href"), sort=("-" if descending else "") + key)
    return None


def grid_filter(driver, name, value, timeout=60):
    """Andika kwenye filter ya GridView na subiri ukurasa ujipakie upya."""
    field = driver.find_element(By.CSS_SELECTOR, f".grid-view tr.filters [name='{name}']")
    old_url = driver.current_url
    field.clear()
    field.send_keys(value)
    field.send_keys(Keys.ENTER)
    wait_until(driver, lambda d: d.current_url != old_url, timeout=timeout)
    wait_page_ready(driver, timeout=timeout)


# ============================================================
# VUE - SORT / FILTER / PER PAGE
# ============================================================

def _vue_dropdown_pick(driver, toolbar_label, item_css, item_text=None, attr=None, value=None):
    # Vue ikiwa bado inajipakia upya, dropdown inachorwa upya: item inakuwa "stale" au menu
    # inajifunga. Jaribu tena (hadi mara 3) kwa kutafuta button na items upya.
    for attempt in range(3):
        try:
            if _vue_dropdown_pick_once(driver, toolbar_label, item_css, item_text, attr, value):
                return True
        except StaleElementReferenceException:
            if attempt == 2:
                raise
        if attempt < 2:
            time.sleep(2)
    return False


def _vue_dropdown_pick_once(driver, toolbar_label, item_css, item_text=None, attr=None, value=None):
    # Menu ikiwa tayari wazi (jaribio lililopita), usibofye button - ingeifunga
    if not any(_safe_displayed(i) for i in driver.find_elements(By.CSS_SELECTOR, item_css)):
        button = driver.find_element(
            By.XPATH,
            f"//div[contains(@class,'ongeza-toolbar')]//button[contains(normalize-space(),'{toolbar_label}')]",
        )
        click(driver, button)
        time.sleep(0.5)
    for item in driver.find_elements(By.CSS_SELECTOR, item_css):
        if not item.is_displayed():  # stale hapa inapanda juu ili _vue_dropdown_pick ijaribu tena
            continue
        if attr and item.get_attribute(attr) == str(value):
            click(driver, item)
            return True
        if item_text and item.text.strip().upper() == item_text.upper():
            click(driver, item)
            return True
    return False


def wait_vue_reload(driver, before_rows, timeout=30):
    """Subiri table ya vue ibadilike (au angalau loader iishe)."""
    wait_until(driver, lambda d: table_data(d, "vue") != before_rows, timeout=timeout)
    time.sleep(0.5)


SORT_ITEMS = "li[class*='sort-dropdown-item']"
ACTIVE_SORT_JS = """
return Array.from(document.querySelectorAll(arguments[0]))
  .filter(li => li.classList.contains('active'))
  .map(li => [li.textContent.trim().toUpperCase(), li.getAttribute('data-sort') || '']);
"""


def _sort_is(driver, key, direction=None):
    """Dropdown inaonyesha sort ya sasa (class 'active' kutoka kwa server) = key (na direction)?"""
    active = driver.execute_script(ACTIVE_SORT_JS, SORT_ITEMS) or []
    if direction is None:
        return any(sort.lstrip("-") == key for _, sort in active)
    want = ("-" if direction == "DESC" else "") + key
    return any(text == direction and sort == want for text, sort in active)


INERTIA_TRACK_JS = """
if (!window.__autoInertia) {
  window.__autoInertia = {started: 0, busy: 0};
  document.addEventListener('inertia:start', () => { window.__autoInertia.started++; window.__autoInertia.busy++; });
  document.addEventListener('inertia:finish', () => { window.__autoInertia.busy = Math.max(0, window.__autoInertia.busy - 1); });
}
return window.__autoInertia.started;
"""


def _inertia_state(driver):
    return driver.execute_script("return window.__autoInertia || {started: 0, busy: 0};")


def vue_sort(driver, key, direction="ASC", timeout=60):
    """Chagua sort (key kisha ASC/DESC) na subiri ombi la server liishe kabla ya hatua inayofuata.
    Staging ni nzito: kubofya ASC kabla ombi la key halijaisha kunalikatiza (sort inapotea)."""
    for want_direction in (None, direction):
        if _sort_is(driver, key, want_direction):
            continue  # tayari imechaguliwa (k.m. ASC baada ya kuchagua ID)
        for attempt in range(3):
            started = driver.execute_script(INERTIA_TRACK_JS)
            if want_direction is None:
                picked = _vue_dropdown_pick(driver, "Sort", SORT_ITEMS, attr="data-sort", value=key)
                assert picked, f"Sort '{key}' haipo"
            else:
                picked = _vue_dropdown_pick(driver, "Sort", SORT_ITEMS, item_text=want_direction)
                assert picked, f"Sort {want_direction} haipo"

            def applied(d):
                state = _inertia_state(d)
                return state["started"] > started and state["busy"] == 0 and _sort_is(d, key, want_direction)
            if wait_until(driver, applied, timeout=timeout):
                break
        else:
            raise AssertionError(
                f"Sort '{key}'{' ' + want_direction if want_direction else ''} haikubaki: dropdown ya Sort "
                f"haionyeshi uchaguzi huo hata baada ya kubofya mara 3 (URL: {driver.current_url})"
            )
    time.sleep(0.5)


def vue_per_page(driver, size):
    before = table_data(driver, "vue")
    assert _vue_dropdown_pick(driver, "Per Page", "li[class*='per-page-dropdown-item']",
                              attr="data-per-page", value=size), f"Per Page {size} haipo"
    wait_vue_reload(driver, before)


def vue_open_filter(driver):
    panel = driver.find_element(By.CSS_SELECTOR, "[id$='-search-block']")
    if "show" not in (panel.get_attribute("class") or ""):
        click(driver, driver.find_element(
            By.XPATH, "//div[contains(@class,'ongeza-toolbar')]//button[contains(normalize-space(),'Filter')]"))
        wait_until(driver, lambda d: "show" in (panel.get_attribute("class") or ""), timeout=5)
        time.sleep(0.5)
    return panel


def vue_filter_text(driver, label, value):
    """Jaza filter ya maandishi (kwa label) kisha 'Apply Filter'."""
    vue_filter_inputs(driver, {label: value})


def vue_filter_inputs(driver, values):
    """Jaza filters kadhaa {label: thamani} kisha 'Apply Filter'."""
    panel = vue_open_filter(driver)
    for label, value in values.items():
        field = None
        for col in panel.find_elements(By.CSS_SELECTOR, ".col"):
            labels = col.find_elements(By.TAG_NAME, "label")
            inputs = col.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='date'], input:not([type])")
            if labels and inputs and labels[0].text.strip().lower() == label.lower():
                field = inputs[0]
                break
        if field is None:
            # Filter isiyo na <label> (k.m. Invalid Payments: ID) - tafuta kwa placeholder/name
            text = label.replace("'", "\\'")
            found = panel.find_elements(By.CSS_SELECTOR, f"input[placeholder='{text}' i], input[name='{text}' i], input[id='{text}' i]")
            field = found[0] if found else None
        assert field is not None, f"Filter '{label}' haipo"
        try:
            field.clear()
            field.send_keys(value)
            field.send_keys(Keys.ESCAPE)  # funga datepicker ikiwa imefunguka
        except InvalidElementStateException:
            # Datepicker za readonly: weka thamani kwa JS na mjulishe Vue
            driver.execute_script(
                "arguments[0].value = arguments[1];"
                "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
                "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                field, value,
            )
    before = table_data(driver, "vue")
    click(driver, panel.find_element(By.XPATH, ".//button[contains(normalize-space(),'Apply Filter')]"))
    wait_vue_reload(driver, before)


def vue_reset_filter(driver):
    panel = vue_open_filter(driver)
    before = table_data(driver, "vue")
    click(driver, panel.find_element(By.XPATH, ".//button[contains(normalize-space(),'Reset')]"))
    wait_vue_reload(driver, before)


def record_total(driver):
    return profile(driver)["total"]


# ============================================================
# MAANDISHI YA TAREHE / NAMBA (kwa kuthibitisha sort)
# ============================================================

def as_number(text):
    cleaned = re.sub(r"[^0-9.\-]", "", text or "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def is_sorted(values, descending=False):
    nums = [as_number(v) for v in values]
    if values and all(n is not None for n in nums):
        seq = nums
    else:
        seq = [v.lower() for v in values]
    return seq == sorted(seq, reverse=descending)
