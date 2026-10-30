"""
Tuma matokeo ya Selenium (reports/modules/<app>/summary.json) kwenye backend ya
"project tester" (Laravel) kupitia REST API yake.

Mifano:
    python -m tools.push_to_tester --app jumla --dry-run          # onyesha tu kitakachoundwa
    python -m tools.push_to_tester --app jumla                    # tuma modules zote za summary.json
    python -m tools.push_to_tester --app jumla --module 12        # module moja (namba/id/jina kama run_module)

Mpangilio (mapping):
    Project      = jina la app (k.m. "JUMLA")
    Module       = sehemu ya kwanza ya jina la module ("Agro" kwa "Agro > Stockist Machinery Orders")
    SubModule    = sehemu iliyobaki ("Stockist Machinery Orders")
    Feature      = kichwa cha test case chini ya sub module hiyo
    Scenario     = kichwa cha test case (discription = hatua)
    Expectation  = matokeo yanayotarajiwa (moja kwa kila scenario)
    Test         = run moja kwa kila push
    TestsResults = kila case: Pass/Fail (SKIP inarukwa; ERROR = scenario bila result, yaani Not tested), result = actual (herufi 255)

Config (.env au environment, kamwe usiandike hapa):
    TESTER_API_URL   k.m. https://tester.example.com  (au .../api)
    TESTER_USERNAME  username ya kuingia (TESTER_EMAIL inakubalika, lakini OTP confirm inatafuta username tu)
    TESTER_PASSWORD
    TESTER_OTP       (hiari) OTP ya login; bila hii script inauliza OTP kwenye terminal
    TESTER_TOKEN     (hiari) Sanctum token tayari; inaruka login/OTP

Token inahifadhiwa .sessions/tester_token (gitignored) ili usiombe OTP kila mara.
"""

import argparse
import json
import mimetypes
import os
import re
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from urllib import error as urlerror
from urllib import parse as urlparse
from urllib import request as urlrequest

from core.config import APPS, REPORTS_DIR, ROOT, get_app
from tools.run_module import CASES, load_all, parse_tests, pick


TOKEN_FILE = ROOT / ".sessions" / "tester_token"
MAX_LEN = 255          # varchar(255): project/module/sub module/feature name, scenario title, result
PER_PAGE = 100         # backend inaweka max 100 kwa page
RETRIES = 4


class ApiError(Exception):
    def __init__(self, status, message, errors=None):
        super().__init__(message)
        self.status = status
        self.errors = errors or {}

    def short(self):
        text = str(self)
        if self.errors:
            first = next(iter(self.errors.values()))
            text = first[0] if isinstance(first, list) and first else str(first)
        return f"HTTP {self.status}: {text}"[:200]


# ============================================================
# HTTP CLIENT (urllib, bila dependency ya ziada)
# ============================================================

def api_base(url):
    url = url.rstrip("/")
    return url if url.endswith("/api") else url + "/api"


def encode_params(params, prefix=""):
    """PHP-style query string: filters[name][operator]=eq, filters[id][value][]=1."""
    pairs = []
    for key, value in params.items():
        name = f"{prefix}[{key}]" if prefix else str(key)
        if isinstance(value, dict):
            pairs.extend(encode_params(value, name))
        elif isinstance(value, (list, tuple)):
            pairs.extend((f"{name}[]", str(v)) for v in value)
        elif value is not None:
            pairs.append((name, str(value)))
    return pairs


def multipart(fields, files):
    boundary = "----tester" + uuid.uuid4().hex
    body = bytearray()
    for name, value in fields.items():
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n"
                 f"{value}\r\n").encode()
    for name, path in files.items():
        ctype = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"; "
                 f"filename=\"{Path(path).name}\"\r\nContent-Type: {ctype}\r\n\r\n").encode()
        body += Path(path).read_bytes() + b"\r\n"
    body += f"--{boundary}--\r\n".encode()
    return bytes(body), f"multipart/form-data; boundary={boundary}"


