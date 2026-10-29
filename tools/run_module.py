"""
Endesha tests za MODULE MOJA na utoe ripoti ya test cases zake (kwa ajili ya
kunakili kwenye project tester).

Mifano:
    python -m tools.run_module --app ongeza --list               # orodha ya modules na namba
    python -m tools.run_module --app ongeza --module agents      # kwa jina / id / path
    python -m tools.run_module --app ongeza --module 12          # kwa namba ya --list
    python -m tools.run_module --app ongeza --module customers --crud   # pamoja na kuunda data
    python -m tools.run_module --app jumla --module customers --crud --edit-real   # edit record halisi na kuirudisha
    python -m tools.run_module --app jumla --all --crud --tests edit   # rudia test ya Edit tu kwa modules zote
    python -m tools.run_module --app jumla --module customers --crud --tests edit --edit-real   # Edit tu ya module moja

    # MODULES ZOTE: kila module inapata ripoti yake + index.html ya muhtasari
    python -m tools.run_module --app ongeza --all                 # modules zote (bila slow)
    python -m tools.run_module --app ongeza --all --from 1 --to 40   # namba 1-40 za --list
    python -m tools.run_module --app ongeza --all --include-slow  # pamoja na slow
    python -m tools.run_module --app ongeza --all --group Worker  # kundi moja la menu (Worker > ...)

Ripoti inaandikwa reports/modules/<app>/<module-id>/:
    report.md    jedwali la test cases (soma au nakili)
    report.html  ripoti ya kuprint / kufungua kwenye browser
    report.csv   test cases kwa Excel / project tester
    screenshots/ picha za tests zilizoshindwa

--all inaongeza reports/modules/<app>/index.html (muhtasari, link ya kila module)
na reports/modules/<app>/all_cases.csv (test cases zote kwenye file moja).
"""

import argparse
import csv
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime

from core.config import APPS, REPORTS_DIR, ROOT, get_app
from core.modules import modules_file


# Tests za ziada (zilizoandikwa kwa mkono) kwa modules fulani
EXTRA_TESTS = {
    ("ongeza", "crud_worker_agents"): ["test_agents"],
    ("ongeza", "crud_customer_index2"): ["test_customers", "test_customer_create"],
}


