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

`highlight()` distinguishes THREE cases, not two -- a fence's language can
be absent, known, or named but unknown to Pygments, and Hugo renders all
three differently:

  - **unlabelled** (25 blocks in this corpus): `None`, and markdown.py's
    fence rule emits Hugo's bare `<pre tabindex="0"><code>` form. A block
    with no language must NEVER be guessed at.
  - **known language**: the styled `<pre>` with Chroma-shaped token spans.
  - **labelled, unknown language** (one block: MoonBit, which Chroma has a
    lexer for and Pygments does not): the SAME structure as a known
    language -- `div.highlight`, the styled `<pre tabindex="0" ...>`,
    `<code class="language-X" data-lang="X">` -- but with the code text
    merely escaped, no token spans. Hugo highlights it, so falling back to
    the unlabelled form would leave that one block visually unlike every
    other code block on the site (unstyled, not Monokai) on top of the
    colouring difference. Only the colouring is accepted drift.

Note this supersedes Task 4's two-case contract, where returning "" meant
"fall back entirely".

Three differences between Pygments' and Chroma's markup are corrected below
(`_compact_styles`, `_drop_default_colour`, `_wrap_lines`). None of them is
visible on the page -- compare.py masks code blocks -- but all three are
visible to the two Hugo pipelines that read a code block back out as text:
the `.Summary` word count and the JSON-LD `articleBody`. Each function says
which, and how it was found.
"""
from __future__ import annotations
import re
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

# Chroma emits NO span at all for a token that takes the theme's default
# colour; Pygments wraps one round every token it recognises, default
# colour included. Invisible in the rendered page, but it moves the text
# nodes' boundaries -- and the JSON-LD `articleBody` pipeline
# (htmlUnescape THEN strip tags, see markdown.py's `plain`) turns a
# boundary into the difference between a `&lt;...&gt;` phrase surviving and
# being swallowed as a tag. Real cases both ways: `<all source files>` in a
# Makefile (one Chroma text node, so Hugo swallows it) and `<html>` in an
# HTML example (Chroma splits it, so Hugo keeps it).
_DEFAULT_COLOUR = _STYLE.styles[_Token].upper()
_DEFAULT_SPAN_RE = re.compile(
    r'<span style="color:' + re.escape(_DEFAULT_COLOUR) + r'">(.*?)</span>', re.S)
_STYLE_ATTR_RE = re.compile(r'style="[^"]*"')
_STYLE_SPACE_RE = re.compile(r"(?<=[:;]) ")

def _compact_styles(body: str) -> str:
    """Chroma writes `style="color:#f92672"`; Pygments puts a space after
    every ":" and ";". Cosmetic in the page, but Hugo's summary word count
    (see markdown.py's `extract_summary`) counts whitespace-separated
    tokens of the raw HTML and skips the ones that look like an attribute,
    so the extra space splits one skipped token into a skipped one and a
    COUNTED one -- inflating the count and cutting the summary short."""
    return _STYLE_ATTR_RE.sub(lambda m: _STYLE_SPACE_RE.sub("", m.group(0)), body)

def _drop_default_colour(body: str) -> str:
    return _DEFAULT_SPAN_RE.sub(r"\1", body)

_SPAN_TAG_RE = re.compile(r"<(/?)span[^>]*>")
_LINE_OPEN = '<span style="display:flex;"><span>'
_LINE_CLOSE = "</span></span>"

def _wrap_lines(body: str) -> str:
    """Chroma puts every source line in its own
    `<span style="display:flex;"><span>...\n</span></span>`; Pygments emits
    one flat run. As with `_compact_styles`, this is invisible in the page
    but not to Hugo's summary word count, which counts the raw HTML's
    whitespace-separated tokens: the "\n</span></span><span" straddling
    each line break is one such token, so a ten-line code block that has no
    wrappers counts nine words short. A span left open at a line break is
    closed before the wrapper and reopened inside the next one, which is
    also what Chroma does with a token spanning several lines."""
    out: list[str] = []
    stack: list[str] = []
    line: list[str] = []
    pos = 0

    def end_line() -> None:
        out.append(_LINE_OPEN + "".join(stack) + "".join(line)
                   + "</span>" * len(stack) + _LINE_CLOSE)
        line.clear()

    def add_text(text: str) -> None:
        while text:
            nl = text.find("\n")
            if nl == -1:
                line.append(text)
                return
            line.append(text[:nl + 1])
            end_line()
            text = text[nl + 1:]

    for m in _SPAN_TAG_RE.finditer(body):
        add_text(body[pos:m.start()])
        if m.group(1):
            if stack:
                stack.pop()
        else:
            stack.append(m.group(0))
        line.append(m.group(0))
        pos = m.end()
    add_text(body[pos:])
    if line:
        end_line()
    return "".join(out)

# Go's html.EscapeString, which is what Chroma escapes code text with.
# markdown-it-py's own escapeHtml differs on two characters (`&quot;` for
# `"`, and no escape at all for `'`); that never shows in the rendered
# <pre> (compare.py masks code blocks) but it does show in the JSON-LD
# `description`, which quotes a code block's own text.
_GO_ESCAPE_HTML = {"&": "&amp;", "'": "&#39;", "<": "&lt;", ">": "&gt;", '"': "&#34;"}
_GO_ESCAPE_HTML_RE = re.compile("[&'<>\"]")

def go_escape_html(s: str) -> str:
    return _GO_ESCAPE_HTML_RE.sub(lambda m: _GO_ESCAPE_HTML[m.group(0)], s)

def _chroma_pre(lang: str, body: str) -> str:
    return (
        f'<pre tabindex="0" style="{_PRE_STYLE}">'
        f'<code class="language-{lang}" data-lang="{lang}">{body}</code></pre>'
    )

def highlight(code: str, lang: str, attrs: str = "") -> str | None:
    """The `<pre>...</pre>` for a fence, or None if there is no language at
    all -- see this module's docstring for the three cases."""
    if not lang:
        return None
    try:
        lexer = get_lexer_by_name(lang.lower())
    except ClassNotFound:
        # Chroma wraps every line whether or not it colours anything in it,
        # so the wrapper goes on here too -- Hugo's summary word count reads
        # those spans (see markdown.py's `extract_summary`).
        return _chroma_pre(lang, _wrap_lines(go_escape_html(code)))
    # Pygments escapes a double quote as `&quot;` where Chroma writes
    # `&#34;`. A bare `&quot;` here can only have come from a real `"` in
    # the source -- a literal "&quot;" typed in the code would already read
    # "&amp;quot;" by this point.
    body = _wrap_lines(_drop_default_colour(
        _compact_styles(_pyg_highlight(code, lexer, _FORMATTER))
    )).replace("&quot;", "&#34;")
    return _chroma_pre(lang, body)
