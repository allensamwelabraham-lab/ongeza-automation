import os
import json
import re
from urllib.parse import urljoin, urlparse

from core.config import MODULES_DIR


# ============================================================
# LINKS AMBAZO HAZIFAI KUFUNGULIWA NA TESTS
# ============================================================

SKIP_PATTERNS = [
    r"logout", r"log-out", r"signout", r"sign-out",
    r"/(delete|destroy|remove)([/?-]|$)",
    r"export", r"download", r"print",
    r"\.(pdf|xlsx?|csv|zip|apk)(\?|$)",
    r"^mailto:", r"^tel:", r"^javascript:",
]


def is_safe_link(href):
    return not any(re.search(p, href, re.IGNORECASE) for p in SKIP_PATTERNS)


# ============================================================
# DISCOVER MENU (sidebar/navbar)
# ============================================================

COLLECT_LINKS_JS = """
const containers = Array.from(document.querySelectorAll(
  'nav, aside, .sidebar, .main-sidebar, .side-menu, .sidenav, .navbar, ' +
  '.menu, [class*="sidebar"], [class*="menu"], [role="navigation"]'
));
let anchors = [];
containers.forEach(c => anchors.push(...c.querySelectorAll('a[href]')));
if (anchors.length < 3) anchors = Array.from(document.querySelectorAll('a[href]'));

function groupOf(a) {
  // Jina la kundi la menu (k.m. "Workers" > "Agents")
  let li = a.closest('li');
  if (!li) return '';
  let parentLi = li.parentElement ? li.parentElement.closest('li') : null;
  if (!parentLi) return '';
  let toggle = parentLi.querySelector(':scope > a, :scope > span, :scope > div, :scope > button');
  return toggle ? toggle.textContent.replace(/\\s+/g, ' ').trim() : '';
}

return anchors.map(a => ({
  href: a.getAttribute('href'),
  text: (a.textContent || a.getAttribute('title') || '').replace(/\\s+/g, ' ').trim(),
  group: groupOf(a),
}));
"""


def slugify(text):
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug or "module"


def discover_menu(driver, base_url):
    base_host = urlparse(base_url).netloc
    raw = driver.execute_script(COLLECT_LINKS_JS)

    modules = {}
    for link in raw:
        href = (link.get("href") or "").strip()
        if not href or href in ("#", "/", "#/") or not is_safe_link(href):
            continue
        if href.startswith("#") and not href.startswith("#/"):
            continue

        url = urljoin(base_url + "/", href)
        parsed = urlparse(url)
        if parsed.netloc != base_host:
            continue

        path = parsed.path + (f"#{parsed.fragment}" if parsed.fragment.startswith("/") else "")
        if path in ("", "/") or path in modules:
            continue

        name = link.get("text") or path
        group = link.get("group") or ""
        if group and group != name:
            name = f"{group} > {name}"

        modules[path] = {
            "id": slugify(path),
            "name": name,
            "path": path,
        }

    return list(modules.values())


# ============================================================
# modules/<app>.json
# ============================================================

def modules_file(app_key):
    return MODULES_DIR / f"{app_key}.json"


def load_modules(app_key):
    path = modules_file(app_key)
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    modules = data.get("modules", [])
    # tools.run_module inaweka INCLUDE_SKIPPED=1 ili module uliyoichagua iendeshwe hata kama ni slow
    if os.getenv("INCLUDE_SKIPPED", "0") == "1":
        return modules
    return [m for m in modules if not m.get("skip")]


def save_modules(app_key, payload):
    MODULES_DIR.mkdir(parents=True, exist_ok=True)
    modules_file(app_key).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    )
