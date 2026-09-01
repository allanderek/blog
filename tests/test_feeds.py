from datetime import datetime, timedelta, timezone
from generator.content import Post
from generator.feeds import ATOM_ENTRY_LIMIT, atom, rss, sitemap, terms_rss
from generator.site import SiteContext

DANGEROUS_TITLE = """Cats & Dogs <script>alert("x")</script> it's "great\""""


def _post(slug: str, title: str = "A Post", tags: list[str] | None = None,
          date: datetime | None = None, description: str | None = None,
          body: str = "Just a *test* post.\n") -> Post:
    return Post(
        slug=slug,
        title=title,
        date=date or datetime(2024, 1, 1, tzinfo=timezone.utc),
        body=body,
        tags=tags if tags is not None else ["testing"],
        description=description,
    )


def _site() -> SiteContext:
    return SiteContext(title="Test Site", base_url="https://example.com",
                        author="Jane Doe")


def _posts(n: int) -> list[Post]:
    # Newest-first, like content.load_posts hands them to site.py.
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return [_post(f"post-{i}", date=start + timedelta(days=n - i)) for i in range(n)]


# --- rss() -------------------------------------------------------------

def test_home_title_is_bare_site_title_not_rewritten():
    # rss.xml: `{{ if eq .Title site.Title }}{{ site.Title }}{{ else }}...`.
    # check-site.sh asserts the home feed's <title> is never "X on <site>".
    site = _site()
    out = rss([], site, title=site.title)
    assert "<title>Test Site</title>" in out
    assert "<title>Test Site on Test Site</title>" not in out


def test_section_title_is_rewritten_on_site_title():
    site = _site()
    out = rss([], site, base_path="/posts/", title="Posts")
    assert "<title>Posts on Test Site</title>" in out
    assert "<description>Recent content in Posts on Test Site</description>" in out


def test_rss_item_has_no_author_tag():
    # site.Params.author is a plain string, not a map, so rss.xml's own
    # $authorEmail is always empty -- see feeds.py's docstring.
    out = rss([_post("p")], _site(), base_path="/posts/", title="Posts")
    assert "<author>" not in out


def test_rss_item_title_and_link_are_escaped():
    out = rss([_post("dangerous", title=DANGEROUS_TITLE)], _site(),
               base_path="/posts/", title="Posts")
    assert "<title>Cats &amp; Dogs" in out
    assert "<script>" not in out


def test_rss_description_falls_back_to_summary_when_no_description():
    out = rss([_post("p", body="Hello *world*.\n")], _site(),
               base_path="/posts/", title="Posts")
    assert "<description>&lt;p&gt;Hello &lt;em&gt;world&lt;/em&gt;.&lt;/p&gt;</description>" in out


def test_rss_description_uses_front_matter_description_when_set():
    out = rss([_post("p", description="A plain summary.")], _site(),
               base_path="/posts/", title="Posts")
    assert "<description>A plain summary.</description>" in out


def test_rss_description_escapes_a_front_matter_apostrophe_twice():
    # Not a typo -- see _rss_item_description's own docstring for why
    # `.Description` (a plain string) gets a second escaping pass that
    # `.Summary` (already `template.HTML`) does not.
    out = rss([_post("p", description="Elm's type parameters.")], _site(),
               base_path="/posts/", title="Posts")
    assert "<description>Elm&amp;#39;s type parameters.</description>" in out


def test_rss_item_link_local_url_within_summary_is_absolutized():
    body = "See [another post](/posts/other/) for more.\n"
    out = rss([_post("p", body=body)], _site(), base_path="/posts/", title="Posts")
    assert 'href=&#34;https://example.com/posts/other/&#34;' in out
    assert 'href=&#34;/posts/other/&#34;' not in out


def test_rss_full_set_of_posts_not_just_a_pagination_page():
    # feeds.rss never trims its own input -- the caller (site._write_section)
    # is responsible for passing the FULL section/tag post list, unlike the
    # HTML listing's own PAGER_SIZE slice.
    posts = _posts(150)
    out = rss(posts, _site(), base_path="/posts/", title="Posts")
    assert out.count("<item>") == 150


def test_last_build_date_is_the_newest_posts_own_date_not_a_clock():
    # posts[0] is the newest (start + 3 days) -- rss.xml:
    # `(index $pages.ByLastmod.Reverse 0).Lastmod`, deterministic content,
    # not `now`; confirmed against two real Hugo builds seconds apart.
    posts = _posts(3)
    out1 = rss(posts, _site(), base_path="/posts/", title="Posts")
    out2 = rss(posts, _site(), base_path="/posts/", title="Posts")
    assert out1 == out2
    assert "<lastBuildDate>Thu, 04 Jan 2024 00:00:00 +0000</lastBuildDate>" in out1


# --- atom() --------------------------------------------------------------

def test_atom_entry_count_is_capped_at_the_limit():
    posts = _posts(ATOM_ENTRY_LIMIT + 5)
    out = atom(posts, _site())
    assert out.count("<entry>") == ATOM_ENTRY_LIMIT == 20


def test_atom_feed_title_is_the_site_title_never_rewritten():
    out = atom([], _site())
    assert "<title>Test Site</title>" in out
    assert "<title>Test Site on Test Site</title>" not in out


def test_atom_author_is_the_site_author():
    out = atom([_post("p")], _site())
    assert "<name>Jane Doe</name>" in out


def test_atom_content_is_the_full_post_not_a_70_word_summary():
    long_body = "Paragraph one.\n\n" + " ".join(f"word{i}" for i in range(100)) + "\n"
    out = atom([_post("p", body=long_body)], _site())
    assert "word99" in out


