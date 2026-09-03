"""Check that no CV content was lost in a rewrite.

Every chunk of visible text in the reference document must still appear in the
candidate. One-directional on purpose: the candidate is a full site page, so it
legitimately adds nav, footer and signature text the reference never had.

Usage: python3 cv-fidelity.py REFERENCE.html CANDIDATE.html

The original reference document, content/cv.html (the opaque, hand-authored
HTML artifact content/cv.toml and generator/cv.py replaced), was deleted
once this check passed against it, ratifying the rewrite. It is still
recoverable with `git show <a commit before that deletion>:content/cv.html`
-- find one with `git log --diff-filter=D -- content/cv.html`.
"""
from __future__ import annotations
import html as htmlmod
import re, sys
from pathlib import Path

_DROP = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
_TAG = re.compile(r"<[^>]+>")

def chunks(path: Path) -> list[str]:
    """Visible text, split into comparable pieces."""
    t = _DROP.sub(" ", path.read_text(encoding="utf-8"))
    t = _TAG.sub("\n", t)
    t = htmlmod.unescape(t)
    # Curly/straight quotes and dashes differ between renderers; compare on
    # the words, not the typography.
    for a, b in [("’", "'"), ("‘", "'"), ("“", '"'),
                 ("”", '"'), ("–", "-"), ("—", "-"),
                 ("…", "..."), (" ", " ")]:
        t = t.replace(a, b)
    out = []
    for line in t.split("\n"):
        line = re.sub(r"\s+", " ", line).strip()
        if len(line) > 3:                      # skip punctuation fragments
            out.append(line)
    return out

def main(ref: str, cand: str) -> int:
    r, c = chunks(Path(ref)), chunks(Path(cand))
    haystack = " ␟ ".join(c)
    missing = [x for x in r if x not in haystack]
    print(f"reference chunks: {len(r)}   candidate chunks: {len(c)}")
    if not missing:
        print("\nALL REFERENCE TEXT PRESENT")
        return 0
    print(f"\nMISSING FROM CANDIDATE ({len(missing)}):\n")
    for m in missing[:40]:
        print(f"  {m[:150]}")
    if len(missing) > 40:
        print(f"  … and {len(missing) - 40} more")
    return 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
