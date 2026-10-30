#!/usr/bin/env bash
# Endesha tests bila kukumbuka venv:  ./run.sh --app jumla --list
# Mara ya kwanza (na kila requirements.txt ikibadilika) inainstall requirements yenyewe.
set -e
cd "$(dirname "$0")"
if [ ! -x venv/bin/python ]; then
  echo "Inatengeneza venv (mara ya kwanza tu)..."
  python3 -m venv venv
fi
if ! cmp -s requirements.txt venv/.requirements; then
  echo "Inainstall requirements..."
  venv/bin/pip install -q -r requirements.txt
  cp requirements.txt venv/.requirements
fi
# Playwright (--engine pw) inahitaji browser yake mara moja
if [[ " $* " == *" pw "* || " $* " == *"--engine=pw"* ]] && [ ! -f venv/.pw_browser ] && [ -z "$CHROME_BINARY" ]; then
  echo "Inapakua browser ya Playwright (mara moja tu)..."
  venv/bin/python -m playwright install chromium
  touch venv/.pw_browser
fi
exec venv/bin/python -m tools.run_module "$@"
