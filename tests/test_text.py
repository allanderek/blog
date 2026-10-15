"""Pins `generator/text.py`, the ANSI text renderer behind every
`index.txt`.

Every fixture here is SYNTHETIC html, never a real post. Real posts get
edited, and a test that asserts a sentence or a count out of one turns an
ordinary edit into a CI failure -- which has already happened once in
this repo. The build-wide invariants (`test_site_text.py`) cover the real
corpus without asserting anything about its content.
"""
from __future__ import annotations

import pytest

from generator import text

BASE = "https://example.com"
PERMALINK = f"{BASE}/posts/thing/"

# Every rendered page ends with this, so a test comparing two whole
# renders is still comparing only the part that differs.
BACK_POINTER = f"Full HTML version: {PERMALINK}"

MONOKAI_FG = "\x1b[38;2;248;248;242m"      # #f8f8f2, the <pre>'s own colour
MONOKAI_BG = "\x1b[48;2;39;40;34m"         # #272822
TOKEN_BLUE = "\x1b[38;2;102;217;239m"      # #66d9ef, a keyword
PRE_OPEN = '<pre style="color:#f8f8f2;background-color:#272822;"><code>'


def render(body: str, *, permalink: str = PERMALINK, base_url: str = BASE) -> str:
    """`body` rendered as the `<main>` of a page."""
    return text.render(f"<html><body><main>{body}</main></body></html>",
                       permalink=permalink, base_url=base_url)


def plain(body: str, **kwargs) -> str:
    """`body` rendered, then stripped of every escape sequence."""
    return text.visible(render(body, **kwargs))


def code_lines(rendered: str) -> list[str]:
    return [line for line in rendered.split("\n") if MONOKAI_BG in line]


# --- headings -----------------------------------------------------------

def test_six_heading_levels_render_distinguishably():
    """h5 and h6 are unused on the site today and still have to work: a
    nested heading is a reasonable thing to reach for while writing, and
    it must not break the build. They are also why h2/h3/h4 cannot all be
    plain bold -- an earlier draft had three levels rendering alike."""
    renders = {level: render(f"<h{level}>Heading</h{level}>") for level in range(1, 7)}
    assert len(set(renders.values())) == 6, "two heading levels render identically"


@pytest.mark.parametrize("level, marker", [
    (1, "━"),
    (2, "─"),
    (3, "\x1b[1m"),
    (4, "\x1b[4m"),
    (5, "\x1b[3m"),
])
def test_each_heading_level_carries_its_own_marker(level, marker):
    assert marker in render(f"<h{level}>Heading</h{level}>")


def test_the_deepest_heading_is_italic_and_dim():
    rendered = render("<h6>Heading</h6>")
    assert "\x1b[3m" in rendered and "\x1b[2m" in rendered


def test_a_heading_rule_is_as_wide_as_the_visible_text_not_the_escapes():
    rendered = render("<h1>Six ch</h1>")
    rule = next(line for line in rendered.split("\n") if "━" in line)
    assert rule == "━" * len("Six ch")


# --- inline -------------------------------------------------------------

@pytest.mark.parametrize("tag, code", [
    ("em", "\x1b[3m"),
    ("strong", "\x1b[1m"),
    ("del", "\x1b[9m"),
    ("code", "\x1b[36m"),
])
def test_inline_elements_carry_their_attribute(tag, code):
    assert code + "x" in render(f"<p><{tag}>x</{tag}></p>")


def test_nested_inline_attributes_both_survive():
    """Each attribute is turned off with its own off-code rather than a
    blanket reset, so the outer style stands after the inner one ends."""
    rendered = render("<p><em>a<strong>b</strong>c</em></p>")
    assert "\x1b[3m" in rendered          # italic opened
    assert "\x1b[1mb\x1b[22m" in rendered  # bold closed with 22, not 0
    assert "\x1b[0m" not in rendered      # no blanket reset to lose the italic


def test_br_becomes_a_newline():
    assert plain("<p>a<br>b</p>").startswith("a\nb")


