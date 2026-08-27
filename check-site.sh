#!/usr/bin/env bash
# Builds the site with a production build and asserts the results.
# Run: ./check-site.sh
set -uo pipefail

OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT

passed=0
failed=0
failures=()

# pass/fail <description>: record a result. Used by check(), and directly for
# the build check, which reports its own output rather than an expression.
pass() { printf '  ok    %s\n' "$1"; passed=$((passed + 1)); }
fail() { printf '  FAIL  %s\n' "$1"; failed=$((failed + 1)); failures+=("$1"); }

# check <description> <shell expression>
check() {
  if eval "$2" >/dev/null 2>&1; then
    pass "$1"
  else
    fail "$1"
  fi
}

# Counts, and the failures repeated, so neither needs scrolling back for.
summary() {
  local total=$((passed + failed)) noun=checks
  [ "$total" -eq 1 ] && noun=check
  echo
  echo "----------------------------------------------------------------"
  printf '%d %s: %d passed, %d failed\n' "$total" "$noun" "$passed" "$failed"
  if [ "$failed" -gt 0 ]; then
    echo
    echo "Failed:"
    printf '  %s\n' "${failures[@]}"
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
  pass "hugo build exits 0"
else
  fail "hugo build exits 0"
  grep '^ERROR' "$OUT/build.log" | head -5
  echo
  echo "Build failed; skipping remaining checks."
  summary
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
check "intro links to the CV"          "grep -q 'href=\"/cv/\"' $OUT/index.html"
check "intro links to Pole Prediction" "grep -q 'href=\"https://www.poleprediction.com\"' $OUT/index.html"
check "no leftover placeholder text"   "! grep -q 'PLACEHOLDER' $OUT/index.html"
check "intro states availability"      "grep -qi 'available for' $OUT/index.html"
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

check "RSS feed still generated"       "test -s $OUT/index.xml"
check "Atom feed still generated"      "test -s $OUT/rss/index.xml"
check "Atom feed has 20 entries"       "test \$(grep -c '<entry>' $OUT/rss/index.xml) -eq 20"
# Both feed templates render the home title as "<title> on <site title>" when
# the two differ, so a 'title' in content/_index.md silently rewrites the feeds.
check "Atom feed title not rewritten"  "! grep -qE '<title>[^<]+ on Allanderek' $OUT/rss/index.xml"
check "RSS feed title not rewritten"   "! grep -qE '<title>[^<]+ on Allanderek' $OUT/index.xml"
check "/posts/ still generated"        "test -f $OUT/posts/index.html"
check "/posts/ still paginated"        "test -f $OUT/posts/page/2/index.html"
check "tag pages still generated"      "test -f $OUT/tags/elm/index.html"
check "CV page still generated"        "test -f $OUT/cv/index.html"

# The consulting page, its nav entry, and the signature block. The signature is
# rendered from layouts/baseof.html, a whole-file override of the theme's, so
# these also catch a theme update silently reinstating the original baseof.
check "consulting page generated"      "test -f $OUT/consulting/index.html"
check "consulting page mentions Elm"   "grep -q 'Elm' $OUT/consulting/index.html"
check "nav links to consulting"        "grep -qE 'href=\"[^\"]*/consulting/\" title=\"Consulting\"' $OUT/index.html"
check "one signature on home"          "test \$(grep -c '<aside class=\"signature' $OUT/index.html) -eq 1"
check "home signature is inline"       "grep -q '<aside class=\"signature signature-inline\"' $OUT/index.html"
check "signature precedes Start here"  "before '<aside class=\"signature' 'id=\"start-here\"'"
check "signature on a post"            "grep -q '<aside class=\"signature\"' \$(ls -d $OUT/posts/*/index.html | head -1)"
check "signature on the CV page"       "grep -q '<aside class=\"signature\"' $OUT/cv/index.html"
check "signature on the archive"       "grep -q '<aside class=\"signature\"' $OUT/archives/index.html"
check "no signature on consulting"     "! grep -q '<aside class=\"signature' $OUT/consulting/index.html"
# The window has to clear the avatar and the .signature-body wrapper, which
# sit between the opening tag and the link.
check "signature links to consulting"  "grep -A12 '<aside class=\"signature\"' \$(ls -d $OUT/posts/*/index.html | head -1) | grep -q 'href=\"/consulting/\"'"
check "signature styles are bundled"   "grep -rq '.signature' $OUT/assets/css/"

summary
[ "$failed" -eq 0 ]
