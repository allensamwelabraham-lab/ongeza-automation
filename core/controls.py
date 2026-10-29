"""
Kila button ya module: test inabofya kila button / link / tab / dropdown iliyo kwenye ukurasa
wa module (si sidebar wala header) na kuhakikisha haileti error.

Kwa kila button:
  * write guard (core/guard.py) inawekwa kwanza, kwa hiyo button ikijaribu kutuma POST/PUT/DELETE
    ombi linazuiwa na hakuna kinachosaviwa wala kufutwa
  * buttons hatari (Delete, Sync, Push, Pay, Approve, Send, Logout, Import ...) hazibofywi kabisa;
    zinaorodheshwa kwenye ripoti kama "hazikubofywa kwa usalama"
  * baada ya kubofya: ukurasa usionyeshe error (500/404/SQL), server isijibu 5xx, browser isiwe na
    JS error, na isirudishe login page. Ukurasa mpya (link / tab mpya) unakaguliwa vilevile.
  * Export / CSV / Excel / PDF: inahakikisha file imepakuliwa
  * <select>: inachagua option nyingine, inakagua, kisha inarudisha ya awali

Buttons zinazofanana (k.m. "Edit" ya kila row) zinabofywa mara moja tu.
"""

import os
import re
import tempfile
import time
from urllib.parse import urlparse

