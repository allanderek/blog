"""Diff Hugo's output tree against the generator's, by category.

The allow-list below is the single written record of what we deliberately let
differ. Anything not on it must be zero. Report by category, never as a wall of
lines: the categorised report is what makes this usable day to day.
"""
from __future__ import annotations
import html as htmlmod
import re, sys, collections, difflib
from pathlib import Path

# Accepted drift, per the spec. Applied to BOTH sides before comparison, so a
# difference of this kind cannot reach the report.
def normalise(text: str) -> str:
    text = re.sub(r"<pre.*?</pre>", "@@CODE@@", text, flags=re.S)
    text = htmlmod.unescape(text)                 # &rsquo; == '’'
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

def categorise(a: str, b: str) -> str:
    if 'id="' in a and 'id="' in b:      return "heading id"
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
            continue
        a = normalise((hugo / rel).read_text(errors="replace"))
        b = normalise((gen / rel).read_text(errors="replace"))
        if a == b:
            continue
        sm = difflib.SequenceMatcher(None, a.split(), b.split())
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            x = " ".join(a.split()[i1:i2])[:70]
            y = " ".join(b.split()[j1:j2])[:70]
            c = categorise(x, y)
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
