"""
Inagundua modules zote za app kutoka kwenye sidebar, inafungua kila moja (bila
kusave chochote) na kuandika modules/<app>.json + modules/<app>.md.

Kwa kila module inahifadhi: aina ya ukurasa (vue / grid / table / page), heading,
columns za table, idadi ya records, sort keys, filters, link ya Create/Add na
fields za form yake. Tests (tests/<app>/test_modules.py n.k.) zinatumia JSON hii
kama "baseline": column ikipotea au ukurasa ukianza kuleta error, test inashindwa.

Mfano:
    python -m tools.discover --app ongeza
    python -m tools.discover --app all --workers 4
    python -m tools.discover --app ongeza --only /crud/district
"""

import argparse
import json
import queue
import re
import threading
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

from selenium.webdriver.common.by import By

from core.config import APPS, get_app
from core.driver import create_driver
from core.helpers import click, describe_form, find_error_on_page, wait_until
from core.modules import MODULES_DIR, is_safe_link, modules_file, save_modules, slugify
from core.pages import open_page, profile
from core.session import ensure_logged_in, is_login_page


# Mipangilio unayoweka mwenyewe kwenye JSON ambayo discover haitaifuta
USER_KEYS = ("skip", "validate_empty_submit", "add_path", "notes", "expect", "ignore_error_text")


SIDEBAR_LINKS_JS = r"""
const sides = Array.from(document.querySelectorAll('#sidebar, .app-sidebar, .sidebar, aside'))
  .sort((a, b) => b.querySelectorAll('a[href]').length - a.querySelectorAll('a[href]').length);
const side = sides.length && sides[0].querySelectorAll('a[href]').length ? sides[0] : document.body;
function label(a) { return (a.innerText || a.textContent || '').replace(/\s+/g, ' ').trim(); }
function groups(a) {
  const out = [];
  let item = a.closest('li, .menu-item');
  while (item) {
    const parent = item.parentElement ? item.parentElement.closest('li, .menu-item') : null;
    if (!parent) break;
    const t = parent.querySelector(':scope > a, :scope > .menu-link');
    if (t) out.unshift(label(t));
    item = parent;
  }
  return out.filter(Boolean);
}
return Array.from(side.querySelectorAll('a[href]')).map(a => ({
  href: a.getAttribute('href'), text: label(a), groups: groups(a),
}));
"""


EXPAND_SIDEBAR_JS = r"""
// Fungua menu zilizofungwa (ONGEZA PRO / shadcn sidebar)
document.querySelectorAll('[data-sidebar="menu-button"][data-slot="collapsible-trigger"]').forEach(b => {
  const item = b.closest('[data-state]');
  if (item && item.getAttribute('data-state') === 'closed') b.click();
});
"""

EXTRA_LINKS_JS = r"""
const prefixes = arguments[0];
return Array.from(document.querySelectorAll('main a[href], #content a[href]'))
  .filter(a => prefixes.some(p => (a.getAttribute('href') || '').startsWith(p)))
  .map(a => ({href: a.getAttribute('href'),
              text: (a.innerText || '').replace(/\s+/g, ' ').trim() || a.getAttribute('href'),
              groups: ['Dashboard']}));
"""


def name_from_path(path):
    """'/reports/sales/by-volume' -> 'Reports > Sales > By volume' (links zisizo na maandishi)."""
    parts = [p.replace("-", " ").replace("_", " ") for p in path.strip("/").split("/") if p]
    return " > ".join(p[:1].upper() + p[1:] for p in parts) or path


