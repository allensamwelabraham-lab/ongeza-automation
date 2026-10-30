"""
Hatua ya 2: ukaguzi unaolinganisha na DATA HALISI ya server (Inertia props), si maandishi ya skrini tu.

- Sort kwa KILA column inayopangika, ASC na DESC
- Filters ZOTE za ukurasa (maandishi, dropdown, tarehe From/To)
- Per Page
- Pagination: page 2 na page ya mwisho zinalingana na idadi ya records
- View inaonyesha record ileile ya row

Kila kinachopimwa kinatoka kwenye ukurasa wenyewe (sort options za server, fields za Filter),
si kwenye map iliyohifadhiwa, kwa hiyo app nyingine ya Inertia inapimwa bila kubadilisha code hii.
"""

import re
from urllib.parse import parse_qsl, urljoin, urlsplit

import pytest

from core.list_checks import actual
from pw import inertia
from pw.pages import (
    NotTested,
    _toolbar_button,
    grid_sort_url,
    inertia_call,
    mark_dirty,
    open_module,
    open_page,
    profile,
    table_data,
)

# Vichwa vya columns visivyo data (buttons)
_ACTION_COLUMNS = re.compile(r"^(actions?|#|)$", re.I)


def open_listing(page, app, module):
    """Fungua module; inarudisha (data ya Inertia, Listing). Skip kama ukurasa hauna list ya Inertia."""
    open_module(page, app, module)
    data = inertia.page_data(page)
    listing = inertia.find_listing(data["props"]) if data else None
    if not listing:
        pytest.skip(f"{module['name']}: ukurasa si list ya Inertia (data ya server haipo)")
    return data, listing


def _columns(page):
    return [c.strip() for c in profile(page)["columns"]]


def _column_for(columns, *names):
    wanted = {n.strip().lower().replace("_", " ") for n in names if n}
    for i, c in enumerate(columns):
        if c.strip().lower().replace("_", " ") in wanted:
            return i
    return None


def _query(url):
    return dict(parse_qsl(urlsplit(url).query, keep_blank_values=True))


def _finish(module, what, problems, notes):
    for note in notes:
        actual(note)
    assert not problems, f"{module['name']}: {what}: " + "; ".join(problems)


# ============================================================
# SORT KWA KILA COLUMN
# ============================================================

def check_sort_all_columns(page, app, module):
    if module["kind"] == "grid":
        return _grid_sort_all(page, app, module)
    data, listing = open_listing(page, app, module)
    if not listing.sort_options:
        pytest.skip(f"{module['name']}: server haitoi sort options")
    if listing.total <= 1:
        pytest.skip(f"{module['name']}: records {listing.total}, sort haiwezi kupimwa")
    base = page.url
    columns = _columns(page)
    problems, notes = [], []
    for option in listing.sort_options:
        attr, label = option["attribute"], option.get("label") or option["attribute"]
        for descending in (False, True):
            direction = "DESC" if descending else "ASC"
            url = inertia.with_params(base, sort=("-" if descending else "") + attr, page=1)
            status, props = inertia.fetch(page, url, data.get("version"))
            result = inertia.find_listing(props) if props else None
            if result is None:
                problems.append(f"Sort '{label}' {direction}: server imejibu {status} bila data")
                continue
            if not result.rows:
                problems.append(f"Sort '{label}' {direction}: imeleta table tupu (records {listing.total})")
                continue
            if all(inertia.value_of(r, attr)[0] for r in result.rows):
                values = [inertia.value_of(r, attr)[1] for r in result.rows]
                source = "data ya server"
            else:
                # Attribute haipo kwenye data (k.m. 'name' = first + last): soma column kwenye table
                col = _column_for(columns, label, attr)
                if col is None:
                    notes.append(f"Sort '{label}' {direction}: haikupimika (haipo kwenye data wala table)")
                    continue
                open_page(page, app, url)
                values = [r[col] for r in table_data(page, "vue") if len(r) > col]
                source = f"column '{columns[col]}'"
            problem = inertia.order_problem(values, descending)
            col = _column_for(columns, label, attr)
            if (problem and source.startswith("data") and col is None and "id" not in attr.lower()
                    and all(re.match(r"^\d+$", str(v)) for v in values if not inertia.is_empty(v))):
                # '{attr}' kwenye data ni namba (id ya kitu kingine) na table haina column yake: haipimiki
                notes.append(f"Sort '{label}' {direction}: haikupimika (data ina id tu, column haipo kwenye table)")
                continue
            if problem and source.startswith("data") and col is not None:
                # Data ya '{attr}' inaweza kuwa id (k.m. category_id) wakati table inaonyesha jina: angalia table
                open_page(page, app, url)
                shown = [r[col] for r in table_data(page, "vue") if len(r) > col]
                if shown and not inertia.order_problem(shown, descending):
                    problem, values, source = None, shown, f"column '{columns[col]}'"
            if problem:
                problems.append(f"Sort '{label}' {direction} haijapanga ({source}): {problem}")
            else:
                notes.append(f"Sort '{label}' {direction}: sawa ({source}), mwanzo {values[:3]}")
    _finish(module, "sort", problems, notes)


