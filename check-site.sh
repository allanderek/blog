#!/usr/bin/env bash
# Builds the site with a production build and asserts the results.
# Run: ./check-site.sh
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

# The newest post, taken from the Atom feed's first entry. The feed template
# sorts by date, so this tracks new posts on its own and needs no editing here.
newest_slug() {
  sed -n '/<entry>/,/<\/entry>/p' "$OUT/rss/index.xml" \
    | grep -o '<id>[^<]*</id>' | head -1 | sed 's|.*/posts/||; s|/</id>||'
}

# The post the home page's Recent list leads with.
first_recent_slug() {
  sed -n '/id="recent"/,/<\/ul>/p' "$OUT/index.html" \
    | grep -o 'href="/posts/[^"]*"' | head -1 | sed 's|href="/posts/||; s|/"$||'
}

# Cross-checks two independently rendered views of the same ordering: a template
# change that broke the Recent sort but left the feed alone would be caught here.
# Guarded so an empty feed fails rather than passing vacuously, the same trap
# before() documents above: 'grep -q ""' matches everything.
leads_with_newest() {
  local a b
  a=$(newest_slug)
  b=$(first_recent_slug)
  [ -n "$a" ] && [ "$a" = "$b" ]
}

archive_lists_newest() {
  local a
  a=$(newest_slug)
  [ -n "$a" ] && grep -q "$a" "$OUT/archives/index.html"
}

echo "Building (production) into $OUT"
if "$PYTHON" -m generator build --out "$OUT" >"$OUT/build.log" 2>&1; then
  pass "generator build exits 0"
else
  fail "generator build exits 0"
  grep '^ERROR' "$OUT/build.log" | head -5
  echo
  echo "Build failed; skipping remaining checks."
  summary
  exit 1
fi

check "no ERROR lines in build output" "! grep -q '^ERROR' $OUT/build.log"

check "archive page exists"            "test -f $OUT/archives/index.html"
check "archive lists a 2016 post"      "grep -q 'selenium-and-casper' $OUT/archives/index.html"
check "archive lists the newest post"  "archive_lists_newest"
# Same-origin nav, so the generator emits a root-relative href -- see
# docs/hugo-quirks.md's "Deliberate deviations" entry (Hugo/PaperMod's
# absLangURL made this absolute, which only multilingual sites need).
check "nav links to the archive"       "grep -qF 'href=\"/archives/\"' $OUT/index.html"

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
check "home leads with the newest post" "leads_with_newest"
check "home shows exactly 8 recent"    "test \$(grep -c 'class=\"home-recent-item\"' $OUT/index.html) -eq 8"
check "home links to all posts"        "grep -qE 'All [0-9]+ posts' $OUT/index.html"
check "home is not the full post list" "test \$(grep -c 'post-entry' $OUT/index.html) -eq 0"

check "home has a Start here section"  "grep -q 'id=\"start-here\"' $OUT/index.html"
check "11 featured posts listed"       "test \$(grep -c 'class=\"home-featured-item\"' $OUT/index.html) -eq 11"
check "11 blurbs listed"               "test \$(grep -c 'class=\"home-blurb\"' $OUT/index.html) -eq 11"
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
check "nav links to consulting"        "grep -qF 'href=\"/consulting/\" title=\"Consulting\"' $OUT/index.html"
check "one signature on home"          "test \$(grep -c '<aside class=\"signature' $OUT/index.html) -eq 1"
check "home signature is inline"       "grep -q '<aside class=\"signature signature-inline\"' $OUT/index.html"
check "signature precedes Start here"  "before '<aside class=\"signature' 'id=\"start-here\"'"
check "signature on a post"            "grep -q '<aside class=\"signature\"' \$(ls -d $OUT/posts/*/index.html | head -1)"
check "signature on the CV page"       "grep -q '<aside class=\"signature\"' $OUT/cv/index.html"

# The CV used to be an opaque HTML document (its own <!DOCTYPE>/<html>/
# <head>) inserted verbatim into the site page, so the built page carried
# two of each -- see generator/cv.py's own docstring. It is now rendered
# from content/cv.toml as ordinary content, so exactly one of each, plus
# the site's own nav/footer chrome and all seven <details> bodies.
check "CV page has exactly one DOCTYPE" "test \$(grep -c '<!DOCTYPE' $OUT/cv/index.html) -eq 1"
check "CV page has the site nav"       "grep -q '<header class=\"header\"' $OUT/cv/index.html"
check "CV page has the site footer"    "grep -q '<footer class=\"footer\"' $OUT/cv/index.html"
check "CV page has all 7 detail bodies" "test \$(grep -o '<details' $OUT/cv/index.html | wc -l) -eq 7"
check "signature on the archive"       "grep -q '<aside class=\"signature\"' $OUT/archives/index.html"
check "no signature on consulting"     "! grep -q '<aside class=\"signature' $OUT/consulting/index.html"
# The window has to clear the avatar and the .signature-body wrapper, which
# sit between the opening tag and the link.
check "signature links to consulting"  "grep -A12 '<aside class=\"signature\"' \$(ls -d $OUT/posts/*/index.html | head -1) | grep -q 'href=\"/consulting/\"'"
check "signature styles are bundled"   "grep -rq '.signature' $OUT/assets/css/"

summary
[ "$failed" -eq 0 ]