def test_entities_are_decoded():
    assert "a & b" in plain("<p>a &amp; b</p>")
    assert "&amp;" not in plain("<p>a &amp; b</p>")


def test_runs_of_markup_whitespace_collapse_to_one_space():
    assert "a b" in plain("<p>a\n    b</p>")


def test_nothing_is_wrapped():
    """A static file cannot know the reader's terminal width, so a
    paragraph stays one line however long it is."""
    words = " ".join(["word"] * 200)
    body = plain(f"<p>{words}</p>")
    assert words in body.split("\n")


# --- sup ----------------------------------------------------------------

def test_an_ordinal_superscript_renders_inline_and_undecorated():
    assert "3rd year" in plain("<p>3<sup>rd</sup> year</p>")


def test_an_archive_count_superscript_is_parenthesised():
    """Bare juxtaposition would read as the mangled number "2026 28"."""
    assert "2026 (28)" in plain(
        '<h2>2026<sup class="archive-count">&nbsp;28</sup></h2>')


# --- blocks -------------------------------------------------------------

def test_an_unordered_list_gets_bullets():
    assert "• one" in plain("<ul><li>one</li><li>two</li></ul>")


def test_an_ordered_list_is_numbered_from_one():
    body = plain("<ol><li>one</li><li>two</li></ol>")
    assert "1. one" in body and "2. two" in body


def test_a_nested_list_is_indented_under_its_parent_item():
    body = plain("<ul><li>outer<ul><li>inner</li></ul></li></ul>")
    assert "• outer" in body
    assert "  • inner" in body


def test_a_list_item_continuation_line_sits_under_its_marker():
    body = plain("<ul><li><p>first</p><p>second</p></li></ul>")
    assert "• first" in body
    assert "  second" in body


def test_a_blockquote_gets_a_rail():
    assert "│ quoted" in plain("<blockquote><p>quoted</p></blockquote>")


def test_a_blockquote_leaves_no_trailing_whitespace_on_a_blank_line():
    body = render("<blockquote><p>one</p><p>two</p></blockquote>")
    assert not any(line != line.rstrip() for line in text.visible(body).split("\n"))


def test_a_definition_list_bolds_the_term_and_indents_the_definition():
    rendered = render("<dl><dt>Term</dt><dd>Meaning</dd></dl>")
    assert "\x1b[1mTerm" in rendered
    assert "    Meaning" in text.visible(rendered)


def test_details_is_always_expanded():
    """A terminal has no disclosure widget, so the body must be visible
    without it."""
    body = plain("<details><summary>Click</summary><p>Hidden body.</p></details>")
    assert "Click" in body
    assert "Hidden body." in body


# --- tables -------------------------------------------------------------

def test_a_table_pads_columns_to_their_widest_cell():
    rendered = plain(
        "<table><thead><tr><th>n</th><th>Sentence</th></tr></thead>"
        "<tbody><tr><td>0</td><td>short</td></tr>"
        "<tr><td>2+</td><td>longer one</td></tr></tbody></table>")
    rows = [line for line in rendered.split("\n") if "│" in line]
    assert len({line.index("│") for line in rows}) == 1, \
        "the column separator is not aligned down the table"


def test_a_table_rules_off_its_header():
    assert "─┼─" in plain(
        "<table><thead><tr><th>h</th><th>i</th></tr></thead>"
        "<tbody><tr><td>a</td><td>b</td></tr></tbody></table>")


# --- code blocks --------------------------------------------------------

def test_a_code_block_translates_inline_hex_into_ansi_truecolour():
    """highlight.py builds these with Pygments' `noclasses=True`, so the
    colour is already in the markup as `style="color:#rrggbb"` -- there
    is no class table to consult."""
    rendered = render(f'{PRE_OPEN}<span style="color:#66d9ef">type</span></code></pre>')
    assert TOKEN_BLUE + "type" in rendered