# Maelezo ya kila aina ya test: (kichwa, hatua, matokeo yanayotarajiwa)
CASES = {
    "test_page_loads": (
        "Ukurasa wa module unafunguka",
        "1. Login kama admin\n2. Fungua module kutoka kwenye menu",
        "Ukurasa unafunguka bila error (500/504/404/SQL), heading sahihi, ndani ya muda",
    ),
    "test_columns": (
        "Columns za table zipo",
        "1. Fungua module\n2. Soma vichwa vya table",
        "Columns zinazoonyeshwa na list page zina majina, hazijirudii, na kila row ina cell ya kila column",
    ),
    "test_records": (
        "Table inaonyesha records",
        "1. Fungua module\n2. Hesabu rows na idadi ya records",
        "Idadi ya records inaonekana, table ina rows, kila row ina cells zote",
    ),
    "test_pagination": (
        "Pagination (page 2)",
        "1. Fungua module\n2. Nenda page 2",
        "Page 2 inafunguka na ina rows tofauti na page 1",
    ),
    "test_sort": (
        "Sort kwa ID (ASC na DESC)",
        "1. Fungua module\n2. Sort kwa ID ASC\n3. Sort kwa ID DESC",
        "Rows zinapangwa kwa mpangilio sahihi kila mara",
    ),
    "test_filter_finds_row": (
        "Filter kwa thamani iliyopo",
        "1. Fungua module\n2. Chukua thamani ya row ya kwanza\n3. Fungua Filter, andika thamani, Apply",
        "Rows zinazorudi ni zile zenye thamani hiyo tu",
    ),
    "test_filter_no_match": (
        "Filter kwa thamani isiyokuwepo",
        "1. Fungua module\n2. Filter kwa thamani isiyokuwepo, Apply",
        "Table haionyeshi row yoyote",
    ),
    "test_view": (
        "Kufungua detail (View) ya record",
        "1. Fungua module\n2. Bofya record ya kwanza",
        "Ukurasa wa View unafunguka bila error na una taarifa za record",
    ),
    "test_create_form_fields": (
        "Fomu ya Add/Create ina fields zote",
        "1. Fungua module\n2. Bofya Add / Create",
        "Fomu inafunguka bila error na fields zote zipo",
    ),
    "test_create_form_rejects_empty": (
        "Fomu tupu inakataliwa",
        "1. Fungua fomu ya Add / Create\n2. Bofya Save bila kujaza chochote",
        "Validation inaonyeshwa na hakuna kinachosaviwa",
    ),
    "test_create_form_saves": (
        "Kujaza fomu ya Add kwa data na kusave (AUTO)",
        "1. Fungua fomu ya Add / Create\n2. Jaza kila field (text, namba, tarehe, select)\n"
        "3. Bofya Save\n4. Fungua list tena",
        "Record inasaviwa bila error wala validation, na inaonekana kwenye list",
    ),
    "test_all_buttons": (
        "Kila button ya ukurasa inafanya kazi",
        "1. Fungua module\n2. Bofya kila button, tab, link, dropdown na Export (si za menu)\n"
        "3. Kagua ukurasa na majibu ya server baada ya kila moja\n4. Delete/Sync/Pay/Send hazibofywi",
        "Kila button inafanya kazi bila error (500/404/SQL/JS), Export inapakua file, na hakuna kinachosaviwa",
    ),
    "test_edit_form_saves": (
        "Kuedit record na kusave (Update)",
        "1. Fungua module\n2. Bofya Edit ya record ya AUTO (--edit-real: record ya kwanza)\n"
        "3. Badilisha field moja ya maandishi kuwa AUTO...\n4. Bofya Update / Save\n5. Fungua Edit tena\n"
        "6. --edit-real: rudisha thamani ya zamani",
        "Inasave bila error wala validation, thamani mpya inaonekana ukifungua Edit tena, "
        "na fields nyingine hazipotei",
    ),
    # Agents
    "test_agents_list_opens": (
        "Agents list inafunguka", "1. Fungua Worker > Agents",
        "List inafunguka bila error na button ya Add ipo",
    ),
    "test_create_agent_form_fields": (
        "Fomu ya Create Agent ina fields zote", "1. Fungua Agents\n2. Bofya Add",
        "Serial number, majina, username, apk, phone, NIDA, DOB, Hire Date, District, Ward, Org, Department zipo",
    ),
    "test_ward_loads_after_district": (
        "Ward zinaload baada ya kuchagua District",
        "1. Fungua Create Agent\n2. Chagua District 'Arusha'", "Ward za Arusha zinaonekana",
    ),
    "test_create_agent": (
        "Kuunda agent mpya (AUTO)",
        "1. Fungua Create Agent\n2. Jaza fields zote\n3. Save\n4. Tafuta agent kwenye list",
        "Agent anasaviwa na anaonekana kwenye list",
    ),
    # Customers
    "test_customers_filter_by_phone": (
        "Filter ya customers kwa Phone",
        "1. Fungua All Customers\n2. Chukua phone ya customer\n3. Filter kwa Phone",
        "Customers wenye phone hiyo tu ndio wanaonekana",
    ),
    "test_customers_filter_by_date_range": (
        "Filter ya customers kwa tarehe (From / To)",
        "1. Fungua All Customers\n2. Weka From na To siku moja\n3. Apply",
        "Customers wa siku hiyo tu, na records zinapungua",
    ),
    "test_customer_view_shows_same_customer": (
        "View ya customer inaonyesha customer sahihi",
        "1. Fungua All Customers\n2. Bofya customer wa kwanza", "Ukurasa unaonyesha jina la customer huyo",
    ),
    "test_create_customer": (
        "Kuunda customer mpya (AUTO)",
        "1. Bofya Add\n2. Jaza first/last name, ward, village, sub village, landmark, description\n"
        "3. Save\n4. Tafuta kwa last name kwenye list",
        "Customer anasaviwa na anaonekana kwenye list na ward sahihi",
    ),
}


