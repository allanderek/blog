"""Markdown rendering configured to match Goldmark where it matters.

Matched deliberately: heading IDs, <del> over <s>, lazy images (in Hugo's
alt/loading/src attribute order), definition lists, linkify tuning, and
goldmark's three-dots-at-a-time ellipsis. Accepted drift: smart-quote
direction and en-dashes — see the spec's accepted-drift list.

The second half of this module is Hugo's own reading of the rendered HTML
back out as text: `.Summary`, `.Plain` and `.WordCount`, which feed the
description meta tags and the JSON-LD block. Those are transcriptions of
Hugo's and Go's source rather than inferences from output, and they say so.

The strikethrough, image, and fence transforms are markdown-it renderer
rules, not blind regexes over the rendered HTML string: they only touch nodes
markdown-it itself produced from `~~..~~` / `![..](..)` / ```` ``` ```` syntax,
so raw HTML an author types by hand (`<s>...</s>`, `<img ...>`, `<pre>...`)
passes through untouched.
"""
from __future__ import annotations
import html as _html_std
import re
from markdown_it import MarkdownIt
from markdown_it.common.utils import unescapeAll
from markdown_it.token import Token as MdToken
from mdit_py_plugins.deflist import deflist_plugin
from .slugs import Slugger
from .highlight import go_escape_html, highlight

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
    css/common/main.css and referenced by chroma-mod.css and
    scroll-bar.css). markdown-it-py's built-in fence rule only skips its own
    `<pre><code>` wrapping when highlight() returns a string starting with
    the literal "<pre" — a div-first result can never satisfy that, so we
    replace the whole rule and make the wrap/don't-wrap decision ourselves.

    `highlight()` returning None means "no language", NOT "could not
    highlight": a named language Pygments does not know still gets Hugo's
    full highlighted structure, just without the colouring. See
    highlight.py's docstring for the three cases.
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
        if highlighted is not None:
            # No trailing newline: Hugo's own output glues the closing
            # </div> directly onto whatever HTML follows (confirmed against
            # the "dsls" post, where "</div><p>As you can see" has zero
            # whitespace between them).
            return f'<div class="highlight">{highlighted}</div>'
        # No language at all. Chroma is still what renders this -- hence the
        # tabindex -- but with nothing to colour it emits no wrapper div, no
        # styling and no language class. (An INDENTED code block is a
        # different thing again and never reaches here: goldmark and
        # markdown-it-py both give it a plain "<pre><code>".) Same story
        # about the trailing newline as above: confirmed against the
        # "builder-pattern" post, where "</code></pre><p>Now you can
        # provide" also has zero whitespace between them.
        return f'<pre tabindex="0"><code>{go_escape_html(token.content)}</code></pre>'
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

