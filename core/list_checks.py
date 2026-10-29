"""
Checks za kina kwa kila module (list page) kwa kutumia baseline ya
modules/<app>.json (iliyoandikwa na `python -m tools.discover`).

Kila check inafanya kazi kwa mitindo yote miwili ya kurasa (vue na grid);
angalia core/pages.py. Form tests zinaweka write guard (core/guard.py) kabla ya kubofya
Save, isipokuwa check_create_form_saves (RUN_CRUD=1 tu) ambayo inajaza na kusave data ya AUTO.
"""

import math
import os
import re
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

import pytest
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

from core.config import PAGE_LOAD_TIMEOUT
from core.form_fill import (
    EDIT_WORDS,
    FORM_SCOPE,
    NOT_FILLED,
    _set_js,
    find_save_button,
    fill_form,
    fix_from_validation,
    validation_messages,
)
from core.guard import (
    blocked_writes,
    describe_server_responses,
    install_write_guard,
    record_server_responses,
    server_error_messages,
    server_responses,
)
from core.helpers import (
    click,
    describe_form,
    find_error_on_page,
    find_submit_button,
    validation_shown,
    wait_until,
)
from core.modules import load_modules
from core.pages import (
    column_index,
    grid_filter,
    grid_sort_url,
    is_sorted,
    open_page,
    profile,
    table_data,
    vue_filter_text,
    vue_sort,
    with_query,
)
from core.session import ensure_logged_in, is_login_page


NO_MATCH = "AUTO-NO-MATCH-9876"
NOT_WRITTEN = NOT_FILLED + ("(imeshindwa kurekebisha",)  # thamani zisizoandikwa kwenye fomu
SORT_TIMEOUT = 60  # sekunde za kusubiri table ya vue ipangwe upya baada ya kuchagua sort


def actual(text):
    """Matokeo halisi ya hatua; tools.run_module inayaweka kwenye ripoti."""
    print(f"ACTUAL: {text}")


# ============================================================
# PARAMETERS
# ============================================================

def params(app_key, predicate=lambda m: True, reason="hakuna module inayofaa"):
    modules = [m for m in load_modules(app_key) if predicate(m)]
    if not modules:
        return [pytest.param(None, id="none", marks=pytest.mark.skip(
            reason=f"{reason} (modules/{app_key}.json). Endesha: python -m tools.discover --app {app_key}"
        ))]
    return [pytest.param(m, id=m["id"]) for m in modules]


def is_list(m):
    return m.get("kind") in ("vue", "grid", "spa") and not m.get("error")


def is_paged_list(m):
    # ONGEZA PRO (spa) haina pagination/sort/filter tunazoweza kutumia kwa sasa
    return m.get("kind") in ("vue", "grid") and not m.get("error")


def has_rows(m):
    return is_list(m) and (m.get("rows") or 0) > 0


def has_more_pages(m):
    return has_rows(m) and is_paged_list(m) and (m.get("total") or 0) > (m.get("rows") or 0)


def has_sort(m):
    return has_rows(m) and is_paged_list(m) and bool(m.get("sort_keys"))


def has_text_filter(m):
    return has_rows(m) and is_paged_list(m) and _text_filter(m) is not None


def has_view(m):
    return has_rows(m) and (m.get("view_href") or m.get("vue_view"))


def has_create(m):
    return bool(m.get("create_path")) and not m.get("create_error")


# Fomu ambazo --crud haizisavi kwa default: zinatuma SMS/notifications kwa watu,
# zinarekodi malipo, au zinabadilisha menu ya mfumo. Weka "crud_save": true
# kwenye modules/<app>.json kuiruhusu module moja.
# ONGEZA PRO: mauzo, malipo, stock, orders na budgets ni miamala ya fedha inayoweza kwenda Zoho.
CRUD_SAVE_EXCLUDE = re.compile(r"workernotification|sms_outbox|gcm|payment|paygtoken|^menu_|upload|import"
                               r"|^sales_list|^stock_pending|^customer_orders|^budget_expenses")


def can_save(m):
    if not has_create(m):
        return False
    if "crud_save" in m:
        return bool(m["crud_save"])
    return not CRUD_SAVE_EXCLUDE.search(m["id"])


# ============================================================
# HELPERS
# ============================================================

def open_module(driver, app, module, path=None):
    error = open_page(driver, app, path or module["path"])
    if is_login_page(driver):
        ensure_logged_in(driver, app)
        error = open_page(driver, app, path or module["path"])
    assert not is_login_page(driver), f"{module['name']}: imerudisha login page"
    # Kurasa kama "Error Logs" zinaonyesha maandishi ya errors kama data
    if module.get("ignore_error_text") and error and "timeout" not in error.lower():
        error = None
    assert error is None, f"{module['name']}: error '{error}' kwenye {driver.current_url}"
    return profile(driver)


def _norm(text):
    return " ".join((text or "").split()).lower()


def _text_filter(module):
    """Filter ya maandishi tunayoweza kutumia, na column yake kwenye table."""
    columns = module.get("columns") or []
    preferred = ["id", "name", "first name", "first_name", "serial number", "serial_number",
                 "order number", "order_number", "username", "phone", "description"]
    filters = module.get("filters") or []

    for want in preferred:
        for f in filters:
            if f.get("tag") != "input" or f.get("type") not in ("text", ""):
                continue
            if module["kind"] == "grid":
                key = (f.get("name") or "").split("[")[-1].rstrip("]").replace("_", " ")
                label = key
            else:
                label = (f.get("label") or f.get("name") or "")
                key = label.replace("_", " ")
            if _norm(key) != want.replace("_", " "):
                continue
            col = column_index(columns, key, key.replace(" ", "_"), key.title())
            if col is None and _norm(key) == "name":
                col = column_index(columns, "full name", "customer", "worker")
            if col is not None:
                return {"filter": f, "label": label, "column": col}
    return None


# ============================================================
# 1. UKURASA UNAFUNGUKA KAMA BASELINE
# ============================================================

