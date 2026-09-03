#!/usr/bin/env bash
# Regenerates static/cv.pdf by printing the site's own /cv/ page with headless
# Chromium, then records what it was built from so check-site.sh can tell you
# when it has gone stale.
#
# Run: ./make-cv-pdf.sh
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

CHROMIUM=${CHROMIUM:-chromium}
if ! command -v "$CHROMIUM" >/dev/null 2>&1; then
  echo "'$CHROMIUM' not found. It is listed in devenv.nix, so a devenv shell"
  echo "should provide it. Set \$CHROMIUM to override."
  exit 1
fi

OUT=$(mktemp -d)
SERVER_PID=""
cleanup() {
  [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null
  rm -rf "$OUT"
}
trap cleanup EXIT

echo "Building into $OUT"
if ! "$PYTHON" -m generator build --out "$OUT" >"$OUT/build.log" 2>&1; then
  echo "  FAIL  generator build exits 0"
  tail -5 "$OUT/build.log"
  exit 1
fi
echo "  ok    generator build exits 0"

# A server, not file://. The page's stylesheet is referenced root-relative
# (/assets/css/...), which under file:// resolves to the filesystem root and
# loads nothing -- the PDF would come out unstyled.
PORT=$("$PYTHON" - <<'PY'
import socket
s = socket.socket(); s.bind(("127.0.0.1", 0))
print(s.getsockname()[1]); s.close()
PY
)
"$PYTHON" -m http.server "$PORT" --bind 127.0.0.1 --directory "$OUT" >/dev/null 2>&1 &
SERVER_PID=$!

for _ in $(seq 1 50); do
  if "$PYTHON" -c "
import sys, urllib.request
try:
    urllib.request.urlopen('http://127.0.0.1:$PORT/cv/', timeout=1)
except Exception:
    sys.exit(1)
" 2>/dev/null; then break; fi
  sleep 0.2
done

echo "Printing http://127.0.0.1:$PORT/cv/"
"$CHROMIUM" --headless --disable-gpu --no-sandbox \
  --no-pdf-header-footer \
  --print-to-pdf="$OUT/cv.pdf" \
  "http://127.0.0.1:$PORT/cv/" >"$OUT/chromium.log" 2>&1

if [ ! -s "$OUT/cv.pdf" ]; then
  echo "  FAIL  chromium produced no PDF"
  tail -10 "$OUT/chromium.log"
  exit 1
fi
echo "  ok    chromium produced a PDF ($(stat -c%s "$OUT/cv.pdf") bytes)"

# The expandable sections are the whole reason this check exists: the previous
# CV's print CSS claimed the <details> were always open but nothing forced
# them, so its PDF may well have been missing this content entirely.
if ! "$PYTHON" - "$OUT/cv.pdf" <<'PY'
import sys
from pypdf import PdfReader
text = " ".join((p.extract_text() or "") for p in PdfReader(sys.argv[1]).pages)
text = " ".join(text.split())
missing = [probe for probe in ("Nitro", "PEPA is a language", "e-commerce platform")
           if probe not in text]
if missing:
    print("  FAIL  PDF is missing expandable content:", ", ".join(missing))
    sys.exit(1)
print(f"  ok    PDF contains the expandable sections ({len(text.split())} words)")
PY
then
  exit 1
fi

cp "$OUT/cv.pdf" static/cv.pdf

# What the PDF was built from, so ./check-site.sh can spot a stale PDF.
# The rule lives in cv-pdf-inputs.py, which that check calls too.
if ! "$PYTHON" ./cv-pdf-inputs.py "$OUT" >static/cv.pdf.inputs; then
  echo "  FAIL  could not record static/cv.pdf.inputs"
  rm -f static/cv.pdf.inputs
  exit 1
fi
echo "  ok    recorded static/cv.pdf.inputs"

echo
echo "static/cv.pdf regenerated."