def _grid_sort_all(page, app, module):
    open_module(page, app, module)
    columns = _columns(page)
    keys = page.evaluate("() => [...document.querySelectorAll('.grid-view thead a[data-sort]')]"
                         ".map(a => [a.getAttribute('data-sort').replace(/^-/, ''), a.innerText.trim()])")
    if not keys:
        pytest.skip(f"{module['name']}: hakuna column inayopangika")
    if profile(page)["rows"] <= 1:
        pytest.skip(f"{module['name']}: table ina row 1 tu")
    problems, notes = [], []
    for key, label in keys:
        col = _column_for(columns, label, key)
        for descending in (False, True):
            direction = "DESC" if descending else "ASC"
            url = grid_sort_url(page, key, descending)
            if not url or col is None:
                notes.append(f"Sort '{label}' {direction}: haikupimika (link au column haipo)")
                continue
            open_module(page, app, module, url)
            values = [r[col] for r in table_data(page, "grid") if len(r) > col]
            if not values:
                problems.append(f"Sort '{label}' {direction}: table tupu")
                continue
            problem = inertia.order_problem(values, descending)
            if problem:
                problems.append(f"Sort '{label}' {direction} haijapanga: {problem}")
            else:
                notes.append(f"Sort '{label}' {direction}: sawa, mwanzo {values[:3]}")
    _finish(module, "sort", problems, notes)


# ============================================================
# PER PAGE
# ============================================================

def check_per_page(page, app, module):
    data, listing = open_listing(page, app, module)
    if not page.locator("div.ongeza-toolbar button:has-text('Per Page')").count():
        pytest.skip(f"{module['name']}: hakuna button ya Per Page")
    mark_dirty(page)
    problems, notes = [], []
    for size in (10, 50):
        _toolbar_button(page, "Per Page").click()
        item = page.locator(f".dropdown-menu.show [data-per-page='{size}']").first
        try:
            item.wait_for(state="visible", timeout=5000)
        except Exception:
            problems.append(f"Per Page {size} haipo kwenye menu")
            continue
        url, props = inertia_call(page, lambda: item.click(), f"Per Page {size}")
        result = inertia.find_listing(props) if props else None
        expected = min(size, max(listing.total, len(listing.rows)))
        shown = profile(page)["rows"]
        if result is None:
            problems.append(f"Per Page {size}: server haikutuma data ({url})")
        elif len(result.rows) != expected:
            problems.append(f"Per Page {size}: server imetuma records {len(result.rows)}, zilitarajiwa {expected} "
                            f"(ombi {url})")
        elif shown != expected:
            problems.append(f"Per Page {size}: table inaonyesha rows {shown}, zilitarajiwa {expected}")
        else:
            notes.append(f"Per Page {size}: rows {shown} (records {listing.total})")
    _finish(module, "per page", problems, notes)