def check_page_matches_baseline(driver, app, module):
    start = time.time()
    info = open_module(driver, app, module)
    seconds = time.time() - start

    assert info["kind"] == module["kind"], (
        f"{module['name']}: aina ya ukurasa imebadilika {module['kind']} -> {info['kind']}"
    )
    if module.get("heading"):
        assert _norm(info["heading"]) == _norm(module["heading"]), (
            f"{module['name']}: heading '{info['heading']}' (ilikuwa '{module['heading']}')"
        )
    # Kurasa zinazochukua muda mrefu sana ni ishara ya tatizo
    limit = max(90, (module.get("load_seconds") or 0) * 3)
    assert seconds < limit, f"{module['name']}: imechukua {seconds:.0f}s kuload (limit {limit:.0f}s)"
    actual(f"Ukurasa '{info['heading']}' umefunguka kwa sekunde {seconds:.1f} bila error")


# ============================================================
# 2. COLUMNS ZA TABLE
# ============================================================

def check_columns(driver, app, module):
    info = open_module(driver, app, module)
    current = {_norm(c) for c in info["columns"]}
    missing = [c for c in module.get("columns") or [] if _norm(c) not in current]
    assert not missing, f"{module['name']}: columns zimepotea {missing}"
    actual(f"Columns {len(info['columns'])} zipo: {', '.join(info['columns'])}")


# ============================================================
# 3. RECORDS / ROWS
# ============================================================

def check_records(driver, app, module):
    info = open_module(driver, app, module)
    if module.get("total") is not None:
        assert info["total"] is not None, f"{module['name']}: idadi ya records haionekani"
    if (module.get("rows") or 0) > 0:
        assert info["rows"] > 0, f"{module['name']}: table iko tupu (ilikuwa na rows {module['rows']})"
        if info["total"] is not None:
            assert info["total"] >= info["rows"], (
                f"{module['name']}: total {info['total']} < rows {info['rows']}"
            )

    # Kila row iwe na idadi sawa ya cells na columns
    data = table_data(driver, module["kind"])
    if data and info["columns"]:
        bad = [i for i, r in enumerate(data) if len(r) < len(info["columns"]) - 1]
        assert not bad, f"{module['name']}: rows {bad[:5]} hazina cells za kutosha"
    actual(f"Records {info['total'] if info['total'] is not None else '-'}; rows {info['rows']} kwenye page 1")


# ============================================================
# 4. PAGINATION
# ============================================================

def check_pagination(driver, app, module):
    open_module(driver, app, module)
    first_page = table_data(driver, module["kind"])

    info = open_module(driver, app, module, with_query(driver.current_url, page=2))
    second_page = table_data(driver, module["kind"])

    assert info["rows"] > 0, f"{module['name']}: page 2 iko tupu"
    assert second_page != first_page, f"{module['name']}: page 2 ni sawa na page 1"
    actual(f"Page 2 ina rows {info['rows']}, tofauti na page 1")


# ============================================================
# 5. SORT
# ============================================================

def check_sort(driver, app, module):
    key = "id" if "id" in module["sort_keys"] else module["sort_keys"][0]
    col = column_index(module.get("columns") or [], key, key.replace("_", " "))

    open_module(driver, app, module)
    if profile(driver)["rows"] <= 1:
        pytest.skip(f"{module['name']}: table ina row {profile(driver)['rows']} tu, sort haiwezi kupimwa")
    if module["kind"] == "grid":
        for descending in (False, True):
            url = grid_sort_url(driver, key, descending)
            assert url, f"{module['name']}: link ya sort '{key}' haipo"
            info = open_module(driver, app, module, url)
            assert info["rows"] > 0, f"{module['name']}: sort {key} imeleta table tupu"
            if col is not None and key == "id":
                values = [v for v in (r[col] for r in table_data(driver, "grid") if len(r) > col) if v]
                assert is_sorted(values, descending), (
                    f"{module['name']}: sort {'-' if descending else ''}{key} haijapanga: {values[:6]}"
                )
            actual(f"Sort {key} {'DESC' if descending else 'ASC'}: rows {info['rows']}, "
                   f"mwanzo {table_data(driver, 'grid')[0][:3]}")
    else:
        for direction in ("ASC", "DESC"):
            vue_sort(driver, key, direction)
            info = profile(driver)
            assert info["rows"] > 0, f"{module['name']}: sort {key} {direction} imeleta table tupu"
            if col is not None and key == "id":
                def id_values(d):
                    return [v for v in (r[col] for r in table_data(d, "vue") if len(r) > col) if v]
                # Staging ni nzito: subiri (hadi SORT_TIMEOUT) table ipangwe kabla ya kuamua imefeli
                # Table yenye row 1 tu tayari imepangwa; table tupu (bado inajipakia) haihesabiki
                need = 2 if min(info["rows"], module.get("rows") or 0) > 1 else 1

                def sorted_now(d):
                    values = id_values(d)
                    return len(values) >= need and is_sorted(values, direction == "DESC")
                wait_until(driver, sorted_now, timeout=SORT_TIMEOUT)
                values = id_values(driver)
                assert values, f"{module['name']}: sort {key} {direction} imeleta table tupu"
                assert is_sorted(values, direction == "DESC"), (
                    f"{module['name']}: sort {key} {direction} haijapanga: {values[:6]}"
                )
            actual(f"Sort {key} {direction}: rows {info['rows']}, mwanzo {table_data(driver, 'vue')[0][:3]}")


# ============================================================
# 6. FILTER (thamani halisi kutoka row ya kwanza + thamani isiyokuwepo)
# ============================================================

def _apply_filter(driver, module, spec, value):
    if module["kind"] == "grid":
        grid_filter(driver, spec["filter"]["name"], value)
    else:
        vue_filter_text(driver, spec["label"], value)


