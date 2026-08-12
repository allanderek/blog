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

check "archive page exists"            "test -f $OUT/archives/index.html"
check "archive lists a 2016 post"      "grep -q 'selenium-and-casper' $OUT/archives/index.html"
check "archive lists a 2026 post"      "grep -q 'link-danluu-pl-token-efficiency' $OUT/archives/index.html"
# PaperMod renders menu URLs through absLangURL, so the nav href is absolute.
check "nav links to the archive"       "grep -qE 'href=\"[^\"]*/archives/\"' $OUT/index.html"

# Match intro prose and explicit hrefs, not page chrome: "Allan Clark" also
# appears in the author meta tag, and "poleprediction.com" is the site's own
# baseURL, so both match even with no intro at all.
check "intro prose present"            "grep -q 'programmer in Edinburgh' $OUT/index.html"
check "intro links to GitHub"          "grep -q 'href=\"https://github.com/allanderek\"' $OUT/index.html"
check "intro links to the CV"          "grep -q 'href=\"/cv.pdf\"' $OUT/index.html"
check "intro links to Pole Prediction" "grep -q 'href=\"https://www.poleprediction.com\"' $OUT/index.html"
check "availability placeholder shown" "grep -q 'AVAILABILITY PLACEHOLDER' $OUT/index.html"
check "stray _readme post is gone"     "! test -d $OUT/posts/_readme"

exit $fail
