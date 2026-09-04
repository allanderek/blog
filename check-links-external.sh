#!/usr/bin/env bash
# Builds the site and checks every external link with lychee.
# Internal links are the job of ./check-links-internal.sh
# Run: ./check-links-external.sh   (extra arguments are passed to lychee)
#
# This one hits the network, so it is slow and occasionally wrong: hosts go
# down, rate-limit, or block anything that is not a browser. Treat a failure
# as "go and look", not as a build error. Hosts that are permanently hostile
# to link checkers belong in .lycheeignore.
set -uo pipefail

# The generator needs Python 3.11+ for tomllib (content/cv.toml). A bare
# `python3` is whatever is on PATH, which outside a devenv shell is often the
# system interpreter and older -- that failed here as a bare "Build failed",
# which reads like a broken site rather than a missing interpreter. Set
# $PYTHON to override.
PYTHON=${PYTHON:-python3}
if ! "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' 2>/dev/null; then
  ver=$("$PYTHON" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))' 2>/dev/null || echo "not found")
  echo "This needs Python 3.11 or newer; '$PYTHON' is $ver."
  echo "Run inside the devenv shell (direnv should load it), or set PYTHON=/path/to/python3."
  exit 1
fi


if ! command -v lychee >/dev/null 2>&1; then
  echo "lychee is not on PATH."
  echo "It is listed in devenv.nix, so 'devenv shell' (or a direnv reload) should provide it."
  echo "Otherwise: nix shell nixpkgs#lychee -c ./check-links-external.sh"
  exit 127
fi

OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT

echo "Building into $OUT"
if "$PYTHON" -m generator build --out "$OUT" >"$OUT/build.log" 2>&1; then
  printf '  ok    generator build exits 0\n'
else
  printf '  FAIL  generator build exits 0\n'
  grep '^ERROR' "$OUT/build.log" | head -5
  echo
  echo "Build failed; cannot check links."
  exit 1
fi
echo

# --scheme http/https limits lychee to external links. That alone used to be
# enough, on the assumption that a link with no scheme is simply skipped --
# but once same-origin links became root-relative, lychee started failing to
# RESOLVE them before any scheme filtering could drop them ("Cannot resolve
# root-relative link '/cv/'"), and reported 5440 errors on a site with no
# broken links at all. --root-dir lets it resolve them against the build, at
# which point they are file:// links and the scheme filter does drop them.
#
# A browser user agent and accepting 403/429 cut out most of the false
# positives from bot-blocking and rate limiting; a real dead link almost
# always answers 404 or fails to connect.
lychee \
  --scheme http --scheme https \
  --root-dir "$OUT" \
  --exclude-all-private \
  --accept '200..=299,403,429' \
  --user-agent 'Mozilla/5.0 (compatible; link-check for blog.poleprediction.com)' \
  --max-concurrency 8 \
  --timeout 20 \
  --max-retries 2 \
  --retry-wait-time 5 \
  --cache --max-cache-age 2w \
  "$@" \
  "$OUT/**/*.html"
