#!/usr/bin/env python3
"""Prints a fingerprint of everything the CV PDF is printed from.

./make-cv-pdf.sh records this alongside static/cv.pdf; ./check-site.sh
recomputes it and compares, so an edit to the CV that never made it into
the checked-in PDF shows up as a failed check rather than a silently
stale file. Both call this one script so the two can never disagree about
what "the same PDF" means.

Deliberately fingerprints only <main> and the stylesheet, not the whole
page: the site header, footer, signature and back-to-top link are all
hidden by the @media print block in css/extended/cv.css, so they cannot
change the PDF. Hashing them would make this check fire for changes that
provably do not matter -- and the footer carries the current year, which
would have turned every 1 January into a mystery CI failure.

Usage: cv-pdf-inputs.py BUILD_DIR
"""

import hashlib
import pathlib
import re
import sys


def fingerprint(build_dir: pathlib.Path) -> str:
    page = build_dir / "cv" / "index.html"
    html = page.read_text(encoding="utf-8")

    match = re.search(r"<main\b.*?</main>", html, re.DOTALL)
    if not match:
        raise SystemExit(f"{page}: no <main> element; the CV page layout changed")

    try:
        sheet = next((build_dir / "assets" / "css").glob("stylesheet.*.css"))
    except StopIteration:
        raise SystemExit(f"{build_dir}: no built stylesheet to fingerprint")

    def sha(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    return (
        f"cv-main {sha(match.group(0).encode('utf-8'))}\n"
        f"stylesheet {sha(sheet.read_bytes())}\n"
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__.strip().splitlines()[-1])
    sys.stdout.write(fingerprint(pathlib.Path(sys.argv[1])))