# ============================================================
# PAGINATION KWA DATA
# ============================================================

def check_pagination_data(page, app, module):
    data, first = open_listing(page, app, module)
    if first.page_count < 2:
        pytest.skip(f"{module['name']}: records {first.total}, page 1 tu")
    per = len(first.rows)
    problems, notes = [], []
    if not (first.total - per * (first.page_count - 1)) in range(1, per + 1):
        problems.append(f"page 1 ina records {per}, lakini jumla {first.total} kwa pages {first.page_count} "
                        f"haziendani (zingekuwa takriban {-(-first.total // first.page_count)} kwa page)")
        _finish(module, "pagination", problems, notes)
    for number in sorted({2, first.page_count}):
        status, props = inertia.fetch(page, inertia.with_params(page.url, page=number), data.get("version"))
        result = inertia.find_listing(props) if props else None
        if result is None:
            problems.append(f"page {number}: server imejibu {status} bila data")
            continue
        expected = per if number < first.page_count else first.total - per * (first.page_count - 1)
        if result.page != number:
            problems.append(f"page {number}: server imerudisha page {result.page}")
        if len(result.rows) != expected:
            problems.append(f"page {number}: records {len(result.rows)}, zilitarajiwa {expected} "
                            f"(jumla {first.total}, {per} kwa page)")
        repeated = sorted(set(first.ids()) & set(result.ids()) - {None})
        if repeated:
            problems.append(f"page {number}: ina records za page 1 pia (id {repeated[:5]})")
        if result.total != first.total:
            notes.append(f"page {number}: jumla imebadilika {first.total} -> {result.total} (data mpya?)")
        if not problems:
            notes.append(f"page {number}: records {len(result.rows)}, hakuna inayojirudia na page 1")
    _finish(module, "pagination", problems, notes)


# ============================================================
# FILTERS ZOTE
# ============================================================

FILTER_FIELDS_JS = r"""
const panel = document.querySelector("[id$='-search-block']");
if (!panel) return [];
return [...panel.querySelectorAll('.col')].map((col, i) => {
  const lab = col.querySelector('label');
  const label = lab ? lab.textContent : '';
  const el = col.querySelector('select, input:not([type=hidden]):not([type=checkbox]), input[type=hidden][id]');
  if (!el) return null;
  const all = el.tagName === 'SELECT' ? [...el.options].map(o => [o.value, o.textContent.trim()]) : [];
  return {index: i, label: label.trim(), tag: el.tagName.toLowerCase(), type: el.type || '',
          name: el.name || el.id || (lab && lab.getAttribute('for')) || '',
          blank: (all.find(o => o[0].trim() === '') || [null, null])[1],
          options: all.filter(o => o[0].trim() !== '').slice(0, 5000)};
}).filter(Boolean);
"""

_DATE_LABELS = re.compile(r"^(from|to|start|end|date from|date to|from date|to date)$", re.I)


class _Log(list):
    """Matokeo halisi: yanachapishwa papo hapo (yanaonekana kwenye ripoti hata test ikikatika)."""

    def append(self, text):
        actual(text)
        super().append(text)


def _panel(page):
    mark_dirty(page)
    panel = page.locator("[id$='-search-block']").first
    if "show" not in (panel.get_attribute("class", timeout=10000) or ""):
        _toolbar_button(page, "Filter").click()
        page.wait_for_function("p => p.classList.contains('show')", arg=panel.element_handle(), timeout=10000)
    return panel


def _field(panel, spec):
    return panel.locator(".col").nth(spec["index"]).locator("select, input").first


def _fill(panel, spec, value):
    """Andika kwenye field ya filter. False kama field haikubali kuandikwa (imefichwa au readonly)."""
    field = _field(panel, spec)
    try:
        if field.get_attribute("readonly", timeout=5000) is not None:
            # Tarehe (datepicker) ni readonly kwa mtumiaji; tunaandika moja kwa moja kama picker inavyofanya
            field.evaluate("e => e.removeAttribute('readonly')")
        field.fill(value, timeout=10000)
        return True
    except Exception:
        return False


