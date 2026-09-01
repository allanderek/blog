"""Minimal helpers for building HTML. This is the substitute for a template
language: plain functions, real Python, a debugger that works.

`esc` deliberately does NOT use Python's `html.escape`. Go's html/template
package (which renders every Hugo page) escapes text and attribute values
alike through one fixed table -- `& < > " ' +` -> named/decimal entities,
using DECIMAL numeric references (`&#39;`, `&#43;`), never the hex form
Python's stdlib produces (`&#x27;`). The apostrophe in the site title alone
("Allanderek's blog") appears in the <title>, the nav logo, the feed-title
attributes and the footer of every single page, so matching the exact
entity form is not cosmetic: with the hex form every one of those pages
would show a real, uncategorised diff against Hugo's output. See
task-6-report.md for how this was found.
"""
from __future__ import annotations
import re

_ESCAPE_TABLE = {
    "&": "&amp;",
    "'": "&#39;",
    '"': "&#34;",
    "+": "&#43;",
    "<": "&lt;",
    ">": "&gt;",
}
_ESCAPE_RE = re.compile("|".join(re.escape(c) for c in _ESCAPE_TABLE))


def esc(s: object) -> str:
    return _ESCAPE_RE.sub(lambda m: _ESCAPE_TABLE[m.group(0)], str(s))


def attrs(**kw: object) -> str:
    out = []
    for k, v in kw.items():
        if v is None or v is False:
            continue
        k = k.rstrip("_").replace("_", "-")
        out.append(k if v is True else f'{k}="{esc(v)}"')
    return (" " + " ".join(out)) if out else ""


def tag(name: str, inner: str = "", **kw: object) -> str:
    return f"<{name}{attrs(**kw)}>{inner}</{name}>"
