#!/usr/bin/env bash
# Endesha tests bila kukumbuka venv:  ./run.sh --app jumla --list
# Mara ya kwanza inatengeneza venv na kuinstall requirements yenyewe.
set -e
cd "$(dirname "$0")"
if [ ! -x venv/bin/python ]; then
  echo "Inatengeneza venv (mara ya kwanza tu)..."
  python3 -m venv venv
  venv/bin/pip install -q -r requirements.txt
fi
exec venv/bin/python -m tools.run_module "$@"