def load_all(app_key):
    path = modules_file(app_key)
    if not path.exists():
        sys.exit(f"modules/{app_key}.json haipo. Endesha: python -m tools.discover --app {app_key}")
    data = json.loads(path.read_text())
    try:
        age = (datetime.now() - datetime.fromisoformat(data.get("discovered_at", ""))).days
    except ValueError:
        age = None
    if age is not None and age > 14 and not getattr(load_all, "warned", False):
        # Menu ya app ikibadilika, orodha ya zamani inatest kurasa zisizo kwenye menu tena
        load_all.warned = True
        print(f"TAHADHARI: modules/{app_key}.json ina siku {age}. Kama menu ya app imebadilika, "
              f"isasishe kwanza: python -m tools.discover --app {app_key} --workers 2")
    return data["modules"]


def print_list(app_key, modules):
    print(f"\nModules za {APPS[app_key]['name']} ({len(modules)}):\n")
    for i, m in enumerate(modules, 1):
        flag = "  (slow)" if m.get("skip") else ""
        print(f"{i:4}. {m['name']:60} {m['id']}{flag}")


def pick(modules, query):
    if query.isdigit() and 1 <= int(query) <= len(modules):
        return modules[int(query) - 1]
    q = query.lower()
    exact = [m for m in modules if q in (m["id"].lower(), m["name"].lower(), m["path"].lower(),
                                         m["name"].split(">")[-1].strip().lower())]
    if len(exact) == 1:
        return exact[0]
    found = [m for m in modules if q in m["id"].lower() or q in m["name"].lower() or q in m["path"].lower()]
    if len(found) == 1:
        return found[0]
    if not found:
        sys.exit(f"Hakuna module inayolingana na '{query}'. Tumia --list.")
    print(f"Modules {len(found)} zinalingana na '{query}', chagua moja kwa namba au id:")
    for m in found:
        print(f"  {modules.index(m) + 1:4}. {m['name']:60} {m['id']}")
    sys.exit(1)


def run_pytest(app_key, modules, xml_path, crud, workers=1, include_skipped=True, edit_real=False, tests=None):
    # Tests za modules hizi (id iko kwenye jina la test) + tests za mkono za modules hizo
    terms = []
    for module in modules:
        terms += [module["id"]] + extra_files(app_key, module)
    expr = " or ".join(terms)
    if tests:  # --tests: aina hizi za tests tu
        expr = f"({expr}) and ({' or '.join(tests)})"
    if os.environ.get("RUN_BUTTONS") != "1":  # test ya buttons ni ndefu: --buttons tu
        expr = f"({expr}) and not test_all_buttons"

    env = dict(os.environ, INCLUDE_SKIPPED="1" if include_skipped else "0")
    if crud:
        env["RUN_CRUD"] = "1"
    if edit_real:
        env["EDIT_REAL_RECORDS"] = "1"

    cmd = [
        sys.executable, "-m", "pytest", f"tests/{app_key}", "-k", expr, "-v",
        "-p", "no:cacheprovider",
        f"--junitxml={xml_path}",
        "-o", "junit_logging=system-out",
    ]
    if workers > 1:
        cmd += ["-n", str(workers)]
    print("\n" + " ".join(cmd if len(expr) < 300 else cmd[:5] + ["<modules %d>" % len(modules)] + cmd[6:]) + "\n")
    subprocess.run(cmd, cwd=ROOT, env=env)


# --tests: majina mafupi -> function za tests
TEST_ALIASES = {
    "edit": "test_edit_form_saves", "update": "test_edit_form_saves",
    "add": "test_create_form_saves", "create": "test_create_form_saves", "crud": None,
    "buttons": "test_all_buttons", "sort": "test_sort", "filter": "test_filter_finds_row or test_filter_no_match",
    "view": "test_view", "read": "test_view", "empty": "test_create_form_rejects_empty", "page": "test_page_loads", "pagination": "test_pagination",
}