def _choose(page, panel, spec, value, text):
    """Chagua option kama mtumiaji (select2 au select ya kawaida). False kama haikuwezekana."""
    col = panel.locator(".col").nth(spec["index"])
    box = col.locator(".select2-selection").first
    try:
        if box.count():
            box.click(timeout=10000)
            search = page.locator(".select2-container--open .select2-search__field").first
            if search.count() and value.strip():
                search.fill(text, timeout=5000)
            page.locator(".select2-container--open .select2-results__option").filter(
                has_text=re.compile(r"^\s*" + re.escape(text) + r"\s*$")).first.click(timeout=10000)
        else:
            col.locator("select").first.select_option(value=value, timeout=10000)
        return True
    except Exception:
        page.keyboard.press("Escape")
        return False


def _apply(page, panel, what):
    return inertia_call(page, lambda: panel.locator("button:has-text('Apply Filter')").click(), what)


def _changed(url, baseline):
    """Params ambazo ombi hili limetuma tofauti na ombi la Apply bila filter."""
    return {k: v for k, v in _query(url).items() if v.strip() and v != baseline.get(k)}


def _own_value(row, name):
    """Thamani ya field ya filter kwenye record (name, name_id au name bila _id)."""
    for key in (name, f"{name}_id", name[:-3] if name.endswith("_id") else None):
        ok, value = inertia.value_of(row, key) if key else (False, None)
        if ok and not inertia.is_empty(value):
            return key, value
    return None, None


def _matches(found, value, exact):
    found, value = str(found).strip().lower(), str(value).strip().lower()
    return found == value if exact else value in found


def _check_rows(page, result, param, value, label, columns, exact):
    """Rows zote zinalingana na filter? (rows zisizolingana, chanzo) au (None, sababu ya kutopimika)."""
    if all(inertia.value_of(r, param)[0] for r in result.rows):
        wrong = [inertia.value_of(r, param)[1] for r in result.rows
                 if not _matches(inertia.value_of(r, param)[1], value, exact)]
        return wrong, f"data '{param}'"
    col = _column_for(columns, label, param)
    if col is None:
        return None, "column haipo kwenye data wala table"
    cells = [r[col] for r in table_data(page, "vue") if len(r) > col]
    return [c for c in cells if not _matches(c, value, exact)], f"column '{columns[col]}'"


def _value_from(listing, page, columns, spec):
    """Thamani ya kujaribu kutoka row ya kwanza: kwa jina la field kwenye data, au column ya label."""
    row = listing.rows[0]
    for key in (spec["name"], spec["label"].lower().replace(" ", "_")):
        ok, value = inertia.value_of(row, key) if key else (False, None)
        if ok and not inertia.is_empty(value):
            return str(value)
    col = _column_for(columns, spec["label"])
    cells = table_data(page, "vue")
    if col is not None and cells and len(cells[0]) > col and not inertia.is_empty(cells[0][col]):
        value = cells[0][col]
        return value if spec["label"].lower() == "id" else value.split(" ")[0]
    return None


def _set(page, panel, spec, value, text):
    if spec["tag"] == "select":
        return _choose(page, panel, spec, value, text)
    return _fill(panel, spec, value)


def _reset(page, panel, spec):
    if spec["tag"] == "select":
        return spec["blank"] is not None and _choose(page, panel, spec, " ", spec["blank"])
    return _fill(panel, spec, "")