def check_filter_finds_row(driver, app, module):
    spec = _text_filter(module)
    open_module(driver, app, module)
    rows = table_data(driver, module["kind"])
    assert rows, f"{module['name']}: hakuna rows za kuchukua thamani ya filter"

    value = rows[0][spec["column"]].strip()
    # Majina kama "Mbwana Sefu (E1513)" -> tumia neno la kwanza tu
    if spec["label"].lower() != "id" and " " in value:
        value = value.split(" ")[0]
    if not value or value in ("--", "-"):
        pytest.skip(f"{module['name']}: row ya kwanza haina thamani ya '{spec['label']}'")
    actual(f"Filter '{spec['label']}' = '{value}'")
    _apply_filter(driver, module, spec, value)
    filtered = table_data(driver, module["kind"])
    assert filtered, f"{module['name']}: filter {spec['label']}='{value}' haikurudisha row"
    wrong = [r[spec["column"]] for r in filtered
             if len(r) > spec["column"] and value.lower() not in r[spec["column"]].lower()]
    assert not wrong, (
        f"{module['name']}: filter {spec['label']}='{value}' imerudisha rows zisizolingana: {wrong[:5]}"
    )
    actual(f"Rows {len(filtered)} zote zina '{value}' kwenye column '{spec['label']}'")


def check_filter_no_match(driver, app, module):
    spec = _text_filter(module)
    open_module(driver, app, module)
    value = "987654321" if spec["label"].lower() == "id" else NO_MATCH
    _apply_filter(driver, module, spec, value)
    assert not table_data(driver, module["kind"]), (
        f"{module['name']}: filter '{value}' (haipo) bado imeonyesha rows"
    )
    actual(f"Filter '{spec['label']}' = '{value}' imerudisha rows 0")


# ============================================================
# 7. VIEW (detail page ya row ya kwanza)
# ============================================================

def check_view(driver, app, module):
    open_module(driver, app, module)

    if module["kind"] in ("grid", "spa"):
        links = driver.find_elements(
            By.CSS_SELECTOR, "table tbody a[href*='/view'], table tbody a[href$='/details']")
        assert links, f"{module['name']}: link ya view haipo"
        href = urljoin(app["base_url"] + "/", links[0].get_attribute("href"))
        open_module(driver, app, module, href)
    else:
        links = [a for a in driver.find_elements(By.CSS_SELECTOR, "table.ongeza-table tbody a[data-id]")
                 if "-view" in (a.get_attribute("class") or "")]
        assert links, f"{module['name']}: link ya view haipo"
        before = driver.current_url
        click(driver, links[0])
        wait_until(driver, lambda d: d.current_url != before
                   or d.find_elements(By.CSS_SELECTOR, ".modal.show"), timeout=20)
        if driver.current_url != before:
            open_module(driver, app, module, driver.current_url)

    body = driver.find_element(By.TAG_NAME, "body").text
    assert len(body.strip()) > 50, f"{module['name']}: ukurasa wa view uko tupu"
    actual(f"View imefunguka: {driver.current_url}")


# ============================================================
# 8. CREATE FORM (bila kusave)
# ============================================================

def _field_key(f):
    return f.get("name") or f.get("id") or f.get("placeholder") or ""


def check_create_form_fields(driver, app, module):
    open_module(driver, app, module, module["create_path"])
    current = {_field_key(f) for f in describe_form(driver)}
    # Search ya juu (topbar) na filter ya menu si sehemu ya form
    ignore = {"serial_number", "Navigation Filter..."}
    expected = [_field_key(f) for f in module.get("form_fields") or []
                if _field_key(f) and _field_key(f) not in ignore]
    missing = [k for k in expected if k not in current]
    assert not missing, f"{module['name']}: fields zimepotea kwenye form: {missing}"
    assert current, f"{module['name']}: form haina fields"
    actual(f"Fields {len(current)} zipo: {', '.join(sorted(current))}")


def check_create_form_rejects_empty(driver, app, module):
    open_module(driver, app, module, module["create_path"])
    url_before = driver.current_url

    submit = find_submit_button(driver)
    if submit is None:
        pytest.skip(f"{module['name']}: button ya Save/Submit haikupatikana")

    install_write_guard(driver)
    click(driver, submit)
    time.sleep(2)

    shown = validation_shown(driver)
    writes = blocked_writes(driver) or []
    if not shown and writes:
        pytest.fail(
            f"{module['name']}: form tupu haikuonyesha validation yoyote kwenye browser na "
            f"ilijaribu kutuma {writes[-1]} (write guard imeizuia, hakuna kilichosaviwa)"
        )
    assert shown or driver.current_url == url_before, f"{module['name']}: form tupu imekubaliwa"
    actual("Form tupu imekataliwa na validation imeonyeshwa")


# ============================================================
# 9. CREATE FORM: JAZA DATA NA USAVE (RUN_CRUD=1 / --crud tu)
# ============================================================

