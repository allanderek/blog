"""generator/cv.py: parsing content/cv.toml's four section kinds, and
rendering them into the CV page's own content markup."""
from __future__ import annotations
from pathlib import Path

from generator import cv

_HEADER = """
name    = "Dr. Test"
address = ["Line one", "Line two"]
pdf     = "/cv.pdf"
headlines = ["Headline one"]

[[profile]]
name = "GitHub"
url  = "https://github.com/example"
"""


def _load(tmp_path: Path, body: str) -> cv.Cv:
    path = tmp_path / "cv.toml"
    path.write_text(_HEADER + body, encoding="utf-8")
    return cv.load(path)


# --- load() -------------------------------------------------------------

def test_load_reads_the_real_content_file():
    # content/cv.toml itself parses cleanly and has the sections this
    # generator actually renders -- a smoke test against the real file,
    # not a fixture, so a typo in the TOML fails a test rather than only
    # showing up in a build.
    data = cv.load(Path("content/cv.toml"))
    assert data.name
    assert data.sections
    assert all(s.kind in ("expandable", "list", "subsections", "prose")
               for s in data.sections)


def test_load_parses_header_fields(tmp_path):
    data = _load(tmp_path, '[[section]]\ntitle="X"\nkind="list"\nitems=[]\n')
    assert data.name == "Dr. Test"
    assert data.address == ["Line one", "Line two"]
    assert data.pdf == "/cv.pdf"
    assert data.headlines == ["Headline one"]
    assert data.profiles == [cv.Profile(name="GitHub", url="https://github.com/example")]


# --- expandable -----------------------------------------------------------

def test_expandable_item_without_detail_is_a_plain_list_entry(tmp_path):
    data = _load(tmp_path, """
[[section]]
title = "Summary"
kind  = "expandable"

  [[section.item]]
  summary = "Plain bullet, no detail."
""")
    section = data.sections[0]
    assert section.kind == "expandable"
    item = section.entries[0]
    assert item.summary == "Plain bullet, no detail."
    assert item.detail is None
    html = cv.render(data)
    assert "<li>Plain bullet, no detail.</li>" in html
    assert "<details" not in html

def test_expandable_item_with_detail_renders_as_details_summary(tmp_path):
    data = _load(tmp_path, """
[[section]]
title = "Summary"
kind  = "expandable"

  [[section.item]]
  summary = "Headline text."
  detail  = "Body text, revealed on expansion."
""")
    item = data.sections[0].entries[0]
    assert item.detail == "Body text, revealed on expansion."
    html = cv.render(data)
    assert "<details" in html
    assert "<summary>Headline text.</summary>" in html
    assert "<p>Body text, revealed on expansion.</p>" in html


# --- list -------------------------------------------------------------------

def test_list_section_renders_each_item_as_an_li(tmp_path):
    data = _load(tmp_path, """
[[section]]
title = "Publications"
kind  = "list"
items = ["First paper.", "Second paper."]
""")
    section = data.sections[0]
    assert section.kind == "list"
    assert section.items == ["First paper.", "Second paper."]
    html = cv.render(data)
    assert "<li>First paper.</li>" in html
    assert "<li>Second paper.</li>" in html


# --- prose --------------------------------------------------------------

def test_prose_section_renders_as_a_paragraph(tmp_path):
    data = _load(tmp_path, """
[[section]]
title = "Other interests"
kind  = "prose"
items = ["Some prose about hobbies."]
""")
    section = data.sections[0]
    assert section.kind == "prose"
    html = cv.render(data)
    assert "<p>Some prose about hobbies.</p>" in html


# --- subsections --------------------------------------------------------

def test_subsections_section_has_list_and_prose_children(tmp_path):
    data = _load(tmp_path, """
[[section]]
title = "Experience"
kind  = "subsections"

  [[section.subsection]]
  title = "Programming"
  kind  = "list"
  items = ["Python", "Elm"]

  [[section.subsection]]
  title = "Testing"
  kind  = "prose"
  items = ["Coverage analysis."]
""")
    section = data.sections[0]
    assert section.kind == "subsections"
    assert [s.title for s in section.subsections] == ["Programming", "Testing"]
    assert section.subsections[0].kind == "list"
    assert section.subsections[1].kind == "prose"
    html = cv.render(data)
    assert '<h3 class="cv-sub-heading">Programming</h3>' in html
    assert "<li>Python</li>" in html
    assert '<h3 class="cv-sub-heading">Testing</h3>' in html
    assert "<p>Coverage analysis.</p>" in html


# --- markdown rendering ---------------------------------------------------

def test_markdown_in_a_detail_renders_to_a_real_link(tmp_path):
    data = _load(tmp_path, """
[[section]]
title = "Summary"
kind  = "expandable"

  [[section.item]]
  summary = "See the project."
  detail  = "Read more [here](https://example.com/project)."
""")
    html = cv.render(data)
    assert '<a href="https://example.com/project">here</a>' in html

def test_markdown_in_a_list_item_renders_to_a_real_link(tmp_path):
    data = _load(tmp_path, """
[[section]]
title = "Publications"
kind  = "list"
items = ["See [my blog](https://example.com/blog) for more."]
""")
    html = cv.render(data)
    assert '<a href="https://example.com/blog">my blog</a>' in html

def test_markdown_in_a_summary_renders_inline_without_a_p_wrapper(tmp_path):
    # A <summary> only accepts phrasing content -- render_inline must not
    # wrap it in a block-level <p>, unlike render() for a detail/prose body.
    data = _load(tmp_path, """
[[section]]
title = "Summary"
kind  = "expandable"

  [[section.item]]
  summary = "An *emphasised* summary."
  detail  = "Some detail so this item gets a <summary> at all."
""")
    html = cv.render(data)
    assert "<summary>An <em>emphasised</em> summary.</summary>" in html
