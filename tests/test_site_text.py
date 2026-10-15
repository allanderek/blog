"""Build-wide invariants for the `.txt` versions of every page.

These run against a real full build, which is where a renderer
regression would actually show up -- but they assert only RELATIONSHIPS
(every page has a text file; no text file contains markup), never a post
count or a sentence from a post. A test that pins either of those turns
an ordinary edit into a CI failure.

`tests/test_text.py` covers the renderer itself, from synthetic html.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from generator import site, text

BASE = site.DEFAULT_BASE_URL

# A code block's lines are the one place markup and entities may appear
# legitimately: twelve posts in this corpus show html inside a fenced
# code block, so their text versions really do contain `<div ...>`.
# Those lines are identified by the Monokai background the renderer
# paints behind them.
CODE_LINE = "\x1b[48;2;"

# Inline code is the OTHER place angle brackets are legitimate prose --
# `<usize>`, `<expr>`, `<VirtualHost *:80>` are all real inline code in
# real posts -- and it is only cyan, with no background to spot it by.
# So it is cut out by its own escape sequences before anything looks for
# markup.
INLINE_CODE_RE = re.compile("\x1b\\[36m.*?\x1b\\[39m", re.DOTALL)

# Only a tag the renderer actually HANDLES counts as a leak. Angle
# brackets alone do not: `let <def-list> in <expr>` is plain prose in
# one post, and `<usize>`, `<i32>`, `<VirtualHost *:80>` are real inline
# code in others. What a leak looks like is `<p>` or `<span style=...>`
# -- an element from the renderer's own tables, which is why the pattern
# is built from them and so covers any element added later.
LEAKED_TAG_RE = re.compile(
    r"</?(?:" + "|".join(sorted(t for t in text._KNOWN if not t.startswith("#")))
    + r")(?:\s[^<>]*)?/?>", re.IGNORECASE)
ENTITY_RE = re.compile(
    r"&(?:amp|lt|gt|quot|apos|nbsp|rsquo|lsquo|ldquo|rdquo|mdash|ndash"
    r"|hellip|#\d+);")


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("site")
    site.build(out)
    return out


def prose_lines(path: Path) -> list[str]:
    """`path`'s lines with every code region removed: whole lines for a
    fenced block, and the cyan runs for inline code."""
    body = INLINE_CODE_RE.sub("", path.read_text(encoding="utf-8"))
    return [line for line in body.split("\n") if CODE_LINE not in line]


def test_every_page_has_a_text_version_and_every_stub_has_none(built: Path):
    """The relationship, not a count: a text file exists for exactly
    those pages that have content."""
    missing, unexpected = [], []
    for page in built.rglob("index.html"):
        text_file = page.with_name("index.txt")
        is_stub = page.parent.parent.name == "page" and page.parent.name == "1"
        if is_stub and text_file.exists():
            unexpected.append(page.relative_to(built))
        if not is_stub and not text_file.exists():
            missing.append(page.relative_to(built))
    assert not missing, f"pages with no text version: {missing[:5]}"
    assert not unexpected, f"alias stubs given a text version: {unexpected[:5]}"


def test_there_is_a_text_version_of_more_than_one_kind_of_page(built: Path):
    """Guards the fixture itself: were the build to stop writing text
    files, every other test here would pass vacuously."""
    for page in ("index.txt", "posts/index.txt", "archives/index.txt",
                 "tags/index.txt", "cv/index.txt", "consulting/index.txt"):
        assert (built / page).exists(), f"no text version of /{page}"


def test_404_has_no_text_version(built: Path):
    assert (built / "404.html").exists()
    assert not (built / "404.txt").exists()


def test_no_text_file_leaks_markup(built: Path):
    """Outside a code block, a tag in the output means the renderer let
    html through."""
    offenders = []
    for path in built.rglob("index.txt"):
        for line in prose_lines(path):
            found = LEAKED_TAG_RE.search(line)
            if found:
                offenders.append((path.relative_to(built), found.group(0)))
                break
    assert not offenders, f"markup in text output: {offenders[:5]}"


def test_no_text_file_leaks_an_html_entity(built: Path):
    offenders = []
    for path in built.rglob("index.txt"):
        for line in prose_lines(path):
            found = ENTITY_RE.search(line)
            if found:
                offenders.append((path.relative_to(built), found.group(0)))
                break
    assert not offenders, f"undecoded entities in text output: {offenders[:5]}"


def test_code_blocks_are_syntax_highlighted_in_the_text_version(built: Path):
    """The whole corpus's code blocks come from highlight.py's inline
    hex, so if the translation broke, no text file would carry a
    truecolour sequence."""
    coloured = [path for path in built.rglob("index.txt")
                if "\x1b[38;2;" in path.read_text(encoding="utf-8")]
    assert coloured, "no text file contains a truecolour sequence"


def test_every_footnote_url_is_absolute(built: Path):
    """OSC 8 cannot resolve a relative url -- a terminal has no document
    base -- and a relative path cannot be pasted into a shell either."""
    numbered = re.compile(r"\[\d+\] (\S+)")
    scheme = re.compile(r"[a-z][a-z0-9+.-]*:")
    offenders = []
    for path in built.rglob("index.txt"):
        for line in prose_lines(path):
            found = numbered.match(text.visible(line).strip())
            if found and not scheme.match(found.group(1)):
                offenders.append((path.relative_to(built), found.group(1)))
    assert offenders == [], f"relative footnote urls: {offenders[:5]}"


def test_every_text_file_points_back_at_its_own_html_page(built: Path):
    """The reciprocal half of the pointer, and the one that can be
    checked mechanically: follow it and you must land on the page the
    text was rendered from."""
    for path in built.rglob("index.txt"):
        body = text.visible(path.read_text(encoding="utf-8"))
        found = re.search(r"Full HTML version: (\S+)", body)
        assert found, f"{path.relative_to(built)} has no back-pointer"
        url = found.group(1)
        assert url.startswith(BASE), f"{url} is not an absolute site url"
        target = built / url[len(BASE):].strip("/") / "index.html"
        assert target.exists(), \
            f"{path.relative_to(built)} points at {url}, which is not a page"
        assert target == path.with_name("index.html"), \
            f"{path.relative_to(built)} points at another page: {url}"


def test_every_page_offers_its_own_text_version(built: Path):
    """The html half of the pair. `page/N/` listings are the trap here:
    they canonicalise to their section, so a pointer built from the
    permalink would advertise page 1's text file."""
    for page in built.rglob("index.html"):
        if page.parent.parent.name == "page" and page.parent.name == "1":
            continue
        html = page.read_text(encoding="utf-8")
        found = re.search(r"curl (\S+index\.txt)</code>", html)
        assert found, f"{page.relative_to(built)} does not offer a text version"
        url = found.group(1)
        expected = page.with_name("index.txt").relative_to(built).as_posix()
        assert url == f"{BASE}/{expected}", \
            f"{page.relative_to(built)} offers {url}, not {expected}"


def test_the_404_page_offers_no_text_version(built: Path):
    """It has none to offer: GitHub Pages serves it for any unknown
    path, including a missing `.txt`."""
    assert "index.txt" not in (built / "404.html").read_text(encoding="utf-8")