def sidebar_modules(driver, base_url, extra_prefixes=()):
    host = urlparse(base_url).netloc
    seen = {}
    driver.execute_script(EXPAND_SIDEBAR_JS)
    time.sleep(0.5)
    links = driver.execute_script(SIDEBAR_LINKS_JS)
    if extra_prefixes:
        links += driver.execute_script(EXTRA_LINKS_JS, list(extra_prefixes))
    for link in links:
        href = (link.get("href") or "").strip()
        if not href or href.startswith(("#", "javascript")) or not is_safe_link(href):
            continue
        url = urljoin(base_url + "/", href)
        parts = urlparse(url)
        if parts.netloc != host:
            continue
        path = parts.path + (f"?{parts.query}" if parts.query else "")
        if parts.path in ("", "/") or path in seen:
            continue
        group = " > ".join(g for g in link.get("groups") or [] if g)
        text = link.get("text") or ""
        # Kadi za dashboard zina namba ndani ya maandishi ("Customers 252,683 total ...")
        card = len(text) > 40 or bool(re.search(r"\d", text))
        name = name_from_path(parts.path) if not text or text.startswith("/") or card else text
        seen[path] = {
            "id": slugify(parts.path),
            "name": f"{group} > {name}" if group else name,
            "path": path,
        }

    # id za kipekee (path moja inaweza kuwa na query tofauti)
    used = {}
    for module in seen.values():
        base = module["id"]
        used[base] = used.get(base, 0) + 1
        if used[base] > 1:
            module["id"] = f"{base}_{used[base]}"
    return list(seen.values())


# ============================================================
# INSPECT MODULE MOJA
# ============================================================

def open_create(driver, app, info):
    """Fungua form ya Create/Add (bila kusave) na urudishe path + fields."""
    if info.get("createHref"):
        open_page(driver, app, urljoin(app["base_url"] + "/", info["createHref"]))
    elif info.get("addButton"):
        before = driver.current_url
        buttons = [
            b for b in driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'ongeza-toolbar-actions')]//*[self::button or self::a]",
            )
            if b.text.strip() == info["addButton"]
        ]
        if not buttons:
            return None
        click(driver, buttons[0])
        time.sleep(2)
        if driver.current_url == before:
            return {"create_path": None, "create_in_modal": True,
                    "form_fields": describe_form(driver)}
    else:
        return None

    return {
        "create_path": driver.current_url.replace(app["base_url"], "", 1),
        "create_error": find_error_on_page(driver),
        "form_fields": describe_form(driver),
    }


def inspect_module(driver, app, module):
    start = time.time()
    error = open_page(driver, app, module["path"])
    if is_login_page(driver):
        ensure_logged_in(driver, app)
        error = open_page(driver, app, module["path"])
    seconds = round(time.time() - start, 1)

    info = profile(driver)
    result = {
        "final_url": driver.current_url.replace(app["base_url"], "", 1),
        "load_seconds": seconds,
        "error": error,
        "kind": info["kind"],
        "heading": info["heading"][:120],
        "columns": info["columns"],
        "total": info["total"],
        "rows": info["rows"],
        "sort_keys": info["sortKeys"],
        "filters": info["filters"],
        "has_pagination": info["hasPagination"],
        "view_href": info["viewHref"],
        "vue_view": info["vueView"],
        "add_button": info["addButton"],
    }

    if not error and (info.get("createHref") or info.get("addButton")):
        try:
            result.update(open_create(driver, app, info) or {})
        except Exception as exc:
            result["create_error"] = f"{exc.__class__.__name__}: {str(exc)[:120]}"

    return result


# ============================================================
# DISCOVER APP (browsers kadhaa kwa pamoja)
# ============================================================