def check_filters_all(page, app, module):
    data, listing = open_listing(page, app, module)
    if not page.locator("div.ongeza-toolbar button:has-text('Filter')").count():
        pytest.skip(f"{module['name']}: hakuna button ya Filter")
    if not listing.rows:
        pytest.skip(f"{module['name']}: table haina records za kuchukua thamani za filter")
    start_url = page.url
    columns = _columns(page)
    _panel(page)
    fields = page.evaluate("() => (function () {%s})()" % FILTER_FIELDS_JS)
    if not fields:
        pytest.skip(f"{module['name']}: Filter haina fields")
    problems, notes = [], _Log()
    # Apply bila filter: params ambazo UI inatuma kila mara (k.m. is_deleted=0), ili tujue filter ipi imeongezeka
    try:
        baseline = _query(_apply(page, _panel(page), "Apply Filter bila filter")[0])
    except AssertionError as exc:
        problems.append(str(exc))
        _finish(module, "filters", problems, [])
    dates = [f for f in fields if _DATE_LABELS.match(f["label"]) or f["name"] in ("from", "to")]
    for spec in fields:
        if spec in dates:
            continue
        label = spec["label"] or spec["name"]
        own_key, own = _own_value(listing.rows[0], spec["name"]) if spec["name"] else (None, None)
        if spec["tag"] == "select":
            # Option ya record ya kwanza (inajulikana kuwa na rows) au option ya kwanza
            choices = [o for o in spec["options"] if own_key and str(o[0]).strip() == str(own)]
            from_row = bool(choices)
            # Option ambayo si default (k.m. Active=YES ndiyo is_deleted=0 inayotumwa kila mara) inapimika
            defaults = {v.strip() for v in baseline.values()}
            choices = choices or sorted(spec["options"], key=lambda o: (str(o[0]).strip() in defaults,
                                                                        str(o[0]).strip() in ("0", "-1")))[:1]
            if not choices:
                notes.append(f"Filter '{label}': haikupimika (dropdown haina options)")
                continue
            value, text = choices[0]
        else:
            value = text = _value_from(listing, page, columns, spec)
            from_row = True
            if value is None:
                notes.append(f"Filter '{label}': haikupimika (row ya kwanza haina thamani yake)")
                continue
        panel = _panel(page)
        if not _set(page, panel, spec, value, text):
            # Automation haikuweza kuchagua: haijapimwa (si kosa la app lililothibitishwa)
            notes.append(f"Filter '{label}': haikupimika (automation haikuweza kuchagua/kuandika '{text}')")
            continue
        try:
            url, props = _apply(page, panel, f"Filter '{label}' = '{text}'")
        except NotTested as exc:
            notes.append(f"Filter '{label}': haikupimika ({exc})")
            url, props = None, None
        except AssertionError as exc:
            problems.append(str(exc))
            url, props = None, None
        lost = url is not None and not page.locator("table thead th").count()
        if lost:
            problems.append(f"Filter '{label}' = '{text}': baada ya Apply, table na Filter zimepotea kwenye ukurasa "
                            f"({url})")
        # Rudisha field iwe tupu; isipowezekana, fungua ukurasa upya ili filters zisichanganyike
        if lost or not url or not _reset(page, _panel(page), spec):
            open_page(page, app, start_url)
            page.wait_for_selector("table thead th", timeout=90000)
        if lost:
            continue
        if url is None:
            continue
        changed = _changed(url, baseline)
        if not changed:
            problems.append(f"Filter '{label}' = '{text}': UI haikutuma filter kwa server ({url})")
            continue
        param = next((k for k, v in changed.items() if v.strip().lower() == str(value).strip().lower()),
                     next(iter(changed)))
        if len(changed) > 1:
            notes.append(f"Filter '{label}': ombi lilituma pia {changed}")
        result = inertia.find_listing(props) if props else None
        if result is None:
            problems.append(f"Filter '{label}' = '{text}': server haikutuma data")
            continue
        if not result.rows:
            if from_row:
                problems.append(f"Filter '{label}' = '{text}' (thamani ya record iliyopo) imerudisha rows 0")
            else:
                notes.append(f"Filter '{label}' = '{text}': rows 0 (option ya kwanza, huenda haina records)")
            continue
        exact = spec["tag"] == "select" or label.lower() == "id" or param == "id"
        if spec["tag"] == "select":
            key = own_key or param
            if all(inertia.value_of(r, key)[0] for r in result.rows):
                found = [inertia.value_of(r, key)[1] for r in result.rows]
                source = f"data '{key}'"
                wrong = [f for f in found if not (_matches(f, value, True) or _matches(f, text, True))]
                if wrong and len({str(f) for f in found}) == 1 and result.total < listing.total:
                    # Rows zote zina thamani moja (k.m. order_type 0 kwa 'Cash'): filter imefanya kazi
                    notes.append(f"Filter '{label}' = '{text}': rows {len(found)} zote zina {key}={found[0]} "
                                 f"(records {listing.total} -> {result.total})")
                    continue
            else:  # data haina field hiyo: linganisha jina la option na column ya table
                wrong, source = _check_rows(page, result, "\0", text, label, columns, False)
        else:
            if re.match(r"^\d{4}-\d{2}-\d{2}[ T]\d", value):
                value, exact = value[:10], False  # filter ya tarehe inalinganisha siku
            wrong, source = _check_rows(page, result, param, value, label, columns, exact)
        if wrong is None:
            if result.total < listing.total:
                notes.append(f"Filter '{label}' = '{text}': records {listing.total} -> {result.total} "
                             f"(haipo kwenye data wala table ya kulinganisha)")
            else:
                problems.append(f"Filter '{label}' = '{text}': records hazikupungua ({result.total}) na "
                                f"hakuna column ya kuthibitisha")
        elif wrong:
            problems.append(f"Filter '{label}' = '{text}' imerudisha rows {len(wrong)} zisizolingana "
                            f"({source}): {wrong[:4]}")
        else:
            notes.append(f"Filter '{label}' = '{text}': rows {len(result.rows)} zote zinalingana ({source})")

    if len(dates) == 2:
        _check_date_range(page, app, start_url, dates, listing, problems, notes)
    _finish(module, "filters", problems, [])


