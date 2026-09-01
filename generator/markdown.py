"""Markdown rendering configured to match Goldmark where it matters.

Matched deliberately: heading IDs, <del> over <s>, lazy images, definition
lists, and linkify tuning. Accepted drift: smart-quote direction, en-dashes,
ellipsis spacing — see the spec's accepted-drift list.
"""
from __future__ import annotations
import re
from markdown_it import MarkdownIt
from mdit_py_plugins.deflist import deflist_plugin
from .slugs import Slugger
from .highlight import highlight

def _make_parser() -> MarkdownIt:
    md = MarkdownIt("gfm-like", {"typographer": True, "html": True,
                                 "highlight": highlight})
    md.use(deflist_plugin)
    md.enable(["replacements", "smartquotes", "linkify"])
    # Goldmark does not linkify bare domains like "coverage.py"; only schemes.
    # Disabling linkify wholesale also kills real "https://..." autolinks, so
    # instead turn off fuzzy (schemeless) matching and keep the rest.
    md.linkify.set({"fuzzy_link": False})
    return md

_MD = _make_parser()
_HEADING = re.compile(r"<h([2-6])>(.*?)</h\1>", re.S)
_S_TAG = re.compile(r"<(/?)s>")
_IMG = re.compile(r"<img ")

def render(text: str) -> str:
    html = _MD.render(text)
    slugger = Slugger()

    def add_id(m: re.Match) -> str:
        level, inner = m.group(1), m.group(2)
        return f'<h{level} id="{slugger.slug(inner)}">{inner}</h{level}>'

    html = _HEADING.sub(add_id, html)
    html = _S_TAG.sub(r"<\1del>", html)            # Goldmark emits <del>
    html = _IMG.sub('<img loading="lazy" ', html)  # the render hook's job
    return html
