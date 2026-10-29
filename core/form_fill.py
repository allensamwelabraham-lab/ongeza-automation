"""
Kujaza fomu yoyote ya Add/Create kwa data ya AUTO (kwa test za --crud).

Kila field inapewa thamani kulingana na aina yake na jina lake:
    email          -> auto<stamp>@example.com
    phone / msisdn -> 07xxxxxxxx
    nida           -> tarakimu 20
    date / dob     -> tarehe ya leo (hata kama ni datepicker ya readonly)
    number, amount, price, qty -> 1
    select / select2 -> option ya kwanza halisi (selects zinazotegemea nyingine,
                      k.m. District -> Ward, zinasubiriwa zijae)
    checkbox       -> inawekwa tick ikiwa ni required
    radio          -> option ya kwanza ya kila group
    file           -> inarukwa (validation ikihitaji file, test itaonyesha)
    text / textarea -> "AUTO <Field> <stamp>"
"""

import re
import time
from datetime import date

from selenium.common.exceptions import InvalidSelectorException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select

from core.helpers import VALIDATION_SELECTORS, _safe_displayed

FORM_SCOPE = "#content, .app-content, main, [data-slot='sidebar-inset']"
# Search ya juu (topbar, name="serial_number" bila id) na menu filter si sehemu ya fomu
SKIP_NAMES = ("_csrf", "navigation filter")
JUNK_OPTION = re.compile(r"^(--|select|choose|chagua|loading|searching|no results)", re.I)


def _label(driver, element):
    key = element.get_attribute("id")
    if key:
        labels = driver.find_elements(By.CSS_SELECTOR, f"label[for='{key}']")
        if labels and labels[0].text.strip():
            return labels[0].text.strip().rstrip("*").strip()
    return (element.get_attribute("placeholder") or element.get_attribute("name")
            or key or "field").strip()


def _set_js(driver, element, value):
    """Weka thamani kwa JS (kwa datepickers za readonly) na utume input/change events."""
    driver.execute_script(
        "const e = arguments[0]; e.removeAttribute('readonly');"
        "const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(e), 'value').set;"
        "setter.call(e, arguments[1]);"
        "e.dispatchEvent(new Event('input', {bubbles: true}));"
        "e.dispatchEvent(new Event('change', {bubbles: true}));"
        "if (window.jQuery) jQuery(e).trigger('change');",
        element, value,
    )


def _type(driver, element, value):
    try:
        element.clear()
        element.send_keys(value)
        if (element.get_attribute("value") or "") == "":
            raise ValueError("haikukubali")
    except Exception:
        _set_js(driver, element, value)


def _text_value(key, label, field_type, stamp, maxlength):
    k = f"{key} {label}".lower()
    today = date.today()
    if field_type == "email" or "email" in k:
        return f"auto{stamp}@example.com"
    if field_type == "tel" or any(w in k for w in ("phone", "msisdn", "mobile", "simu")):
        return "07" + stamp[-8:]
    if "nida" in k or "national" in k:
        return ("1990" + stamp + "00000000000000")[:20]
    if field_type == "date" or any(w in k for w in ("date", "dob", "birth", "tarehe")):
        return today.isoformat()
    if field_type == "datetime-local":
        return today.isoformat() + "T08:00"
    if field_type == "time":
        return "08:00"
    if field_type == "month":
        return today.strftime("%Y-%m")
    if field_type == "year" or re.search(r"\byear\b", k):
        return str(today.year)
    if key.lower() == "id" or label.strip().lower() == "id":
        return str(int(stamp[-9:]) + 100000)  # ID ya kipekee (fomu nyingine zinaonyesha ID)
    if (re.search(r"(_id|_by)\b", key.lower()) or re.search(r"\b(id|created by|modified by|updated by)$", label.lower())
            or "status" in k):
        return "1"
    if key.lower().startswith("is_") or label.lower().startswith("is "):
        return "0" if "delete" in k else "1"
    if "apk" in k or "version" in k:
        return "1.0"
    if "color" in k or "colour" in k:
        return "#1a7f37"
    if "sha256" in k or "hash" in k or "checksum" in k:
        return (stamp * 7)[:64].replace("1", "a")
    if "mime" in k:
        return "text/plain"
    if "extension" in k:
        return "txt"
    if re.search(r"\bdisk\b", k):
        return "local"
    if "path" in k:
        return f"auto/{stamp}.txt"
    if field_type == "number" or any(w in k for w in (
            "amount", "price", "qty", "quantity", "cost", "number", "count", "percent",
            "rate", "days", "limit", "budget", "salary", "latitude", "longitude", "size")):
        return "1"
    if field_type == "url" or "url" in k or "link" in k:
        return f"https://example.com/auto{stamp}"
    if field_type == "password" or "password" in k:
        return f"Auto@{stamp}"
    if "username" in k:
        return f"auto{stamp}"
    # Fupi (<=20) ili ipite validation ya "at most N characters"; stamp inabaki ndani
    word = (re.sub(r"[^A-Za-z0-9 ]", " ", label).split() or ["Test"])[0]
    value = f"AUTO{stamp} {word}"[:20].strip()
    if maxlength and maxlength.isdigit() and int(maxlength) < len(value):
        value = (f"A{stamp}")[: int(maxlength)]
    return value


