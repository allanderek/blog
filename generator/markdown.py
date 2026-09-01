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
import html as _html_std
import re
from html.parser import HTMLParser
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
            # No trailing newline: Hugo's own output glues the closing
            # </div> directly onto whatever HTML follows (confirmed against
            # the "dsls" post, where "</div><p>As you can see" has zero
            # whitespace between them).
            return f'<div class="highlight">{highlighted}</div>'
        # Same story for the plain <pre><code> fallback (an unlabelled or
        # unrecognised fence, e.g. a bare ``` block): confirmed against the
        # "builder-pattern" post, "</code></pre><p>Now you can provide"
        # also has zero whitespace between them.
        escaped = escapeHtml(token.content)
        if info:
            tmp_token = MdToken(type="", tag="", nesting=0, attrs=token.attrs.copy())
            tmp_token.attrJoin("class", options.langPrefix + lang_name)
            return "<pre><code" + renderer.renderAttrs(tmp_token) + ">" + escaped + "</code></pre>"
        return "<pre><code" + renderer.renderAttrs(token) + ">" + escaped + "</code></pre>"
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

# --- Auto-summary (Hugo's `.Summary`, used for og:/twitter:/JSON-LD
# description when a post has no `description` front matter) --------------
#
# Reverse-engineered from real output, not from Hugo's source: build a
# candidate description for a post with no explicit `description:`, render
# both with Hugo and this generator, and diff. Evidence from three posts
# with different shapes (a single long paragraph; paragraph+heading+
# paragraph; paragraph+fenced-code+paragraph) shows Hugo accumulates whole
# top-level blocks -- paragraphs, headings, fences, list items -- in document
# order, in *plain* text (marks like `**`/`*`/`` ` `` stripped, link/image
# targets dropped, smartquotes/typographer already applied since this reuses
# the shared parser's tokens), joined by "\n", and stops as soon as the
# cumulative word count reaches `length` -- never splitting a block, even
# when that block alone blows past the limit (a 124-word first paragraph is
# still quoted in full for a 70-word summary). Fenced code keeps its
# original source line breaks verbatim: unlike `plain()` below, this never
# goes through the chroma-highlighted HTML, so no line-joining collapse
# applies.
def _iter_top_blocks(tokens: list) -> list:
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t.type.endswith("_open"):
            depth, j = 1, i + 1
            while depth:
                if tokens[j].type.endswith("_open"):
                    depth += 1
                elif tokens[j].type.endswith("_close"):
                    depth -= 1
                j += 1
            yield tokens[i:j]
            i = j
        else:
            yield tokens[i:i + 1]
            i += 1

def _inline_plain(children) -> str:
    parts = []
    for tok in children or []:
        if tok.type in ("text", "code_inline"):
            parts.append(tok.content)
        elif tok.type in ("softbreak", "hardbreak"):
            # A literal "\n", not a space: Hugo's own <meta name="description">
            # keeps the source's own mid-paragraph line wrap verbatim ("...for a
            # \nreasonable default...", matching the .md file's own line break).
            parts.append("\n")
        elif tok.type == "image":
            parts.append(tok.attrGet("alt") or _inline_plain(tok.children) or "")
        # strong/em/s/link open-close and other marker tokens contribute no
        # text of their own -- only their children do.
    return "".join(parts)

