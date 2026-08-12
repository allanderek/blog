#!/usr/bin/env bash
# Builds the site with a production build and asserts the results.
# Run: ./check-site.sh
set -uo pipefail

OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT
fail=0

# check <description> <shell expression>
check() {
  if eval "$2" >/dev/null 2>&1; then
    printf '  ok    %s\n' "$1"
  else
    printf '  FAIL  %s\n' "$1"
    fail=1
  fi
}

echo "Building (production) into $OUT"
if hugo --destination "$OUT" >"$OUT/build.log" 2>&1; then
  printf '  ok    hugo build exits 0\n'
else
  printf '  FAIL  hugo build exits 0\n'
  grep '^ERROR' "$OUT/build.log" | head -5
  echo
  echo "Build failed; skipping remaining checks."
  exit 1
fi

check "no ERROR lines in build output" "! grep -q '^ERROR' $OUT/build.log"

exit $fail
