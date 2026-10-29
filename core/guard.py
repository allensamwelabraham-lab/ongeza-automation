"""
"Write guard": inazuia ukurasa wa sasa kutuma data kwa server.

Tunaitumia kabla ya kubofya Save kwenye form tupu (validation tests), ili hata
form ikikosa validation ya browser, hakuna record inayoundwa. Inazuia:

* <form> submit ya kawaida (Yii2 ActiveForm bado inaendesha validation yake)
* form.submit() ya JS
* fetch / XMLHttpRequest zisizo GET (Vue / React / axios)

Guard inaishi mpaka ukurasa ubadilike (navigation mpya inaiondoa).
"""

import json

GUARD_JS = r"""
if (window.__autoWriteGuard) return true;
window.__autoWriteGuard = {blocked: []};
const log = (what) => window.__autoWriteGuard.blocked.push(what);

window.addEventListener('submit', e => { e.preventDefault(); log('submit:' + (e.target.action || '')); }, true);
HTMLFormElement.prototype.submit = function () { log('form.submit:' + (this.action || '')); };

const origFetch = window.fetch;
window.fetch = function (input, init) {
  const method = ((init && init.method) || (input && input.method) || 'GET').toUpperCase();
  if (method !== 'GET' && method !== 'HEAD') {
    log('fetch:' + method + ':' + (typeof input === 'string' ? input : input.url));
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
  if (this.__autoMethod !== 'GET' && this.__autoMethod !== 'HEAD') {
    log('xhr:' + this.__autoMethod + ':' + this.__autoUrl);
    try { this.abort(); } catch (e) {}
    return;
  }
  return origSend.apply(this, arguments);
};
return true;
"""


def install_write_guard(driver):
    return driver.execute_script(GUARD_JS)


def blocked_writes(driver):
    return driver.execute_script(
        "return window.__autoWriteGuard ? window.__autoWriteGuard.blocked : null;"
    )


# ============================================================
# KUREKODI MAJIBU YA SERVER (bila kuzuia) - kwa tests za kusave
# ============================================================

RECORD_JS = r"""
if (window.__autoRecorder) return true;
window.__autoRecorder = [];
function shrink(body) {
  // JSON kubwa (k.m. Inertia props zenye menus) -> message + errors tu
  try {
    const data = JSON.parse(body);
    const p = (data && data.props) || data || {};
    // API (k.m. ONGEZA PRO): {"status":false,"message":"Validation failed","data":{"field":["..."]}}
    const small = p.data && typeof p.data === 'object' && JSON.stringify(p.data).length < 2000 ? p.data : undefined;
    return JSON.stringify({response: p.response, message: p.message, errors: p.errors, data: small});
  } catch (e) { return String(body || '').slice(0, 2000); }
}
const keep = (method, url, status, body) =>
  window.__autoRecorder.push({method, url: String(url), status, body: shrink(body)});

const origOpen = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function (method, url) {
  this.__autoMethod = (method || 'GET').toUpperCase();
  this.__autoUrl = url;
  this.addEventListener('loadend', () => {
    if (this.__autoMethod !== 'GET') keep(this.__autoMethod, this.__autoUrl, this.status, this.responseText);
  });
  return origOpen.apply(this, arguments);
};
const origFetch = window.fetch;
window.fetch = function (input, init) {
  const method = ((init && init.method) || 'GET').toUpperCase();
  return origFetch.apply(this, arguments).then(r => {
    if (method !== 'GET') r.clone().text().then(t => keep(method, r.url, r.status, t));
    return r;
  });
};
return true;
"""


def record_server_responses(driver):
    """Anza kurekodi majibu ya POST/PUT (ukurasa wa sasa tu)."""
    return driver.execute_script(RECORD_JS)


def server_responses(driver):
    try:
        return driver.execute_script("return window.__autoRecorder || [];")
    except Exception:
        return []


def _summary(body):
    """Toa message + errors kutoka JSON ya server (Inertia/Laravel/Yii), au mwanzo wa body."""
    try:
        data = json.loads(body)
    except ValueError:
        return body[:200]
    props = data.get("props", data) if isinstance(data, dict) else {}
    parts = []
    response = props.get("response") or {}
    if isinstance(response, dict) and response.get("message"):
        parts.append(str(response["message"]))
    if props.get("message"):
        parts.append(str(props["message"]))
    for field, messages in _field_errors(props).items():
        parts.append(f"{field}: {' '.join(messages) if isinstance(messages, list) else messages}")
    return "; ".join(parts) or body[:200]


def _field_errors(props):
    """{field: [messages]} kutoka "errors" (Laravel/Inertia/Yii) au "data" ya API (ONGEZA PRO)."""
    errors = dict(props.get("errors") or {}) if isinstance(props.get("errors"), dict) else {}
    data = props.get("data")
    if isinstance(data, dict) and data and all(isinstance(v, list) for v in data.values()):
        errors.update(data)
    return errors


def server_error_messages(driver):
    """Ujumbe wa validation kutoka majibu ya server, k.m. ["color: The color field format is invalid."]"""
    messages = []
    for r in server_responses(driver):
        try:
            data = json.loads(r["body"])
        except (ValueError, TypeError):
            continue
        props = data.get("props", data) if isinstance(data, dict) else {}
        for field, items in _field_errors(props).items():
            for text in items if isinstance(items, list) else [items]:
                messages.append(f"{field}: {text}")
    return messages


def describe_server_responses(driver):
    return " | ".join(f"{r['method']} {r['url']} -> {r['status']}: {_summary(r['body'])}"
                      for r in server_responses(driver)) or "hakuna jibu la server lililorekodiwa"
