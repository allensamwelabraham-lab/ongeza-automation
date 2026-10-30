"""
Checks za list page kwa Playwright: zilezile za core/list_checks.py, lakini zinasubiri jibu la server
(si muda) kabla ya kuamua, na hazihesabu Fail ikiwa staging haikujibu (NotTested -> ERROR).
"""

import time
from urllib.parse import urljoin

import pytest

from core.list_checks import NO_MATCH, _norm, _text_filter, actual
from core.pages import column_index, is_sorted, with_query
from pw import inertia
from pw.pages import (
    NotTested,
    grid_filter,
    grid_sort_url,
    mark_dirty,
    open_module,
    profile,
    table_data,
    vue_filter,
    vue_sort,
)


def check_page_loads(page, app, module):
    mark_dirty(page)  # muda wa kuload unapimwa kwa kuufungua upya
    start = time.time()
    info = open_module(page, app, module)
    seconds = time.time() - start
    assert info["kind"] == module["kind"], (
        f"{module['name']}: aina ya ukurasa imebadilika {module['kind']} -> {info['kind']}")
    if module.get("heading"):
        assert _norm(info["heading"]) == _norm(module["heading"]), (
            f"{module['name']}: heading '{info['heading']}' (ilikuwa '{module['heading']}')")
    limit = max(90, (module.get("load_seconds") or 0) * 3)
    assert seconds < limit, f"{module['name']}: imechukua {seconds:.0f}s kuload (limit {limit:.0f}s)"
    actual(f"Ukurasa '{info['heading']}' umefunguka kwa sekunde {seconds:.1f} bila error")


def check_columns(page, app, module):
    info = open_module(page, app, module)
    columns = [c.strip() for c in info["columns"]]
    assert columns, f"{module['name']}: table haina vichwa vya columns"
    named = [c for c in columns if c]
    repeated = sorted({c for c in named if named.count(c) > 1})
    assert not repeated, f"{module['name']}: columns zinajirudia: {repeated}"
    data = table_data(page, module["kind"])
    short = [i + 1 for i, r in enumerate(data) if len(r) < len(columns) - 1]
    assert not short, f"{module['name']}: rows {short[:5]} hazina cell kwa kila column ({len(columns)})"
    actual(f"Columns {len(columns)} zinaonekana: {', '.join(columns)}")


def check_records(page, app, module):
    info = open_module(page, app, module)
    data = inertia.page_data(page)
    listing = inertia.find_listing(data["props"]) if data else None
    if listing:
        # Kurasa za Inertia: idadi halisi kutoka kwa server, si kutoka maandishi ya ukurasa
        info["total"] = listing.total
        assert listing.total >= len(listing.rows), (
            f"{module['name']}: server inasema jumla ya records ni {listing.total} lakini imetuma {len(listing.rows)}")
        assert len(listing.rows) == info["rows"], (
            f"{module['name']}: server imetuma records {len(listing.rows)} lakini table inaonyesha rows {info['rows']}")
    if (module.get("rows") or 0) > 0 and info["rows"] == 0:
        pytest.skip(f"{module['name']}: table haina records sasa (ilikuwa na rows {module['rows']})")
    if info["total"] is not None:
        assert info["total"] >= info["rows"], f"{module['name']}: total {info['total']} < rows {info['rows']}"
    data = table_data(page, module["kind"])
    if data and info["columns"]:
        bad = [i for i, r in enumerate(data) if len(r) < len(info["columns"]) - 1]
        assert not bad, f"{module['name']}: rows {bad[:5]} hazina cells za kutosha"
    actual(f"Records {info['total'] if info['total'] is not None else '-'}; rows {info['rows']} kwenye page 1")


def check_pagination(page, app, module):
    first = open_module(page, app, module)
    first_page = table_data(page, module["kind"])
    if first.get("total") is not None and first["total"] <= len(first_page):
        pytest.skip(f"{module['name']}: records {first['total']} tu, zote ziko page 1 (hakuna page 2)")
    info = open_module(page, app, module, with_query(page.url, page=2))
    second_page = table_data(page, module["kind"])
    assert info["rows"] > 0, f"{module['name']}: page 2 iko tupu"
    assert second_page != first_page, f"{module['name']}: page 2 ni sawa na page 1"
    actual(f"Page 2 ina rows {info['rows']}, tofauti na page 1")


