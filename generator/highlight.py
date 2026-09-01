"""Pygments highlighting shaped like Chroma's output.

Hugo emits inline styles (Monokai), not CSS classes — the .chroma rules in the
bundled stylesheet are currently dead. We match that shape so the stylesheet
question can be revisited independently later.

An unlabelled block must NEVER be guessed at: 25 blocks have no language and
must stay unhighlighted.

markdown-it-py's fence renderer (see `markdown_it.renderer.RendererHTML.fence`)
uses our return value as-is only when it starts with the literal string
"<pre"; otherwise it wraps it in a second `<pre><code>...</code></pre>`. A
plain `HtmlFormatter(noclasses=True, nowrap=False)` call returns
`<div class="highlight">...<pre>...</pre></div>`, which starts with "<div",
not "<pre" — that mismatch would leave every highlighted block double-wrapped
in nested, invalid `<pre>` tags. We avoid the div by asking Pygments for the
bare token spans (`nowrap=True`) and building the single `<pre><code>` shell
ourselves, carrying the block's background as an inline style the way Chroma
does.
"""
from __future__ import annotations
from pygments import highlight as _pyg_highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.styles import get_style_by_name
from pygments.util import ClassNotFound

_STYLE_NAME = "monokai"
_FORMATTER = HtmlFormatter(style=_STYLE_NAME, noclasses=True, nowrap=True)
_BACKGROUND = get_style_by_name(_STYLE_NAME).background_color

def highlight(code: str, lang: str, attrs: str = "") -> str:
    if not lang:
        return ""          # unlabelled: let markdown-it escape it plainly
    try:
        lexer = get_lexer_by_name(lang.lower())
    except ClassNotFound:
        return ""          # unknown language: plain, never guessed
    body = _pyg_highlight(code, lexer, _FORMATTER)
    return (
        f'<pre style="background-color:{_BACKGROUND}">'
        f'<code class="language-{lang}">{body}</code></pre>'
    )