# --- The typographer, in goldmark's own output form ----------------------
#
# Goldmark's typographer does not emit the substituted characters; it emits
# their HTML ENTITIES ("&rsquo;", "&mdash;", ...), which then survive
# verbatim into `.Summary` and so into <meta name="description"> and the
# JSON-LD "description" -- neither of which decodes them. markdown-it-py
# emits the characters themselves. compare.py's accepted-drift list folds
# the two everywhere they appear as themselves, but NOT inside a JSON
# string, where Go has already rewritten the entity's own "&" as
# "\u0026".
#
# The two cannot be reconciled after the fact by rewriting characters back
# to entities in the rendered HTML: a smart quote or em-dash TYPED AS ITSELF
# in the markdown source is not a typographer substitution at all, and Hugo
# leaves those as characters (real cases: `elm-queue-shootout`, quoting a
# blockquote with a curly apostrophe; `link-sw-html-tools-patterns`, a
# literal em-dash). Only the parser knows which is which, so the entity form
# is produced by a SECOND parser, identical to the first except that its
# typographer substitutes entities. It feeds the description fields only --
# the rendered page, its heading ids and its alt text all still come from
# `render()` below, unchanged.
#
# markdown-it-py's smartquotes rule rewrites a quote in place by byte
# offset and mis-tracks the offsets of later quotes in the same token when
# the replacement is longer than one character (real corpus damage:
# "Specifically" coming out as "Spec'fically"). So the typographer here
# substitutes single-character SENTINELS, and those become entities in one
# pass over the finished HTML -- which also catches the copies that reach
# an alt attribute rather than a text node.
_S_LDQUO, _S_RDQUO, _S_LSQUO, _S_RSQUO = "\u2e00", "\u2e01", "\u2e02", "\u2e03"
_S_APOS, _S_HELLIP, _S_NDASH, _S_MDASH = "\u2e04", "\u2e05", "\u2e06", "\u2e07"
# All eight are Unicode category Po, like the characters they stand in for,
# so markdown-it's own "is this quote next to punctuation?" tests behave
# the same as they would on the real thing.
_SENTINEL_ENTITY = {
    _S_LDQUO: "&ldquo;", _S_RDQUO: "&rdquo;", _S_LSQUO: "&lsquo;",
    _S_RSQUO: "&rsquo;", _S_APOS: "&rsquo;", _S_HELLIP: "&hellip;",
    _S_NDASH: "&ndash;", _S_MDASH: "&mdash;",
}
_SENTINEL_RE = re.compile("[" + "".join(_SENTINEL_ENTITY) + "]")
_CHAR_FOR_ENTITY = {
    "&ldquo;": "\u201c", "&rdquo;": "\u201d", "&lsquo;": "\u2018",
    "&rsquo;": "\u2019", "&hellip;": "\u2026", "&ndash;": "\u2013",
    "&mdash;": "\u2014",
}
_ENTITY_TO_CHAR_RE = re.compile("|".join(_CHAR_FOR_ENTITY))

_GOLDMARK_ELLIPSIS_RE = re.compile(r"\.\.\.")

def _make_replacements(hellip: str, ndash: str, mdash: str):
    """markdown-it-py's own `replacements` core rule with two changes: the
    ellipsis takes exactly three dots (goldmark's rule; markdown-it-py folds
    any run of two or more into one, so "...." came out a character short of
    Hugo's "&hellip;."), and the three substitutions are parameterised so the
    entity parser can emit sentinels for them. Everything else -- which
    regexes, in which order, and the autolink guard -- is left as upstream
    has it."""
    from markdown_it.rules_core import replacements as _r

    def replace_rare(tokens) -> None:
        inside_autolink = 0
        for token in tokens:
            if (token.type == "text" and not inside_autolink
                    and _r.RARE_RE.search(token.content)):
                c = _r.PLUS_MINUS_RE.sub("\u00b1", token.content)
                c = _GOLDMARK_ELLIPSIS_RE.sub(hellip, c)
                c = re.sub("([?!])" + re.escape(hellip), r"\1..", c)
                c = _r.QUESTION_EXCLAMATION_RE.sub(r"\1\1\1", c)
                c = _r.COMMA_RE.sub(",", c)
                c = _r.EM_DASH_RE.sub(r"\1" + mdash, c)
                c = _r.EN_DASH_RE.sub(r"\1" + ndash, c)
                c = _r.EN_DASH_INDENT_RE.sub(r"\1" + ndash, c)
                token.content = c
            if token.type == "link_open" and token.info == "auto":
                inside_autolink -= 1
            if token.type == "link_close" and token.info == "auto":
                inside_autolink += 1

    def rule(state) -> None:
        if not state.md.options.typographer:
            return
        for token in state.tokens:
            if token.type != "inline" or token.children is None:
                continue
            if _r.SCOPED_ABBR_RE.search(token.content):
                _r.replace_scoped(token.children)
            if _r.RARE_RE.search(token.content):
                replace_rare(token.children)
    return rule