def _select2_pick(driver, key, index):
    """Fungua select2 ya #key na ubofye option halisi ya namba `index` (ndani ya dropdown iliyo wazi tu)."""
    opener = driver.find_element(By.CSS_SELECTOR, f"#{key} + span.select2 .select2-selection")
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", opener)
    opener.click()

    def options():
        found = []
        for li in driver.find_elements(By.CSS_SELECTOR, ".select2-container--open li.select2-results__option"):
            text = li.text.strip()
            if text and not JUNK_OPTION.match(text) and li.get_attribute("aria-disabled") != "true":
                found.append(li)
        return found

    deadline, typed = time.time() + 8, False
    found = options()
    while len(found) <= index and time.time() < deadline:
        search = driver.find_elements(By.CSS_SELECTOR, ".select2-container--open .select2-search__field")
        if not typed and search and time.time() > deadline - 5:
            search[0].send_keys("a")  # select2 za ajax zinahitaji maandishi
            typed = True
        time.sleep(0.5)
        found = options()
    if len(found) <= index:
        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
        return None
    text = found[index].text.strip()
    found[index].click()
    time.sleep(1)
    return text


def _choose_select(driver, element, index=0):
    """Chagua option halisi ya namba `index`. Inasubiri hadi 8s kwa selects zinazojazwa baadaye."""
    key = element.get_attribute("id")
    if key and driver.find_elements(By.CSS_SELECTOR, f"#{key} + span.select2"):
        try:
            return _select2_pick(driver, key, index)
        except Exception:
            pass

    def real_options():
        return [o for o in Select(element).options
                if (o.get_attribute("value") or "") and o.text.strip()
                and not JUNK_OPTION.match(o.text.strip())]

    deadline = time.time() + 8
    options = real_options()
    while len(options) <= index and time.time() < deadline:
        time.sleep(0.5)
        options = real_options()
    if len(options) <= index:
        return None

    chosen = options[index]
    if element.is_displayed():
        Select(element).select_by_value(chosen.get_attribute("value"))
    else:
        driver.execute_script(
            "arguments[0].value = arguments[1];"
            "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));"
            "if (window.jQuery) jQuery(arguments[0]).trigger('change');",
            element, chosen.get_attribute("value"),
        )
    return chosen.text.strip()


VISIBLE_JS = """
const e = arguments[0];
if (!e.getClientRects().length) return false;
const cs = getComputedStyle(e);
return cs.visibility !== 'hidden' && cs.display !== 'none' && cs.opacity !== '0';
"""


def _js_visible(driver, element):
    # Selenium is_displayed() inasema "haionekani" kwa field iliyo nje ya sehemu inayoonekana ya
    # container yenye scroll (k.m. rows za juu za Sale targets) - tumia CSS badala yake
    return bool(driver.execute_script(VISIBLE_JS, element))


MAX_FILL_PASSES = 6
NOT_FILLED = ("(hakuna option)", "(imeshindwa kujaza", "(file imerukwa)")  # hazikuandikwa kwenye fomu


def fill_form(driver, stamp, scope_css=FORM_SCOPE, report_existing=True):
    """Jaza fields zote zinazoonekana. Passes zinazofuata zinajaza fields zilizoongezeka baada ya
    kuchagua kitu (k.m. Asset Name inaongeza fields zake, Sale targets inaongeza row kwa kila
    warehouse taratibu) mpaka pass isijaze kitu kipya. Inarudisha [(label, thamani)].
    report_existing=False: usiripoti radio/file zilizokuwepo, ni kile kilichoandikwa tu."""
    gave_up = set()  # selects zisizo na option: usizijaribu tena kila pass
    filled = _fill_pass(driver, stamp, scope_css, gave_up, first=report_existing)
    for _ in range(MAX_FILL_PASSES - 1):
        time.sleep(1.5)
        more = _fill_pass(driver, stamp, scope_css, gave_up)
        filled += more
        if not any(not str(value).startswith(NOT_FILLED) for _, value in more):
            break
    return filled


