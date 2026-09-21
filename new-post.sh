#!/usr/bin/env bash
# Creates an empty post at content/posts/<slug>.md and prints its path.
#
#   ./new-post.sh my-new-post
#   ./new-post.sh my-new-post "A better title"
#
# The path is the only thing on stdout, so it composes with an editor:
#   bash:  $EDITOR $(./new-post.sh my-post)
#   fish:  e (./new-post.sh my-post)
set -uo pipefail

cd "$(dirname "$0")"

# The generator needs Python 3.11+ for tomllib (content/cv.toml). A bare
# `python3` is whatever is on PATH, which outside a devenv shell is often the
# system interpreter and older. Set $PYTHON to override.
PYTHON=${PYTHON:-python3}
if ! "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
  ver=$("$PYTHON" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' 2>/dev/null || echo "not found")
  echo "This needs Python 3.11 or newer; '$PYTHON' is $ver." >&2
  echo "Run inside the devenv shell (direnv should load it), or set PYTHON=/path/to/python3." >&2
  exit 1
fi

exec "$PYTHON" -m generator new "$@"
