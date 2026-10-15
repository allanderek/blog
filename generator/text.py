"""Render a built HTML page as ANSI-styled text for terminal readers.

    curl https://blog.poleprediction.com/posts/some-post/index.txt

Design: docs/superpowers/specs/2026-10-15-curl-text-version-design.md.

Text is rendered from the BUILT HTML, not from the markdown source, for
two reasons. Only posts have a markdown source -- the home page,
`/archives/`, the listings, every tag page and the CV are generated HTML,
so a markdown backend would cover 187 pages of 266 and need a bespoke
path for each of the rest. And markdown permits raw HTML, which
markdown-it hands through as an opaque `html_block`: a markdown backend
would meet a `<table>` it could not interpret and either emit the tags
literally or drop the content, with nothing to say so. Reading from HTML
makes that whole category unrepresentable, because embedded HTML *is* the
input.

The inverse risk -- an element this module does not know -- is handled by
raising (see `_UNKNOWN_TAG`), so a new element in a template breaks the
build instead of silently vanishing from 266 text files.

Nothing here wraps text. A static file cannot know the reader's terminal
width and the terminal already wraps. The two places that do need a width
use a LOCALLY known one: a code block pads to its own longest line, and a
table pads to its own widest cell.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser

from . import highlight

# --- ANSI ---------------------------------------------------------------
#
# Styling uses only attributes and the eight standard colours, which the
# reader's own terminal theme resolves, so prose stays legible on light
# and dark alike. Truecolor appears in exactly one place -- a code block,
# which is deliberately reproducing Monokai and paints its own
# background, so it is internally consistent (see `_code_block`).
#
# Each attribute is turned off with its OWN off-code rather than a blanket
# reset, so that nesting composes without a style stack: bold inside
# italic ends the bold and leaves the italic standing.

_ON = {
    "bold": "\x1b[1m",
    "dim": "\x1b[2m",
    "italic": "\x1b[3m",
    "underline": "\x1b[4m",
    "strike": "\x1b[9m",
    "cyan": "\x1b[36m",
}
_OFF = {
    "bold": "\x1b[22m",
    "dim": "\x1b[22m",
    "italic": "\x1b[23m",
    "underline": "\x1b[24m",
    "strike": "\x1b[29m",
    "cyan": "\x1b[39m",
}
RESET = "\x1b[0m"


def style(text: str, *names: str) -> str:
    """`text` wrapped in the named attributes, innermost last."""
    if not text:
        return text
    return ("".join(_ON[n] for n in names) + text
            + "".join(_OFF[n] for n in reversed(names)))


def _fg(hex6: str) -> str:
    r, g, b = (int(hex6[i:i + 2], 16) for i in (1, 3, 5))
    return f"\x1b[38;2;{r};{g};{b}m"


def _bg(hex6: str) -> str:
    r, g, b = (int(hex6[i:i + 2], 16) for i in (1, 3, 5))
    return f"\x1b[48;2;{r};{g};{b}m"


def osc8(url: str, text: str) -> str:
    """A terminal hyperlink: `text` is clickable and points at `url`.

    OSC 8 needs an ABSOLUTE url -- a terminal has no document base to
    resolve a relative one against. That is why footnote targets are
    absolute, and so why `base_url` has to be right in development as
    well as production (see site.py's `--base-url`).
    """
    return f"\x1b]8;;{url}\x1b\\{text}\x1b]8;;\x1b\\"


# SGR sequences and OSC 8 hyperlinks both occupy no columns, so they have
# to come out before anything measures a width.
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m|\x1b\]8;;[^\x1b\x07]*(?:\x1b\\|\x07)")


def visible(s: str) -> str:
    return _ANSI_RE.sub("", s)


def visible_len(s: str) -> int:
    return len(visible(s))


# --- the tree -----------------------------------------------------------

@dataclass
class _Node:
    tag: str
    attrs: dict[str, str]
    children: list = field(default_factory=list)


_VOID = {"br", "img", "hr", "meta", "link", "input", "source", "col", "area"}


class _TreeParser(HTMLParser):
    """Whole-document parse into `_Node`s.

    A tree rather than a stream because three things need to see all of
    their content before emitting any of it: a code block pads to its own
    longest line, a table pads to its own widest cell, and an `<li>` has
    to indent its continuation lines under its own marker.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("#root", {})
        self._stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = _Node(tag, dict(attrs))
        self._stack[-1].children.append(node)
        if tag not in _VOID:
            self._stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self._stack[-1].children.append(_Node(tag, dict(attrs)))

    def handle_endtag(self, tag):
        # Close the nearest matching ancestor. An unmatched end tag is
        # ignored rather than fatal: `_DROP`ped subtrees (inline <svg>)
        # contain shapes this module has no business validating.
        for i in range(len(self._stack) - 1, 0, -1):
            if self._stack[i].tag == tag:
                del self._stack[i:]
                return

    def handle_data(self, data):
        self._stack[-1].children.append(data)


def _parse(html_text: str) -> _Node:
    parser = _TreeParser()
    parser.feed(html_text)
    parser.close()
    return parser.root


def _find(node: _Node, tag: str) -> _Node | None:
    if node.tag == tag:
        return node
    for child in node.children:
        if isinstance(child, _Node):
            found = _find(child, tag)
            if found is not None:
                return found
    return None


# --- element classification --------------------------------------------

_HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}