import pytest
from selenium.common.exceptions import (
    NoAlertPresentException,
    StaleElementReferenceException,
    TimeoutException,
    UnexpectedAlertPresentException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from core.helpers import find_error_on_page, wait_page_ready
from core.modules import load_modules
from core.pages import _wait_content_stable
from core.session import is_login_page

MAX_CONTROLS = 60       # buttons tofauti zinazobofywa kwa module moja (zilizobaki zinatajwa kwenye ripoti)
SETTLE = 1.5            # sekunde za kusubiri baada ya kubofya
DOWNLOAD_WAIT = 25      # sekunde za kusubiri file ya Export
# Muda wa juu kwa module moja (kurasa nzito za staging): buttons zilizobaki zinatajwa kwenye ripoti
MODULE_BUDGET = int(os.getenv("BUTTONS_MODULE_SECONDS", "360"))

# Maandishi ya buttons ambazo hazibofywi kamwe (zinabadilisha data, zinatuma kwa watu au mifumo mingine)
DANGER_TEXT = re.compile(
    r"\b(delete|remove|trash|destroy|sync|push|patch|re-?queue|pay|paid|approve|reject|decline|send|resend|"
    r"import|upload|log ?out|sign ?out|reset|clear|disburse|publish|unpublish|activate|deactivate|enable|"
    r"disable|block|unblock|transfer|retry|restart|purge|auto-?map|map workers|hierarchy|dry run|preview|"
    r"generate|close|cancel|restore|confirm|save|submit|move up|move down|assign|refresh|populate|process|"
    r"calculate|recalculate|compute|execute|run now|start|stop|rebuild|regenerate|apply|post|reverse|"
    r"allocate|merge|split|lock|unlock|clone|duplicate|copy|archive|verify|validate|reconcile|commit|"
    r"migrate|seed|flush|notify|broadcast|dispatch|issue|receive|return|refund|write ?off|recompute)\b"
    r"|futa|tuma|hifadhi|lipa",
    re.I,
)
# Links ambazo hata GET yake inabadilisha kitu (k.m. /crud/x/delete?id=5)
DANGER_PATH = re.compile(
    r"^(delete\w*|remove\w*|destroy\w*|logout|sign-?out|sync\w*|push\w*|approve\w*|reject\w*|cancel\w*|"
    r"send\w*|resend\w*|pay|activate\w*|deactivate\w*|reset\w*|clear\w*|requeue\w*|import\w*|generate\w*|"
    r"disburse\w*|close\w*|restore\w*|toggle\w*|changestatus\w*|setstatus\w*|lock\w*|unlock\w*|block\w*|"
    r"unblock\w*|run\w*)$",
    re.I,
)
EXPORT_TEXT = re.compile(r"\b(export|csv|excel|xlsx?|pdf|json|download|pakua)\b", re.I)
# Icon-only buttons za kusoma tu (refresh ya list) zinaruhusiwa ingawa "refresh" iko kwenye DANGER_TEXT
SAFE_ICONS = ("refresh-cw", "fa-refresh", "fa-sync", "rotate")

CONTENT_ROOT = {
    # ONGEZA PRO (React/shadcn): maudhui yako ndani ya <main> ya pili; sidebar na nav ya juu ni nje
    "spa": "main main",
}
DEFAULT_ROOT = "#content"            # JUMLA / ONGEZA (Color Admin template)
EXCLUDE = (".breadcrumb, .panel-heading-btn, #sidebar, #header, .sidebar, nav.sticky, "
           "[data-slot=sidebar], .bg-sidebar, .pagination-info")

CONTROLS_JS = r"""
const [rootSel, excludeSel, menuPaths] = arguments;
const root = document.querySelector(rootSel) || document.querySelector('main') || document.body;
const vis = e => {
  const r = e.getClientRects();
  if (!r.length) return false;
  const s = getComputedStyle(e);
  return s.visibility !== 'hidden' && s.display !== 'none';
};
const iconOf = e => {
  const i = e.querySelector('svg[class*=lucide], i[class*=fa], i[class*=ion], span.glyphicon, i[class*=mdi]');
  if (!i) return '';
  const cls = (i.getAttribute('class') || '').split(/\s+/).filter(c => /^(lucide-|fa-|ion-|glyphicon-|mdi-)/.test(c) && !/-icon$/.test(c));
  return cls.join(' ');
};
const textOf = e => (e.tagName === 'SELECT' ? '' : (e.innerText || e.value || '')).trim().replace(/\s+/g, ' ').slice(0, 60);
const all = [...root.querySelectorAll(
  'a[href], a[class*=btn], a[data-id], button, [role=button], [role=tab], input[type=button], input[type=checkbox], select')];
const seen = new Map();
const out = [];
for (const e of all) {
  if (!vis(e) || e.closest(excludeSel)) continue;
  if (e.parentElement && e.parentElement.closest('a[href], button')) continue;   // button ndani ya link
  const href = e.getAttribute('href') || '';
  let path = '';
  try { path = href && !/^(javascript|#|mailto|tel)/i.test(href) ? new URL(href, location.href).pathname : ''; } catch (x) {}
  if (path && menuPaths.includes(path) && path !== location.pathname) continue;   // link ya menu (module nyingine)
  const inRow = e.closest('tbody tr');
  if (inRow && inRow !== inRow.parentElement.querySelector('tr')) continue;        // row ya kwanza tu
  const d = {
    tag: e.tagName.toLowerCase(), type: (e.getAttribute('type') || '').toLowerCase(),
    text: textOf(e), title: (e.getAttribute('title') || e.getAttribute('aria-label') || e.getAttribute('data-original-title') || '').trim().slice(0, 60),
    icon: iconOf(e), href: href.slice(0, 200), path, inRow: !!inRow,
    th: !!e.closest('thead'),
    disabled: !!(e.disabled || e.classList.contains('disabled') || e.getAttribute('aria-disabled') === 'true'),
    method: (e.getAttribute('data-method') || '').toLowerCase(), confirm: !!e.getAttribute('data-confirm'),
    target: e.getAttribute('target') || '',
    options: e.tagName === 'SELECT' ? [...e.options].map(o => o.text.trim()).slice(0, 30) : null,
  };
  // Kwa <select>: jina la field / label ndilo linaitambulisha
  if (d.tag === 'select') d.title = d.title || e.name || e.id || '';
  // Pagination: First / Prev / Next / Last na page "2" tu, si kila namba
  if (e.closest('.pagination, nav[aria-label*=agination], [data-slot=pagination]') && /^\d+$/.test(d.text) && d.text !== '2') continue;
  const sig = inRow ? [d.tag, d.type, '', d.title, d.icon, href.replace(/\d+/g, '#').slice(0, 200), true].join('|')
                    : [d.tag, d.type, d.text, d.title, d.icon, d.href, false].join('|');
  const n = seen.get(sig) || 0;
  seen.set(sig, n + 1);
  if (n) continue;   // inayofanana imeshaorodheshwa
  d.sig = sig;
  out.push(d);
}
return out;
"""

FIND_JS = r"""
const [rootSel, excludeSel, sig] = arguments;
const root = document.querySelector(rootSel) || document.querySelector('main') || document.body;
const iconOf = e => {
  const i = e.querySelector('svg[class*=lucide], i[class*=fa], i[class*=ion], span.glyphicon, i[class*=mdi]');
  if (!i) return '';
  return (i.getAttribute('class') || '').split(/\s+/).filter(c => /^(lucide-|fa-|ion-|glyphicon-|mdi-)/.test(c) && !/-icon$/.test(c)).join(' ');
};
const textOf = e => (e.tagName === 'SELECT' ? '' : (e.innerText || e.value || '')).trim().replace(/\s+/g, ' ').slice(0, 60);
for (const e of root.querySelectorAll('a[href], a[class*=btn], a[data-id], button, [role=button], [role=tab], input[type=button], input[type=checkbox], select')) {
  if (!e.getClientRects().length || e.closest(excludeSel)) continue;
  if (e.parentElement && e.parentElement.closest('a[href], button')) continue;
  const inRow = e.closest('tbody tr');
  if (inRow && inRow !== inRow.parentElement.querySelector('tr')) continue;
  let title = (e.getAttribute('title') || e.getAttribute('aria-label') || e.getAttribute('data-original-title') || '').trim().slice(0, 60);
  if (e.tagName === 'SELECT') title = title || e.name || e.id || '';
  const href = e.getAttribute('href') || '';
  const s = inRow ? [e.tagName.toLowerCase(), (e.getAttribute('type') || '').toLowerCase(), '', title, iconOf(e),
                     href.replace(/\d+/g, '#').slice(0, 200), true].join('|')
                  : [e.tagName.toLowerCase(), (e.getAttribute('type') || '').toLowerCase(), textOf(e), title, iconOf(e),
                     href.slice(0, 200), false].join('|');
  if (s === sig) return e;
}
return null;
"""

# Kama write guard ya core/guard.py, lakini POST za KUSOMA (list/search/report) zinaruhusiwa:
# ONGEZA PRO inasoma list zake kwa POST /api/.../list
READ_PATHS = r"/(list|search|index\d*|data|datatable|filter|report\w*|view|show|details|options|lookup|autocomplete|count|summary|stats|export\w*|preview-?list)(\?|/?$)"
GUARD_JS = r"""
if (window.__autoWriteGuard) return true;
const readOnly = new RegExp(arguments[0], 'i');
window.__autoWriteGuard = {blocked: []};
const log = (what) => window.__autoWriteGuard.blocked.push(what);
const pathOf = u => { try { return new URL(u, location.href).pathname; } catch (e) { return String(u); } };
window.addEventListener('submit', e => {
  if ((e.target.method || 'get').toLowerCase() === 'get') return;
  e.preventDefault(); log('submit:' + (e.target.action || ''));
}, true);
const origSubmit = HTMLFormElement.prototype.submit;
HTMLFormElement.prototype.submit = function () {
  if ((this.method || 'get').toLowerCase() === 'get') return origSubmit.apply(this);
  log('form.submit:' + (this.action || ''));
};
const origFetch = window.fetch;
window.fetch = function (input, init) {
  const method = ((init && init.method) || (input && input.method) || 'GET').toUpperCase();
  const url = typeof input === 'string' ? input : (input && input.url);
  if (method !== 'GET' && method !== 'HEAD' && !(method === 'POST' && readOnly.test(pathOf(url)))) {
    log('fetch:' + method + ':' + url);
    return Promise.reject(new Error('AUTO write guard'));
  }
  return origFetch.apply(this, arguments);
};
const origOpen = XMLHttpRequest.prototype.open;
const origSend = XMLHttpRequest.prototype.send;
XMLHttpRequest.prototype.open = function (method, url) {
  this.__autoMethod = (method || 'GET').toUpperCase();
  this.__autoUrl = url;
  return origOpen.apply(this, arguments);
};
XMLHttpRequest.prototype.send = function () {
  const m = this.__autoMethod;
  if (m !== 'GET' && m !== 'HEAD' && !(m === 'POST' && readOnly.test(pathOf(this.__autoUrl)))) {
    log('xhr:' + m + ':' + this.__autoUrl);
    try { this.abort(); } catch (e) {}
    return;
  }
  return origSend.apply(this, arguments);
};
return true;
"""

# Majibu yote ya server (GET pia) + JS errors, ili button inayoleta 500 kwa nyuma ionekane
WATCH_JS = r"""
if (window.__autoWatch) { window.__autoWatch.responses = []; window.__autoWatch.errors = []; return true; }
window.__autoWatch = {responses: [], errors: [], printed: 0};
const W = window.__autoWatch;
window.print = () => { W.printed++; };
window.addEventListener('error', e => W.errors.push(String(e.message || e.type).slice(0, 200)));
window.addEventListener('unhandledrejection', e => {
  const m = String((e.reason && (e.reason.message || e.reason)) || 'unhandled rejection');
  if (!/AUTO write guard|abort|cancel/i.test(m)) W.errors.push(m.slice(0, 200));
});
const oOpen = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function (method, url) {
  this.addEventListener('loadend', () => W.responses.push({method: String(method).toUpperCase(), url: String(url), status: this.status}));
  return oOpen.apply(this, arguments);
};
const oFetch = window.fetch;
window.fetch = function (input, init) {
  const method = ((init && init.method) || (input && input.method) || 'GET').toUpperCase();
  const url = typeof input === 'string' ? input : (input && input.url);
  return oFetch.apply(this, arguments).then(r => { W.responses.push({method, url: String(url), status: r.status}); return r; });
};
return true;
"""


# ============================================================
# MSAADA
# ============================================================

def _root(module):
    return CONTENT_ROOT.get(module.get("kind"), DEFAULT_ROOT)


def _menu_paths(app_key):
    return sorted({urlparse(m["path"]).path for m in load_modules(app_key) if m.get("path")})


def label(c):
    """Jina la button kwa ripoti."""
    icon = re.sub(r"^(lucide|fa|ion|glyphicon|mdi)-", "", c["icon"].split()[-1]) if c["icon"] else ""
    name = c["text"] or c["title"] or (f"icon {icon}" if icon else "") or c["path"] or c["tag"]
    if c["tag"] == "input" and c["type"] == "checkbox":
        name = "checkbox ya kuchagua" + (" row" if c["inRow"] else " zote")
    if c["tag"] == "select":
        name = f"dropdown {c['title'] or c['text'] or ''}".strip()
    if c["th"]:
        name = f"column {name}"
    if c["inRow"]:
        name = f"{name} (row)"
    return name[:50]


def classify(c):
    """'disabled', 'danger', 'export', au 'click'."""
    if c["disabled"]:
        return "disabled"
    words = f"{c['text']} {c['title']}"
    if re.fullmatch(r"\s*(print|chapisha)\s*", c["text"] or "", re.I) or "fa-print" in (c["icon"] or ""):
        return "print"   # dirisha la printer linakwamisha headless Chrome
    if EXPORT_TEXT.search(words) and not DANGER_TEXT.search(re.sub(EXPORT_TEXT, "", words)):
        return "export"
    segments = [s for s in (c["path"] or "").split("/") if s]
    if segments and DANGER_PATH.match(segments[-1]):
        return "danger"
    if c["method"] in ("post", "delete", "put") or c["confirm"]:
        return "danger"
    if DANGER_TEXT.search(words):
        if not c["text"] and any(i in c["icon"] for i in SAFE_ICONS):
            return "click"   # icon ya refresh ya list
        return "danger"
    if any(i in c["icon"] for i in ("trash", "fa-times", "lucide-x", "ban", "power", "log-out", "send", "upload")):
        return "danger"
    return "click"


def enable_downloads(driver):
    folder = getattr(driver, "_auto_downloads", None)
    if folder is None:
        folder = tempfile.mkdtemp(prefix="auto_downloads_")
        driver._auto_downloads = folder
    try:
        driver.execute_cdp_cmd("Browser.setDownloadBehavior", {"behavior": "allow", "downloadPath": folder})
    except Exception:
        try:
            driver.execute_cdp_cmd("Page.setDownloadBehavior", {"behavior": "allow", "downloadPath": folder})
        except Exception:
            pass
    return folder


def _files(folder):
    try:
        return {f for f in os.listdir(folder) if not f.endswith((".crdownload", ".tmp"))}
    except OSError:
        return set()


def _dismiss_alert(driver, accept=False):
    try:
        alert = driver.switch_to.alert
        text = alert.text
        alert.accept() if accept else alert.dismiss()
        return text
    except NoAlertPresentException:
        return None
    except Exception:
        return None


def _watch(driver, guard=True):
    try:
        if guard:
            driver.execute_script(GUARD_JS, READ_PATHS)
        driver.execute_script(WATCH_JS)
    except Exception:
        pass


def _watched(driver):
    try:
        return driver.execute_script("return window.__autoWatch || {responses: [], errors: []};")
    except Exception:
        return {"responses": [], "errors": []}


def _blocked(driver):
    try:
        return driver.execute_script("return window.__autoWriteGuard ? window.__autoWriteGuard.blocked : [];") or []
    except Exception:
        return []


def _settle(driver):
    try:
        wait_page_ready(driver, timeout=30)
    except Exception:
        pass
    _wait_content_stable(driver, timeout=8, quiet=1.0)


def _page_problem(driver, base_url):
    """Error ya ukurasa ulio wazi sasa, au None."""
    if is_login_page(driver):
        return "imerudisha login page"
    marker = find_error_on_page(driver)
    if marker:
        return f"ukurasa unaonyesha '{marker}'"
    try:
        empty = driver.execute_script("return !document.body || document.body.innerText.trim().length === 0;")
    except Exception:
        empty = False
    if empty:
        return "ukurasa mweupe kabisa (hakuna maandishi)"
    return None


def _bad_responses(watch, base_url):
    host = urlparse(base_url).netloc
    bad = []
    for r in watch.get("responses", []):
        url = r.get("url") or ""
        same = not urlparse(url).netloc or urlparse(url).netloc == host
        if same and (r.get("status") or 0) >= 500:
            bad.append(f"{r['method']} {urlparse(url).path} -> {r['status']}")
        elif same and r.get("status") == 404 and r.get("method") == "GET":
            bad.append(f"GET {urlparse(url).path} -> 404")
    return bad


# ============================================================
# CHECK: KILA BUTTON YA MODULE
# ============================================================

def check_all_buttons(driver, app, module, open_module):
    """open_module: core.list_checks.open_module (inapitishwa ili kuepuka import ya mzunguko)."""
    enable_downloads(driver)
    open_module(driver, app, module)
    list_url = driver.current_url
    root, menu = _root(module), _menu_paths(app["key"])
    controls = driver.execute_script(CONTROLS_JS, root, EXCLUDE, menu) or []
    if not controls:
        pytest.skip(f"{module['name']}: ukurasa hauna button yoyote nje ya menu")

    groups = {"disabled": [], "danger": [], "export": [], "click": [], "print": []}
    for c in controls:
        groups[classify(c)].append(c)
    to_test = groups["click"] + groups["export"]
    dropped = to_test[MAX_CONTROLS:]
    to_test = to_test[:MAX_CONTROLS]

    ok, failed, notes = [], [], []
    dirty = False
    ignore_text = bool(module.get("ignore_error_text"))
    # Kurasa kama "Error Logs" zinaonyesha maandishi ya errors kama data
    quiet = {urlparse(m["path"]).path for m in load_modules(app["key"]) if m.get("ignore_error_text")}
    started = time.time()
    for i, c in enumerate(to_test):
        name = label(c)
        if time.time() - started > MODULE_BUDGET:
            dropped = to_test[i:] + dropped
            break
        try:
            if dirty or driver.current_url != list_url or classify(c) == "export":  # Export: hali safi ya list
                open_module(driver, app, module)
                dirty = False
            result = _try_control(driver, app, module, c, root, list_url, ignore_text,
                                  reopen=lambda: open_module(driver, app, module), quiet=quiet)
        except AssertionError as e:   # module yenyewe haikufunguka tena
            failed.append(f"{name}: {str(e)[:160]}")
            dirty = True
            continue
        except Exception as e:
            _dismiss_alert(driver)
            result = {"status": "fail", "msg": f"{type(e).__name__}: {str(e).splitlines()[0][:120]}", "dirty": True}
        dirty = dirty or result.get("dirty", False)
        if result["status"] == "ok":
            ok.append(name + (f" ({result['msg']})" if result.get("msg") else ""))
        elif result["status"] == "note":
            notes.append(f"{name}: {result['msg']}")
        else:
            failed.append(f"{name}: {result['msg']}")

    summary = [f"Buttons {len(controls)} kwenye ukurasa: {len(ok)} zimebofywa bila error"]
    if ok:
        summary.append("Zimefanya kazi: " + ", ".join(ok))
    if notes:
        summary.append("Maelezo: " + "; ".join(notes))
    if groups["danger"]:
        summary.append("Hazikubofywa kwa usalama (zinabadilisha data au kutuma nje): "
                       + ", ".join(label(c) for c in groups["danger"]))
    if groups["print"]:
        summary.append("Hazikubofywa (Print inafungua dirisha la printer): "
                       + ", ".join(label(c) for c in groups["print"]))
    if groups["disabled"]:
        summary.append("Disabled: " + ", ".join(label(c) for c in groups["disabled"]))
    if dropped:
        summary.append(f"Hazikubofywa (zaidi ya {MAX_CONTROLS} au muda wa dakika {MODULE_BUDGET // 60} "
                       f"umeisha): " + ", ".join(label(c) for c in dropped))
    for line in summary:
        print(f"ACTUAL: {line}")
    assert not failed, (f"{module['name']}: buttons {len(failed)} zina tatizo: " + " | ".join(failed))


def _try_control(driver, app, module, c, root, list_url, ignore_text, reopen=None, quiet=()):
    kind = classify(c)
    el = driver.execute_script(FIND_JS, root, EXCLUDE, c["sig"])
    if el is None and reopen is not None:
        # Ukurasa umebadilika (k.m. tab nyingine iko wazi): fungua upya utafute tena
        reopen()
        el = driver.execute_script(FIND_JS, root, EXCLUDE, c["sig"])
    if el is None:
        return {"status": "note", "msg": "haikuonekana tena baada ya kufungua ukurasa upya", "dirty": True}

    _watch(driver, guard=(kind != "export"))
    folder = enable_downloads(driver) if kind == "export" else None
    if folder:
        # Pages nyingi zinapakua file lenye jina lilelile (k.m. worker.csv); Chrome
        # inaliandika juu ya lile la zamani, kwa hiyo futa folder kwanza ili file jipya lionekane.
        for f in os.listdir(folder):
            try:
                os.remove(os.path.join(folder, f))
            except OSError:
                pass
    before_files = _files(folder) if folder else set()
    handles = driver.window_handles
    before_url = driver.current_url

    if c["tag"] == "select":
        return _try_select(driver, app, el, list_url, ignore_text)

    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
        try:
            # Click halisi: dropdowns za Radix (ONGEZA PRO) zinafunguka kwa pointerdown, si kwa JS click()
            el.click()
        except UnexpectedAlertPresentException:
            raise
        except Exception:
            driver.execute_script("arguments[0].click();", el)
    except StaleElementReferenceException:
        return {"status": "note", "msg": "ilibadilika wakati wa kubofya", "dirty": True}
    except UnexpectedAlertPresentException:
        pass

    time.sleep(0.5)
    alert = _dismiss_alert(driver, accept=(kind == "export"))
    time.sleep(SETTLE)

    # Tab / window mpya
    new = [h for h in driver.window_handles if h not in handles]
    if new:
        main = driver.current_window_handle
        driver.switch_to.window(new[0])
        _settle(driver)
        problem = None if ignore_text else _page_problem(driver, app["base_url"])
        opened = driver.current_url
        driver.close()
        driver.switch_to.window(main)
        if problem:
            return {"status": "fail", "msg": f"tab mpya {urlparse(opened).path}: {problem}"}
        return {"status": "ok", "msg": f"imefungua tab mpya {urlparse(opened).path}"}

    navigated = driver.current_url != before_url
    if navigated:
        _settle(driver)
        ignore_text = urlparse(driver.current_url).path in quiet
    else:
        _wait_content_stable(driver, timeout=6, quiet=1.0)

    problem = None if ignore_text else _page_problem(driver, app["base_url"])
    if ignore_text and is_login_page(driver):
        problem = "imerudisha login page"
    if problem == "imerudisha login page":
        return {"status": "fail", "msg": problem, "dirty": True}
    watch = _watched(driver) if not navigated else {"responses": [], "errors": []}
    bad = _bad_responses(watch, app["base_url"])
    js = [e for e in watch.get("errors", []) if e]
    blocked = _blocked(driver) if not navigated else []

    msg_ok = []
    if watch.get("printed"):
        msg_ok.append("imefungua dirisha la Print")
    if navigated:
        msg_ok.append(f"imefungua {urlparse(driver.current_url).path}")
    if alert:
        msg_ok.append(f"confirm '{alert[:60]}' {'imekubaliwa' if kind == 'export' else 'imekataliwa'}")
    if blocked:
        msg_ok.append("ilijaribu kutuma " + ", ".join(b.split(':')[0] + ':' + urlparse(b.split(':', 2)[-1]).path
                                                     for b in blocked[:2]) + " (imezuiwa, hakuna kilichobadilika)")

    if kind == "export":
        got = _wait_download(folder, before_files)
        if got:
            msg_ok.append(f"imepakua file {got}")
        elif not problem and not bad:
            # Export yenye menu (CSV / Excel ...): bofya option ya kwanza
            sub = _export_option(driver, root)
            if sub is not None:
                try:
                    try:
                        sub.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", sub)
                    time.sleep(0.5)
                    _dismiss_alert(driver, accept=True)
                    got = _wait_download(folder, before_files)
                except Exception:
                    got = None
                if got:
                    msg_ok.append(f"imepakua file {got}")
                else:
                    problem = "Export haikupakua file yoyote"
            else:
                problem = "Export haikupakua file yoyote"

    _close_popups(driver)
    if problem or bad or js:
        parts = [p for p in (problem, ("server: " + ", ".join(bad[:3])) if bad else "",
                             ("JS error: " + "; ".join(js[:2])) if js else "") if p]
        return {"status": "fail", "msg": " / ".join(parts), "dirty": True}
    return {"status": "ok", "msg": "; ".join(msg_ok), "dirty": navigated or bool(alert)}


def _try_select(driver, app, el, list_url, ignore_text):
    """Chagua option nyingine ya dropdown, kagua, kisha rudisha ya awali (bila kusave)."""
    info = driver.execute_script(
        "const s = arguments[0]; return {i: s.selectedIndex, multi: s.multiple,"
        " texts: [...s.options].map(o => o.disabled ? '' : o.text.trim())};", el)
    if not info or info["multi"]:
        return {"status": "note", "msg": "dropdown ya kuchagua nyingi, haikubadilishwa"}
    real = [i for i, t in enumerate(info["texts"])
            if i != info["i"] and t and not re.match(r"^(--|select|choose|chagua|all\b)", t, re.I)]
    others = real or [i for i, t in enumerate(info["texts"]) if i != info["i"]]
    if not others:
        return {"status": "note", "msg": "haina option nyingine ya kuchagua"}
    target = others[0]
    text = driver.execute_script(
        "const s = arguments[0]; s.selectedIndex = arguments[1];"
        "s.dispatchEvent(new Event('input', {bubbles: true})); s.dispatchEvent(new Event('change', {bubbles: true}));"
        "return s.options[arguments[1]].text.trim();", el, target)
    time.sleep(SETTLE)
    navigated = driver.current_url != list_url
    if navigated:
        _settle(driver)
    else:
        _wait_content_stable(driver, timeout=6, quiet=1.0)
    problem = None if ignore_text else _page_problem(driver, app["base_url"])
    watch = _watched(driver) if not navigated else {"responses": [], "errors": []}
    bad = _bad_responses(watch, app["base_url"])
    js = [e for e in watch.get("errors", []) if e]
    if not navigated:
        try:
            driver.execute_script(
                "const s = arguments[0]; s.selectedIndex = arguments[1];"
                "s.dispatchEvent(new Event('change', {bubbles: true}));", el, info["i"])
        except Exception:
            pass
    if problem or bad or js:
        parts = [p for p in (problem, ("server: " + ", ".join(bad[:3])) if bad else "",
                             ("JS error: " + "; ".join(js[:2])) if js else "") if p]
        return {"status": "fail", "msg": f"option '{text[:30]}': " + " / ".join(parts), "dirty": True}
    return {"status": "ok", "msg": f"option '{text[:30]}'", "dirty": True}


def _wait_download(folder, before, timeout=DOWNLOAD_WAIT):
    """Jina la file mpya iliyopakuliwa, au None. Download isipoanza ndani ya sekunde 8, inaacha."""
    start = time.time()
    while time.time() - start < timeout:
        new = _files(folder) - before
        if new:
            return sorted(new)[0]
        try:
            pending = any(f.endswith(".crdownload") for f in os.listdir(folder))
        except OSError:
            pending = False
        if not pending and time.time() - start > 8:
            return None
        time.sleep(0.7)
    return None


def _export_option(driver, root):
    return driver.execute_script(r"""
    const items = [...document.querySelectorAll('.dropdown-menu a, [role=menuitem], [role=option], .export-menu a')]
      .filter(e => e.getClientRects().length && /csv|excel|xls|pdf|json|text/i.test(e.innerText || ''));
    return items.find(e => /csv/i.test(e.innerText)) || items[0] || null;
    """)


def _close_popups(driver):
    try:
        driver.switch_to.active_element.send_keys(Keys.ESCAPE)
    except Exception:
        pass
    try:
        driver.execute_script("document.body.click();")
    except Exception:
        pass
