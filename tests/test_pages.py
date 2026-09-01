from datetime import datetime, timezone
from generator.content import Post
from generator.pages import post_page
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
