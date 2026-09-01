"""Diff Hugo's output tree against the generator's, by category.

The allow-list below is the single written record of what we deliberately let
differ. Anything not on it must be zero. Report by category, never as a wall of
lines: the categorised report is what makes this usable day to day.
"""
from __future__ import annotations
import hashlib
import re, sys, collections, difflib
from pathlib import Path

# Only these entities are typographic equivalences on the accepted-drift
# allow-list (smart quotes, dashes, ellipsis). Everything else — crucially
# &lt; &gt; &amp; &quot; &#39; — is structural markup/escaping and must stay
# untouched: decoding those would equate escaped text with live markup (e.g.
# a documented "&lt;script&gt;" turning into an executable <script>) or a
# correctly-escaped URL query string ("&amp;") with a malformed one ("&").
# &nbsp; is deliberately NOT in this map: it is pervasive in real layout
# markup (pagination, breadcrumbs, post meta) and folding it to a plain
# space could mask a real difference in how that whitespace is produced.
_TYPOGRAPHIC = {
    "&rsquo;": "'", "&lsquo;": "'", "&ldquo;": '"', "&rdquo;": '"',
    "&hellip;": "...", "&ndash;": "--", "&mdash;": "---",
}

_HEADING_ID_RE = re.compile(r'<h[1-6]\b[^>]*\bid="([^"]+)"')
_ID_ATTR_RE = re.compile(r'id="([^"]+)"')

# Accepted drift, per the spec. Applied to BOTH sides before comparison, so a
# difference of this kind cannot reach the report.
def normalise(text: str) -> str:
    text = re.sub(r"<pre.*?</pre>", "@@CODE@@", text, flags=re.S)
    for entity, literal in _TYPOGRAPHIC.items():
        text = text.replace(entity, literal)
    text = text.replace("‘", "'").replace("’", "'")   # quote direction
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "--").replace("—", "---")  # dashes
    # The ellipsis and dash replacements above also absorb two corpus cases
    # that read literally rather than under the "smart quote/dash/ellipsis"
    # heading: a four-dot run ("....") where Goldmark keeps a trailing literal
    # period but markdown-it-py folds all four into "…" (both sides normalise
    # to "..."), and an unflanked "--" run that Goldmark converts to an
    # en-dash but markdown-it-py leaves literal (both sides normalise to
    # "--"). Both were considered and are deliberately accepted, not
    # overlooked.
    text = text.replace("…", "...")          # ellipsis
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def categorise(a: str, b: str, heading_ids_a: set[str], heading_ids_b: set[str]) -> str:
    # An id="..." only counts as a heading-slug problem when that exact id
    # value is attested as an <h1>-<h6> id on its own side. Chrome ids like
    # id="top-link"/"menu"/"theme-toggle" never appear in a heading tag, so
    # they fall through to a more honest category instead of being mislabeled.
    ids_a = set(_ID_ATTR_RE.findall(a))
    ids_b = set(_ID_ATTR_RE.findall(b))
    if ids_a & heading_ids_a and ids_b & heading_ids_b:
        return "heading id"
    if "<a href" in b and "<a href" not in a: return "extra link (over-linkify)"
    if "<a href" in a and "<a href" not in b: return "missing link"
    if "src=" in a or "src=" in b:       return "image"
    if "@@CODE@@" in a or "@@CODE@@" in b: return "code block placement"
    return "other"

def main(hugo_dir: str, gen_dir: str) -> int:
    hugo, gen = Path(hugo_dir), Path(gen_dir)
    hugo_files = {p.relative_to(hugo) for p in hugo.rglob("*") if p.is_file()}
    gen_files = {p.relative_to(gen) for p in gen.rglob("*") if p.is_file()}

    missing = sorted(hugo_files - gen_files)
    extra = sorted(gen_files - hugo_files)
    cats: collections.Counter = collections.Counter()
    examples: dict = {}

    for rel in sorted(hugo_files & gen_files):
        if rel.suffix not in (".html", ".xml"):
            # Non-markup files (images, PDFs, fingerprinted CSS/JS, favicons,
            # the webmanifest, ...) are build artifacts, not prose. Nothing
            # about them is on the accepted-drift allow-list, so they are
            # compared byte-for-byte rather than skipped.
            a_bytes = (hugo / rel).read_bytes()
            b_bytes = (gen / rel).read_bytes()
            if a_bytes != b_bytes:
                c = "binary/asset content differs"
                cats[c] += 1
                ha = hashlib.sha256(a_bytes).hexdigest()[:12]
                hb = hashlib.sha256(b_bytes).hexdigest()[:12]
                examples.setdefault(c, (str(rel), f"sha256:{ha}", f"sha256:{hb}"))
            continue
        raw_a = (hugo / rel).read_text(errors="replace")
        raw_b = (gen / rel).read_text(errors="replace")
        a = normalise(raw_a)
        b = normalise(raw_b)
        if a == b:
            continue
        heading_ids_a = set(_HEADING_ID_RE.findall(raw_a))
        heading_ids_b = set(_HEADING_ID_RE.findall(raw_b))
        sm = difflib.SequenceMatcher(None, a.split(), b.split())
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            x = " ".join(a.split()[i1:i2])[:70]
            y = " ".join(b.split()[j1:j2])[:70]
            c = categorise(x, y, heading_ids_a, heading_ids_b)
            cats[c] += 1
            examples.setdefault(c, (str(rel), x, y))

    print(f"files: hugo {len(hugo_files)}, generator {len(gen_files)}")
    if missing:
        print(f"\nMISSING from generator ({len(missing)}):")
        for m in missing[:20]: print(f"  {m}")
    if extra:
        print(f"\nEXTRA in generator ({len(extra)}):")
        for e in extra[:20]: print(f"  {e}")
    if cats:
        print("\nCONTENT DIFFERENCES by category:")
        for c, n in cats.most_common():
            rel, x, y = examples[c]
            print(f"  {n:5}  {c}")
            print(f"         e.g. {rel}")
            print(f"           hugo: {x!r}")
            print(f"           mine: {y!r}")
    ok = not missing and not extra and not cats
    print("\nCLEAN" if ok else "\nDIFFERENCES PRESENT")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