# Containers with no text of their own: recurse and forget them.
_TRANSPARENT = {"#root", "#inline", "main", "div", "header", "footer",
                "article", "nav", "section", "aside"}

# Dropped whole, children included. Chrome that cannot become text.
_DROP = {"script", "style", "svg", "button", "noscript", "head"}

_BLOCK = (set(_HEADINGS) | _TRANSPARENT
          | {"p", "pre", "blockquote", "ul", "ol", "dl", "table", "details",
             "hr"})

_INLINE = {"span", "code", "em", "strong", "del", "sup", "time", "a", "br",
           "img", "b", "i", "s", "small", "abbr", "kbd", "q", "cite", "mark",
           "var", "samp"}

# Handled by whichever block owns them, never reached on their own.
_OWNED = {"li", "dt", "dd", "summary", "thead", "tbody", "tfoot", "tr",
          "td", "th", "caption", "colgroup", "figcaption"}

_KNOWN = _BLOCK | _INLINE | _OWNED | _DROP

_UNKNOWN_TAG = (
    "generator/text.py does not know how to render <{tag}>, found inside "
    "<main>. Every element on the site needs a rendering here, or the "
    "text version silently loses that content on 266 pages. Add it to "
    "one of the tables in generator/text.py and give it a test in "
    "tests/test_text.py."
)

# <sup> has two unrelated uses: ordinal suffixes in the CV, where it must
# render inline and undecorated so `3<sup>rd</sup>` reads "3rd", and the
# post count beside a year on /archives/, where bare juxtaposition would
# read as the mangled number "2026 28".
_ARCHIVE_COUNT = "archive-count"

_COLOUR_RE = re.compile(r"(?:^|;)\s*color:\s*(#[0-9a-fA-F]{6})")
_BACKGROUND_RE = re.compile(r"background-color:\s*(#[0-9a-fA-F]{6})")
_WHITESPACE_RE = re.compile(r"\s+")
# Runs of spaces are collapsed the way a browser collapses them, but
# newlines are left alone: a <br> has already become one, and collapsing
# "\s+" at this stage would swallow it. Without this, markup whitespace
# before an element that supplies its own leading space shows up as a
# double space -- /archives/ rendered "2026  (28)".
_DOUBLE_SPACE_RE = re.compile(r" {2,}")
_BLANK_RUN_RE = re.compile(r"\n{3,}")


def _classes(node: _Node) -> set[str]:
    return set(node.attrs.get("class", "").split())


def _indent(text: str, prefix: str, first: str | None = None) -> str:
    """Indent `text`, with an optional different prefix for line one.

    A blank line is left blank rather than indented, so an indented block
    does not leave lines of trailing spaces behind it.
    """
    lines = text.split("\n")
    head = (first if first is not None else prefix) + lines[0]
    return "\n".join([head] + [prefix + line if line else "" for line in lines[1:]])


# --- the renderer -------------------------------------------------------