def _make_parser(entities: bool = False) -> MarkdownIt:
    md = MarkdownIt("gfm-like", {"typographer": True, "html": True})
    md.use(deflist_plugin)
    md.enable(["replacements", "smartquotes", "linkify"])
    # Goldmark does not linkify bare domains like "coverage.py"; only schemes.
    # Disabling linkify wholesale also kills real "https://..." autolinks, so
    # instead turn off fuzzy (schemeless) matching and keep the rest.
    md.linkify.set({"fuzzy_link": False})
    md.core.ruler.at("replacements",
                     _make_replacements("\u2026", "\u2013", "\u2014"))
    _widen_email_fuzzy_boundary(md)
    md.renderer.rules["s_open"] = _render_strikethrough_open
    md.renderer.rules["s_close"] = _render_strikethrough_close
    md.renderer.rules["image"] = _make_image_rule(md.renderer)
    md.renderer.rules["fence"] = _make_fence_rule(md.renderer)
    if entities:
        md.options["quotes"] = [_S_LDQUO, _S_RDQUO, _S_LSQUO, _S_RSQUO]
        md.core.ruler.at("replacements",
                         _make_replacements(_S_HELLIP, _S_NDASH, _S_MDASH))
    return md

_MD = _make_parser()
_MD_ENTITIES = _make_parser(entities=True)
_HEADING = re.compile(r"<h([1-6])>(.*?)</h\1>", re.S)

# Goldmark's "'twas / 'em / 'net" rule: a single quote that opens, sitting
# after a space or punctuation and followed by t, e, n or l, is treated as
# an apostrophe rather than an opening quote (extension/typographer.go).
# markdown-it-py has no such case and pairs the quote instead, so
# "'test first'" comes out &lsquo;...&rsquo; where Hugo has
# &rsquo;...&rsquo;. Safe to apply to the rendered string: in THIS parser
# "&lsquo;" can only ever be the typographer's own output -- a quote typed
# as a character stays a character. Tags in between are skipped because
# goldmark decides this on the SOURCE character following the quote, which
# an autolink or an emphasis marker puts a tag in front of.
_OPENING_SQUO_APOSTROPHE_RE = re.compile(r"&lsquo;(?=(?:<[^>]*>)*[tenl])")

def _apply_heading_ids(html: str, entity_form: bool = False) -> str:
    slugger = Slugger()

    def add_id(m: re.Match) -> str:
        level, inner = m.group(1), m.group(2)
        # Goldmark assigns heading ids while parsing BLOCKS, before the
        # typographer touches anything, so a substitution contributes
        # nothing to the id either way ("Elm doesn't have functors" ->
        # "elm-doesnt-have-functors"). Feeding the slugger the character
        # form keeps both parsers agreeing on that.
        text = _ENTITY_TO_CHAR_RE.sub(lambda e: _CHAR_FOR_ENTITY[e.group(0)], inner) \
            if entity_form else inner
        return f'<h{level} id="{slugger.slug(text)}">{inner}</h{level}>'

    return _HEADING.sub(add_id, html)

def render(text: str) -> str:
    return _apply_heading_ids(_MD.render(text))

def render_inline(text: str) -> str:
    """Inline-only rendering: links, emphasis, raw HTML, etc. survive, but
    the text is never wrapped in a block-level element (`<p>`, `<ul>`, ...).
    Used for markdown that has to sit inside an element that only accepts
    phrasing content -- a `<summary>` or a `<li>` built by `cv.py` -- where
    `render()`'s own `<p>` wrapper would be either invalid or just add
    unwanted margin."""
    return _MD.renderInline(text)

def _smartquotes_module():
    # `markdown_it.rules_core.smartquotes` as an attribute is the rule
    # FUNCTION, re-exported over its own module; reach the module itself.
    import importlib
    return importlib.import_module("markdown_it.rules_core.smartquotes")

def render_entities(text: str) -> str:
    """`render()`'s output with the typographer's substitutions in
    goldmark's entity form. Used only to build the description fields."""
    _sq = _smartquotes_module()
    # The one substitution smartquotes does not take from `options.quotes`:
    # a module-level constant for the apostrophe it inserts mid-word
    # ("don't") and for an unmatched closing quote. Swapped only for the
    # duration of this render, which is synchronous.
    saved, _sq.APOSTROPHE = _sq.APOSTROPHE, _S_APOS
    try:
        html = _MD_ENTITIES.render(text)
    finally:
        _sq.APOSTROPHE = saved
    html = _SENTINEL_RE.sub(lambda m: _SENTINEL_ENTITY[m.group(0)], html)
    return _apply_heading_ids(_OPENING_SQUO_APOSTROPHE_RE.sub("&rsquo;", html),
                              entity_form=True)


