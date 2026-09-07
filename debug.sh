#!/usr/bin/env bash
# Builds the site, serves it at http://localhost:8080, and rebuilds whenever
# content/, css/ or static/ changes. See docs/dev-server.md.
# Run: ./debug.sh          (extra arguments are passed to `generator serve`)
set -uo pipefail

# The generator needs Python 3.11+ for tomllib (content/cv.toml). A bare
# `python3` is whatever is on PATH, which outside a devenv shell is often the
# system interpreter and older. Set $PYTHON to override.
PYTHON=${PYTHON:-python3}
if ! "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
  ver=$("$PYTHON" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' 2>/dev/null || echo "not found")
  echo "This needs Python 3.11 or newer; '$PYTHON' is $ver."
  echo "Run inside the devenv shell (direnv should load it), or set PYTHON=/path/to/python3."
  exit 1
fi

exec "$PYTHON" -m generator serve --port 8080 "$@"
