"""Markdown rendering configured to match Goldmark where it matters.

Matched deliberately: heading IDs, <del> over <s>, lazy images (in Hugo's
alt/loading/src attribute order), definition lists, and linkify tuning.
Accepted drift: smart-quote direction, en-dashes, ellipsis spacing — see the
spec's accepted-drift list.

The strikethrough and image transforms are markdown-it renderer rules, not
blind regexes over the rendered HTML string: they only touch nodes markdown-it
itself produced from `~~..~~` / `![..](..)` syntax, so raw HTML an author
types by hand (`<s>...</s>`, `<img ...>`) passes through untouched.
"""
from __future__ import annotations
import re
from markdown_it import MarkdownIt
from mdit_py_plugins.deflist import deflist_plugin
from .slugs import Slugger
from .highlight import highlight

def _render_strikethrough_open(tokens, idx, options, env) -> str:
    return "<del>"

def _render_strikethrough_close(tokens, idx, options, env) -> str:
    return "</del>"

def _make_image_rule(renderer):
    """Build the `image` render rule bound to this MarkdownIt's renderer.

    Mirrors Hugo's render-image.html hook: it merges alt/src/title/loading
    into one attribute set and ranges over it as a Go map, which iterates in
    sorted-key order and drops falsy (empty) values.
    """
    def render_image(tokens, idx, options, env) -> str:
        token = tokens[idx]
        if token.children:
            token.attrSet("alt", renderer.renderInlineAsText(token.children, options, env))
        else:
            token.attrSet("alt", "")
        token.attrSet("loading", "lazy")
        token.attrs = {k: v for k, v in sorted(token.attrs.items()) if v}
        return f"<img{renderer.renderAttrs(token)}>"
    return render_image

def _widen_email_fuzzy_boundary(md: MarkdownIt) -> None:
    """linkify-it's fuzzy-email match requires a "boundary" character right
    before the address (start-of-string, whitespace, `"`, `(`, ...) but does
    NOT treat an apostrophe as one, even though its own trailing boundary
    check does. Goldmark's autolinker has no such gap: a quoted address like
    'lovesakina33@gmail.com' (real text in this corpus) still gets linked.
    Add the apostrophe (straight and both curly forms) to the leading
    boundary set so we match that.
    """
    pattern = md.linkify.re["email_fuzzy"]
    marker = '"|\\('
    assert marker in pattern, "linkify-it internals changed; boundary patch no longer applies"
    md.linkify.re["email_fuzzy"] = pattern.replace(marker, marker + "|'|‘|’", 1)

def _make_parser() -> MarkdownIt:
    md = MarkdownIt("gfm-like", {"typographer": True, "html": True,
                                 "highlight": highlight})
    md.use(deflist_plugin)
    md.enable(["replacements", "smartquotes", "linkify"])
    # Goldmark does not linkify bare domains like "coverage.py"; only schemes.
    # Disabling linkify wholesale also kills real "https://..." autolinks, so
    # instead turn off fuzzy (schemeless) matching and keep the rest.
    md.linkify.set({"fuzzy_link": False})
    _widen_email_fuzzy_boundary(md)
    md.renderer.rules["s_open"] = _render_strikethrough_open
    md.renderer.rules["s_close"] = _render_strikethrough_close
    md.renderer.rules["image"] = _make_image_rule(md.renderer)
    return md

_MD = _make_parser()
_HEADING = re.compile(r"<h([1-6])>(.*?)</h\1>", re.S)

def render(text: str) -> str:
    html = _MD.render(text)
    slugger = Slugger()

    def add_id(m: re.Match) -> str:
        level, inner = m.group(1), m.group(2)
        return f'<h{level} id="{slugger.slug(inner)}">{inner}</h{level}>'

    return _HEADING.sub(add_id, html)