class _Renderer:
    def __init__(self, *, permalink: str, base_url: str) -> None:
        self.permalink = permalink
        self.base_url = base_url.rstrip("/")
        self._footnotes: list[str] = []
        self._numbers: dict[str, int] = {}

    # -- links

    def absolute(self, href: str) -> str:
        """`href` as an absolute url, and for a PAGE, its `.txt`.

        Only a path ending in "/" is a page: every page url on this site
        is a directory index. `/cv.pdf`, `/index.xml` and `/images/*.png`
        all keep their own extension, so the PDF CV stays a PDF and a
        feed stays a feed.
        """
        if href.startswith(self.base_url + "/"):
            href = href[len(self.base_url):]
        if not href.startswith("/"):
            return href  # external, mailto:, or already absolute elsewhere
        if href.endswith("/"):
            return f"{self.base_url}{href}index.txt"
        return f"{self.base_url}{href}"

    def footnote(self, url: str) -> int:
        if url not in self._numbers:
            self._footnotes.append(url)
            self._numbers[url] = len(self._footnotes)
        return self._numbers[url]

    # -- dispatch

    def children(self, node: _Node) -> str:
        """Render `node`'s children, blocks separated by a blank line.

        Consecutive inline children are gathered into one block, so mixed
        content (`<div>text<p>para</p></div>`) keeps the loose text.
        """
        blocks: list[str] = []
        inline: list[str] = []

        def flush() -> None:
            if not inline:
                return
            joined = _DOUBLE_SPACE_RE.sub(" ", "".join(inline)).strip()
            inline.clear()
            if joined:
                blocks.append(joined)

        for child in node.children:
            if isinstance(child, str):
                inline.append(_WHITESPACE_RE.sub(" ", child))
                continue
            if child.tag in _DROP:
                continue
            if child.tag in _BLOCK:
                flush()
                rendered = self.block(child)
                if rendered.strip():
                    blocks.append(rendered)
            elif child.tag in _INLINE:
                inline.append(self.inline(child))
            elif child.tag in _OWNED:
                # Reached only when markup nests unusually; treat as a
                # block so nothing is lost.
                flush()
                rendered = self.children(child)
                if rendered.strip():
                    blocks.append(rendered)
            else:
                raise ValueError(_UNKNOWN_TAG.format(tag=child.tag))
        flush()
        return "\n\n".join(blocks)

    def inline_of(self, node: _Node) -> str:
        """`node`'s children as a single inline string."""
        out: list[str] = []
        for child in node.children:
            if isinstance(child, str):
                out.append(_WHITESPACE_RE.sub(" ", child))
            elif child.tag in _DROP:
                continue
            elif child.tag in _INLINE:
                out.append(self.inline(child))
            elif child.tag in _KNOWN:
                out.append(self.children(child))
            else:
                raise ValueError(_UNKNOWN_TAG.format(tag=child.tag))
        return _DOUBLE_SPACE_RE.sub(" ", "".join(out)).strip()

    def block(self, node: _Node) -> str:
        tag = node.tag
        if tag in _HEADINGS:
            return self._heading(node)
        if tag in _TRANSPARENT:
            return self.children(node)
        if tag == "p":
            return self.children(node)
        if tag == "pre":
            return self._code_block(node)
        if tag == "blockquote":
            return self._blockquote(node)
        if tag in ("ul", "ol"):
            return self._list(node, ordered=(tag == "ol"))
        if tag == "dl":
            return self._definitions(node)
        if tag == "table":
            return self._table(node)
        if tag == "details":
            return self._details(node)
        if tag == "hr":
            return style("─" * 40, "dim")
        raise ValueError(_UNKNOWN_TAG.format(tag=tag))

    def inline(self, node: _Node) -> str:
        tag = node.tag
        if tag == "a":
            return self._link(node)
        if tag == "img":
            return self._image(node)
        if tag == "br":
            return "\n"
        if tag in ("code", "kbd", "samp", "var"):
            return style(self.inline_of(node), "cyan")
        if tag in ("em", "i", "cite"):
            return style(self.inline_of(node), "italic")
        if tag in ("strong", "b"):
            return style(self.inline_of(node), "bold")
        if tag in ("del", "s"):
            return style(self.inline_of(node), "strike")
        if tag == "sup":
            text = self.inline_of(node)
            if _ARCHIVE_COUNT in _classes(node):
                return f" ({text})"
            return text
        if tag in ("span", "time", "small", "abbr", "q", "mark"):
            return self.inline_of(node)
        raise ValueError(_UNKNOWN_TAG.format(tag=tag))

    # -- blocks

    def _heading(self, node: _Node) -> str:
        """Six levels that descend by weight, using only attributes the
        reader's terminal resolves -- never a colour."""
        text = self.inline_of(node)
        if not text:
            return ""
        level = _HEADINGS[node.tag]
        if level == 1:
            return style(text, "bold") + "\n" + "━" * visible_len(text)
        if level == 2:
            return style(text, "bold") + "\n" + "─" * visible_len(text)
        if level == 3:
            return style(text, "bold")
        if level == 4:
            return style(text, "underline")
        if level == 5:
            return style(text, "italic")
        return style(text, "italic", "dim")

    def _blockquote(self, node: _Node) -> str:
        """Only the `│ ` rail is dimmed, not the quoted text.

        Dimming the content would be undone by the first `<strong>`
        inside it: bold-off and dim-off are the same SGR code (22), so an
        inner bold would silently end the dim for the rest of the line.
        """
        body = self.children(node)
        # A blank line inside a quote keeps its rail -- the quote reads as
        # one continuous block -- but without the trailing space.
        return "\n".join(
            style("│ ", "dim") + line if line else style("│", "dim")
            for line in body.split("\n"))

    def _list(self, node: _Node, *, ordered: bool) -> str:
        items: list[str] = []
        number = 0
        for child in node.children:
            if not isinstance(child, _Node) or child.tag != "li":
                continue
            number += 1
            marker = f"{number}. " if ordered else "• "
            body = self.children(child)
            if not body.strip():
                continue
            items.append(_indent(body, " " * len(marker), first=marker))
        return "\n".join(items)

    def _definitions(self, node: _Node) -> str:
        out: list[str] = []
        for child in node.children:
            if not isinstance(child, _Node):
                continue
            if child.tag == "dt":
                out.append(style(self.inline_of(child), "bold"))
            elif child.tag == "dd":
                out.append(_indent(self.children(child), "    "))
        return "\n".join(line for line in out if line.strip())

    def _details(self, node: _Node) -> str:
        """Always expanded: a terminal has no disclosure widget."""
        summary = ""
        rest: list = []
        for child in node.children:
            if isinstance(child, _Node) and child.tag == "summary":
                summary = style(self.inline_of(child), "bold")
            else:
                rest.append(child)
        body = self.children(_Node("#inline", {}, rest))
        parts = [p for p in (summary, _indent(body, "  ") if body else "") if p.strip()]
        return "\n".join(parts)

    def _table(self, node: _Node) -> str:
        rows: list[tuple[bool, list[str]]] = []

        def collect(n: _Node) -> None:
            for child in n.children:
                if not isinstance(child, _Node):
                    continue
                if child.tag == "tr":
                    header = False
                    cells: list[str] = []
                    for cell in child.children:
                        if isinstance(cell, _Node) and cell.tag in ("td", "th"):
                            header = header or cell.tag == "th"
                            cells.append(self.inline_of(cell))
                    if cells:
                        rows.append((header, cells))
                else:
                    collect(child)

        collect(node)
        if not rows:
            return ""
        width = max(len(cells) for _, cells in rows)
        columns = [
            max((visible_len(cells[i]) for _, cells in rows if i < len(cells)),
                default=0)
            for i in range(width)
        ]

        def line(cells: list[str]) -> str:
            padded = [
                cells[i] + " " * (columns[i] - visible_len(cells[i]))
                if i < len(cells) else " " * columns[i]
                for i in range(width)
            ]
            return " │ ".join(padded).rstrip()

        out: list[str] = []
        for index, (header, cells) in enumerate(rows):
            out.append(line([style(c, "bold") for c in cells] if header else cells))
            following = rows[index + 1][0] if index + 1 < len(rows) else False
            if header and not following:
                out.append("─┼─".join("─" * c for c in columns))
        return "\n".join(out)

    # -- code blocks

    def _code_block(self, node: _Node) -> str:
        """A `<pre>` as a filled Monokai rectangle.

        highlight.py builds these with Pygments' `noclasses=True`, so
        every colour is already inline as `style="color:#rrggbb"` -- no
        class table to consult, just a hex to convert.

        The BACKGROUND is painted too, and every line padded to the
        block's own longest line. Monokai's default foreground is
        `#f8f8f2`, near-white: without its `#272822` behind it,
        unhighlighted code would be invisible on a light terminal. Padding
        to the longest line in the block is what makes that a rectangle
        without needing to know the terminal's width.
        """
        pre_style = node.attrs.get("style", "")
        found_colour = _COLOUR_RE.search(pre_style)
        found_background = _BACKGROUND_RE.search(pre_style)
        # An unlabelled fence has NO inline style -- highlight.py emits
        # Hugo's bare `<pre tabindex="0"><code>` for it, because a block
        # with no language must never be guessed at. Falling back to the
        # theme's defaults is what stops those 25 blocks rendering as
        # plain prose with no background behind them.
        colour = found_colour.group(1) if found_colour else highlight.DEFAULT_COLOUR
        background = (found_background.group(1) if found_background
                      else highlight.BACKGROUND_COLOUR)
        runs: list[tuple[str, str | None]] = []

        def walk(n: _Node, colour: str | None) -> None:
            for child in n.children:
                if isinstance(child, str):
                    runs.append((child, colour))
                    continue
                if child.tag in _DROP:
                    continue
                if child.tag == "br":
                    runs.append(("\n", colour))
                    continue
                # `display:flex` marks highlight.py's per-line wrapper
                # spans, which carry no colour; a token span carries one.
                # Restoring the ENCLOSING colour on the way out is what
                # the recursion buys -- a blanket reset would lose it.
                found = _COLOUR_RE.search(child.attrs.get("style", ""))
                walk(child, found.group(1) if found else colour)

        walk(node, colour)

        lines: list[list[tuple[str, str | None]]] = [[]]
        for text, colour in runs:
            pieces = text.split("\n")
            for index, piece in enumerate(pieces):
                if index:
                    lines.append([])
                if piece:
                    lines[-1].append((piece, colour))
        while lines and not lines[-1]:
            lines.pop()
        if not lines:
            return ""

        widths = [sum(len(text) for text, _ in line) for line in lines]
        column = max(widths)
        open_bg = _bg(background)
        out: list[str] = []
        for line, used in zip(lines, widths):
            body = "".join(
                (_fg(colour) if colour else "") + text for text, colour in line)
            out.append(open_bg + body + " " * (column - used) + RESET)
        return "\n".join(out)

    # -- inline

    def _link(self, node: _Node) -> str:
        text = self.inline_of(node)
        href = node.attrs.get("href")
        if not (href or "").strip():
            # Two different things arrive here.
            #
            # No href at all is markdown.py's `dead:` scheme, marking a
            # link whose target is gone and has no archive. That has to
            # survive into text or the feature quietly stops meaning
            # anything here.
            #
            # An EMPTY href is a content slip -- a markdown `[words]()`
            # whose url was never pasted in. It is invisible in a
            # browser, where it merely re-links the current page, so it
            # can sit in a post unnoticed for a long time; footnoting it
            # would put a blank entry in the Links section. It renders as
            # its words and nothing more.
            if "dead-link" in _classes(node):
                return style(text, "dim", "strike")
            return text
        if href.startswith("#"):
            # An in-page anchor cannot be followed in a flat file.
            return text
        if not text:
            return text
        url = self.absolute(href)
        return osc8(url, text) + style(f"[{self.footnote(url)}]", "dim")

    def _image(self, node: _Node) -> str:
        """An image as its alt text, or nothing at all if it is decorative.

        `alt=""` is html's way of saying "decorative, skip me" -- it is
        why a screen reader passes over the signature avatar -- so the
        text version passes over it too. Announcing `[image]` and
        footnoting its url would be noise on every page that has one.

        A MISSING alt attribute is different: it says nothing about the
        image, so the reader is told one is there and given its url.
        """
        if "alt" in node.attrs and not node.attrs["alt"].strip():
            return ""
        alt = node.attrs.get("alt", "").strip()
        label = f"[image: {alt}]" if alt else "[image]"
        src = node.attrs.get("src", "")
        if not src:
            return label
        return label + style(f"[{self.footnote(self.absolute(src))}]", "dim")

    # -- the page

    def footnote_section(self) -> str:
        if not self._footnotes:
            return ""
        heading = style("Links", "bold") + "\n" + "─" * len("Links")
        lines = [
            style(f"[{number}] ", "dim") + osc8(url, url)
            for number, url in enumerate(self._footnotes, start=1)
        ]
        return heading + "\n" + "\n".join(lines)


