from datetime import datetime, timezone
from pathlib import Path
from generator.content import Post, load_page
from generator.pages import (alias_stub, archives_page, categories_index,
                              consulting_page, cv_page, group_posts_by_tag,
                              list_page, not_found_page, post_page,
                              strip_style_comments, tag_title, term_page,
                              terms_index)
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

def test_tag_title_capitalises_after_space_and_hyphen_but_leaves_rest():
    assert tag_title("SQLite") == "SQLite"
    assert tag_title("LLMs") == "LLMs"
    assert tag_title("language-design") == "Language-Design"
    assert tag_title("dead code") == "Dead Code"

def test_term_page_title_uses_real_spelling_and_marks_entries_tag_entry():
    # A tag's own term page auto-titles itself via `tag_title`'s
    # capitalise-after-boundary rule applied to the real front-matter
    # spelling ("SQLite" survives unchanged) -- never derived from the
    # lowercased URL slug (the same trap `list_page`'s own title param
    # guards against). Every entry also gets list.html's extra
    # "tag-entry" class, which a section listing (e.g. /posts/) never
    # does.
    page = term_page("SQLite", [_post()], 1, 1, _site())
    assert "\n    SQLite\n" in page
    assert 'class="post-entry tag-entry"' in page
    assert "https://example.com/tags/sqlite/" in page

def test_term_page_title_capitalises_after_hyphen_not_derived_from_slug():
    page = term_page("language-design", [], 1, 1, _site())
    assert "\n    Language-Design\n" in page
    assert "https://example.com/tags/language-design/" in page

def test_term_page_has_no_json_ld():
    # Kind "term" satisfies neither schema_json.html's `.IsPage` nor
    # `.IsSection` guard -- confirmed zero `application/ld+json` scripts
    # on Hugo's own /tags/<tag>/index.html.
    page = term_page("Elm", [], 1, 1, _site())
    assert "application/ld+json" not in page

def test_term_page_description_is_site_wide_not_title_suffixed():
    # Unlike a section (e.g. /posts/, whose description is "Posts -
    # site.Title"), a term page's description falls straight through to
    # the site-wide description -- see `_head_taxonomy`.
    page = term_page("Elm", [], 1, 1, _site())
    assert "Elm - Test Site" not in page

def test_terms_index_shows_raw_spelling_verbatim():
    # /tags/ lists each tag's RAW front-matter spelling (terms.html's own
    # `.Name`) -- unlike that same tag's own term page, which auto-titles
    # itself via `tag_title`'s capitalise-after-boundary rule. Confirmed
    # against real Hugo output: /tags/index.html shows "language-design"
    # all lowercase for the very same tag whose own
    # /tags/language-design/ page titles itself "Language-Design".
    tags = [("language-design", "language-design", [_post()])]
    page = terms_index(tags, _site())
    assert ">language-design <sup>" in page
    assert "Language-Design" not in page

def test_terms_index_has_no_json_ld():
    page = terms_index([], _site())
    assert "application/ld+json" not in page

def test_group_posts_by_tag_sorts_by_slug_and_preserves_newest_first_order():
    newer = Post(slug="newer", title="Newer", tags=["Elm", "SQLite"],
                 date=datetime(2024, 2, 1, tzinfo=timezone.utc), body="Body.\n")
    older = Post(slug="older", title="Older", tags=["Elm"],
                 date=datetime(2024, 1, 1, tzinfo=timezone.utc), body="Body.\n")
    grouped = group_posts_by_tag([newer, older])  # already newest-first
    slugs = [slug for _, slug, _ in grouped]
    assert slugs == sorted(slugs)
    elm_posts = next(posts for name, slug, posts in grouped if slug == "elm")
    assert elm_posts == [newer, older]

def test_archives_page_groups_newest_year_first_with_typographic_title():
    newer = Post(slug="a", title="Link: python's constants",
                 date=datetime(2024, 3, 5, tzinfo=timezone.utc), body="Body.\n")
    older = Post(slug="b", title="Older post", date=datetime(2023, 12, 1, tzinfo=timezone.utc), body="Body.\n")
    page = archives_page([newer, older], _site())
    assert page.index('id="2024"') < page.index('id="2023"')
    # archives.html's `.Title | markdownify` renders the typographer's
    # substitution as a literal entity ("&rsquo;"), unlike every other
    # listing's plain `html.esc(post.title)` ("&#39;") -- see
    # `_render_inline_markdown_entities`.
    assert "python&rsquo;s constants" in page
    assert 'aria-label="post link to Link: python&#39;s constants"' in page

def test_archives_page_has_breadcrumb_and_blog_posting_json_ld():
    # Unlike a term/taxonomy list, content/archives.md is a genuine Kind
    # "page" and gets the full pair, built from its own front matter
    # (title "Archive", summary "archives", no date) rather than a Post.
    page = archives_page([], _site())
    assert page.count("application/ld+json") == 2
    assert '"@type": "BreadcrumbList"' in page
    assert '"@type": "BlogPosting"' in page
    assert '"datePublished": "0001-01-01T00:00:00Z"' in page

