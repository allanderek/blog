"""Markdown rendering configured to match Goldmark where it matters.

Matched deliberately: heading IDs, <del> over <s>, lazy images (in Hugo's
alt/loading/src attribute order), definition lists, and linkify tuning.
Accepted drift: smart-quote direction, en-dashes, ellipsis spacing — see the
spec's accepted-drift list.

The strikethrough, image, and fence transforms are markdown-it renderer
rules, not blind regexes over the rendered HTML string: they only touch nodes
markdown-it itself produced from `~~..~~` / `![..](..)` / ```` ``` ```` syntax,
so raw HTML an author types by hand (`<s>...</s>`, `<img ...>`, `<pre>...`)
passes through untouched.
"""
from __future__ import annotations
import re
from markdown_it import MarkdownIt
from markdown_it.common.utils import escapeHtml, unescapeAll
from markdown_it.token import Token as MdToken
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

def _make_fence_rule(renderer):
    """Build the `fence` render rule bound to this MarkdownIt's renderer.

    Chroma wraps a highlighted block in `<div class="highlight">...</div>`,
    with the div sitting *outside* the `<pre>` (`div.highlight` is styled in
    assets/css/common/main.css and referenced by chroma-mod.css and
    scroll-bar.css). markdown-it-py's built-in fence rule only skips its own
    `<pre><code>` wrapping when highlight() returns a string starting with
    the literal "<pre" — a div-first result can never satisfy that, so we
    replace the whole rule and make the wrap/don't-wrap decision ourselves,
    mirroring the built-in rule's plain-text fallback exactly for an
    unlabelled or unrecognised language.
    """
    def render_fence(tokens, idx, options, env) -> str:
        token = tokens[idx]
        info = unescapeAll(token.info).strip() if token.info else ""
        lang_name, lang_attrs = "", ""
        if info:
            arr = info.split(maxsplit=1)
            lang_name = arr[0]
            if len(arr) == 2:
                lang_attrs = arr[1]
        highlighted = highlight(token.content, lang_name, lang_attrs)
        if highlighted:
            return f'<div class="highlight">{highlighted}</div>\n'
        escaped = escapeHtml(token.content)
        if info:
            tmp_token = MdToken(type="", tag="", nesting=0, attrs=token.attrs.copy())
            tmp_token.attrJoin("class", options.langPrefix + lang_name)
            return "<pre><code" + renderer.renderAttrs(tmp_token) + ">" + escaped + "</code></pre>\n"
        return "<pre><code" + renderer.renderAttrs(token) + ">" + escaped + "</code></pre>\n"
    return render_fence

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
    md = MarkdownIt("gfm-like", {"typographer": True, "html": True})
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
    md.renderer.rules["fence"] = _make_fence_rule(md.renderer)
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
