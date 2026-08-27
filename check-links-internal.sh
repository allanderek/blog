#!/usr/bin/env bash
# Builds the site and checks every internal link resolves to a real page.
# No network access; external links are the job of ./check-links-external.sh
# Run: ./check-links-internal.sh
set -uo pipefail

BASEURL_HOST='blog.poleprediction.com'
CONTENT_DIR='content'

OUT=$(mktemp -d)
WORK=$(mktemp -d)
trap 'rm -rf "$OUT" "$WORK"' EXIT

echo "Building into $OUT"
if hugo --destination "$OUT" >"$WORK/build.log" 2>&1; then
  printf '  ok    hugo build exits 0\n'
else
  printf '  FAIL  hugo build exits 0\n'
  grep '^ERROR' "$WORK/build.log" | head -5
  echo
  echo "Build failed; cannot check links."
  exit 1
fi

# Every href/src in the generated HTML, one per line, as PATH:attr="value".
# grep -o puts the match at the end of the line, so awk can split on the last
# occurrence rather than the first colon (post slugs may contain colons).
grep -roE '(href|src)="[^"]*"' "$OUT" --include='*.html' >"$WORK/raw.txt"

# Classify each link. Emits: KIND <TAB> URL <TAB> PAGE
#   internal  - root-relative, or absolute into our own site; must resolve
#   relative  - no scheme and no leading slash; resolved against the page dir.
#               Nearly always a typo: "document", "www.example.com/x.html".
#   scheme    - an unknown URL scheme, e.g. the Pelican-era link://slug/...
#   external  - someone else's problem (check-links-external.sh)
#   skip      - fragments, mailto:, data:, javascript:, empty
awk -v out="$OUT" -v host="$BASEURL_HOST" '
{
  idx = match($0, /(href|src)="[^"]*"$/)
  if (idx == 0) next
  page = substr($0, 1, idx - 2)
  attr = substr($0, idx)
  url  = substr(attr, index(attr, "\"") + 1)
  url  = substr(url, 1, length(url) - 1)

  gsub(/&amp;/, "\\&", url)

  sub("^" out, "", page)

  if (url == "" || url ~ /^#/) next
  if (url ~ /^(mailto|data|javascript|tel):/) next
  if (url ~ /^\/\//) next                      # protocol-relative: external

  if (url ~ ("^https?://" host)) {
    sub(/^https?:\/\/[^\/]*/, "", url)
    if (url == "") url = "/"
    print "internal\t" url "\t" page
  } else if (url ~ /^https?:\/\//) {
    print "external\t" url "\t" page
  } else if (url ~ /^[a-zA-Z][a-zA-Z0-9+.-]*:/) {
    print "scheme\t" url "\t" page
  } else if (url ~ /^\//) {
    print "internal\t" url "\t" page
  } else {
    print "relative\t" url "\t" page
  }
}' "$WORK/raw.txt" >"$WORK/links.txt"

# Collapse to unique (kind, url), keeping one example page for each.
sort -u -t$'\t' -k1,2 "$WORK/links.txt" >"$WORK/unique.txt"

# Resolve a site-relative path to a file in the build output. Hugo emits
# pretty URLs as dir/index.html, but static assets are plain files, so try
# both. Prints the path it found, or nothing.
resolve() {
  local p=${1#/}
  p=${p%%\#*}
  p=${p%%\?*}
  [ -z "$p" ] && p='index.html'
  case "$p" in
    */) [ -f "$OUT/$p/index.html" ] && { echo "$OUT/$p/index.html"; return 0; } ;;
    *)
      [ -f "$OUT/$p" ]            && { echo "$OUT/$p"; return 0; }
      [ -f "$OUT/$p/index.html" ] && { echo "$OUT/$p/index.html"; return 0; }
      [ -f "$OUT/$p.html" ]       && { echo "$OUT/$p.html"; return 0; }
      ;;
  esac
  return 1
}

# The markdown file a link came from, so the failure is directly fixable.
# The built page path is the more reliable guide, but a raw grep catches links
# that Hugo rewrote (a shortcode, or a slug that differs from the filename).
source_file() {
  local url=$1 page=$2 slug hit
  slug=${page#/posts/}
  slug=${slug%/index.html}
  if [ -f "$CONTENT_DIR/posts/$slug.md" ] &&
     grep -qF -- "$url" "$CONTENT_DIR/posts/$slug.md" 2>/dev/null; then
    echo "$CONTENT_DIR/posts/$slug.md"
    return
  fi
  hit=$(grep -rlF -- "$url" "$CONTENT_DIR" 2>/dev/null | head -3 | paste -sd', ')
  [ -n "$hit" ] && echo "$hit"
}

# n_internal counts root-relative links; n_checked also counts the malformed
# kinds (scheme, relative), which are checked here but are not internal links
# in the sense the "Checked ..." line above reports.
n_internal=0 n_external=0 n_broken=0 n_checked=0
declare -a broken_urls broken_reasons broken_pages

while IFS=$'\t' read -r kind url page; do
  case "$kind" in
    external) n_external=$((n_external + 1)) ;;
    internal)
      n_internal=$((n_internal + 1))
      n_checked=$((n_checked + 1))
      if ! resolve "$url" >/dev/null; then
        broken_urls+=("$url"); broken_reasons+=("no such page in the build"); broken_pages+=("$page")
        n_broken=$((n_broken + 1))
      fi
      ;;
    scheme)
      n_checked=$((n_checked + 1))
      broken_urls+=("$url"); broken_reasons+=("unknown URL scheme"); broken_pages+=("$page")
      n_broken=$((n_broken + 1))
      ;;
    relative)
      n_checked=$((n_checked + 1))
      # Resolve against the directory of the page it appears on.
      dir=$(dirname "$page")
      if ! resolve "$dir/$url" >/dev/null; then
        broken_urls+=("$url")
        broken_reasons+=("relative link, and $dir/$url is not in the build")
        broken_pages+=("$page")
        n_broken=$((n_broken + 1))
      fi
      ;;
  esac
done <"$WORK/unique.txt"

total=$(wc -l <"$WORK/links.txt")
echo
printf 'Checked %s links (%s unique internal, %s unique external, not checked here)\n' \
  "$total" "$n_internal" "$n_external"

# Counts last, so the verdict does not need scrolling back for. The broken
# links themselves are already listed immediately above, so they are counted
# here rather than repeated.
summary() {
  local noun=links
  [ "$n_checked" -eq 1 ] && noun=link
  echo
  echo "----------------------------------------------------------------"
  printf '%s unique %s checked: %s ok, %s broken\n' \
    "$n_checked" "$noun" "$((n_checked - n_broken))" "$n_broken"
}

if [ "$n_broken" -eq 0 ]; then
  echo
  echo "No broken internal links."
  summary
  exit 0
fi

echo
printf 'BROKEN INTERNAL LINKS (%s)\n' "$n_broken"
for i in "${!broken_urls[@]}"; do
  printf '\n  %s\n' "${broken_urls[$i]}"
  printf '    %s\n' "${broken_reasons[$i]}"
  printf '    on: %s\n' "${broken_pages[$i]}"
  src=$(source_file "${broken_urls[$i]}" "${broken_pages[$i]}")
  [ -n "$src" ] && printf '    in: %s\n' "$src"
done

summary
exit 1