def parse_tests(text):
    """'edit,add' -> ['test_edit_form_saves', 'test_create_form_saves']"""
    tests = []
    for word in (w.strip().lower() for w in text.split(",") if w.strip()):
        if word == "crud":
            # Kipaumbele cha kila module: Create (fomu tupu + iliyojazwa), Read (View), Update (Edit)
            tests += ["test_create_form_rejects_empty", "test_create_form_saves", "test_view",
                      "test_edit_form_saves"]
        elif word in TEST_ALIASES:
            tests += TEST_ALIASES[word].split(" or ")
        elif word.startswith("test_") and word in CASES:
            tests.append(word)
        else:
            sys.exit(f"--tests: '{word}' haijulikani. Tumia: {', '.join(TEST_ALIASES)} au jina la test (k.m. test_sort)")
    return list(dict.fromkeys(tests))


def _clean(text):
    text = (text or "").replace("AssertionError: ", "").replace("Failed: ", "")
    return re.sub(r"\s*assert .*", "", text.split("\n")[0]).strip()


def extra_files(app_key, module):
    return EXTRA_TESTS.get((app_key, module["id"]), [])


def belongs(case, app_key, module):
    """Test case ni ya module hii? (param = id, au test ya mkono ya module hii)"""
    name = case.get("name", "")
    func = name.split("[")[0]
    param = name[len(func):].strip("[]")
    if param:
        return param == module["id"]
    test_file = case.get("classname", "").split(".")[-1]
    return test_file in extra_files(app_key, module)


def parse_results(xml_path, module, app_key):
    cases = []
    for case in ET.parse(xml_path).getroot().iter("testcase"):
        if not belongs(case, app_key, module):
            continue
        name = case.get("name", "")
        func = name.split("[")[0]

        out = case.find("system-out")
        actual = [line[len("ACTUAL: "):] for line in (out.text or "").splitlines()
                  if out is not None and line.startswith("ACTUAL: ")] if out is not None else []

        status, message = "PASS", ""
        for tag, label in (("failure", "FAIL"), ("error", "ERROR"), ("skipped", "SKIP")):
            node = case.find(tag)
            if node is not None:
                status = label
                message = _clean(node.get("message") or node.text)
                if status == "FAIL" and message.startswith("selenium.common.exceptions."):
                    # Browser imekwama/muda umeisha kabla ya kufika kwenye ukaguzi: si kosa la app
                    status = "ERROR"
                    message = "Test haikumaliza (tatizo la browser au muda): " + message.split(".")[-1]
                break

        title, steps, expected = CASES.get(func, (func.replace("test_", "").replace("_", " ").capitalize(), "", ""))
        if status == "PASS":
            result = "; ".join(actual) or "Kama ilivyotarajiwa"
        else:
            result = message
        cases.append({
            "func": func, "title": title, "steps": steps, "expected": expected,
            "actual": result, "status": status, "seconds": float(case.get("time", 0)),
        })
    order = list(CASES)
    cases.sort(key=lambda c: order.index(c["func"]) if c["func"] in order else len(order))
    return cases


def screenshots_for(out_dir, module, cases):
    """Nakili screenshots za tests zilizoshindwa za module hii -> {func: path}."""
    src = REPORTS_DIR / "screenshots"
    dst = out_dir / "screenshots"
    dst.mkdir(parents=True, exist_ok=True)
    found = {}
    if not src.exists():
        return found
    pngs = list(src.glob("*.png"))
    for c in cases:
        for png in pngs:
            name = png.name
            if f"__{c['func']}_{module['id']}_" in name or name.endswith(f"__{c['func']}.png"):
                shutil.copy(png, dst / name)
                found[c["func"]] = f"screenshots/{name}"
    return found