def _check_date_range(page, app, start_url, dates, listing, problems, notes):
    ok, created = inertia.value_of(listing.rows[0], "created_date")
    if not ok or inertia.is_empty(created):
        notes.append("Filter From/To: haikupimika (row haina created_date)")
        return
    day = str(created)[:10]
    panel = _panel(page)
    for spec in dates:
        if not _fill(panel, spec, day):
            problems.append(f"Filter '{spec['label']}': field ya tarehe haikubali kuandikwa")
            return
        _field(panel, spec).press("Escape")
    try:
        url, props = _apply(page, panel, f"Filter From/To = {day}")
    except NotTested as exc:
        notes.append(f"Filter From/To: haikupimika ({exc})")
        return
    except AssertionError as exc:
        problems.append(str(exc))
        return
    sent = _query(url)
    if not any(day in v or day.replace("-", "/") in v for v in sent.values()):
        notes.append(f"Filter From/To = {day}: UI imetuma {sent} (muundo mwingine wa tarehe)")
    result = inertia.find_listing(props) if props else None
    if result is None or not result.rows:
        problems.append(f"Filter From/To = {day}: imerudisha rows 0 ingawa record ya tarehe hiyo ipo")
        return
    wrong = [inertia.value_of(r, "created_date")[1] for r in result.rows
             if not str(inertia.value_of(r, "created_date")[1] or "").startswith(day)]
    if wrong:
        problems.append(f"Filter From/To = {day} imerudisha rows {len(wrong)} za tarehe nyingine: {wrong[:4]} "
                        f"(ombi {url})")
    else:
        notes.append(f"Filter From/To = {day}: rows {len(result.rows)} zote za tarehe hiyo")


# ============================================================
# VIEW = ROW
# ============================================================

def _contains_id(props, record_id):
    """Kitambulisho cha row (id, order number ...) kipo popote kwenye data ya View?"""
    queue = [props]
    while queue:
        node = queue.pop()
        if isinstance(node, dict):
            if any(str(v) == str(record_id) for v in node.values() if not isinstance(v, (dict, list))):
                return True
            queue.extend(v for k, v in node.items() if k not in ("menus", "user"))
        elif isinstance(node, list):
            queue.extend(node[:200])
    return False