def check_create_form_saves(driver, app, module):
    open_module(driver, app, module, module["create_path"])
    create_url = driver.current_url
    stamp = datetime.now().strftime("%m%d%H%M%S")

    filled = fill_form(driver, stamp)
    assert filled, f"{module['name']}: fomu haina fields za kujaza"
    summary = ", ".join(f"{label}={value}" for label, value in filled)
    print("FILLED: " + summary)

    submit = find_save_button(driver) or find_submit_button(driver)
    if submit is None:
        pytest.skip(f"{module['name']}: button ya Save/Submit haikupatikana")

    def finished(d):
        return (d.current_url != create_url or server_responses(d)
                or (validation_shown(d) and validation_messages(d)))

    def save(button):
        record_server_responses(driver)
        driver.execute_script("if (window.__autoRecorder) window.__autoRecorder.length = 0;")  # jaribio jipya
        click(driver, button)
        try:
            wait_until(driver, finished, PAGE_LOAD_TIMEOUT)
        except Exception:
            pass
        time.sleep(3)  # redirect / ujumbe wa success

    save(submit)

    # Validation (ya browser au ya server) ikisema field ina aina mbaya (k.m. "must be an integer",
    # "format is invalid"), irekebishe na ujaribu tena mara 1
    if driver.current_url == create_url:
        problems = validation_messages(driver) + server_error_messages(driver)
        fixed = fix_from_validation(driver, problems, stamp)
        if problems:
            # Haijasave: jaza pia fields zilizoongezeka/zilizobaki tupu (k.m. rows za items).
            # report_existing=False -> inarudisha tu kile ilichoandika kweli kwenye fomu.
            fixed += fill_form(driver, stamp, report_existing=False)
        fixed = [(label, value) for label, value in fixed if not str(value).startswith(NOT_WRITTEN)]
        if fixed:
            summary += " | Imerekebishwa: " + ", ".join(f"{label}={value}" for label, value in fixed)
            submit = find_save_button(driver) or find_submit_button(driver)
            if submit is not None:
                save(submit)

    error = find_error_on_page(driver)
    responses = server_responses(driver)
    bad = [r for r in responses if r.get("status", 0) >= 400 or '"errors":{"' in (r.get("body") or "")]
    messages = validation_messages(driver)

    assert error is None, (
        f"{module['name']}: kusave kumeleta error '{error}' ({driver.current_url}). Data: {summary}"
    )
    assert not bad, (
        f"{module['name']}: server imekataa: {describe_server_responses(driver)}. Data: {summary}"
    )
    still_on_form = driver.current_url == create_url and not responses
    assert not (still_on_form and messages), (
        f"{module['name']}: haikusave, validation: {'; '.join(messages[:5])}. Data: {summary}"
    )
    if still_on_form and "(file imerukwa)" in summary:
        pytest.skip(f"{module['name']}: fomu inahitaji file (upload), automation hairuki kuweka file")
    assert not still_on_form, (
        f"{module['name']}: baada ya Save hakuna kilichotokea (URL haikubadilika, server "
        f"haikujibu). Data: {summary}"
    )

    redirected = driver.current_url != create_url
    server_said = describe_server_responses(driver)[:200] if responses else ""
    actual(f"Data iliyojazwa: {summary}")

    # Record mpya inaonekana kwenye list?
    open_module(driver, app, module)
    seen = stamp in driver.find_element(By.TAG_NAME, "body").text
    # Fomu ikibaki kwenye create bila ujumbe wa success, list ndiyo ushahidi pekee
    assert seen or redirected, (
        f"{module['name']}: Save haikusave na haikuonyesha ujumbe wowote: server imerudisha fomu "
        f"ileile bila error ({server_said or '-'}), na record '{stamp}' haionekani kwenye list. Data: {summary}"
    )
    actual("Imesave" + (f"; server: {server_said}" if server_said else ""))
    actual(f"Record yenye '{stamp}' {'inaonekana' if seen else 'haionekani (list haionyeshi field hii)'} "
           f"kwenye page 1 ya list")


# ============================================================
# 10. EDIT: BADILISHA RECORD NA USAVE (RUN_CRUD=1 / --crud tu)
# ============================================================
# Inaedit record ya AUTO (iliyoundwa na test ya Create): inaitafuta page 1, kisha kwa ID DESC,
# kisha page ya mwisho. EDIT_REAL_RECORDS=1 (--edit-real): kama hakuna record ya AUTO, inaedit
# record ya kwanza ya list (field moja ya maandishi) kisha inarudisha thamani zake zote za zamani.

AUTO_TOKEN = re.compile(r"AUTO(?: automation test )?\d{10}")
EDIT_REAL_RECORDS = os.getenv("EDIT_REAL_RECORDS", "0") == "1"
# Hata kwa --edit-real, records halisi za watumiaji, roles na ruhusa haziguswi
EDIT_REAL_EXCLUDE = re.compile(r"^users|^role|permission")
SETTLE_SECONDS = 2   # thamani za fomu ya Edit zisibadilike kwa sekunde hizi kabla ya kuzisoma
SETTLE_TIMEOUT = 20

ROWS_EDIT_JS = r"""
const auto = /AUTO(?: automation test )?\d{10}/;
const editHref = /(^|[\/?_-])(update|edit)\d*([\/?&#]|$)/i;
const isEdit = e => !e.classList.contains('disabled') && !e.hasAttribute('disabled') && (
    editHref.test(e.getAttribute('href') || '')
    || /^(update|edit)$/i.test((e.getAttribute('title') || e.getAttribute('aria-label') || e.textContent || '').trim())
    || !!e.querySelector('.fa-pencil, .fa-edit, .fa-pen, .fa-pencil-alt, .glyphicon-pencil, .lucide-square-pen, .lucide-pencil'));
const isView = e => /\/(view|details)\b/i.test(e.getAttribute('href') || '') && !/^javascript/i.test(e.getAttribute('href'));
return [...document.querySelectorAll('table tbody tr')].map(row => {
    const ctl = [...row.querySelectorAll('a, button')];
    const text = row.innerText.replace(/\s+/g, ' ').trim();
    return {edit: ctl.find(isEdit) || null, view: ctl.find(isView) || null,
            auto: (row.innerText.match(auto) || [null])[0],
            autos: [...new Set(row.innerText.match(new RegExp(auto.source, 'g')) || [])],
            text: text.slice(0, 100), full: text};
}).filter(r => r.edit || r.view);
"""

# ONGEZA PRO: Edit iko kwenye ukurasa wa record (View), si kwenye row
EDIT_BUTTON_JS = r"""
const root = arguments[0] || document;
return [...root.querySelectorAll('a, button')].find(e => e.getClientRects().length && !e.disabled && (
    /^(edit|update)$/i.test(e.textContent.trim())
    || !!e.querySelector('.lucide-square-pen, .lucide-pencil'))) || null;
"""