def write_reports(app, module, cases, out_dir, shots):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    counts = {s: sum(c["status"] == s for c in cases) for s in ("PASS", "FAIL", "ERROR", "SKIP")}
    url = app["base_url"] + module["path"]

    for i, c in enumerate(cases, 1):
        c["id"] = f"TC-{i:02d}"
        c["screenshot"] = shots.get(c["func"], "") if c["status"] in ("FAIL", "ERROR") else ""

    # Markdown
    md = [
        f"# Ripoti ya test: {module['name']}",
        "",
        f"- **App:** {app['name']} ({app['base_url']})",
        f"- **Module:** {module['name']}",
        f"- **URL:** {url}",
        f"- **Tarehe:** {now}",
        f"- **Matokeo:** {counts['PASS']} Pass, {counts['FAIL'] + counts['ERROR']} Fail, {counts['SKIP']} Skip",
        "",
        "| ID | Test case | Hatua | Matokeo yanayotarajiwa | Matokeo halisi | Status |",
        "|---|---|---|---|---|---|",
    ]
    for c in cases:
        cell = lambda t: (t or "").replace("|", "/").replace("\n", "<br>")
        shot = f" ([screenshot]({c['screenshot']}))" if c["screenshot"] else ""
        md.append(f"| {c['id']} | {cell(c['title'])} | {cell(c['steps'])} | {cell(c['expected'])} | "
                  f"{cell(c['actual'])}{shot} | **{c['status']}** |")
    (out_dir / "report.md").write_text("\n".join(md) + "\n")

    # CSV
    with open(out_dir / "report.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Module", "Test case", "Hatua", "Matokeo yanayotarajiwa",
                         "Matokeo halisi", "Status", "Screenshot"])
        for c in cases:
            writer.writerow([c["id"], module["name"], c["title"], c["steps"], c["expected"],
                             c["actual"], c["status"], c["screenshot"]])

    # HTML
    colors = {"PASS": "#1a7f37", "FAIL": "#cf222e", "ERROR": "#cf222e", "SKIP": "#9a6700"}
    rows = []
    for c in cases:
        esc = lambda t: html.escape(t or "").replace("\n", "<br>")
        shot = (f'<br><a href="{c["screenshot"]}"><img src="{c["screenshot"]}" width="320"></a>'
                if c["screenshot"] else "")
        rows.append(
            f"<tr><td>{c['id']}</td><td>{esc(c['title'])}</td><td>{esc(c['steps'])}</td>"
            f"<td>{esc(c['expected'])}</td><td>{esc(c['actual'])}{shot}</td>"
            f"<td style='color:{colors[c['status']]};font-weight:bold'>{c['status']}</td></tr>"
        )
    (out_dir / "report.html").write_text(f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(module['name'])} - test report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; color: #1f2328; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