# --- Hugo's `.Summary`, `.Plain` and `.WordCount` --------------------------
#
# These three are transcriptions of Hugo v0.165.0's own Go source, not
# guesses reverse-engineered from output: three earlier attempts at
# inferring the truncation rule from rendered pages each fitted the posts
# they were derived from and broke others, because the real rule counts
# *HTML tokens*, not prose words, and no amount of staring at prose can
# show that. The two functions transcribed are
# `resources/page/page_markup.go:ExtractSummaryFromHTML` and
# `tpl/template.go:StripHTML`; the escaping/stripping helper is Go's own
# `html/template.stripTags`. Every claim below was re-checked against a
# throwaway Hugo site that prints `.Summary`/`.Plain`/`.WordCount` as JSON
# for all 176 real posts: all three match exactly, 176/176.

# Go's unicode.IsSpace.
_GO_SPACE = frozenset(
    "\t\n\v\f\r \x85\xa0     　"
    + "".join(chr(c) for c in range(0x2000, 0x200B))
)

def _go_is_space(ch: str) -> bool:
    return ch in _GO_SPACE

def _go_trim_space(s: str) -> str:
    return s.strip("".join(_GO_SPACE))

# --- Go's html/template.stripTags -----------------------------------------
#
# What a `template.HTML` value gets run through when it lands in a quoted
# attribute (`<meta name="description" content="{{ .Summary }}">`): the
# tags go, the text between them survives byte for byte -- entities
# included, since nothing decodes them, and newlines included, which is
# why the raw description form keeps a code block's own line breaks.
# Go's own tag-name rule: ASCII letters/digits, with single "-" or ":"
# separators. A "<" that is not followed by one is ordinary text
# ("I <3 Ponies!"), which is what keeps a code sample's own angle brackets
# from all disappearing.
_TAG_NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:[-:][A-Za-z0-9]+)*")
# The elements whose content Go's escaper does not treat as markup. Their
# text still reaches the output for `textarea`/`title` (context stateRCDATA,
# which stripTags emits) but not for `script`/`style` (stateJS/stateCSS,
# which it drops). Nothing in this corpus renders one -- but `plain()` feeds
# entity-DECODED content in here, where a documented "&lt;textarea&gt;" turns
# into a real one.
_RCDATA_ELEMENTS = frozenset({"textarea", "title"})
_OPAQUE_ELEMENTS = frozenset({"script", "style"})
_SPECIAL_ELEMENTS = _RCDATA_ELEMENTS | _OPAQUE_ELEMENTS

_GO_TAG_SPACE = " \t\n\f\r"
_ATTR_NAME_END = " \t\n\f\r=>"
# Go's eatAttrName treats these three as a hard parse error, not as the end
# of the attribute: the escaper goes to stateError, consumes the rest of the
# input and emits none of it. That is why a whole article can vanish from
# `articleBody` -- an Apache config in a code block renders as
# `<span ...>&lt;Directory</span> <span ...>/var/www/...`, and once the
# decoded "<Directory" is read as a tag, the "<" of the following "</span>"
# lands where an attribute name should be.
_ATTR_NAME_ERROR = "'\"<"

def _parse_tag(s: str, k: int):
    """Parse the tag starting at s[k] == '<', following Go's own transition
    functions closely enough to reproduce where they give up. Returns
    (index just past the tag, lowercase name, is-a-closing-tag, ok), or None
    if this '<' does not start a tag at all ("I <3 Ponies!"). ok=False means
    the escaper entered an error or unterminated-value state, from which
    nothing further is ever emitted."""
    n = len(s)
    closing = s.startswith("</", k)
    m = _TAG_NAME_RE.match(s, k + (2 if closing else 1))
    if m is None:
        return None
    i, name = m.end(), m.group(0).lower()
    while True:
        while i < n and s[i] in _GO_TAG_SPACE:
            i += 1
        if i >= n:
            return n, name, closing, True
        if s[i] == ">":
            return i + 1, name, closing, True
        while i < n and s[i] not in _ATTR_NAME_END:      # eatAttrName
            if s[i] in _ATTR_NAME_ERROR:
                return n, name, closing, False
            i += 1
        while i < n and s[i] in _GO_TAG_SPACE:           # tAfterName
            i += 1
        if i >= n:
            return n, name, closing, True
        if s[i] != "=":
            continue                                     # valueless attribute
        i += 1
        while i < n and s[i] in _GO_TAG_SPACE:           # tBeforeValue
            i += 1
        if i >= n:
            return n, name, closing, True
        if s[i] in "\"'":
            end = s.find(s[i], i + 1)
            if end == -1:
                return n, name, closing, False
            i = end + 1                                  # the quote is consumed
        else:
            ends = [p for p in (s.find(c, i) for c in " \t\n\f\r>") if p != -1]
            if not ends:
                return n, name, closing, False
            i = min(ends)                                # the terminator is not