def test_a_code_block_paints_its_own_background():
    """Monokai's default foreground is near-white; without its background
    behind it, unhighlighted code would be invisible on a light
    terminal."""
    assert MONOKAI_BG in render(f"{PRE_OPEN}plain</code></pre>")


def test_leaving_a_token_span_restores_the_enclosing_colour():
    """highlight.py wraps every source line in two structural spans, so a
    `</span>` has to restore the colour outside it rather than reset."""
    rendered = render(
        f'{PRE_OPEN}<span style="display:flex;"><span>'
        'a<span style="color:#66d9ef">b</span>c'
        "</span></span></code></pre>")
    assert MONOKAI_FG + "a" in rendered
    assert TOKEN_BLUE + "b" in rendered
    assert MONOKAI_FG + "c" in rendered, "the colour after the token span was lost"


def test_every_line_of_a_code_block_is_padded_to_the_blocks_longest_line():
    """Padding to a width known from the BLOCK is what lets the background
    form a rectangle without knowing the terminal's width."""
    rendered = render(f"{PRE_OPEN}short\na much longer line\n</code></pre>")
    widths = {text.visible_len(line) for line in code_lines(rendered)}
    assert len(widths) == 1, f"code block lines have differing widths: {widths}"
    assert widths == {len("a much longer line")}


def test_a_code_block_keeps_its_own_whitespace():
    rendered = plain(f"{PRE_OPEN}    indented\n</code></pre>")
    assert "    indented" in rendered


# --- links --------------------------------------------------------------

def test_a_link_is_both_clickable_and_footnoted():
    rendered = render('<p><a href="https://example.org/x">text</a></p>')
    assert "\x1b]8;;https://example.org/x\x1b\\text" in rendered
    assert "[1]" in text.visible(rendered)
    assert "https://example.org/x" in text.visible(rendered).split("Links")[1]


def test_a_same_origin_link_points_at_the_text_version():
    """So that a reader can curl their way around the site."""
    assert f"{BASE}/posts/other/index.txt" in plain(
        '<p><a href="/posts/other/">other</a></p>')


def test_a_link_to_a_file_keeps_its_own_extension():
    """Only a path ending in "/" is a page. The PDF CV stays a PDF."""
    body = plain('<p><a href="/cv.pdf">CV</a> <a href="/index.xml">feed</a></p>')
    assert f"{BASE}/cv.pdf" in body
    assert f"{BASE}/index.xml" in body
    assert ".pdf/index.txt" not in body


def test_an_external_link_is_left_alone():
    assert "https://example.org/page/" in plain(
        '<p><a href="https://example.org/page/">x</a></p>')


def test_a_repeated_url_reuses_its_footnote_number():
    body = plain('<p><a href="/a/">one</a> <a href="/a/">two</a> '
                 '<a href="/b/">three</a></p>')
    assert "one[1]" in body and "two[1]" in body and "three[2]" in body
    # One footnote entry, not one per occurrence. (The inline text shows
    # the link's words; the url lives in the OSC 8 target, which carries
    # no visible columns.)
    assert body.count(f"{BASE}/a/index.txt") == 1


def test_footnote_urls_are_absolute():
    """An OSC 8 hyperlink has no document base to resolve against, and a
    relative path cannot be pasted into a terminal either."""
    footnotes = plain('<p><a href="/posts/other/">x</a></p>').split("Links")[1]
    numbered = [line for line in footnotes.split("\n") if line.startswith("[")]
    assert numbered
    for line in numbered:
        assert "://" in line, f"relative footnote: {line!r}"


def test_a_dead_link_is_marked_and_gets_no_footnote():
    """markdown.py's `dead:` scheme emits an <a> with no href. The
    feature has to survive into text or it quietly stops meaning
    anything here."""
    rendered = render('<p><a class="dead-link" title="gone">words</a></p>')
    assert "\x1b[9m" in rendered, "a dead link is not struck through"
    assert "Links" not in text.visible(rendered), "a dead link was footnoted"
    assert "words" in text.visible(rendered)