def _fill_pass(driver, stamp, scope_css, gave_up=None, first=False):
    filled, done_radio, previous_select = [], set(), None
    gave_up = set() if gave_up is None else gave_up
    for attempt in range(2):  # fomu ikichorwa upya wakati huu (Vue) -> elements "stale"
        try:
            scopes = driver.find_elements(By.CSS_SELECTOR, scope_css)
            root = scopes[0] if scopes else driver
            elements = root.find_elements(By.CSS_SELECTOR, "input, select, textarea")
            break
        except StaleElementReferenceException:
            if attempt == 1:
                return filled
            time.sleep(1)

    for element in elements:
        key = ""
        try:
            tag = element.tag_name
            field_type = (element.get_attribute("type") or tag).lower()
            name = element.get_attribute("name") or ""
            key = name or element.get_attribute("id") or ""
            if field_type in ("hidden", "submit", "button", "reset", "image", "search"):
                continue
            if any(s in f"{key} {element.get_attribute('placeholder') or ''}".lower() for s in SKIP_NAMES):
                continue
            if name == "serial_number" and not element.get_attribute("id"):
                continue
            if element.get_attribute("disabled") is not None:
                continue
            visible = _js_visible(driver, element)
            if not visible and tag != "select":
                continue
            label = _label(driver, element)

            if field_type == "file":
                if first:
                    filled.append((label, "(file imerukwa)"))
                continue
            if tag == "select":
                current = Select(element).first_selected_option if element.get_attribute("value") else None
                if current is not None and current.text.strip() and not JUNK_OPTION.match(current.text.strip()):
                    continue  # tayari imechaguliwa (default au pass iliyopita)
                if (key or element.id) in gave_up:
                    continue
                value = _choose_select(driver, element)
                # Select tegemezi (k.m. Ward) tupu: badilisha option ya select iliyotangulia
                # (k.m. District) hadi mara 5 mpaka hii ipate options
                attempt = 1
                while value is None and previous_select is not None and attempt <= 5:
                    prev_el, prev_pos = previous_select
                    prev_value = _choose_select(driver, prev_el, attempt)
                    if prev_value is None:
                        break
                    filled[prev_pos] = (filled[prev_pos][0], prev_value)
                    value = _choose_select(driver, element)
                    attempt += 1
                filled.append((label, value or "(hakuna option)"))
                if value is None:
                    gave_up.add(key or element.id)
                previous_select = (element, len(filled) - 1)
                continue
            if field_type == "checkbox":
                if element.get_attribute("required") is not None and not element.is_selected():
                    element.click()
                    filled.append((label, "tick"))
                continue
            if field_type == "radio":
                if name not in done_radio:
                    done_radio.add(name)
                    clicked = not element.is_selected()
                    if clicked:
                        driver.execute_script("arguments[0].click();", element)
                    if clicked or first:
                        filled.append((name or label, element.get_attribute("value") or "radio 1"))
                continue
            if (element.get_attribute("value") or "").strip():
                continue  # tayari ina thamani (default ya fomu au pass iliyopita)

            if tag == "textarea":
                value = f"AUTO automation test {stamp}"
            else:
                value = _text_value(key, label, field_type, stamp, element.get_attribute("maxlength"))
            if element.get_attribute("readonly") is not None:
                _set_js(driver, element, value)
            else:
                _type(driver, element, value)
            filled.append((label, value))
        except Exception as exc:  # field moja isivunje fomu nzima
            filled.append((key or "field", f"(imeshindwa kujaza: {type(exc).__name__})"))
    return filled


def validation_messages(driver):
    """Ujumbe wa validation unaoonekana (k.m. 'Name cannot be blank.')."""
    messages = []
    for e in driver.find_elements(By.CSS_SELECTOR, VALIDATION_SELECTORS):
        try:
            text = e.text.strip()
            if _safe_displayed(e) and text and text not in messages and len(text) < 300:
                messages.append(text)
        except Exception:
            pass
    try:
        html5 = driver.execute_script(
            "return Array.from(document.querySelectorAll('input,select,textarea'))"
            ".filter(e => e.willValidate && !e.checkValidity())"
            ".map(e => (e.name || e.id) + ': ' + e.validationMessage);"
        )
    except Exception:  # ukurasa unabadilika wakati huu
        html5 = []
    return messages + [m for m in html5 or [] if m not in messages]


def _format_fix(label, m, stamp):
    """'format is invalid': rangi -> #hex, vinginevyo tarakimu."""
    if "colo" in label.lower():
        return "#1a7f37"
    return stamp