class Client:
    def __init__(self, base_url):
        self.base = api_base(base_url)
        self.token = None

    def call(self, method, path, params=None, data=None, files=None):
        url = self.base + path
        if params:
            url += "?" + urlparse.urlencode(encode_params(params))
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        body = None
        if files:
            body, headers["Content-Type"] = multipart(data or {}, files)
        elif data is not None:
            body = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"

        for attempt in range(RETRIES + 1):
            req = urlrequest.Request(url, data=body, headers=headers, method=method)
            try:
                with urlrequest.urlopen(req, timeout=60) as resp:
                    raw = resp.read()
                    return json.loads(raw) if raw else {}
            except urlerror.HTTPError as e:
                raw = e.read()
                # POST/PUT/DELETE zinarudiwa kwa 429 tu: 5xx inaweza kuja baada ya server kusave,
                # na kurudia kungeunda nakala (results mbili za scenario moja)
                retry = e.code == 429 or (e.code >= 500 and method == "GET")
                if retry and attempt < RETRIES:
                    wait = e.headers.get("Retry-After")
                    time.sleep(min(float(wait), 30) if wait and wait.isdigit() else 2 ** attempt)
                    continue
                try:
                    payload = json.loads(raw)
                except ValueError:
                    payload = {"message": raw[:200].decode(errors="replace")}
                raise ApiError(e.code, payload.get("message") or f"HTTP {e.code}", payload.get("errors"))
            except (urlerror.URLError, TimeoutError, ConnectionError) as e:
                if attempt < RETRIES and method == "GET":
                    time.sleep(2 ** attempt)
                    continue
                raise ApiError(0, f"Haiwezi kufikia {self.base}: {getattr(e, 'reason', e)}")

    def data(self, method, path, **kw):
        """Rudisha 'data' ya Helpers::success ({status, code, message, data})."""
        resp = self.call(method, path, **kw)
        if isinstance(resp, dict) and resp.get("status") is False:
            raise ApiError(resp.get("code", 500), resp.get("message", "Error"), resp.get("data"))
        return resp.get("data") if isinstance(resp, dict) else resp

    def list_all(self, path, filters=None):
        """Pitia pages zote za list endpoint (data.data + data.meta)."""
        rows, page = [], 1
        while True:
            params = {"params": {"page": page, "per_page": PER_PAGE}}
            if filters:
                params["filters"] = filters
            result = self.data("GET", path, params=params) or {}
            rows.extend(result.get("data") or [])
            meta = result.get("meta") or {}
            if page >= int(meta.get("last_page") or 1):
                return rows
            page += 1


def eq(**fields):
    return {k: {"operator": "eq", "value": v} for k, v in fields.items()}


# ============================================================
# LOGIN (username + password -> OTP -> token)
# ============================================================

def env(name):
    value = os.getenv(name)
    return value.strip() if value else None


def read_cached_token():
    try:
        return TOKEN_FILE.read_text().strip() or None
    except OSError:
        return None


def save_token(token):
    try:
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_FILE.write_text(token)
        os.chmod(TOKEN_FILE, 0o600)
    except OSError as e:
        print(f"  ! Imeshindwa kuhifadhi token: {e}")


def token_works(client, token):
    client.token = token
    try:
        client.call("GET", "/profile")
        return True
    except ApiError:
        client.token = None
        return False