def strip_tags(s: str) -> str:
    out: list[str] = []
    i = 0
    n = len(s)
    special = ""
    while i < n:
        if special:
            k = s.lower().find("</" + special, i)
            emits = special in _RCDATA_ELEMENTS
            if k == -1:
                if emits:
                    out.append(s[i:])
                break
            if emits:
                out.append(s[i:k])
            parsed = _parse_tag(s, k)
            special = ""
            if parsed is None:
                i = k + 1
                continue
            i, _, _, ok = parsed
            if not ok:
                break
            continue
        k = s.find("<", i)
        if k == -1:
            out.append(s[i:])
            break
        if s.startswith("<!--", k):
            out.append(s[i:k])
            e = s.find("-->", k + 4)
            i = n if e == -1 else e + 3
            continue
        parsed = _parse_tag(s, k)
        if parsed is None:
            out.append(s[i:k + 1])
            i = k + 1
            continue
        out.append(s[i:k])
        i, name, closing, ok = parsed
        if not ok:
            break
        if not closing and name in _SPECIAL_ELEMENTS:
            special = name
    return "".join(out)

# --- Hugo's tpl.StripHTML (the `plainify` template function) --------------
_HUGO_NL = "___hugonl_"
# Order matters: strings.NewReplacer takes the first pattern in argument
# order that matches at a given position.
_STRIP_PRE = (("\n", " "), ("</p>", _HUGO_NL), ("<br>", _HUGO_NL), ("<br />", _HUGO_NL))

def _strip_pre_replace(s: str) -> str:
    out: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        for pat, rep in _STRIP_PRE:
            if s.startswith(pat, i):
                out.append(rep)
                i += len(pat)
                break
        else:
            out.append(s[i])
            i += 1
    return "".join(out)

def plainify(s: str) -> str:
    """Hugo's `plainify`/`.Plain`: a literal newline becomes a space, a
    closing `</p>` (or a `<br>`) becomes a newline, tags are stripped, and
    finally every run of whitespace collapses to its own FIRST character.
    That last step is what makes a paragraph break read as "\\n" while a
    code block's own indentation reads as a single space."""
    if "<" not in s and ">" not in s:
        return s
    pre = _strip_pre_replace(s)
    out = strip_tags(pre)
    if pre != s:
        out = out.replace(_HUGO_NL, "\n")
    kept: list[str] = []
    was_space = False
    for ch in out:
        is_space = _go_is_space(ch)
        if not (is_space and was_space):
            kept.append(ch)
        was_space = is_space
    return "".join(kept) if kept else out

def plain(rendered_html: str) -> str:
    """Plain text for the JSON-LD `articleBody`: tags are stripped first,
    then entities are decoded.

    Hugo does the reverse (`.Content | safeJS | htmlUnescape | plainify`)
    and loses text by it, because decoding first turns escaped prose back
    into things its tag stripper eats. A fenced code block containing a
    literal `<all source files>` renders as `&lt;all source files&gt;`,
    decodes into what Go reads as a tag, and vanishes; worse, a decoded
    fragment that trips the stripper's error state (an Apache
    `<Directory ...>` block) silently drops the whole rest of the article.
    We reproduced that deliberately during the Hugo migration and stopped
    once nothing needed to diff against Hugo's own `articleBody` -- see
    docs/hugo-quirks.md quirk 1.

    Stripping first is safe in a way decoding first is not: the input is
    well-formed rendered HTML, so the only `<` the stripper sees are real
    tags, and escaped prose survives to be decoded afterwards. This is the
    same order the rest of the codebase already uses (`pages.py`'s
    `_meta_description`, `extract_summary`'s plain form)."""
    return _html_std.unescape(plainify(rendered_html))