def _ids(page, kind, col):
    return [v for v in (r[col] for r in table_data(page, kind) if len(r) > col) if v]


def check_sort(page, app, module):
    key = "id" if "id" in module["sort_keys"] else module["sort_keys"][0]
    col = column_index(module.get("columns") or [], key, key.replace("_", " "))
    open_module(page, app, module)
    if profile(page)["rows"] <= 1:
        pytest.skip(f"{module['name']}: table ina row {profile(page)['rows']} tu, sort haiwezi kupimwa")
    for direction in ("ASC", "DESC"):
        if module["kind"] == "grid":
            url = grid_sort_url(page, key, direction == "DESC")
            assert url, f"{module['name']}: link ya sort '{key}' haipo"
            info = open_module(page, app, module, url)
        else:
            vue_sort(page, key, direction)
            info = profile(page)
        assert info["rows"] > 0, f"{module['name']}: sort {key} {direction} imeleta table tupu"
        if col is not None and key == "id":
            values = _ids(page, module["kind"], col)
            assert is_sorted(values, direction == "DESC"), (
                f"{module['name']}: sort {key} {direction} haijapanga: {values[:6]}")
        actual(f"Sort {key} {direction}: rows {info['rows']}, mwanzo {table_data(page, module['kind'])[0][:3]}")


def _apply_filter(page, module, spec, value):
    if module["kind"] == "grid":
        grid_filter(page, spec["filter"]["name"], value)
    else:
        vue_filter(page, spec["label"], value)


def check_filter_finds_row(page, app, module):
    spec = _text_filter(module)
    open_module(page, app, module)
    rows = table_data(page, module["kind"])
    if not rows or len(rows[0]) <= spec["column"]:
        raise NotTested(f"{module['name']}: hakuna row ya kuchukua thamani ya filter")
    value = rows[0][spec["column"]].strip()
    if spec["label"].lower() != "id" and " " in value:
        value = value.split(" ")[0]
    if not value or value in ("--", "-"):
        pytest.skip(f"{module['name']}: row ya kwanza haina thamani ya '{spec['label']}'")
    actual(f"Filter '{spec['label']}' = '{value}'")
    _apply_filter(page, module, spec, value)
    filtered = table_data(page, module["kind"])
    assert filtered, f"{module['name']}: filter {spec['label']}='{value}' haikurudisha row"
    col = spec["column"]
    if spec["label"].lower() == "id":
        wrong = [r[col] for r in filtered if len(r) > col and r[col].strip() != value]
    else:
        wrong = [r[col] for r in filtered if len(r) > col and value.lower() not in r[col].lower()]
    assert not wrong, f"{module['name']}: filter {spec['label']}='{value}' imerudisha rows zisizolingana: {wrong[:5]}"
    actual(f"Rows {len(filtered)} zote zina '{value}' kwenye column '{spec['label']}'")


def check_filter_no_match(page, app, module):
    spec = _text_filter(module)
    open_module(page, app, module)
    value = "987654321" if spec["label"].lower() == "id" else NO_MATCH
    _apply_filter(page, module, spec, value)
    rows = table_data(page, module["kind"])
    assert not rows, f"{module['name']}: filter '{value}' (haipo) bado imeonyesha rows {len(rows)}"
    actual(f"Filter '{spec['label']}' = '{value}' imerudisha rows 0")


def check_view(page, app, module):
    open_module(page, app, module)
    mark_dirty(page)
    if module["kind"] in ("grid", "spa"):
        link = page.locator("table tbody a[href*='/view'], table tbody a[href$='/details']").first
        assert link.count(), f"{module['name']}: link ya view haipo"
        open_module(page, app, module, urljoin(app["base_url"] + "/", link.get_attribute("href")))
    else:
        link = page.locator("table.ongeza-table tbody a[data-id][class*='-view']").first
        assert link.count(), f"{module['name']}: link ya view haipo"
        before = page.url
        link.click()
        try:
            page.wait_for_function("u => location.href !== u || document.querySelector('.modal.show')",
                                   arg=before, timeout=30000)
        except Exception:
            raise NotTested(f"{module['name']}: View haikufunguka ndani ya sekunde 30") from None
        if page.url != before:
            open_module(page, app, module, page.url)
    body = page.inner_text("body")
    assert len(body.strip()) > 50, f"{module['name']}: ukurasa wa view uko tupu"
    actual(f"View imefunguka: {page.url}")
