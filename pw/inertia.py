"""
Data halisi ya kurasa za Inertia (Vue) za JUMLA/ONGEZA.

Kila ukurasa wa Inertia unakuja na JSON (props) yenye records, pagination, sort na filters.
Tunaitumia kama ukweli wa kulinganisha (badala ya kubahatisha kutoka maandishi ya skrini), na
tunaweza kuiomba moja kwa moja (GET + header X-Inertia) bila kuchora ukurasa: ni haraka mara kadhaa.
App yoyote ya Inertia yenye list ya umbo {data: [...], pagination: {...}} inafanya kazi bila kubadilisha code.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from pw.pages import REQUEST_TIMEOUT, NotTested


@dataclass
class Listing:
    rows: list
    page: int = 1
    page_count: int = 1
    total: int = 0
    sort_options: list = field(default_factory=list)  # [{"attribute": "id", "label": "ID"}, ...]
    params: dict = field(default_factory=dict)
    links: dict = field(default_factory=dict)

    def ids(self):
        return [r.get("id") for r in self.rows if isinstance(r, dict)]


def find_listing(props):
    """Tafuta list ndani ya props: dict yenye 'data' (list) na 'pagination' (dict). None kama haipo."""
    queue = [props]
    while queue:
        node = queue.pop(0)
        if isinstance(node, dict):
            if isinstance(node.get("data"), list) and isinstance(node.get("pagination"), dict):
                p = node["pagination"]
                return Listing(
                    rows=node["data"],
                    page=int(p.get("page") or 1),
                    page_count=int(p.get("pageCount") or p.get("last_page") or 1),
                    total=int(p.get("totalCount") or p.get("total") or 0),
                    sort_options=[s for s in node.get("sort") or [] if isinstance(s, dict) and s.get("attribute")],
                    params=node.get("params") if isinstance(node.get("params"), dict) else {},
                    links=p.get("links") or {},
                )
            queue.extend(v for k, v in node.items() if k not in ("menus", "user", "badges"))
    return None


def page_data(page):
    """{component, url, version, props} ya ukurasa ulio wazi, au None (ukurasa si Inertia)."""
    if not page.locator("[data-page]").count():
        return None
    try:
        return json.loads(page.get_attribute("[data-page]", "data-page", timeout=5000))
    except (ValueError, TypeError):
        return None


def with_params(url, **params):
    """URL yenye query params hizi (None = ondoa param)."""
    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    for key, value in params.items():
        if value is None:
            query.pop(key, None)
        else:
            query[key] = str(value)
    return urlunsplit(parts._replace(query=urlencode(query)))


def fetch(page, url, version):
    """Omba ukurasa kama Inertia inavyofanya (JSON tu, bila kuchora). Inarudisha (status, props au None)."""
    url = urljoin(page.url, url)
    try:
        response = page.request.get(url, timeout=REQUEST_TIMEOUT * 1000, headers={
            "X-Inertia": "true", "X-Inertia-Version": version or "", "X-Requested-With": "XMLHttpRequest",
            "Accept": "text/html, application/xhtml+xml"})
    except Exception as exc:
        raise NotTested(f"{url}: server haikujibu ndani ya sekunde {REQUEST_TIMEOUT} ({str(exc)[:100]})") from None
    if response.status in (502, 503, 504):
        raise NotTested(f"staging imejibu {response.status} kwa {url}")
    if response.status >= 400:
        return response.status, None
    try:
        return response.status, response.json().get("props")
    except Exception:
        return response.status, None


# ============================================================
# KULINGANISHA MPANGILIO (SORT)
# ============================================================

_NUMBER = re.compile(r"^-?\d+(\.\d+)?$")
_DATE_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y")


def value_of(row, attribute):
    """Thamani ya attribute kwenye row (inafuata 'a.b' kwa relations). (True, value) au (False, None)."""
    node = row
    for part in attribute.split("."):
        if not isinstance(node, dict) or part not in node:
            return False, None
        node = node[part]
    if isinstance(node, (dict, list)):
        return False, None
    return True, node


def sort_key(value):
    """Ufunguo wa kulinganisha kama database: namba kama namba, tarehe kama tarehe, maandishi bila herufi kubwa."""
    if isinstance(value, bool):
        return (0, int(value))
    if isinstance(value, (int, float)):
        return (0, value)
    text = str(value).strip()
    plain = text.replace(",", "")
    if _NUMBER.match(plain):
        return (0, float(plain))
    for fmt in _DATE_FORMATS:
        try:
            return (1, datetime.strptime(text[:19], fmt).timestamp())
        except ValueError:
            pass
    return (2, text.casefold())


def is_empty(value):
    return value is None or (isinstance(value, str) and value.strip() in ("", "-", "--"))


def order_problem(values, descending):
    """None kama values zimepangwa (zikiacha tupu); vinginevyo maelezo ya jozi ya kwanza iliyokosewa."""
    keys = [(v, sort_key(v)) for v in values if not is_empty(v)]
    kinds = {k[0] for _, k in keys}
    if len(kinds) > 1:  # mchanganyiko (namba na maandishi): linganisha kama maandishi
        keys = [(v, (2, str(v).strip().casefold())) for v, _ in keys]
    for i in range(1, len(keys)):
        before, after = keys[i - 1][1], keys[i][1]
        if (after > before) if descending else (after < before):
            return f"'{keys[i - 1][0]}' kisha '{keys[i][0]}' (nafasi {i}-{i + 1})"
    return None