def test_an_in_page_anchor_gets_no_footnote():
    rendered = render('<p><a href="#section">jump</a></p>')
    assert "jump" in text.visible(rendered)
    assert "Links" not in text.visible(rendered)


def test_an_image_names_its_alt_text_and_footnotes_its_source():
    body = plain('<p><img src="/images/x.png" alt="A chart"></p>')
    assert "[image: A chart]" in body
    assert f"{BASE}/images/x.png" in body


def test_a_decorative_image_is_skipped_entirely():
    """`alt=""` is html's way of saying "decorative" -- a screen reader
    passes over it, and so does this. The site's signature avatar is one,
    so without this every home page would footnote a portrait."""
    body = plain('<p>Words.<img src="/images/x.png" alt=""></p>')
    assert "Words." in body
    assert "image" not in body
    assert "Links" not in body, "a decorative image was footnoted"


def test_an_image_with_no_alt_attribute_is_announced():
    """A missing attribute says nothing about the image, unlike an empty
    one, so the reader is told it is there."""
    body = plain('<p><img src="/images/x.png"></p>')
    assert "[image]" in body
    assert f"{BASE}/images/x.png" in body


def test_a_page_with_no_links_has_no_footnote_section():
    assert "Links" not in plain("<p>Nothing to see.</p>")


# --- the page -----------------------------------------------------------

def test_only_main_is_rendered():
    page = ('<html><body><header><nav><a href="/">Home</a></nav></header>'
            "<main><p>Body.</p></main>"
            '<aside class="signature"><p>About the author.</p></aside>'
            '<footer class="footer"><span>&copy; 2026</span></footer>'
            "</body></html>")
    body = text.visible(text.render(page, permalink=PERMALINK, base_url=BASE))
    assert "Body." in body
    for chrome in ("Home", "About the author.", "2026"):
        assert chrome not in body, f"chrome leaked into the text version: {chrome!r}"


def test_the_back_pointer_is_generated_not_inherited():
    """The naive version of this feature is circular: were the text
    version to inherit the html side's pointer, it would tell its reader
    to fetch the thing they are already reading."""
    page = ('<html><body><main><p>Body.</p></main>'
            '<footer class="footer"><span class="footer-text-version">'
            f"This page in your terminal: <code>curl {PERMALINK}index.txt</code>"
            "</span></footer></body></html>")
    body = text.visible(text.render(page, permalink=PERMALINK, base_url=BASE))
    assert "in your terminal" not in body
    assert BACK_POINTER in body


def test_the_base_url_is_honoured_so_a_dev_build_stays_local():
    """`serve` builds against http://localhost:PORT. Without this every
    footnote on a local page would point at the live site."""
    local = "http://localhost:8080"
    body = plain('<p><a href="/posts/other/">x</a></p>',
                 permalink=f"{local}/posts/thing/", base_url=local)
    assert f"{local}/posts/other/index.txt" in body
    assert "example.com" not in body


def test_a_page_with_no_main_is_rejected():
    """The `page/1/` alias stubs and 404.html have no content to render;
    this is what stops them being written as empty text files."""
    with pytest.raises(ValueError, match="no <main>"):
        text.render("<html><body><p>stub</p></body></html>",
                    permalink=PERMALINK, base_url=BASE)


def test_an_unknown_element_raises():
    """The one real risk of rendering from html: a new element in a
    template would otherwise vanish silently from every text file."""
    with pytest.raises(ValueError, match="<marquee>"):
        render("<marquee>scrolling</marquee>")


def test_scripts_and_styles_are_dropped_not_rejected():
    body = plain("<p>Body.</p><script>var x = 1;</script><style>p{color:red}</style>")
    assert "Body." in body
    assert "var x" not in body and "color:red" not in body


def test_the_rendered_page_ends_with_a_single_newline():
    rendered = render("<p>Body.</p>")
    assert rendered.endswith("\n") and not rendered.endswith("\n\n")


def test_blocks_are_separated_by_one_blank_line():
    body = text.visible(render("<p>one</p><p>two</p>"))
    assert "one\n\ntwo" in body
