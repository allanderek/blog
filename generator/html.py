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


# Go's html/template uses a second, "normalising" table for a value that is
# already `template.HTML` (Hugo's `.Summary`, `.Content`, ...) landing in an
# attribute: identical to the one above except that "&" is left alone, so
# entities the value already carries ("&rsquo;") are not double-encoded.
_ESCAPE_TABLE_NORM = {k: v for k, v in _ESCAPE_TABLE.items() if k != "&"}
_ESCAPE_RE_NORM = re.compile("|".join(re.escape(c) for c in _ESCAPE_TABLE_NORM))


def esc_norm(s: object) -> str:
    return _ESCAPE_RE_NORM.sub(lambda m: _ESCAPE_TABLE_NORM[m.group(0)], str(s))


# A THIRD table, for the one place Hugo calls the explicit `html` template
# function (`{{ .Summary | html }}` in the RSS/Atom feed templates) rather
# than relying on html/template's own contextual auto-escaping. That
# function is Go's plain `html/template.HTMLEscapeString`, which escapes
# `& < > " '` but -- unlike the contextual escaper `esc` above mirrors --
# never touches `+`. Confirmed against a real feed: an escaped `<code>+</code>`
# survives as a literal "+", not "&#43;". Used for feed `<description>` and
# `<content>` text nodes, where the value being escaped is already-rendered
# HTML (so its own "&rsquo;"-style entities get their "&" doubled into
# "&amp;rsquo;", same as any other "&").
_ESCAPE_TABLE_TEXT = {k: v for k, v in _ESCAPE_TABLE.items() if k != "+"}
_ESCAPE_RE_TEXT = re.compile("|".join(re.escape(c) for c in _ESCAPE_TABLE_TEXT))


def esc_text(s: object) -> str:
    return _ESCAPE_RE_TEXT.sub(lambda m: _ESCAPE_TABLE_TEXT[m.group(0)], str(s))