# Two representations of a summary are needed, and they disagree at
# exactly the boundaries `plain()` above already knows how to draw. The
# "raw" form (`summary()`, used for <meta name="description"> and
# twitter:description) keeps every line break verbatim, headings included.
# The "plainified" form (`summary_description()`, used for og:description
# and the JSON-LD description) collapses a heading's own boundaries and any
# incidental whitespace (soft wraps, a code block's internal line breaks)
# to a single space, while real paragraph/list/blockquote boundaries still
# read as "\n" -- confirmed against Hugo's own output for the same post
# three ways: <meta name="description"> keeps "pattern\nTo be clear" and
# "for a\nreasonable default" verbatim, but og:description and the JSON-LD
# description both give "pattern To be clear" and "for a reasonable
# default". So `_block_html` wraps paragraph/heading/list/blockquote text
# in real (if minimal) tags -- letting `plain()` itself, unmodified, derive
# the second form from the first.
def _block_html(block: list) -> str:
    t0 = block[0]
    if t0.type == "paragraph_open":
        # A *tight* list's paragraph (no blank line between items) has its
        # paragraph_open/close marked `hidden` by markdown-it -- it's not a
        # real paragraph, just how a list item's content happens to be
        # tokenized. Wrapping it in <p> anyway synthesises a paragraph
        # boundary `plain()` has no business treating as one: it made
        # `summary_description()` insert a spurious extra "\n" for any
        # summary ending inside a (near-universally tight) list, which
        # Hugo's own output does not have.
        if t0.hidden:
            return _inline_plain(block[1].children)
        return f"<p>{_inline_plain(block[1].children)}</p>"
    if t0.type == "heading_open":
        return f"<h2>{_inline_plain(block[1].children)}</h2>"
    if t0.type in ("fence", "code_block"):
        return t0.content.rstrip("\n")
    if t0.type in ("bullet_list_open", "ordered_list_open", "dl_open"):
        # Each child here is a whole list_item/dt/dd block; flatten its own
        # inner blocks (usually one loose/tight paragraph) the same way.
        items = []
        for item in _iter_top_blocks(block[1:-1]):
            inner = "\n".join(_block_html(b) for b in _iter_top_blocks(item[1:-1]))
            if inner:
                items.append(f"<li>{inner}</li>")
        return "\n".join(items)
    if t0.type == "blockquote_open":
        inner = "\n".join(_block_html(b) for b in _iter_top_blocks(block[1:-1]))
        return f"<blockquote>{inner}</blockquote>"
    return ""

_SUMMARY_TAGS_RE = re.compile(r"</?(?:p|h2|li|blockquote)>")

def _summary_html(body: str, length: int) -> str:
    """Walks top-level blocks in order, including each one in full while
    the running word count has not yet reached `length` -- never splitting
    a block, even one that alone blows past the limit.

    Where the cut lands when a fenced code block sits near the boundary is
    NOT reliably reproduced here. Confirmed right for a threshold crossed
    inside a plain paragraph with no code nearby, and for one crossed
    inside a large fence followed by exactly one more paragraph. But two
    *other* posts whose threshold is also crossed just past a fence run
    Hugo's real output on through a further whole fence+paragraph pair
    before stopping -- and a rule built to explain those two broke a
    previously-working case (crossing inside a large paragraph that
    itself follows a fence, where Hugo stops immediately, no run-on at
    all). Every per-block rule tried (fence counting in full, counting as
    zero, run-on counts keyed to which kind of block crossed the
    threshold or what preceded it) fixes some of these posts while
    breaking others already known to be correct -- see task-6-report.md's
    "word-count boundary" section for the specific posts and numbers.
    Left as plain full-word-count accumulation, which is exactly right
    whenever the boundary doesn't fall inside or right after a fence.
    """
    tokens = _MD.parse(body)
    parts: list[str] = []
    count = 0
    for block in _iter_top_blocks(tokens):
        if count >= length:
            break
        block_html = _block_html(block)
        block_text = _SUMMARY_TAGS_RE.sub("", block_html)
        if block_text:
            parts.append(block_html)
            count += len(block_text.split())
    return "\n".join(parts)

def summary(body: str, length: int = 70) -> str:
    return _SUMMARY_TAGS_RE.sub("", _summary_html(body, length))

def summary_description(body: str, length: int = 70) -> str:
    return plain(_summary_html(body, length))