def discover_app(app_key, workers=3, only=None, resume=True):
    app = get_app(app_key)

    driver = create_driver()
    try:
        ensure_logged_in(driver, app)
        modules = []
        # Dashboard ni nzito (inaweza kuleta 504); sidebar ipo kwenye kila ukurasa
        for start_path in ("/", app.get("menu_page", "/crud/ticket/index")):
            if open_page(driver, app, start_path):
                continue
            wait_until(driver, lambda d: len(sidebar_modules(d, app["base_url"])) > 5, timeout=30)
            time.sleep(2)
            modules = sidebar_modules(driver, app["base_url"], app.get("extra_link_prefixes", ()))
            if modules:
                break
        # Kurasa zenye links za ziada (k.m. ONGEZA PRO /reports)
        for page in app.get("extra_pages", ()):
            if open_page(driver, app, page):
                continue
            time.sleep(2)
            known = {m["path"] for m in modules}
            modules += [m for m in sidebar_modules(driver, app["base_url"], app.get("extra_link_prefixes", ()))
                        if m["path"] not in known]
    finally:
        driver.quit()

    if only:
        modules = [m for m in modules if any(o in m["path"] for o in only)]
    print(f"[{app['name']}] Sidebar modules: {len(modules)}")

    previous = {}
    if modules_file(app_key).exists():
        saved = json.loads(modules_file(app_key).read_text())
        previous = {m["path"]: m for m in saved.get("modules", [])}

    # Checkpoint: kila module ikimalizika inahifadhiwa kwenye <app>.partial.json, ili run
    # ikisimamishwa (Ctrl+C / kuzima kompyuta) inayofuata iendelee pale ilipoishia.
    partial_file = MODULES_DIR / f"{app_key}.partial.json"
    done = {}
    if resume and partial_file.exists():
        try:
            done = json.loads(partial_file.read_text())
        except ValueError:
            done = {}
        print(f"[{app['name']}] Inaendelea: {len(done)} modules zilikuwa zimeshagunduliwa")

    jobs = queue.Queue()
    for index, module in enumerate(modules):
        if module["path"] in done:
            module.update({k: v for k, v in done[module["path"]].items() if k not in ("id", "name", "path")})
            continue
        jobs.put((index, module))
    lock = threading.Lock()

    def worker():
        browser = create_driver()
        try:
            ensure_logged_in(browser, app)
            while True:
                try:
                    index, module = jobs.get_nowait()
                except queue.Empty:
                    return
                try:
                    module.update(inspect_module(browser, app, module))
                except Exception as exc:
                    module["error"] = f"inspect failed: {exc.__class__.__name__}: {str(exc)[:150]}"
                with lock:
                    done[module["path"]] = module
                    partial_file.write_text(json.dumps(done, ensure_ascii=False))
                    print(f"  [{index + 1}/{len(modules)}] {module['name']} "
                          f"({module['path']}) {module.get('kind')} "
                          f"{module.get('load_seconds')}s {module.get('error') or ''}", flush=True)
        finally:
            browser.quit()

    threads = [threading.Thread(target=worker) for _ in range(max(1, workers))]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for module in modules:
        for key in USER_KEYS:
            if key in previous.get(module["path"], {}):
                module[key] = previous[module["path"]][key]

    if only and previous:
        # Badilisha zile zilizochaguliwa tu, zingine zibaki
        merged = dict(previous)
        merged.update({m["path"]: m for m in modules})
        modules = list(merged.values())

    payload = {
        "app": app["name"],
        "base_url": app["base_url"],
        "discovered_at": datetime.now().isoformat(timespec="seconds"),
        "modules": modules,
    }
    save_modules(app_key, payload)
    write_summary(app, modules)
    partial_file.unlink(missing_ok=True)
    print(f"[{app['name']}] {len(modules)} modules -> {modules_file(app_key)}")


def write_summary(app, modules):
    lines = [
        f"# {app['name']} modules",
        "",
        "| Module | Path | Aina | Records | Columns | Sort | Filters | Create | Sek | Error |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for m in modules:
        create = m.get("create_path") or ("modal" if m.get("create_in_modal") else "")
        total = m.get("total")
        lines.append(
            f"| {m['name']} | `{m['path']}` | {m.get('kind', '')} | {'' if total is None else total} | "
            f"{len(m.get('columns') or [])} | {len(m.get('sort_keys') or [])} | "
            f"{len(m.get('filters') or [])} | {create} | {m.get('load_seconds', '')} | "
            f"{m.get('error') or m.get('create_error') or ''} |"
        )
    (MODULES_DIR / f"{app['key']}.md").write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app", required=True, choices=list(APPS) + ["all"])
    parser.add_argument("--workers", type=int, default=3, help="browsers za kufanya kazi pamoja")
    parser.add_argument("--only", nargs="*", help="gundua tu paths zenye maneno haya")
    parser.add_argument("--fresh", action="store_true",
                        help="anza upya (usiendelee na run iliyosimamishwa)")
    args = parser.parse_args()

    for app_key in (APPS if args.app == "all" else [args.app]):
        discover_app(app_key, workers=args.workers, only=args.only, resume=not args.fresh)


if __name__ == "__main__":
    main()
