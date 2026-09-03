#!/usr/bin/env bash
# Runs the unit test suite.
#
# Use this rather than a bare `pytest`: that resolves to the console script,
# which does not put the repo root on sys.path, so every test module fails to
# import `generator`. `python -m pytest` does put it there. The failure looks
# like a broken checkout ("ModuleNotFoundError: No module named 'generator'")
# rather than a wrong command, so it is worth not having to rediscover.
#
# Any arguments are passed straight through to pytest:
#   ./run-tests.sh -k slugs -v
#
# The other two things CI runs are separate harnesses, not pytest:
#   ./check-site.sh            build-and-assert checks over the built site
#   ./check-links-internal.sh  every internal link resolves
set -uo pipefail

cd "$(dirname "$0")"

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

exec "$PYTHON" -m pytest "$@"