def test_archives_page_marks_its_own_nav_entry_active():
    # header.html: `<span {{- if eq $menu_item_url $page_url }}
    # class="active" {{- end }}>` -- /archives/ is the only page kind
    # this generator builds whose own permalink coincides with a menu URL.
    page = archives_page([], _site())
    assert '<span class="active">Archive</span>' in page
    assert "<span>Consulting</span>" in page

def test_other_page_kinds_have_no_active_nav_entry():
    assert 'class="active"' not in post_page(_post(), _site())
    assert 'class="active"' not in term_page("Elm", [], 1, 1, _site())


# --- strip_style_comments ---------------------------------------------------
#
# Reproduces one, narrow Hugo behaviour found while building the CV page:
# every CSS comment inside a <style>...</style> block becomes a single
# space in Hugo's own rendered .Content -- confirmed against a real build
# (see pages.py's own docstring for that function). These pin down the
# regex's actual, deliberately narrow behaviour at its edges, since a CSS
# comment stripper is easy to get subtly wrong.

def test_strip_style_comments_removes_a_comment_that_looks_like_a_css_rule():
    # The comment's own text could itself be mistaken for a real
    # declaration by a careless implementation (e.g. one that just looked
    # for "{...}" pairs) -- it must vanish as a unit, and the real rules
    # either side must survive untouched.
    html = '<style>a{color:red}/* .b{color:blue} */c{color:green}</style>'
    result = strip_style_comments(html)
    assert ".b" not in result
    assert "color:blue" not in result
    # Replaced with exactly one space -- never simply deleted (deleting
    # instead of spacing risks joining the tokens either side into one).
    assert result == '<style>a{color:red} c{color:green}</style>'

def test_strip_style_comments_leaves_an_unterminated_comment_untouched():
    # No closing "*/" anywhere in the block, so nothing here looks like a
    # complete comment to the regex -- the literal "/*" and everything
    # after it survive untouched, same as any other <style> byte that
    # isn't part of a real, closed comment.
    html = '<style>a { color: red; } /* never closes c { color: green; }</style>'
    assert strip_style_comments(html) == html

def test_strip_style_comments_is_not_css_string_aware():
    # A known, narrow limitation, pinned down rather than left implicit: a
    # "/* ... */"-shaped run INSIDE a CSS string literal still reads as a
    # real comment to this transform, since it has no notion of CSS
    # string context -- this matches the one, specific behaviour observed
    # in a real Hugo build, not a general-purpose CSS parser.
    html = '<style>content: "/* not a comment */"; color: red;</style>'
    assert strip_style_comments(html) == '<style>content: " "; color: red;</style>'

def test_strip_style_comments_only_touches_style_blocks():
    html = '<p>Some prose with /* not css */ in it.</p>'
    assert strip_style_comments(html) == html

# --- cv_page / consulting_page / not_found_page / categories_index --------

def _cv_front_matter() -> dict:
    return {"title": "", "linktitle": "CV", "menu": "main",
            "hidePageTitle": True, "weight": 10}

def test_cv_page_inserts_the_shortcode_verbatim():
    # The CV is an opaque artifact authored outside this repo -- it must
    # land in the page unescaped and unreformatted. A raw double-quoted
    # attribute survives verbatim only if nothing along the way ran it
    # through html.esc() (which would turn '"' into "&#34;" and '<a'
    # into "&lt;a").
    cv_html = Path("content/cv.html").read_text()
    page = cv_page(_site(), _cv_front_matter(), cv_html)
    assert '<a href="https://github.com/allanderek" class="profile-link">GitHub</a>' in page

def test_cv_page_has_a_signature_block():
    cv_html = Path("content/cv.html").read_text()
    page = cv_page(_site(), _cv_front_matter(), cv_html)
    assert '<aside class="signature"' in page

def test_consulting_page_renders_its_markdown_body():
    front_matter, body = load_page(Path("content/consulting.md"))
    page = consulting_page(_site(), front_matter, body)
    assert "Elm" in page
    assert "<h1" in page and "Consulting" in page

def test_consulting_page_has_no_signature_block():
    # Unlike every other page kind this generator builds -- the signature
    # itself links to /consulting/, so the consulting page doesn't also
    # point back at itself. check-site.sh asserts the same thing against
    # a real Hugo build ("no signature on consulting").
    front_matter, body = load_page(Path("content/consulting.md"))
    page = consulting_page(_site(), front_matter, body)
    assert '<aside class="signature' not in page

def test_not_found_page_renders_the_404_marker():
    page = not_found_page(_site())
    assert '<div class="not-found">404</div>' in page
    assert "<title>404 Page not found" in page

def test_categories_index_has_no_terms():
    # The `categories` taxonomy is unused site-wide -- no post ever sets
    # `categories:` -- so Hugo still emits this page, just with a bare
    # <ul> and no <li> entries at all.
    page = categories_index(_site())
    assert "<h1>Categories</h1>" in page
    terms_list = page[page.index('<ul class="terms-tags">'):page.index("</ul>")]
    assert "<li>" not in terms_list

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
