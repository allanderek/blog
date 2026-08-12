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

# Line number of the first match in the home page, empty if absent.
first_line() { grep -n "$1" "$OUT/index.html" | head -1 | cut -d: -f1; }

# True only when both posts are present AND the first precedes the second.
# Written as a function so a missing post fails rather than passing vacuously:
# 'test $(empty) -lt $(empty)' collapses to 'test -lt', which is true.
before() {
  local a b
  a=$(first_line "$1")
  b=$(first_line "$2")
  [ -n "$a" ] && [ -n "$b" ] && [ "$a" -lt "$b" ]
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

check "home has a Recent section"      "grep -q 'id=\"recent\"' $OUT/index.html"
check "home shows the newest post"     "grep -q 'link-danluu-pl-token-efficiency' $OUT/index.html"
check "home shows exactly 8 recent"    "test \$(grep -c 'class=\"home-recent-item\"' $OUT/index.html) -eq 8"
check "home links to all posts"        "grep -qE 'All [0-9]+ posts' $OUT/index.html"
check "home is not the full post list" "test \$(grep -c 'post-entry' $OUT/index.html) -eq 0"

check "home has a Start here section"  "grep -q 'id=\"start-here\"' $OUT/index.html"
check "10 featured posts listed"       "test \$(grep -c 'class=\"home-featured-item\"' $OUT/index.html) -eq 10"
check "10 blurbs listed"               "test \$(grep -c 'class=\"home-blurb\"' $OUT/index.html) -eq 10"
check "Ladybird is featured"           "grep -q 'ladybird-and-strong-static-typing' $OUT/index.html"
check "Mo Gawdat is featured"          "grep -q 'mo-gawdat-diary-of-a-ceo' $OUT/index.html"
# The real ordering test: Mo Gawdat (2026) is newer than Ladybird (2025), so
# under plain date sorting it would come first. This only passes if
# featuredWeight is actually being applied.
check "Ladybird outranks Mo Gawdat"    "before ladybird-and-strong-static-typing mo-gawdat-diary-of-a-ceo"

check "home styles are bundled"        "grep -rqs 'home-featured' $OUT/assets/css/"

exit $fail