# --- Plain text of rendered content (Hugo's `.Plain`/`.WordCount`, used for
# the JSON-LD articleBody and wordCount) ------------------------------------
#
# Hugo's schema template does `.Content | safeJS | htmlUnescape | plainify`:
# entities are decoded FIRST, tags stripped SECOND. That order is not
# reversible -- a body that literally reads "<all source files>" (typed as
# `<all source files>` inside a fenced code block, so its rendered HTML has
# it as `&lt;all source files&gt;`) gets entity-decoded back into something
# that *looks* like a tag before stripping, and Hugo's tag stripper duly
# deletes it, silently. Confirmed against the "dsls" post: that exact phrase
# vanishes from Hugo's own articleBody. Reproduced here as decode-then-parse
# for the same reason.
#
# Only a closing `</p>` inserts a newline -- confirmed by the
# paragraph/paragraph boundary ("...run everything.\nMy problem...", from a
# plain "</p>\n<p>"). Every other "block-ish" tag was tried and rejected by
# real evidence: headings join the next paragraph with a single SPACE, not
# "\n" ("...pattern To be clear...", "...Convenience The builder..."), and
# so do list items ("...in-depth instructions. Such articles are...", the
# boundary between two `<li>`s) -- while both still take a "\n" from a real
# `</p>` immediately before them. That space isn't a boundary rule of its
# own either -- it's the plain "\n" already sitting as literal text between
# e.g. "</h2>" and "<p>" in the rendered HTML, picked up by ordinary
# whitespace-collapsing the same as any other text node.
#
# The chroma wrapper (`<div class="highlight"><pre>...`) is NOT a boundary
# of its own either: at the end of a code block, "</div>" is glued directly
# onto the next "<p>" in Hugo's real HTML (see markdown.py's fence rule),
# yet articleBody still shows a single space there ("...utils.o As you can
# see..."). Same mechanism: chroma's own per-line `<span>` keeps the source
# line's trailing "\n" as literal text, and that collapses to a space too.
_CLOSE_BLOCK_TAGS = frozenset({"p"})
_VOID_BLOCK_TAGS = frozenset({"br", "hr"})

class _PlainTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self.had_block = False   # did any real block tag actually fire?
        self._li_depth = 0

    def _mark_block(self) -> None:
        # A *loose* list (blank line between items) renders its item's
        # content as a real, non-hidden <p> -- unlike a tight list, whose
        # <p> the renderer suppresses entirely (see markdown.py's
        # _block_html docstring for that half of the story). That real <p>
        # closing right before </li> is NOT a boundary though: confirmed
        # against a post whose body ends inside a loose list's last item --
        # Hugo's articleBody has no trailing "\n" there, matching every
        # other "<p> inside <li>" case where a *following* sibling item
        # would otherwise wrongly read as a fresh top-level paragraph.
        if self._li_depth:
            return
        self._parts.append("\n")
        self.had_block = True

    def handle_starttag(self, tag, attrs) -> None:
        if tag == "li":
            self._li_depth += 1
        if tag in _VOID_BLOCK_TAGS:
            self._mark_block()

    def handle_startendtag(self, tag, attrs) -> None:
        if tag in _VOID_BLOCK_TAGS:
            self._mark_block()

    def handle_endtag(self, tag) -> None:
        if tag in _CLOSE_BLOCK_TAGS:
            self._mark_block()
        if tag == "li" and self._li_depth:
            self._li_depth -= 1

    def handle_data(self, data) -> None:
        self._parts.append(re.sub(r"\s+", " ", data))

    def text(self) -> str:
        joined = "".join(self._parts)
        joined = re.sub(r"[ \t]*\n[ \t]*", "\n", joined)
        joined = re.sub(r"\n{2,}", "\n", joined)
        joined = re.sub(r" {2,}", " ", joined)
        return joined.strip("\n")

def plain(rendered_html: str) -> str:
    parser = _PlainTextExtractor()
    parser.feed(_html_std.unescape(rendered_html))
    text = parser.text()
    # A trailing "\n" only belongs here when at least one real block tag
    # fired: true for anything with actual paragraphs (articleBody always
    # ends this way), but a tag-free plain string -- an explicit
    # `description:` front-matter value run through the same `plainify`
    # pipeline -- gets none, confirmed against Hugo's own JSON-LD output.
    if text and parser.had_block:
        return text + "\n"
    return text

def word_count(rendered_html: str) -> int:
    return len(plain(rendered_html).split())