def render(html_text: str, *, permalink: str, base_url: str) -> str:
    """A built page's `<main>` as ANSI text, with its link footnotes.

    Only `<main>` is rendered. Everything outside it is site chrome that
    cannot usefully become text -- the nav, the signature aside, the
    back-to-top link, the scripts -- and dropping the site footer also
    drops the copyright year it generates from the current date, the same
    reason `cv-pdf-inputs.py` excludes it from the CV fingerprint.

    The pointer back to the HTML version is GENERATED here from
    `permalink`, never read out of the markup. The HTML side carries its
    own pointer the other way, in the site footer -- outside `<main>`, so
    this function never sees it. Were either side to inherit the other's
    line, the text version would tell its reader to fetch the thing they
    are already reading.
    """
    main = _find(_parse(html_text), "main")
    if main is None:
        raise ValueError(
            "no <main> element: generator/text.py was handed a page it "
            "cannot render (an alias stub or 404.html?)")
    renderer = _Renderer(permalink=permalink, base_url=base_url)
    sections = [renderer.children(main), renderer.footnote_section(),
                style("Full HTML version: ", "dim") + osc8(permalink, permalink)]
    body = "\n\n".join(section for section in sections if section.strip())
    return _BLANK_RUN_RE.sub("\n\n", body).strip("\n") + "\n"
