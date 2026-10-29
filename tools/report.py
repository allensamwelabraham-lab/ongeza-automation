"""
Inageuza matokeo ya pytest (JUnit XML) kuwa ripoti fupi ya errors kwa kila app.

Mfano:
    pytest --junitxml=reports/results.xml
    python -m tools.report reports/results.xml            # -> reports/errors.md
"""

import argparse
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from core.config import REPORTS_DIR


APP_NAMES = {"jumla": "JUMLA", "ongeza": "ONGEZA (staging)", "ongezapro": "ONGEZA PRO"}

TEST_LABELS = {
    "test_page_loads": "Ukurasa haufunguki / error",
    "test_columns": "Columns zimepotea",
    "test_records": "Records / rows",
    "test_pagination": "Pagination",
    "test_sort": "Sort",
    "test_filter_finds_row": "Filter (thamani halisi)",
    "test_filter_no_match": "Filter (thamani isiyokuwepo)",
    "test_view": "View / detail page",
    "test_create_form_fields": "Create form fields",
    "test_create_form_rejects_empty": "Form tupu haikataliwi",
}


def short_message(case):
    node = case.find("failure")
    if node is None:
        node = case.find("error")
    text = (node.get("message") or node.text or "") if node is not None else ""
    text = text.replace("AssertionError: ", "").replace("Failed: ", "")
    text = re.sub(r"\s*assert .*", "", text.split("\n")[0])
    return text.strip()[:300]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("xml", nargs="?", default=str(REPORTS_DIR / "results.xml"))
    parser.add_argument("--out", default=str(REPORTS_DIR / "errors.md"))
    args = parser.parse_args()

    root = ET.parse(args.xml).getroot()
    totals = defaultdict(lambda: defaultdict(int))
    failures = defaultdict(lambda: defaultdict(list))

    for case in root.iter("testcase"):
        classname = case.get("classname", "")
        parts = classname.split(".")
        app = parts[1] if len(parts) > 2 and parts[0] == "tests" else "other"
        name = case.get("name", "")
        test = name.split("[")[0]

        if case.find("skipped") is not None:
            totals[app]["skipped"] += 1
        elif case.find("failure") is not None or case.find("error") is not None:
            totals[app]["failed"] += 1
            failures[app][test].append(short_message(case))
        else:
            totals[app]["passed"] += 1

    lines = ["# Ripoti ya errors za automation", ""]
    lines += ["| App | Passed | Failed | Skipped |", "|---|---|---|---|"]
    for app, t in totals.items():
        lines.append(f"| {APP_NAMES.get(app, app)} | {t['passed']} | {t['failed']} | {t['skipped']} |")

    for app, tests in failures.items():
        lines += ["", f"## {APP_NAMES.get(app, app)}", ""]
        for test, messages in tests.items():
            lines += [f"### {TEST_LABELS.get(test, test)} ({len(messages)})", ""]
            lines += [f"- {m}" for m in sorted(set(messages))]
            lines.append("")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines) + "\n")
    print(f"Ripoti -> {args.out}")


if __name__ == "__main__":
    main()