# Select yenye "--Select--"/"Loading..." inasomwa kama tupu
EDIT_FIELDS_JS = r"""
const root = arguments[0] || document;
const junk = /^(--|select|choose|chagua|loading|searching|no results)/i;
const label = e => {
    if (e.id) {
        const l = document.querySelector('label[for="' + CSS.escape(e.id) + '"]');
        if (l && l.innerText.trim()) return l.innerText.trim();
    }
    let p = e.parentElement;
    for (let i = 0; i < 2 && p; i++, p = p.parentElement) {
        const l = [...p.querySelectorAll('label')].find(l => !l.contains(e) && l.innerText.trim());
        if (l) return l.innerText.trim();
    }
    return e.placeholder || e.name || e.id || '';
};
const visible = e => {
    const s = getComputedStyle(e);
    return e.getClientRects().length && s.visibility !== 'hidden' && s.display !== 'none';
};
const valueOf = e => {
    if (e.tagName === 'SELECT') {
        if (e.multiple)
            return [...e.selectedOptions].filter(o => o.value !== '' && !junk.test(o.text.trim()))
                .map(o => o.text.trim()).join(', ');
        const o = e.selectedIndex >= 0 ? e.options[e.selectedIndex] : null;
        const t = o ? o.text.trim() : '';
        return !o || o.value === '' || junk.test(t) ? '' : t;
    }
    return ['checkbox', 'radio'].includes(e.type) ? String(e.checked) : (e.value || '');
};
// Select ambayo bado inapakia options (DepDrop/select2 "Loading...")
const loading = e => e.tagName === 'SELECT' && e.selectedIndex >= 0
    && /^(loading|searching)/i.test(e.options[e.selectedIndex].text.trim());
return [...root.querySelectorAll('input, select, textarea')]
    .filter(e => !['hidden', 'password', 'file', 'submit', 'button', 'search'].includes(e.type)
                 && e.name !== 'serial_number' && !/navigation filter/i.test(e.placeholder || '')
                 && (e.tagName === 'SELECT' || visible(e)))
    .map((e, i) => ({
        el: e, index: i, tag: e.tagName.toLowerCase(), type: e.type || '', key: e.name || e.id || '',
        label: label(e).replace(/\s*\*\s*$/, '').slice(0, 60), value: valueOf(e),
        option: e.tagName === 'SELECT' && !e.multiple && valueOf(e) !== '' ? e.value : '',
        multiple: !!e.multiple, loading: loading(e),
        maxlength: e.maxLength > 0 ? e.maxLength : 0, locked: e.readOnly || e.disabled, disabled: e.disabled,
    }));
"""

# Chagua option kwa value yake (au maandishi; '' = option tupu) na utume change (Vue na jQuery/select2)
SELECT_TEXT_JS = r"""
const [s, text, value] = arguments;
const norm = t => (t || '').replace(/\s+/g, ' ').trim();
const byText = o => text === '' ? o.value === '' : norm(o.text) === norm(text);
const opts = [...s.options];
const o = value ? (opts.find(o => o.value === value && byText(o)) || opts.find(o => o.value === value))
                : opts.find(byText);
if (!o) return false;
s.value = o.value;
o.selected = true;
s.dispatchEvent(new Event('change', {bubbles: true}));
if (window.jQuery) jQuery(s).trigger('change');
return true;
"""

# Field ya kubadilisha: ile yenye AUTO, kisha maelezo/maoni, kisha majina; si namba, simu, tarehe, codes n.k.
EDIT_PREFER = re.compile(r"\b(description|desc|notes?|comments?|remarks?|land ?mark|address|details?|reason|narration)\b", re.I)
EDIT_NAME_LIKE = re.compile(r"\b(name|title|label|category)\b", re.I)
EDIT_AVOID = re.compile(
    r"\b(phone|mobile|email|username|user|serial|code|imei|number|no|nida|tin|password|amount|price|cost|qty|"
    r"quantity|date|time|lat|latitude|lon|lng|longitude|colou?r|url|link|token|key|sku|barcode|percent|rate|id)\b",
    re.I)
TOO_LONG = re.compile(r"at most|greater than|too long", re.I)


def _field_words(f):
    return re.sub(r"[_\[\]\-.]", " ", f"{f['key']} {f['label']}")


def _field_name(f):
    return f["label"] or f["key"] or "field"


def _is_text(f):
    return f["tag"] == "textarea" or (f["tag"] == "input" and f["type"] in ("text", ""))


def _watched(fields):
    """Fields ambazo Save inazituma, kwa hiyo tunazilinda: zote isipokuwa disabled."""
    return [f for f in fields if not f["disabled"]]


def _pick_edit_field(fields):
    texts = [f for f in fields if not f["locked"] and _is_text(f)]
    for f in texts:
        if AUTO_TOKEN.search(f["value"]):
            return f
    pool = [f for f in texts if not EDIT_AVOID.search(_field_words(f))]
    for pattern in (EDIT_PREFER, EDIT_NAME_LIKE):
        for f in pool:
            if pattern.search(_field_words(f)):
                return f
    return pool[0] if pool else None


def _edit_value(old, stamp, maxlength):
    token = f"AUTO{stamp}"
    if AUTO_TOKEN.search(old):
        new = AUTO_TOKEN.sub(token, old, count=1)
    elif old.strip():
        new = f"{old.strip()} {token}"
    else:
        new = token
    if maxlength and len(new) > maxlength:
        new = token[-maxlength:]
    return new


def _same_value(a, b):
    a, b = (a or "").strip(), (b or "").strip()
    if a == b:
        return True
    try:  # "12500" na "12500.00"
        return float(a.replace(",", "")) == float(b.replace(",", ""))
    except ValueError:
        return False


def _set_text(driver, element, value):
    try:
        click(driver, element)
        element.send_keys(Keys.CONTROL, "a")
        element.send_keys(Keys.DELETE)
        if value:
            element.send_keys(value)
    except Exception:
        pass
    try:
        current = element.get_attribute("value") or ""
    except Exception:
        current = None
    if current != value:
        _set_js(driver, element, value)


def _select_text(driver, element, text, value="", timeout=8):
    """Chagua option (kwa value, au maandishi); subiri options za select tegemezi (k.m. Ward) zijae."""
    end = time.time() + timeout
    while not driver.execute_script(SELECT_TEXT_JS, element, text, value):
        if time.time() > end:
            raise LookupError(f"option '{text}' haipo")
        time.sleep(0.5)
    time.sleep(1)  # selects tegemezi zinaanza kujaza options


def _edit_fields(driver):
    """Fields za fomu ya Edit (ndani ya <form> ya button ya Save) na button yenyewe."""
    button = find_save_button(driver, words=EDIT_WORDS) or find_submit_button(driver)
    form = driver.execute_script("return arguments[0].closest('form');", button) if button else None
    roots = driver.find_elements(By.CSS_SELECTOR, FORM_SCOPE)
    root = form or (roots[0] if roots else None)
    return driver.execute_script(EDIT_FIELDS_JS, root) or [], button


