"""Pygments highlighting shaped like Chroma's output.

Hugo/Chroma wraps every highlighted block as:

    <div class="highlight"><pre tabindex="0" style="...">
      <code class="language-X" data-lang="X">...</code>
    </pre></div>

The outer `<div class="highlight">` is added by markdown.py's custom `fence`
render rule (it sits outside the `<pre>`, so it has to be the caller's
decision whether to add it — see that module for why). This module only
builds the `<pre>...</pre>` itself, matching Chroma's attributes: the
`tabindex="0"` Chroma always emits, the default foreground colour and
background colour as inline styles (Pygments' `noclasses=True` only colours
tokens it recognises; anything else falls through to the `<pre>`'s own
`color`), and the tab-size declarations, which matter for the `make`
examples that contain literal tabs.

An unlabelled block must NEVER be guessed at: 25 blocks have no language and
must stay unhighlighted.
"""
from __future__ import annotations
from pygments import highlight as _pyg_highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.styles import get_style_by_name
from pygments.token import Token as _Token
from pygments.util import ClassNotFound

_STYLE_NAME = "monokai"
_FORMATTER = HtmlFormatter(style=_STYLE_NAME, noclasses=True, nowrap=True)
_STYLE = get_style_by_name(_STYLE_NAME)
_PRE_STYLE = (
    f"color:{_STYLE.styles[_Token]};background-color:{_STYLE.background_color};"
    "-moz-tab-size:4;-o-tab-size:4;tab-size:4;-webkit-text-size-adjust:none;"
)

def highlight(code: str, lang: str, attrs: str = "") -> str:
    if not lang:
        return ""          # unlabelled: let the fence rule escape it plainly
    try:
        lexer = get_lexer_by_name(lang.lower())
    except ClassNotFound:
        return ""          # unknown language: plain, never guessed
    body = _pyg_highlight(code, lexer, _FORMATTER)
    return (
        f'<pre tabindex="0" style="{_PRE_STYLE}">'
        f'<code class="language-{lang}" data-lang="{lang}">{body}</code></pre>'
    )