def test_atom_content_local_links_are_left_relative():
    # Unlike RSS's <description>, Atom's <content> is NOT absolutized --
    # confirmed against real Hugo output; see _atom_entry's docstring.
    body = "See [another post](/posts/other/) for more.\n"
    out = atom([_post("p", body=body)], _site())
    assert 'href=&#34;/posts/other/&#34;' in out
    assert 'href=&#34;https://example.com/posts/other/&#34;' not in out


def test_atom_categories_use_raw_front_matter_tag_spelling():
    out = atom([_post("p", tags=["Elm", "programming"])], _site())
    assert '<category term="Elm"/>' in out
    assert '<category term="programming"/>' in out


def test_atom_entry_with_no_tags_has_no_category_element():
    out = atom([_post("p", tags=[])], _site())
    assert "<category" not in out


def test_atom_published_and_updated_match_the_posts_own_date():
    when = datetime(2023, 6, 15, 9, 30, 0, tzinfo=timezone.utc)
    out = atom([_post("p", date=when)], _site())
    assert "<published>2023-06-15T09:30:00+00:00</published>" in out
    assert "<updated>2023-06-15T09:30:00+00:00</updated>" in out


def test_atom_entry_category_block_has_hugos_exact_whitespace_padding():
    # A real bug, not paranoia: the first attempt at this only emitted ONE
    # of the two whitespace-only lines Hugo's own output has before the
    # first <category>, and neither the zero-tag nor the single-tag test
    # above caught it -- only a byte-exact real-corpus diff did. Two tags
    # is the minimum that exercises "two before the first, one between,
    # two after".
    out = atom([_post("p", tags=["Elm", "programming"])], _site())
    expected_tail = (
        '    <content type="html">'
        + out.split('<content type="html">', 1)[1].split("</content>", 1)[0]
        + "</content>\n"
        '    \n'
        '    \n'
        '    <category term="Elm"/>\n'
        '    \n'
        '    <category term="programming"/>\n'
        '    \n'
        '    \n'
        '  </entry>'
    )
    assert expected_tail in out


def test_rss_include_site_pages_adds_cv_and_consulting_cv_first():
    # cv.md's real weight: 10 puts it before every (weight-0) post
    # regardless of date; consulting.md's real zero .Date puts it dead
    # last among the weight-0 group. Reads the real content/cv.md and
    # content/consulting.md front matter (no fixture to swap in without
    # threading a content root through feeds.py -- see _load_root_extras).
    posts = _posts(2)
    out = rss(posts, _site(), title=_site().title, include_site_pages=True)
    assert out.count("<item>") == len(posts) + 2
    links = [line.strip().removeprefix("<link>").removesuffix("</link>")
             for line in out.splitlines() if line.strip().startswith("<link>")][1:]  # [0] is the channel's own
    assert links[0] == "https://example.com/cv/"
    assert links[-1] == "https://example.com/consulting/"
    assert links[1:-1] == [f"https://example.com/posts/{p.slug}/" for p in posts]


def test_rss_without_include_site_pages_is_posts_only():
    posts = _posts(2)
    out = rss(posts, _site(), title=_site().title)
    assert out.count("<item>") == len(posts)
    assert "/cv/" not in out
    assert "/consulting/" not in out


# --- terms_rss() -----------------------------------------------------------

def test_terms_rss_items_are_terms_not_posts():
    tags = [("Elm", "elm", [_post("p1", tags=["Elm"])])]
    out = terms_rss(tags, _site(), "/tags/", "Tags")
    assert "<title>Elm</title>" in out
    assert "<link>https://example.com/tags/elm/</link>" in out
    assert "<description></description>" in out


def test_terms_rss_empty_has_no_items_and_no_last_build_date():
    # The real /categories/index.xml: an unused taxonomy, no terms.
    out = terms_rss([], _site(), "/categories/", "Categories")
    assert "<item>" not in out
    assert "<lastBuildDate>" not in out
    assert "<title>Categories on Test Site</title>" in out


def test_terms_rss_orders_by_newest_post_then_linktitle_case_insensitively():
    newer = datetime(2024, 6, 1, tzinfo=timezone.utc)
    older = datetime(2024, 1, 1, tzinfo=timezone.utc)
    tags = [
        ("zzz", "zzz", [_post("p1", date=older)]),
        ("Aaa", "aaa", [_post("p2", date=newer)]),
    ]
    out = terms_rss(tags, _site(), "/tags/", "Tags")
    assert out.index("Aaa") < out.index("zzz")


# --- sitemap() ---------------------------------------------------------

def test_sitemap_lists_every_post_and_omits_lastmod_for_dateless_pages():
    posts = _posts(3)
    out = sitemap(posts, [], _site())
    for post in posts:
        assert f"<loc>https://example.com/posts/{post.slug}/</loc>" in out
    assert "<loc>https://example.com/</loc>" in out
    assert "<loc>https://example.com/posts/</loc>" in out
    assert "<loc>https://example.com/archives/</loc>" in out
    assert "<loc>https://example.com/consulting/</loc>" in out
    assert "<loc>https://example.com/cv/</loc>" in out
    # cv.md/consulting.md/archives.md/categories all carry no date in the
    # real corpus this reads front matter from -- none should get a
    # <lastmod> line of its own: one dated entry per post, plus home,
    # /posts/, and /tags/ (all sharing the newest post's own date).
    assert out.count("<lastmod>") == len(posts) + 3