def login(client, interactive=True):
    for token in (env("TESTER_TOKEN"), read_cached_token()):
        if token and token_works(client, token):
            print("Login: token iliyopo inafanya kazi")
            return True
    if not interactive:
        return False

    username = env("TESTER_USERNAME") or env("TESTER_EMAIL")
    password = os.getenv("TESTER_PASSWORD")
    if not username or not password:
        sys.exit("Weka TESTER_USERNAME na TESTER_PASSWORD kwenye .env (au TESTER_TOKEN).")
    if "@" in username and not env("TESTER_USERNAME"):
        print("  ! Tahadhari: backend inakubali email kwenye login, lakini OTP confirm "
              "inatafuta username tu. Ikishindwa, weka TESTER_USERNAME.")

    client.data("POST", "/auth/login", data={"username": username, "password": password})
    print("Login: OTP imetumwa (email)")
    code = env("TESTER_OTP")
    if not code:
        if not sys.stdin.isatty():
            sys.exit("Backend inahitaji OTP. Weka TESTER_OTP au TESTER_TOKEN, au endesha kwenye terminal.")
        code = input("Weka OTP uliyopokea: ").strip()
    result = client.data("POST", "/auth/otp/confirm",
                         data={"identifier": username, "code": code, "type": "login"})
    token = (result or {}).get("token")
    if not token:
        sys.exit("OTP confirm haikurudisha token.")
    client.token = token
    save_token(token)
    print("Login: imefanikiwa (token imehifadhiwa .sessions/tester_token)")
    return True


# ============================================================
# DATA YA RIPOTI
# ============================================================

TAG_RE = re.compile(r"</?[a-z][a-z0-9]*\b[^>]*/?>", re.IGNORECASE)


def norm(text):
    """Kama backend (SanitizeInput + TrimStrings) ili lookup kwa jina ilingane."""
    text = str(text or "").replace("\0", "").replace("\r\n", "\n").replace("\r", "\n")
    return TAG_RE.sub("", text).strip()


def clip(text, limit=MAX_LEN):
    text = norm(text)
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def split_name(name):
    parts = [p.strip() for p in name.split(" > ") if p.strip()]
    if len(parts) < 2:
        return name.strip(), name.strip()
    return parts[0], " > ".join(parts[1:])


def find_screenshot(app_key, module_id, case):
    rel = case.get("screenshot") or ""
    candidates = []
    if rel:
        candidates += [REPORTS_DIR / "modules" / app_key / module_id / rel, REPORTS_DIR / rel]
    shots = REPORTS_DIR / "screenshots"
    func = case.get("func", "")
    if func and shots.exists():
        candidates += sorted(shots.glob(f"*__{func}_{module_id}_*.png"))
    return next((p for p in candidates if p.is_file()), None)


def load_jobs(app_key, module_query=None, since=None, tests=None):
    summary_path = REPORTS_DIR / "modules" / app_key / "summary.json"
    if not summary_path.exists():
        sys.exit(f"{summary_path} haipo. Endesha: python -m tools.run_module --app {app_key} --all")
    summary = json.loads(summary_path.read_text())
    try:
        known = {m["id"]: m for m in load_all(app_key)}
    except SystemExit:
        known = {}

    ids = list(summary)
    if module_query:
        chosen = pick(list(known.values()), module_query) if known else {"id": module_query}
        if chosen["id"] not in summary:
            sys.exit(f"Module '{chosen['id']}' haina matokeo kwenye {summary_path}.")
        ids = [chosen["id"]]

    if since:
        # Modules zilizoendeshwa kwenye run hii tu (summary.json ina matokeo ya runs zilizopita pia)
        ids = [mid for mid in ids if summary[mid].get("ran_at", 0) >= since]
        if not ids:
            sys.exit("Hakuna matokeo mapya ya run hii; hakuna kilichotumwa.")

    jobs, seen = [], {}
    for mid in ids:
        entry = summary[mid]
        cases = entry.get("cases", [])
        if tests:   # --tests: tests zilizoendeshwa sasa tu, si zile zilizobaki kutoka run iliyopita
            cases = [c for c in cases if c.get("func") in tests]
        info = known.get(mid, {})
        name = entry.get("name") or info.get("name") or mid
        mod_name, sub_name = split_name(name)
        key = (mod_name.lower(), sub_name.lower())
        if key in seen and seen[key] != mid:   # page mbili zenye jina moja: tofautisha kwa path
            sub_name = f"{sub_name} ({info.get('path') or mid})"
        seen[key] = mid
        jobs.append({"id": mid, "name": name, "path": info.get("path", ""), "module": clip(mod_name),
                     "sub": clip(sub_name), "cases": cases})
    return jobs