def _settled_fields(driver, need_text=False):
    """Soma fomu ya Edit baada ya thamani kutulia: AJAX/select2/SPA zinajaza fields baada ya page
    kufunguka, na thamani za inputs hazionekani kwenye maandishi ya ukurasa."""
    end = time.time() + SETTLE_TIMEOUT
    last, since, result = None, time.time(), ([], None)
    while time.time() < end:
        try:
            fields, button = _edit_fields(driver)
        except StaleElementReferenceException:
            time.sleep(0.5)
            continue
        result = (fields, button)
        snap = [(f["key"], f["label"], f["value"]) for f in fields]
        filled = not need_text or any(f["value"] for f in fields if _is_text(f))
        busy = any(f["loading"] for f in fields)
        if snap != last:
            last, since = snap, time.time()
        elif time.time() - since >= SETTLE_SECONDS and filled and not busy:
            break
        time.sleep(0.5)
    return result


def _reopen_edit(driver, app, module, edit_url):
    open_module(driver, app, module, edit_url)
    return _settled_fields(driver, need_text=module["kind"] == "spa")


def _same_field(fields, f):
    for match in (lambda x: x["index"] == f["index"] and x["label"] == f["label"],
                  lambda x: f["key"] and x["key"] == f["key"],
                  lambda x: f["label"] and x["label"] == f["label"]):
        found = [x for x in fields if match(x)]
        if found:
            return found[0]
    return None


def _value_of(fields, f):
    same = _same_field(fields, f)
    return None if same is None else (same["value"] or "").strip()


def _unchanged(fields, f):
    """Field f ina thamani ileile kwenye fields (select: option ileile, si maandishi tu)."""
    same = _same_field(fields, f)
    if same is None:
        return False
    if f["tag"] == "select" and f["option"] and same["option"] and same["option"] != f["option"]:
        return False
    return _same_value(same["value"], f["value"])


def _edit_rows(driver):
    return driver.execute_script(ROWS_EDIT_JS) or []


def _find_auto_rows(driver, app, module):
    """Rows za AUTO zenye Edit/View: page 1, kisha ID DESC, kisha page ya mwisho.
    Inarudisha (rows za AUTO kwenye ukurasa ulio wazi sasa, idadi ya rows zenye Edit/View page 1)."""
    info = open_module(driver, app, module)
    list_url = driver.current_url
    rows = _edit_rows(driver)
    found = len(rows)
    auto = [r for r in rows if r["auto"]]
    if auto or not rows or not is_paged_list(module):
        return auto, found
    if "id" in (module.get("sort_keys") or []):
        try:
            if module["kind"] == "grid":
                url = grid_sort_url(driver, "id", descending=True)
                if url:
                    open_module(driver, app, module, url)
            else:
                vue_sort(driver, "id", "DESC")
            auto = [r for r in _edit_rows(driver) if r["auto"]]
        except Exception:  # sort isiyofanya kazi ni kosa la test ya Sort, si ya Edit
            pass
        if auto:
            return auto, found
    total, size = info.get("total"), info.get("rows") or 0
    if total and size and total > size:
        try:
            open_module(driver, app, module, with_query(list_url, page=math.ceil(total / size)))
            auto = [r for r in _edit_rows(driver) if r["auto"]]
        except Exception:
            auto = []
    return auto, found


def _navigates(href, current):
    """Link inayofungua ukurasa mwingine (si "javascript:..." wala "#")."""
    if not href or href.startswith("javascript"):
        return False
    return urlparse(href)._replace(fragment="").geturl() != urlparse(current)._replace(fragment="").geturl()


def _open_edit_form(driver, app, module, record):
    """Fungua fomu ya Edit ya record na urudishe URL yake."""
    control = record["edit"]
    if control is None:
        open_module(driver, app, module, record["view"].get_attribute("href"))
        roots = driver.find_elements(By.CSS_SELECTOR, FORM_SCOPE)
        control = driver.execute_script(EDIT_BUTTON_JS, roots[0] if roots else None)
        if control is None:
            pytest.skip(f"{module['name']}: record haina button ya Edit (kwenye row wala ukurasa wa View)")
    href = control.get_attribute("href") or ""
    if _navigates(href, driver.current_url):
        url = href
    else:
        before = driver.current_url
        click(driver, control)
        wait_until(driver, lambda d: d.current_url != before, timeout=30)
        url = driver.current_url
        if url == before:
            pytest.skip(f"{module['name']}: Edit inafunguka kama popup kwenye ukurasa uleule; haijaungwa mkono bado")
    open_module(driver, app, module, url)
    return driver.current_url


def _save_edit(driver, edit_url, button):
    record_server_responses(driver)
    driver.execute_script("if (window.__autoRecorder) window.__autoRecorder.length = 0;")
    click(driver, button)
    wait_until(driver, lambda d: (d.current_url != edit_url or server_responses(d)
                                  or (validation_shown(d) and validation_messages(d))), PAGE_LOAD_TIMEOUT)
    time.sleep(3)  # redirect / ujumbe wa success


def _rejected(driver, edit_url):
    """Ujumbe wa validation ikiwa Save imekataliwa na fomu bado iko wazi, la sivyo []."""
    if find_error_on_page(driver):
        return []
    errors = server_error_messages(driver)
    if errors:
        return errors
    if driver.current_url == edit_url and not server_responses(driver):
        return validation_messages(driver)
    return []


def _resave(driver, edit_url, target, value, fill_stamp=None):
    """Save tena baada ya kukataliwa. fill_stamp: kwanza jaza fields zilizo tupu kwa AUTO.
    Inarudisha [(label, thamani)] za fields zilizojazwa."""
    filled = []
    if fill_stamp:
        filled = [(label, v) for label, v in fill_form(driver, fill_stamp, report_existing=False)
                  if not str(v).startswith(NOT_WRITTEN)]
        if not filled:
            return []
    fields, button = _edit_fields(driver)
    same = _same_field(fields, target)
    if same is None or button is None:
        return []
    _set_text(driver, same["el"], value)
    _save_edit(driver, edit_url, button)
    return filled


