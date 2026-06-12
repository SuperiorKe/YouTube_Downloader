#!/usr/bin/env bash
# SessionStart hook: prepare a Claude Code (web) session to run the test suite.
# Installs the lightweight, non-GUI test dependencies. Best-effort: never fails
# the session if the network is unavailable.
set -u

echo "[session-start] Installing test dependencies..."
if pip install -q -r requirements-dev.txt 2>/dev/null; then
  echo "[session-start] Test dependencies ready. Run: python -m pytest -q"
else
  echo "[session-start] Could not install test dependencies (offline?). Skipping."
fi

exit 0