# Ujumbe wa validation (Yii2: "X must be an integer.", Laravel: "The x field must be an integer.")
FIXES = [
    (re.compile(r"^(?:the )?(.+?)(?: field)? must be an? (integer|number|numeric)", re.I),
     lambda label, m, stamp: "0" if "delete" in label.lower() else "1"),
    (re.compile(r"^(?:the )?(.+?)(?: field)? should contain at most (\d+) characters", re.I),
     lambda label, m, stamp: stamp[-int(m.group(2)):] if int(m.group(2)) >= 2 else "1"),
    (re.compile(r"^(?:the )?(.+?)(?: field)? must not be greater than (\d+) characters", re.I),
     lambda label, m, stamp: stamp[-int(m.group(2)):] if int(m.group(2)) >= 2 else "1"),
    (re.compile(r"^(?:the )?(.+?)(?: field)? (?:must be|is not) a valid date", re.I),
     lambda label, m, stamp: date.today().isoformat()),
    (re.compile(r"^(?:the )?(.+?)(?: field)? (?:format is invalid|is invalid)", re.I), _format_fix),
]


def _field_by_label(driver, label):
    for lab in driver.find_elements(By.TAG_NAME, "label"):
        if lab.text.strip().rstrip("*").strip().lower() == label.lower() and lab.get_attribute("for"):
            found = driver.find_elements(By.ID, lab.get_attribute("for"))
            if found:
                return found[0]
    # Majina ya API (k.m. "mime type" -> mime_type)
    key = _css_string(label.strip().replace(" ", "_"))
    text = _css_string(label)
    for css in (f"[id='{key}' i]", f"[name='{key}' i]", f"[name$='[{key}]' i]", f"[placeholder='{text}' i]",
                f"[placeholder='Enter {text}' i]"):
        try:
            found = driver.find_elements(By.CSS_SELECTOR, css)
        except InvalidSelectorException:  # label yenye herufi za ajabu - ruka
            continue
        if found:
            return found[0]
    return None


def _css_string(value):
    """Thamani salama ndani ya '...' ya CSS selector."""
    return value.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")


def fix_from_validation(driver, messages, stamp):
    """Rekebisha fields ambazo validation imesema zina aina mbaya. Inarudisha [(label, thamani)]."""
    fixed = []
    for message in messages:
        for pattern, make in FIXES:
            m = pattern.match(message.split(": ", 1)[-1])
            if not m:
                continue
            label = m.group(1).strip()
            element = _field_by_label(driver, label)
            if element is None or element.tag_name == "select":
                continue
            value = make(label, m, stamp)
            try:
                _type(driver, element, value)
            except Exception as exc:  # field moja isivunje test
                fixed.append((label, f"(imeshindwa kurekebisha: {type(exc).__name__})"))
                continue
            fixed.append((label, value))
    return fixed


SAVE_WORDS = ("save", "submit", "create", "add", "hifadhi", "tuma", "send")
# Fomu za Edit: "Update" (Yii), "Edit" (vue), "Save Changes" (ONGEZA PRO)
EDIT_WORDS = ("update", "save", "edit", "submit", "hifadhi")


def find_save_button(driver, scope_css=FORM_SCOPE, words=SAVE_WORDS):
    """Button ya kusave. Kwanza kwa maandishi (Save/Submit/Create/Add), kisha type=submit yenye maandishi.
    (Fomu nyingine zina buttons nyingi za icon zenye type=submit, k.m. kuondoa row.)"""
    scopes = driver.find_elements(By.CSS_SELECTOR, scope_css)
    root = scopes[0] if scopes else driver
    # offsetParent badala ya is_displayed(): fomu ndefu ndani ya container yenye overflow
    # hufanya Selenium iseme button "haionekani" ingawa inabofyeka baada ya scroll
    candidates = [el for el in root.find_elements(By.CSS_SELECTOR, "button, input[type=submit], a.btn")
                  if driver.execute_script(
                      "const s = getComputedStyle(arguments[0]);"
                      "return arguments[0].offsetParent !== null && s.visibility !== 'hidden';", el)]

    def text(el):
        # textContent (si .text): Selenium inarudisha "" kwa elements inazoona "hazionekani"
        return (el.get_attribute("textContent") or el.get_attribute("value") or "").strip().lower()

    for word in words:
        for el in candidates:
            if text(el).startswith(word) and "filter" not in text(el):
                return el
    for el in candidates:
        if el.get_attribute("type") == "submit" and text(el):
            return el
    return None