# ============================================================
# PUSH
# ============================================================

class Pusher:
    def __init__(self, client, app, dry_run=False, can_read=True, images=True, verbose=False):
        self.c = client
        self.app = app
        self.dry = dry_run
        self.can_read = can_read      # dry-run bila token: hakuna lookups, kila kitu ni "kipya"
        self.images = images
        self.verbose = verbose
        self.fake_id = 0
        self.created = {k: 0 for k in ("project", "module", "sub_module", "feature", "scenario",
                                       "expectation", "test")}
        self.results = {"created": 0, "replaced": 0, "dropped": 0, "Pass": 0, "Fail": 0, "skipped": 0}
        self.img = {"sent": 0, "failed": 0}
        self.failures = []
        self.image_error = None
        # caches: jina -> id
        self.project_id = None
        self.modules, self.subs, self.features, self.scenarios = {}, {}, {}, {}
        self.with_expectation = set()
        self.test_id = None
        self.test_rows = {}          # scenario_id -> [rows za results zilizopo kwenye test hii]
        self.delete_error = None     # sababu ya DELETE ya kwanza iliyoshindwa (inaonyeshwa mara moja)
        self.done_scenarios = set()

    # ---------- helpers ----------
    def new_id(self):
        self.fake_id -= 1
        return self.fake_id

    def create(self, kind, path, payload, label):
        self.created[kind] += 1
        if self.dry:
            if self.verbose:
                print(f"    + {kind}: {label}")
            return {"id": self.new_id()}
        return self.c.data("POST", path, data=payload)

    @staticmethod
    def key(text):
        return norm(text).lower()

    # ---------- project + prefetch ----------
    def ensure_project(self):
        name = clip(self.app["name"])
        if self.can_read:
            for row in self.c.list_all("/projects/list", eq(name=name)):
                if self.key(row.get("name")) == self.key(name):
                    self.project_id = row["id"]
                    print(f"Project '{name}' ipo (id {self.project_id})")
                    self.prefetch()
                    return
        row = self.create("project", "/projects/create",
                          {"name": name, "status": "Active",
                           "description": f"Selenium automation: {self.app['base_url']}"}, name)
        self.project_id = row["id"]
        print(f"Project '{name}' {'itaundwa' if self.dry else 'imeundwa'}")

    def prefetch(self):
        pid = self.project_id
        for row in self.c.list_all("/modules/list", eq(project_id=pid)):
            self.modules.setdefault(self.key(row.get("name")), row["id"])
        for row in self.c.list_all("/sub-module/list", eq(project_id=pid)):
            self.subs.setdefault((row.get("module_id"), self.key(row.get("name"))), row["id"])
        for row in self.c.list_all("/features/list", eq(project_id=pid)):
            self.features.setdefault((row.get("sub_module_id"), self.key(row.get("name"))), row["id"])
        for row in self.c.list_all("/scenarios/list", eq(project_id=pid)):
            self.scenarios.setdefault((row.get("features_id"), self.key(row.get("title"))), row["id"])
        ids = sorted(set(self.scenarios.values()))
        for i in range(0, len(ids), 100):
            chunk = ids[i:i + 100]
            rows = self.c.list_all("/expectations/list",
                                   {"scenarios_id": {"operator": "in", "value": chunk}})
            self.with_expectation.update(r.get("scenarios_id") for r in rows)
        print(f"  Vilivyopo: modules {len(self.modules)}, sub modules {len(self.subs)}, "
              f"features {len(self.features)}, scenarios {len(self.scenarios)}, "
              f"expectations {len(self.with_expectation)}")

    # ---------- hierarchy ----------
    def ensure_module(self, name):
        k = self.key(name)
        if k not in self.modules:
            row = self.create("module", "/modules/create",
                              {"project_id": self.project_id, "name": name}, name)
            self.modules[k] = row["id"]
        return self.modules[k]

    def ensure_sub(self, module_id, name, job):
        k = (module_id, self.key(name))
        if k not in self.subs:
            row = self.create("sub_module", "/sub-module/create",
                              {"project_id": self.project_id, "module_id": module_id, "name": name,
                               "discription": f"{job['name']} ({job['path'] or job['id']})"}, name)
            self.subs[k] = row["id"]
        return self.subs[k]

    def ensure_feature(self, module_id, sub_id, title):
        k = (sub_id, self.key(title))
        if k not in self.features:
            row = self.create("feature", "/features/create",
                              {"project_id": self.project_id, "module_id": module_id,
                               "sub_module_id": sub_id, "name": title}, title)
            self.features[k] = row["id"]
        return self.features[k]

    def ensure_scenario(self, module_id, sub_id, feature_id, title, steps):
        k = (feature_id, self.key(title))
        if k not in self.scenarios:
            row = self.create("scenario", "/scenarios/create",
                              {"project_id": self.project_id, "module_id": module_id,
                               "sub_module": sub_id, "features_id": feature_id,
                               "title": title, "discription": norm(steps) or None}, title)
            self.scenarios[k] = row["id"]
        return self.scenarios[k]

    def ensure_expectation(self, scenario_id, expected):
        if scenario_id in self.with_expectation:
            return
        self.create("expectation", "/expectations/create",
                    {"scenarios_id": scenario_id, "expectation": norm(expected)}, expected[:60])
        self.with_expectation.add(scenario_id)

    # ---------- test + results ----------
    def start_test(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = self.create("test", "/tests/create", {"project_id": self.project_id, "test_date": now},
                          f"test {now}")
        self.test_id = row["id"]
        if not self.dry:
            # Backend inanakili Pass za test iliyopita kwenye test mpya (carried rows)
            for r in self._rows_of_test():
                self.test_rows.setdefault(str(r.get("scenario_id")), []).append(r)
            print(f"Test mpya id {self.test_id} (round {row.get('test_round') or '-'}), "
                  f"results zilizonakiliwa kutoka test iliyopita: {len(self.test_rows)}")
        else:
            print(f"Test mpya itaundwa ({now})")

    def _rows_of_test(self, **filters):
        """Results za test hii tu (backend ikipuuza filter, rows za tests nyingine zisiguswe)."""
        rows = self.c.list_all("/tests-results/list", eq(test_id=self.test_id, **filters))
        return [r for r in rows if str(r.get("test_id")) == str(self.test_id)
                and (not filters or str(r.get("scenario_id")) == str(filters["scenario_id"]))]

    def send_result(self, scenario_id, remark, result):
        payload = {"test_id": self.test_id, "scenario_id": scenario_id, "remark": remark, "result": result}
        if self.dry:
            return {"id": self.new_id()}
        olds = self.test_rows.pop(str(scenario_id), None)
        if not olds:
            try:
                return self.c.data("POST", "/tests-results/create", data=payload)
            except ApiError as e:
                if e.status != 422:
                    raise
                # Scenario tayari ina result kwenye test hii (k.m. iliyonakiliwa) ambayo haikuonekana mwanzo
                olds = self._rows_of_test(scenario_id=scenario_id)
                if not olds:
                    raise
        # Row iliyonakiliwa (carried): ifute na uandike matokeo mapya ya run hii.
        # (Edit ingeacha carried_from_test_id, na test isiyo na results zake ingefutwa na push ijayo.)
        # Rows zikiwa zaidi ya moja kwa scenario moja, zile za ziada zinafutwa.
        keep, extra = olds[0], olds[1:]
        for r in extra:
            self._delete(r)
        self.results["replaced"] += 1
        if not extra and self._delete(keep):
            return self.c.data("POST", "/tests-results/create", data=payload)
        return self.c.data("PUT", f"/tests-results/{keep['uuid']}/edit", data=payload)

    def drop_carried(self, scenario_id):
        """Futa result iliyonakiliwa kutoka test iliyopita: bila hivyo test ambayo haikumaliza
        ingeonekana Pass ya zamani badala ya "Not tested"."""
        if self.dry:
            return
        for r in self.test_rows.pop(str(scenario_id), None) or []:
            if self._delete(r):
                self.results["dropped"] += 1

    def _delete(self, row):
        try:
            self.c.data("DELETE", f"/tests-results/{row['uuid']}/delete")
            return True
        except ApiError as e:
            if self.delete_error is None:
                self.delete_error = e.short()
                print(f"  ! Kufuta result iliyonakiliwa kumekataliwa ({self.delete_error}); "
                      f"itabadilishwa (Edit) badala yake")
            return False

    def send_image(self, result_id, path):
        if not self.images or self.image_error:
            return
        if self.dry:
            self.img["sent"] += 1
            return
        try:
            self.c.data("POST", "/test-results-images/create",
                        data={"test_result_id": result_id}, files={"images": path})
            self.img["sent"] += 1
        except ApiError as e:
            self.img["failed"] += 1
            if e.status == 422:
                # Validation ya images ni 'string' + 'mimes' -> faili lolote linakataliwa; usirudie
                self.image_error = e.short()
                print(f"  ! Screenshot haikukubaliwa ({self.image_error}); picha zimezimwa kwa run hii")
            else:
                print(f"  ! Screenshot imeshindwa: {e.short()}")

    def push_module(self, n, total, job):
        before = dict(self.created)
        counts = {"Pass": 0, "Fail": 0, "skip": 0, "err": 0}
        try:
            module_id = self.ensure_module(job["module"])
            sub_id = self.ensure_sub(module_id, job["sub"], job)
        except ApiError as e:
            self.failures.append(f"{job['name']}: {e.short()}")
            print(f"[{n}/{total}] {job['name']}: imeshindwa ({e.short()})")
            return
        for case in job["cases"]:
            status = (case.get("status") or "").upper()
            if status not in ("PASS", "FAIL", "ERROR"):
                counts["skip"] += 1
                self.results["skipped"] += 1
                continue
            func = case.get("func", "")
            default = CASES.get(func, ("", "", ""))
            title = clip(case.get("title") or default[0] or func or "Test")
            steps = case.get("steps") or default[1]
            expected = case.get("expected") or default[2] or title
            remark = "Pass" if status == "PASS" else "Fail"
            try:
                feature_id = self.ensure_feature(module_id, sub_id, title)
                scenario_id = self.ensure_scenario(module_id, sub_id, feature_id, title, steps)
                self.ensure_expectation(scenario_id, expected)
                if scenario_id in self.done_scenarios or status == "ERROR":
                    # ERROR: test haikumaliza (browser/muda), si Pass wala Fail. Scenario ipo bila
                    # result, kwa hiyo project tester inaionyesha kama "Not tested".
                    if status == "ERROR" and scenario_id not in self.done_scenarios:
                        self.drop_carried(scenario_id)
                    counts["skip"] += 1
                    self.results["skipped"] += status == "ERROR"
                    continue
                row = self.send_result(scenario_id, remark, clip(case.get("actual") or status))
                self.done_scenarios.add(scenario_id)
                self.results["created"] += 1
                self.results[remark] += 1
                counts[remark] += 1
                if remark == "Fail":
                    shot = find_screenshot(self.app["key"], job["id"], case)
                    if shot and row and row.get("id") is not None:
                        self.send_image(row["id"], shot)
            except ApiError as e:
                counts["err"] += 1
                self.failures.append(f"{job['name']} / {title}: {e.short()}")
                if e.status == 401:
                    raise
        new = sum(self.created[k] - before[k] for k in self.created)
        verb = "vitaundwa" if self.dry else "vimeundwa"
        line = (f"[{n}/{total}] {job['name']}: Pass {counts['Pass']}, Fail {counts['Fail']}, "
                f"zimerukwa {counts['skip']}, {verb} {new}")
        if counts["err"]:
            line += f", makosa {counts['err']}"
        print(line)

    def summary(self):
        c = self.created
        verb = "Vitaundwa" if self.dry else "Vimeundwa"
        print("\n" + "=" * 60)
        print(("MUHTASARI (DRY RUN - hakuna kilichotumwa)" if self.dry else "MUHTASARI"))
        print(f"{verb}: project {c['project']}, modules {c['module']}, sub modules {c['sub_module']}, "
              f"features {c['feature']}, scenarios {c['scenario']}, expectations {c['expectation']}, "
              f"tests {c['test']}")
        r = self.results
        word = "Results zitakazotumwa" if self.dry else "Results zilizotumwa"
        print(f"{word}: {r['created']} (Pass {r['Pass']}, Fail {r['Fail']}), "
              f"zilizobadilisha carried rows {r['replaced']}, SKIP zilizorukwa {r['skipped']}")
        if r["dropped"]:
            print(f"Carried results za tests zilizokuwa ERROR zimefutwa (sasa Not tested): {r['dropped']}")
        if self.dry:
            print(f"Screenshots za Fail zitakazojaribiwa: {self.img['sent']}")
        else:
            print(f"Screenshots: zimetumwa {self.img['sent']}, zimeshindwa {self.img['failed']}"
                  + (f" ({self.image_error})" if self.image_error else ""))
        print(f"Makosa: {len(self.failures)}")
        for f in self.failures[:20]:
            print(f"  - {f}")
        if len(self.failures) > 20:
            print(f"  ... na mengine {len(self.failures) - 20}")


def main():
    parser = argparse.ArgumentParser(description="Tuma matokeo ya tests kwenye project tester")
    parser.add_argument("--app", required=True, choices=list(APPS))
    parser.add_argument("--module", help="module moja: id, jina, path au namba ya --list")
    parser.add_argument("--dry-run", action="store_true", help="usitume chochote, onyesha tu kitakachoundwa")
    parser.add_argument("--no-images", action="store_true", help="usitume screenshots")
    parser.add_argument("--since", type=int, help="modules zilizoendeshwa baada ya muda huu (epoch) tu")
    parser.add_argument("--tests", help="tuma tests hizi tu, k.m. 'edit' au 'sort,edit'")
    parser.add_argument("-v", "--verbose", action="store_true", help="na --dry-run: onyesha kila kitu kipya")
    args = parser.parse_args()

    app = get_app(args.app)
    jobs = load_jobs(args.app, args.module, args.since, parse_tests(args.tests) if args.tests else None)
    print(f"{app['name']}: modules {len(jobs)} kutoka summary.json")

    url = env("TESTER_API_URL")
    client = Client(url or "http://localhost")
    can_read = True
    if args.dry_run:
        # Dry run: soma tu (GET) ikiwa token iliyopo inafanya kazi; login (POST) hairuhusiwi
        can_read = bool(url) and login(client, interactive=False)
        if not can_read:
            print("Dry run bila token: hakuna lookups, kila kitu kinahesabiwa kama kipya")
    else:
        if not url:
            sys.exit("Weka TESTER_API_URL kwenye .env")
        try:
            login(client)
        except ApiError as e:
            sys.exit(f"Login imeshindwa: {e.short()}")

    pusher = Pusher(client, app, dry_run=args.dry_run, can_read=can_read,
                    images=not args.no_images, verbose=args.verbose)
    try:
        pusher.ensure_project()
        pusher.start_test()
        for n, job in enumerate(jobs, 1):
            pusher.push_module(n, len(jobs), job)
    except ApiError as e:
        if e.status == 401:
            try:
                TOKEN_FILE.unlink()
            except OSError:
                pass
            pusher.failures.append("Token imekataliwa (401); endesha tena ili kuingia upya")
        else:
            pusher.failures.append(f"Imesimama: {e.short()}")
    except KeyboardInterrupt:
        pusher.failures.append("Imesimamishwa na mtumiaji")
    pusher.summary()
    sys.exit(1 if pusher.failures and not args.dry_run else 0)


if __name__ == "__main__":
    main()