th, td {{ border: 1px solid #d0d7de; padding: 6px 8px; vertical-align: top; text-align: left; }}
th {{ background: #f6f8fa; }}
</style></head><body>
<h2>Ripoti ya test: {html.escape(module['name'])}</h2>
<p><b>App:</b> {html.escape(app['name'])} &nbsp; <b>URL:</b> <a href="{url}">{html.escape(url)}</a><br>
<b>Tarehe:</b> {now} &nbsp; <b>Matokeo:</b> {counts['PASS']} Pass, {counts['FAIL'] + counts['ERROR']} Fail,
{counts['SKIP']} Skip</p>
<table><tr><th>ID</th><th>Test case</th><th>Hatua</th><th>Matokeo yanayotarajiwa</th>
<th>Matokeo halisi</th><th>Status</th></tr>
{''.join(rows)}
</table></body></html>
""")
    return counts


def prepare_dir(out_dir):
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    return out_dir


def report_module(app, app_key, module, xml_path, out_dir):
    cases = parse_results(xml_path, module, app_key)
    counts = write_reports(app, module, cases, out_dir, screenshots_for(out_dir, module, cases))
    return cases, counts


def write_index(app, app_key, results, base_dir):
    """Muhtasari wa modules zote: index.html + all_cases.csv"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = {s: sum(r["counts"][s] for r in results) for s in ("PASS", "FAIL", "ERROR", "SKIP")}

    with open(base_dir / "all_cases.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Module #", "Module", "URL", "ID", "Test case", "Hatua",
                         "Matokeo yanayotarajiwa", "Matokeo halisi", "Status", "Screenshot"])
        for r in results:
            m = r["module"]
            for c in r["cases"]:
                shot = f"{m['id']}/{c['screenshot']}" if c["screenshot"] else ""
                writer.writerow([r["number"], m["name"], app["base_url"] + m["path"], c["id"], c["title"],
                                 c["steps"], c["expected"], c["actual"], c["status"], shot])

    rows = []
    for r in results:
        m, k = r["module"], r["counts"]
        failed = k["FAIL"] + k["ERROR"]
        color = "#cf222e" if failed else ("#9a6700" if not r["cases"] else "#1a7f37")
        problems = "<br>".join(html.escape(f"{c['title']}: {c['actual']}")
                               for c in r["cases"] if c["status"] in ("FAIL", "ERROR"))
        if not r["cases"]:
            problems = "Hakuna test iliyoendeshwa"
        rows.append(
            f"<tr><td>{r['number']}</td><td><a href='{m['id']}/report.html'>{html.escape(m['name'])}</a>"
            f"{' <small>(slow)</small>' if m.get('skip') else ''}</td>"
            f"<td>{k['PASS']}</td><td>{failed}</td><td>{k['SKIP']}</td>"
            f"<td style='color:{color};font-weight:bold'>{'FAIL' if failed else ('-' if not r['cases'] else 'PASS')}</td>"
            f"<td style='font-size:12px'>{problems}</td></tr>"
        )
    bad = sum(1 for r in results if r["counts"]["FAIL"] + r["counts"]["ERROR"])
    (base_dir / "index.html").write_text(f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{html.escape(app['name'])} - modules</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; color: #1f2328; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
th, td {{ border: 1px solid #d0d7de; padding: 6px 8px; vertical-align: top; text-align: left; }}
th {{ background: #f6f8fa; }}
</style></head><body>
<h2>{html.escape(app['name'])}: ripoti za modules</h2>
<p><b>Tarehe:</b> {now} &nbsp; <b>Modules:</b> {len(results)} ({len(results) - bad} zimepita zote, {bad} zina fail)<br>
<b>Test cases:</b> {total['PASS']} Pass, {total['FAIL'] + total['ERROR']} Fail, {total['SKIP']} Skip
&nbsp; <a href="all_cases.csv">all_cases.csv</a></p>
<table><tr><th>#</th><th>Module</th><th>Pass</th><th>Fail</th><th>Skip</th><th>Status</th><th>Kilichoshindwa</th></tr>
{''.join(rows)}
</table></body></html>
""")
    return total, bad


def is_report(module):
    text = (module["name"] + " " + module["path"]).lower()
    return "report" in text or "summary" in text or "chart" in text


def in_group(module, group):
    """'Customer' inachukua 'Customer > ...' lakini si 'Customer Service > ...'"""
    if not group:
        return True
    name, group = module["name"].lower(), group.lower().strip()
    return name == group or name.startswith(group + " >")


def run_all(args, app, modules):
    numbered = list(enumerate(modules, 1))
    first, last = args.from_ or 1, args.to or len(modules)
    chosen = [(n, m) for n, m in numbered if first <= n <= last and (args.include_slow or not m.get("skip"))
              and in_group(m, args.group)]
    if args.group and not chosen:
        # Apps zisizo na makundi ya menu (k.m. ONGEZA PRO): 'Zoho' -> 'Zoho Sync', 'Zoho Bills'...
        chosen = [(n, m) for n, m in numbered if first <= n <= last
                  and (args.include_slow or not m.get("skip"))
                  and m["name"].lower().startswith(args.group.lower().strip())]
    if not (args.include_reports or args.only):
        # Kurasa za reports zinachukua muda mrefu sana kufunguka: zinarukwa isipokuwa --include-reports
        reports = [m for _, m in chosen if is_report(m)]
        chosen = [(n, m) for n, m in chosen if not is_report(m)]
        if reports:
            print(f"Modules za reports {len(reports)} zimerukwa (ongeza --include-reports kuzitest)")
    base_dir = REPORTS_DIR / "modules" / args.app
    if args.only:
        # k.m. --only 6,40,116-120
        wanted = set()
        for part in args.only.split(","):
            a, _, b = part.strip().partition("-")
            wanted.update(range(int(a), int(b or a) + 1))
        chosen = [(n, m) for n, m in chosen if n in wanted]
    if args.failed:
        # Rudia modules zilizofail kwenye run iliyopita tu (kutoka summary.json)
        try:
            previous = json.loads((base_dir / "summary.json").read_text())
        except (OSError, ValueError):
            sys.exit("Hakuna run iliyopita (summary.json haipo). Endesha --all kwanza.")
        chosen = [(n, m) for n, m in chosen
                  if m["id"] in previous and previous[m["id"]]["counts"]["FAIL"] + previous[m["id"]]["counts"]["ERROR"]]
    if not chosen:
        sys.exit("Hakuna module kwenye range hiyo.")

    base_dir.mkdir(parents=True, exist_ok=True)
    tag = ("failed_" if args.failed else "") + ("only_" if args.only else "") + ("tests_" if args.tests else "")
    xml_path = base_dir / f"results_{tag}{first}-{last}.xml"
    if not args.tests:
        # --tests huendeshwa kwa vipande; usifute screenshots za vipande vilivyotangulia
        shutil.rmtree(REPORTS_DIR / "screenshots", ignore_errors=True)

    print(f"\n=== {app['name']}: modules {len(chosen)} (namba {first}-{last}) ===")
    tests = parse_tests(args.tests) if args.tests else None
    run_pytest(args.app, [m for _, m in chosen], xml_path, args.crud, args.workers, args.include_slow,
               args.edit_real, tests)

    # Ripoti za range hii zinaungana na za runs zilizopita (summary.json)
    summary_path = base_dir / "summary.json"
    try:
        summary = json.loads(summary_path.read_text())
    except (OSError, ValueError):
        summary = {}

    for number, module in chosen:
        if tests:
            # Tests nyingine za module hii zinabaki kama zilivyokuwa kwenye run iliyopita
            out_dir = base_dir / module["id"]
            out_dir.mkdir(parents=True, exist_ok=True)
            fresh = parse_results(xml_path, module, args.app)
            kept = [c for c in summary.get(module["id"], {}).get("cases", []) if c["func"] not in tests]
            shots = {c["func"]: c["screenshot"] for c in kept if c.get("screenshot")}
            shots.update(screenshots_for(out_dir, module, fresh))
            order = list(CASES)
            cases = sorted(kept + fresh, key=lambda c: order.index(c["func"]) if c["func"] in order else len(order))
            counts = write_reports(app, module, cases, out_dir, shots)
        else:
            out_dir = prepare_dir(base_dir / module["id"])
            cases, counts = report_module(app, args.app, module, xml_path, out_dir)
        summary[module["id"]] = {"number": number, "cases": cases, "counts": counts, "ran_at": int(time.time())}
        failed = counts["FAIL"] + counts["ERROR"]
        print(f"{number:4}. {module['name']:55} {counts['PASS']:3} Pass {failed:3} Fail {counts['SKIP']:3} Skip")
    summary_path.write_text(json.dumps(summary, indent=1, ensure_ascii=False))

    by_id = {m["id"]: m for m in modules}
    results = sorted(({"module": by_id[i], **r} for i, r in summary.items() if i in by_id),
                     key=lambda r: r["number"])
    total, bad = write_index(app, args.app, results, base_dir)
    print(f"\nJumla: modules {len(results)}, {bad} zina fail; test cases {total['PASS']} Pass, "
          f"{total['FAIL'] + total['ERROR']} Fail, {total['SKIP']} Skip")
    print(f"Muhtasari: {base_dir / 'index.html'}\n           {base_dir / 'all_cases.csv'}")


def main():
    parser = argparse.ArgumentParser(description="Endesha tests za module moja (au zote) na utoe ripoti")
    parser.add_argument("--app", required=True, choices=list(APPS))
    parser.add_argument("--module", help="jina, id, path au namba kutoka --list")
    parser.add_argument("--list", action="store_true", help="onyesha modules zote")
    parser.add_argument("--all", action="store_true", help="modules zote, kila moja ripoti yake + index.html")
    parser.add_argument("--from", dest="from_", type=int, help="na --all: anza namba hii ya --list")
    parser.add_argument("--to", type=int, help="na --all: ishia namba hii ya --list")
    parser.add_argument("--group", help="na --all: modules za kundi moja tu, k.m. 'Worker' au 'Stock > Items'")
    parser.add_argument("--include-slow", action="store_true", help="na --all: endesha pia modules za slow")
    parser.add_argument("--include-reports", action="store_true",
                        help="na --all: test pia kurasa za reports (zinachukua muda mrefu)")
    parser.add_argument("--workers", type=int, default=1, help="browsers sambamba (staging: usizidi 2)")
    parser.add_argument("--crud", action="store_true", help="endesha pia tests zinazounda data (AUTO)")
    parser.add_argument("--tests", help="na --all au --module: aina hizi za tests tu, k.m. 'edit' au 'add,edit' au 'sort'; "
                                        "matokeo mengine ya modules yanabaki")
    parser.add_argument("--buttons", action="store_true",
                        help="bofya pia kila button ya kila module (ndefu; buttons hatari hazibofywi)")
    parser.add_argument("--edit-real", action="store_true",
                        help="na --crud: kama hakuna record ya AUTO, edit record halisi kisha urudishe thamani yake")
    parser.add_argument("--only", help="na --all: namba za modules tu, k.m. '6,40,116-120'")
    parser.add_argument("--failed", action="store_true",
                        help="na --all: rudia modules zilizofail kwenye run iliyopita tu")
    parser.add_argument("--push", action="store_true",
                        help="baada ya run, tuma matokeo kwenye project tester (tools/push_to_tester.py)")
    args = parser.parse_args()
    started = time.time()
    try:
        _run(args)
    except KeyboardInterrupt:
        if args.push:
            print("\nRun imesimamishwa kabla ya kuisha: hakuna kilichotumwa kwenye project tester.")
        sys.exit(130)
    if args.push and not args.list:
        # Tuma matokeo ya run hii tu (modules na tests zilizoendeshwa sasa), si ya runs zilizopita
        cmd = [sys.executable, "-m", "tools.push_to_tester", "--app", args.app, "--since", str(int(started))]
        if args.module and not args.all:
            cmd += ["--module", args.module]
        if args.tests:
            cmd += ["--tests", args.tests]
        print("\n=== Kutuma matokeo kwenye project tester ===")
        subprocess.run(cmd, cwd=str(ROOT))


def _run(args):
    if args.tests and {w.strip().lower() for w in args.tests.split(",")} & {
            "crud", "add", "create", "edit", "update", "empty"}:
        args.crud = True  # tests za kusave/kuedit zinaruka bila --crud
    if args.buttons or (args.tests and "buttons" in args.tests.lower()):
        os.environ["RUN_BUTTONS"] = "1"

    modules = load_all(args.app)
    app = get_app(args.app)
    if args.all:
        run_all(args, app, modules)
        return
    if args.list or not args.module:
        print_list(args.app, modules)
        return

    module = pick(modules, args.module)
    if args.tests or args.push:
        # --module na --tests: aina hizo za tests tu; matokeo mengine ya module yanabaki.
        # --push: matokeo lazima yaingie summary.json ambayo push_to_tester inaisoma.
        args.only = str(next(n for n, m in enumerate(modules, 1) if m["id"] == module["id"]))
        args.include_slow = True
        run_all(args, app, modules)
        return
    out_dir = prepare_dir(REPORTS_DIR / "modules" / args.app / module["id"])
    if not args.tests:
        # --tests huendeshwa kwa vipande; usifute screenshots za vipande vilivyotangulia
        shutil.rmtree(REPORTS_DIR / "screenshots", ignore_errors=True)

    print(f"\n=== {app['name']} > {module['name']} ({module['path']}) ===")
    xml_path = out_dir / "results.xml"
    run_pytest(args.app, [module], xml_path, args.crud, edit_real=args.edit_real)
    cases, counts = report_module(app, args.app, module, xml_path, out_dir)

    print(f"\n{module['name']}: {counts['PASS']} Pass, {counts['FAIL'] + counts['ERROR']} Fail, "
          f"{counts['SKIP']} Skip")
    for c in cases:
        print(f"  {c['id']} [{c['status']:5}] {c['title']}: {c['actual']}")
    print(f"\nRipoti: {out_dir / 'report.html'}\n        {out_dir / 'report.md'}\n        {out_dir / 'report.csv'}")


if __name__ == "__main__":
    main()
