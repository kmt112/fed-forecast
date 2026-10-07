#!/bin/bash
# Double-click to open the FedCast front end (macOS). First run creates the venv and installs.
cd "$(dirname "$0")" || exit 1
if [ ! -x .venv/bin/python ]; then
  echo "First run: creating the virtual environment and installing FedCast..."
  python3 -m venv .venv && .venv/bin/python -m pip install -q -e ".[dev,api]" || {
    echo "Install failed. Make sure Python 3.11+ is installed (brew install python)."; read -r -p "Press Enter to close."; exit 1; }
fi
if [ ! -f .env ]; then
  echo "No .env found. Create one in this folder containing:  FRED_API_KEY=<your key>"
  echo "The UI still opens; only 'Take snapshot' needs the key."
fi
exec .venv/bin/python -m fedcast.cli ui