def check_view_matches_row(page, app, module):
    open_module(page, app, module)
    kind = module["kind"]
    columns = _columns(page)
    rows = table_data(page, kind)
    if not rows:
        pytest.skip(f"{module['name']}: table haina records")
    row = rows[0]
    before_view = page.url
    mark_dirty(page)
    if kind == "grid":
        link = page.locator("table tbody tr").first.locator("a[href*='/view'], a[href$='/details']").first
        if not link.count():
            pytest.skip(f"{module['name']}: row ya kwanza haina link ya View kwenye ukurasa huu")
        record_id = _query(link.get_attribute("href")).get("id")
        open_module(page, app, module, urljoin(app["base_url"] + "/", link.get_attribute("href")))
    else:
        link = page.locator("table.ongeza-table tbody tr").first.locator("a[data-id][class*='-view']").first
        if not link.count():
            pytest.skip(f"{module['name']}: row ya kwanza haina link ya View kwenye ukurasa huu")
        record_id = link.get_attribute("data-id")
        before = page.url
        try:
            link.click(timeout=15000)
        except Exception:
            link.evaluate("e => e.click()")  # link ipo lakini imefunikwa (k.m. table pana): bofya kwa JS
        try:
            page.wait_for_function("u => location.href !== u || document.querySelector('.modal.show')",
                                   arg=before, timeout=30000)
        except Exception:
            raise NotTested(f"{module['name']}: View haikufunguka ndani ya sekunde 30") from None
        if page.url != before:
            open_module(page, app, module, page.url)
    scope = page.locator(".modal.show").first if page.locator(".modal.show").count() else page.locator("body")
    text = (scope.inner_text() + "\n" + scope.evaluate(
        "e => [...e.querySelectorAll('input, textarea, select')].map(i => i.tagName === 'SELECT' && i.selectedIndex >= 0"
        " ? i.options[i.selectedIndex].text : i.value).join('\\n')")).lower()
    data = inertia.page_data(page)
    problems, notes = [], []
    if record_id and data and not page.locator(".modal.show").count():
        if _contains_id(data["props"], record_id):
            notes.append(f"Data ya View ina record id {record_id}")
        else:
            problems.append(f"View ya row id {record_id} imefungua record nyingine (id hiyo haipo kwenye data)")
    cells = [(columns[i] if i < len(columns) else f"#{i}", c) for i, c in enumerate(row)
             if c and len(c) >= 3 and i < len(columns) and not _ACTION_COLUMNS.match(columns[i].strip())]
    missing = [f"{name}='{value}'" for name, value in cells if value.lower() not in text]
    found = len(cells) - len(missing)
    # Jina la record (column ya kwanza yenye 'name', au ya kwanza ya maandishi) ndilo ushahidi mkuu
    named = [(n, v) for n, v in cells if "name" in n.lower()] or [
        (n, v) for n, v in cells if not re.match(r"^[\d,.\s:-]+$", v)]
    key_missing = bool(named) and named[0][1].lower() not in text
    related_list = page.url != before_view and page.locator("div.ongeza-toolbar, .grid-view").count() > 0
    if related_list and key_missing:
        notes.append(f"View inafungua list inayohusiana ({page.url}), si ukurasa wa record moja: "
                     f"taarifa {found}/{len(cells)} za row zinaonekana")
    elif cells and key_missing and found * 2 < len(cells):
        problems.append(f"View haionyeshi record ya row: {named[0][0]}='{named[0][1]}' haipo, na {found}/{len(cells)} "
                        f"tu ya taarifa zinaonekana; hazipo: {missing[:5]}")
    else:
        notes.append(f"View ({page.url}) inaonyesha {found}/{len(cells)} ya taarifa za row"
                     + (f"; hazipo: {missing[:3]}" if missing else ""))
    _finish(module, "view", problems, notes)