def _edit_problems(driver, app, module, edit_url, before, target, new, skip=()):
    """Baada ya Save: matatizo yaliyoonekana, na fields nyingine zilizoharibika.
    skip: fields zilizobadilika zenyewe kabla ya Save (si kosa la Save)."""
    problems = []
    error = find_error_on_page(driver)
    if error:
        problems.append(f"baada ya Save ukurasa umeonyesha error '{error}' ({driver.current_url})")
    responses = server_responses(driver)
    bad = [r for r in responses if r.get("status", 0) >= 400 or '"errors":{"' in (r.get("body") or "")]
    if bad:
        problems.append(f"server imekataa: {describe_server_responses(driver)}")
    messages = validation_messages(driver)
    if driver.current_url == edit_url and not responses and messages:
        problems.append(f"haikusave, validation: {'; '.join(messages[:5])}")

    after, _ = _reopen_edit(driver, app, module, edit_url)
    now = _value_of(after, target)
    if now is None:
        problems.append(f"field '{_field_name(target)}' haipo ukifungua Edit tena")
    elif now != new.strip():
        problems.append(f"mabadiliko hayakuhifadhiwa: ukifungua Edit tena '{_field_name(target)}' = '{now}', "
                        f"si '{new}'")

    def harmed(f):
        now = _value_of(after, f)
        if now is None:
            return "haipo tena"
        if now == "":
            return "imefutwa"
        if not _unchanged(after, f):
            return f"imebadilika kuwa '{now}'"
        return None

    lost = [f for f in _watched(before) if f is not target and not any(f is m for m in skip)
            and f["value"] and harmed(f)]
    if lost:
        problems.append("Save imeharibu fields nyingine: "
                        + ", ".join(f"{_field_name(f)}='{f['value']}' {harmed(f)}" for f in lost[:5]))
    return problems, lost


def _restore_record(driver, app, module, edit_url, before, target, new):
    """--edit-real: rudisha thamani zote za zamani za record halisi. Inarudisha (imerudi?, ujumbe)."""
    watched = _watched(before)
    known = [target]

    def manual(fields):
        return ("rudisha kwa mkono " + ", ".join(f"'{_field_name(f)}' = '{f['value']}'" for f in fields)
                + f" kwenye {edit_url}")

    try:
        fields, button = _reopen_edit(driver, app, module, edit_url)
        now = _value_of(fields, target)
        if now is None or not (_same_value(now, target["value"]) or _same_value(now, new)):
            return False, (f"TAHADHARI: fomu sasa inaonyesha '{_field_name(target)}' = '{now}' (si thamani ya "
                           f"zamani wala mpya), kwa hiyo haikuguswa. Hakikisha: {manual([target])}")
        changed = [f for f in watched if not _unchanged(fields, f)]
        if not changed:
            return True, "Record haikubadilika, hakuna cha kurudisha"
        known = changed
        missed = []
        for f in changed:
            same = _same_field(fields, f)
            try:
                if same is None or same["multiple"]:  # multi-select haiwezi kurudishwa salama
                    raise LookupError(_field_name(f))
                if same["type"] in ("checkbox", "radio"):
                    if same["value"] != f["value"]:
                        driver.execute_script("arguments[0].click();", same["el"])
                elif same["tag"] == "select":
                    _select_text(driver, same["el"], f["value"], f["option"])
                elif same["locked"]:  # readonly (k.m. datepicker): andika kwa JS
                    _set_js(driver, same["el"], f["value"])
                else:
                    _set_text(driver, same["el"], f["value"])
            except Exception:
                missed.append(f)
        _, button = _edit_fields(driver)
        if len(missed) == len(changed) or button is None:
            return False, f"TAHADHARI: thamani za zamani hazikuweza kuandikwa; {manual(changed)}"
        _save_edit(driver, edit_url, button)
        fields, _ = _reopen_edit(driver, app, module, edit_url)
        bad = [f for f in watched if not _unchanged(fields, f)]
        if bad:
            return False, f"TAHADHARI: thamani za zamani hazikurudi; {manual(bad)}"
        return True, ("Thamani za zamani zimerudishwa: "
                      + ", ".join(f"{_field_name(f)}='{f['value']}'" for f in changed))
    except Exception as exc:
        return False, (f"TAHADHARI: kurudisha thamani za zamani kumeshindwa ({type(exc).__name__}); "
                       f"{manual(known)}")


def _identity_values(fields):
    """Maandishi ya fomu yanayoweza kutambulisha record (si tarehe/namba tupu)."""
    return [f["value"].strip() for f in fields if _is_text(f) and not f["locked"]
            and len(f["value"].strip()) >= 3 and not re.fullmatch(r"[\d\s.,:/+-]+", f["value"].strip())]


def _matches_row(values, row_text, others=None):
    """Fomu ni ya row hii ikiwa thamani 2 za fomu zinaonekana kwenye row, au 1 ambayo haipo
    kwenye rows nyingine za page."""
    def found(v, text):
        return re.search(r"(?<!\w)" + re.escape(v) + r"(?!\w)", text, re.I)

    hits = {v.lower() for v in values if found(v, row_text)}
    if len(hits) >= 2:
        return True
    return len(hits) == 1 and bool(others) and not any(found(next(iter(hits)), o) for o in others)


