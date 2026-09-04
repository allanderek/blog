"""Pins the two responsibilities of `_write_section` that no user-facing
check (check-site.sh) would ever notice going wrong: the pagerSize page-
count math, and that the `page/1/` alias stub always exists -- even for a
single-page listing, matching Hugo's `disableAliases = false`. See
`tests/test_pages.py` for `list_page`/`alias_stub` themselves, which are
pure and don't need a filesystem."""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from generator.content import Post
from generator.site import PAGER_SIZE, SiteContext, _write_section

def _posts(n: int) -> list[Post]:
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return [
        Post(slug=f"post-{i}", title=f"Post {i}", date=base + timedelta(days=i), body="Body.\n")
        for i in range(n)
    ]

def _site() -> SiteContext:
    return SiteContext(title="Test Site", base_url="https://example.com")

@pytest.mark.parametrize("count, expected_pages", [
    (1, 1),
    (PAGER_SIZE, 1),           # exactly one page's worth: no second page
    (PAGER_SIZE + 1, 2),       # one over: forces a second page
    (2 * PAGER_SIZE + 1, 3),   # one over two pages: forces a third
])
def test_page_count_is_the_pager_size_ceiling(tmp_path: Path, count, expected_pages):
    _write_section(tmp_path, "/posts/", _posts(count), _site())
    assert (tmp_path / "posts" / "index.html").exists()
    for n in range(2, expected_pages + 1):
        assert (tmp_path / "posts" / "page" / str(n) / "index.html").exists(), \
            f"expected page {n} for {count} posts ({expected_pages} pages)"
    one_past = tmp_path / "posts" / "page" / str(expected_pages + 1)
    assert not one_past.exists(), f"unexpected page {expected_pages + 1} for {count} posts"

def test_write_section_paginates_a_tag_listing_too(tmp_path: Path):
    # A tag can need a second page just like /posts/ does -- "programming"
    # alone has 106 posts in the real corpus, one over PAGER_SIZE.
    _write_section(tmp_path, "/tags/elm/", _posts(PAGER_SIZE + 1), _site(),
                    title="Elm", taxonomy=True)
    assert (tmp_path / "tags" / "elm" / "index.html").exists()
    assert (tmp_path / "tags" / "elm" / "page" / "2" / "index.html").exists()
    assert (tmp_path / "tags" / "elm" / "page" / "1" / "index.html").exists()
    page1 = (tmp_path / "tags" / "elm" / "index.html").read_text()
    assert 'class="post-entry tag-entry"' in page1
    assert "application/ld+json" in page1

def test_page_1_alias_stub_is_written_even_for_a_single_page_listing(tmp_path: Path):
    # Nothing in check-site.sh asserts this stub exists; only compare.py
    # against Hugo's own `disableAliases = false` output catches it if a
    # future change starts skipping it for a listing with just one page.
    _write_section(tmp_path, "/posts/", _posts(1), _site())
    stub = tmp_path / "posts" / "page" / "1" / "index.html"
    assert stub.exists()
    text = stub.read_text()
    assert "https://example.com/posts/" in text
    assert 'meta http-equiv="refresh"' in text
    # And it must not be confused with a real second page: a 1-post
    # listing has none.
    assert not (tmp_path / "posts" / "page" / "2").exists()
