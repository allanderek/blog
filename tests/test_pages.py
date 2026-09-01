from datetime import datetime, timezone
from generator.content import Post
from generator.pages import alias_stub, list_page, post_page
from generator.site import SiteContext

# A title an author could plausibly type, deliberately containing every
# character html.esc() must neutralise: & ' " < >. If any interpolation
# site in pages.py forgot to escape, this either breaks the page (a bare
# "<script>" or unbalanced quote) or, worse, is a real XSS hole -- the
# title comes from author-written front matter, but so would a compromised
# dependency's injected content, or a future feature that pulls titles
# from somewhere less trusted.
DANGEROUS_TITLE = """Cats & Dogs <script>alert("x")</script> it's "great\""""

# Go's html/template table (& ' " + < > -> entities), which html.esc()
# deliberately matches -- see html.py's module docstring for why.
_ESCAPED_TITLE = (
    'Cats &amp; Dogs &lt;script&gt;alert(&#34;x&#34;)&lt;/script&gt; '
    "it&#39;s &#34;great&#34;"
)

def _post(title: str = DANGEROUS_TITLE) -> Post:
    return Post(
        slug="dangerous-title",
        title=title,
        date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        body="Just a *test* post.\n",
        tags=["testing"],
    )

def _site() -> SiteContext:
    return SiteContext(title="Test Site", base_url="https://example.com")

def test_no_raw_tag_or_unescaped_special_chars_anywhere():
    # The blunt, whole-page check: the dangerous title's own "<script>"
    # must not survive as a real tag anywhere in the page. (The page
    # legitimately contains its own seven *literal* <script> tags --
    # matching on the title's specific payload, not the bare string
    # "<script>", is what keeps this test honest.)
    page = post_page(_post(), _site())
    assert "<script>alert" not in page
    assert 'alert("x")' not in page

def test_title_is_escaped_in_a_text_position():
    # <title>...</title> and the <h1> are HTML TEXT positions -- a raw "<"
    # there would be parsed as a new tag, not literal text.
    page = post_page(_post(), _site())
    title_tag = page[page.index("<title>"):page.index("</title>")]
    assert _ESCAPED_TITLE in title_tag

    h1_start = page.index('class="post-title')
    h1 = page[h1_start:h1_start + 300]
    assert _ESCAPED_TITLE in h1

def test_title_is_escaped_in_an_attribute_position():
    # og:title's content="..." is an HTML ATTRIBUTE position -- a raw
    # unescaped quote there would terminate the attribute early.
    page = post_page(_post(), _site())
    idx = page.index('property="og:title"')
    attr_area = page[idx:idx + 250]
    assert f'content="{_ESCAPED_TITLE}"' in attr_area

def test_tag_names_are_escaped_too():
    # Tags flow into keywords, article:tag, and the post-footer <li> the
    # same uncontrolled way titles do.
    post = _post()
    post.tags = ['<b>bold</b> & "quoted"']
    page = post_page(post, _site())
    assert "<b>bold</b>" not in page
    assert "&lt;b&gt;bold&lt;/b&gt;" in page

def test_pagination_nav_at_both_ends_of_a_three_page_set():
    # Page 1 of N: next only. A middle page: both. The last page: prev
    # only. Real bug risk is an off-by-one at either boundary.
    site = _site()
    posts = [_post()]
    p1 = list_page(posts, 1, 3, "/posts/", site)
    p2 = list_page(posts, 2, 3, "/posts/", site)
    p3 = list_page(posts, 3, 3, "/posts/", site)

    assert '<a class="prev"' not in p1
    assert '<a class="next" href="https://example.com/posts/page/2/">' in p1

    assert '<a class="prev" href="https://example.com/posts/">' in p2
    assert '<a class="next" href="https://example.com/posts/page/3/">' in p2

    assert '<a class="prev" href="https://example.com/posts/page/2/">' in p3
    assert '<a class="next"' not in p3

def test_single_page_listing_has_no_pagination_nav_at_all():
    # gt $paginator.TotalPages 1 guards the whole <footer class="page-footer">
    # element in list.html, not just the individual prev/next links.
    page = list_page([_post()], 1, 1, "/posts/", _site())
    assert "page-footer" not in page

def test_list_page_title_override_survives_untouched():
    # A tag's real front-matter spelling ("SQLite", "LLMs", ...) is
    # unrecoverable from its lowercased URL slug by any capitalisation
    # rule -- an explicit `title` must come through verbatim, not get
    # re-derived (and mangled) from base_path.
    page = list_page([], 1, 1, "/tags/sqlite/", _site(), title="SQLite")
    assert "\n    SQLite\n" in page
    assert "Sqlite" not in page

def test_list_page_title_default_capitalises_after_hyphens_not_just_first_letter():
    # The fallback derivation (no explicit title) must match _tag_title's
    # word-boundary rule, not Python's str.capitalize() (which lowercases
    # everything after the first letter, turning a hyphenated name like
    # "language-design" into "Language-design" instead of "Language-Design").
    page = list_page([], 1, 1, "/language-design/", _site())
    assert "\n    Language-Design\n" in page

def test_alias_stub_matches_hugos_pagination_alias_format():
    # Byte-exact against /tmp/t8-hugo/posts/page/1/index.html (base_url
    # substituted for the real site's).
    stub = alias_stub("/posts/", _site())
    assert stub == (
        '<!DOCTYPE html>\n'
        '<html lang="en-us">\n'
        '\t<head>\n'
        '\t\t<title>https://example.com/posts/</title>\n'
        '\t\t<link rel="canonical" href="https://example.com/posts/">\n'
        '\t\t<meta charset="utf-8">\n'
        '\t\t<meta http-equiv="refresh" content="0; url=https://example.com/posts/">\n'
        '\t</head>\n'
        '</html>\n'
    )