def check_edit_form_saves(driver, app, module):
    auto_rows, found = _find_auto_rows(driver, app, module)
    if not found:
        pytest.skip(f"{module['name']}: table haina record yenye button ya Edit")
    others = None
    if auto_rows:
        auto_rows.sort(key=lambda r: r["edit"] is None)  # zenye Edit kwenye row kwanza
        record, is_auto = auto_rows[0], True
    else:
        if not EDIT_REAL_RECORDS:
            pytest.skip(f"{module['name']}: hakuna record ya AUTO kwenye list (page 1, ID DESC, page ya mwisho): "
                        f"Create haikusave, au list haionyeshi field ya AUTO. --edit-real inaruhusu kuedit "
                        f"record halisi na kuirudisha")
        if EDIT_REAL_EXCLUDE.search(module["id"]):
            pytest.skip(f"{module['name']}: hakuna record ya AUTO, na records halisi za module hii haziguswi")
        open_module(driver, app, module)
        rows = sorted(_edit_rows(driver), key=lambda r: r["edit"] is None)
        if not rows:
            pytest.skip(f"{module['name']}: table haina record yenye button ya Edit")
        record, is_auto = rows[0], False
        others = [r["full"] for r in rows[1:]]

    edit_url = _open_edit_form(driver, app, module, record)
    before, button = _settled_fields(driver, need_text=module["kind"] == "spa")
    if button is None:
        pytest.skip(f"{module['name']}: fomu ya Edit haina button ya Save/Update")
    target = _pick_edit_field(before)
    if target is None:
        pytest.skip(f"{module['name']}: fomu ya Edit haina field ya maandishi inayoweza kubadilishwa")

    # Fomu lazima ionyeshe data ya record iliyochaguliwa. Isipoonyesha, Save ingeandika data ya
    # record nyingine juu ya hii, kwa hiyo tunasimama kabla ya kusave.
    texts = [f["value"].strip() for f in before if f["value"].strip() and f["type"] not in ("checkbox", "radio")]
    ident = _identity_values(before)
    if is_auto:
        own = [f for f in before if _is_text(f) and not f["locked"]
               and any(t in f["value"] for t in record["autos"])]
        if own:
            target = own[0]  # field ya AUTO ya record hii yenyewe
        elif any(t in v for v in texts for t in record["autos"]):
            # AUTO ya row ni ya record nyingine inayohusiana (k.m. select), si ya record hii
            if not (EDIT_REAL_RECORDS and not EDIT_REAL_EXCLUDE.search(module["id"])
                    and _matches_row(ident, record["full"])):
                pytest.skip(f"{module['name']}: AUTO kwenye row ('{record['auto']}') ni ya record nyingine "
                            f"inayohusiana, si field ya record hii; record halisi haikuguswa")
            is_auto = False
        else:
            assert False, (
                f"{module['name']}: fomu ya Edit ({edit_url}) haionyeshi data ya record iliyochaguliwa: row ina "
                f"'{record['auto']}', lakini fomu inaonyesha {texts[:4]} (data ya record nyingine). Haikusaviwa."
            )
    elif not _matches_row(ident, record["full"], others):
        pytest.skip(f"{module['name']}: haikuthibitishwa kuwa fomu ya Edit ({edit_url}) ni ya row "
                    f"'{record['text']}' (fomu inaonyesha {texts[:3]}), kwa hiyo record halisi haikuguswa")
    if not is_auto:
        still = [_field_name(f) for f in before if f["loading"]]
        if still:
            pytest.skip(f"{module['name']}: fomu ya Edit bado inajaa ({', '.join(still)}), kwa hiyo record "
                        f"halisi haikusaviwa")

    stamp = datetime.now().strftime("%m%d%H%M%S")
    old = target["value"] or ""
    new = _edit_value(old, stamp, target["maxlength"])
    print(f"EDIT: Record: {record['text']} ({edit_url}). Field '{_field_name(target)}': '{old}' -> '{new}'")
    problems, lost, restored, blanks, rejected, moved = [], [], None, [], [], []
    saved = False  # restore inahitajika tu ikiwa Save imebofywa
    try:
        _set_text(driver, target["el"], new)
        # Fomu ikibadilika yenyewe baada ya kusomwa (field iliyochelewa kujaa), Save ingeandika thamani
        # ambazo hatuna nakala yake: record halisi haisaviwi
        current, button = _edit_fields(driver)
        moved = [f for f in _watched(before) if f is not target and not _unchanged(current, f)]
        moved += [f for f in current if f["loading"]]
        if moved and not is_auto:
            pytest.skip(f"{module['name']}: fomu ya Edit ilikuwa bado inajaa ({_field_name(moved[0])}), "
                        f"kwa hiyo record halisi haikusaviwa")
        saved = True
        _save_edit(driver, edit_url, button)

        # Thamani ndefu ikikataliwa (k.m. "at most 50 characters"), jaribu tena kwa AUTO<stamp> tu
        rejected = _rejected(driver, edit_url)
        if rejected and new != f"AUTO{stamp}" and any(TOO_LONG.search(m) for m in rejected):
            new = f"AUTO{stamp}"
            _resave(driver, edit_url, target, new)
            rejected = _rejected(driver, edit_url)
        # Record ya AUTO: fomu ikidai fields zilizo tupu (k.m. "Village cannot be blank"), zijaze kwa AUTO
        # na ujaribu tena ili tujue kama Edit yenyewe inafanya kazi. Test bado inashindwa na kueleza.
        # Record halisi haijazwi fields nyingine.
        if rejected and is_auto:
            blanks = _resave(driver, edit_url, target, new, fill_stamp=stamp)
        problems, lost = _edit_problems(driver, app, module, edit_url, before, target, new, skip=moved)
    except Exception as exc:
        problems.append(f"kukagua Edit kumeshindwa: {(str(exc).strip().splitlines() or [type(exc).__name__])[0][:300]}")
    finally:
        if not is_auto and saved:
            restored = _restore_record(driver, app, module, edit_url, before, target, new)
            print("RESTORE: " + restored[1])

    if blanks:
        problems.insert(0, f"Save ilikataliwa ({'; '.join(rejected[:4])}) mpaka fields zilizokuwa tupu "
                           f"zijazwe: {', '.join(dict.fromkeys(label for label, _ in blanks))}"
                        + ("" if problems else "; baada ya kuzijaza imesave na thamani mpya inaonekana"))
    what = f"Record: {record['text']}. Field '{_field_name(target)}': '{old}' -> '{new}'"
    note = f" {restored[1]}." if restored else ""
    # Ripoti inachukua mstari wa kwanza wa ujumbe tu
    one_line = lambda text: " ".join(text.split())
    assert not problems, one_line(f"{module['name']}: Edit: {'; '.join(problems)}. {what}.{note}")
    assert restored is None or restored[0], one_line(f"{module['name']}: {restored[1]}. {what}")
    actual(one_line(f"Record {'ya AUTO' if is_auto else 'halisi'}: {record['text']}"))
    actual(one_line(f"Field '{_field_name(target)}': '{old}' -> '{new}'"))
    actual("Imesave bila error, na ukifungua Edit tena thamani mpya inaonekana")
    if restored:
        actual(one_line(restored[1]))