def word_count(rendered_html: str) -> int:
    """Hugo's `.WordCount`: fields of `.Plain`. NOT the `articleBody`
    pipeline -- no `htmlUnescape` here, so the words Hugo's own articleBody
    loses to the quirk above are still counted."""
    return len(plainify(rendered_html).split())

# --- The auto-summary ------------------------------------------------------
#
# The summary is a PREFIX OF THE RENDERED HTML ending at a `</p>`: walk the
# document paragraph by paragraph, count the prose words in each, and cut
# after the paragraph that reaches the limit. Cutting on `</p>` is what keeps
# the result valid HTML and is also why a heading or a code fence never ends
# a summary -- neither contains one, so the walk carries on to the next real
# paragraph.
#
# Hugo counted whitespace-separated tokens of the RAW HTML instead, scoring
# anything that looked like a tag (`<a`, `</em>`) or an attribute
# (`href="..."`) as zero, dropping each paragraph's final character, and
# advancing by len("</p") so every chunk after the first began on the
# previous paragraph's ">". The effect was that a paragraph of exactly 70
# prose words ended the summary when it was plain text but not when it held
# a link, because the link's markup tokens displaced the words they wrapped.
# It took a throwaway Hugo build and a read of the Go source to reconstruct,
# and it produced an approximately-70-word summary either way. We count
# prose words now. See docs/hugo-quirks.md quirk 3.

def _extract_summary(content_html: str, num_words: int) -> tuple[str, bool]:
    """The summary prefix, and whether anything was actually cut (Hugo's
    `.Truncated`, which list.html uses to decide whether to append a
    literal "..."). Reaching the limit inside the document's own last
    paragraph keeps the whole document and reports not-truncated, so
    `truncated` means "something real is left over", not "we returned
    early"."""
    if num_words <= 0:
        return content_html, False
    count = 0
    j = 0
    while j < len(content_html):
        closing = content_html.find("</p>", j)
        if closing == -1:
            break
        count += len(plainify(content_html[j:closing]).split())
        cut = closing + len("</p>")
        if count >= num_words:
            rest = _go_trim_space(content_html[cut:])
            return _go_trim_space(content_html[:cut]), rest != ""
        j = cut
    return _go_trim_space(content_html), False

def extract_summary(content_html: str, num_words: int = 70) -> str:
    return _extract_summary(content_html, num_words)[0]

# Hugo's default `summaryLength`; hugo.toml does not override it.
SUMMARY_LENGTH = 70

def summary(body: str, length: int = SUMMARY_LENGTH) -> str:
    """The raw `.Summary` form, as `<meta name="description">` and
    `twitter:description` get it: Go's attribute escaper runs `stripTags`
    over the `template.HTML` value, keeping entities and newlines."""
    return strip_tags(extract_summary(render_entities(body), length))

def summary_description(body: str, length: int = SUMMARY_LENGTH) -> str:
    """The `plainify`d `.Summary` form, as `og:description` and the JSON-LD
    `description` get it."""
    return plainify(extract_summary(render_entities(body), length))

def entry_summary(body: str, length: int = SUMMARY_LENGTH) -> tuple[str, bool]:
    """list.html's own post-entry summary: `.Summary | plainify |
    htmlUnescape`, plus whether `.Truncated` -- unlike the meta/JSON-LD
    forms above, list.html always reads `.Summary` regardless of any
    front-matter `description:`, and appends a literal "..." itself when
    Truncated (left to the caller, same as the `og:description`/JSON-LD
    "..." -- there is none of those -- so this returns only the text and
    the flag)."""
    html_summary, truncated = _extract_summary(render_entities(body), length)
    return _html_std.unescape(plainify(html_summary)), truncated
