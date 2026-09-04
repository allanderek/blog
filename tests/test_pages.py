from datetime import datetime, timezone
from pathlib import Path
from generator import cv
from generator.content import Post, load_page
from generator.pages import (alias_stub, archives_page, categories_index,
                              consulting_page, cv_page, group_posts_by_tag,
                              home_page, list_page, not_found_page, post_page,
                              tag_title, term_page, terms_index)
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

# docs/hugo-quirks.md quirk 7. Hugo labelled the same instant two ways --
# "+0000 UTC" for a bare or "Z" date, "+0000 +0000" for an explicit
# "+00:00" one -- because Go prints a named and an unnamed time.Location
# differently. One label now, whatever the front matter said.
def test_post_meta_date_tooltip_always_says_utc():
    for raw in ("2024-01-01", "2024-01-01T09:00:00Z", "2024-01-01T09:00:00+00:00"):
        page = post_page(_post_dated(raw), _site())
        assert "+0000 UTC'" in page, raw
        assert "+0000 +0000" not in page, raw

def _post_dated(raw: str) -> Post:
    import tempfile, pathlib as _pl
    from generator.content import parse_post
    d = _pl.Path(tempfile.mkdtemp())
    f = d / "p.md"
    f.write_text(f'---\ntitle: "T"\ndate: {raw}\ntags: [x]\n---\n\nBody\n')
    return parse_post(f)

# docs/hugo-quirks.md quirk 2. Hugo escaped JSON-LD fields at two
# different strengths depending on whether its template source happened to
# wrap the placeholder in literal quotes, so the same title came out as
# "python's" in one field and "python\u0027s" in another.
def test_jsonld_escapes_every_field_the_same_way():
    import json, re
    page = post_page(_post(title="Link: python's / Go's \"quoting\""), _site())
    block = [b for b in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
        if '"@type": "BlogPosting"' in b][0]
    doc = json.loads(block)
    assert doc["headline"] == doc["name"]
    assert "\\u0027" not in block and "\\/" not in block

# The JSON-LD sits inside a <script> element, which the HTML parser scans
# for "</script" before any JSON parser sees it. quirk 1's fix puts literal
# "<" into real posts' articleBody, so this escaping is load-bearing.
#
# The assertion is that each block still PARSES. Asserting "no raw '<'"
# would not work: the extracting regex stops at the first "</script>", so a
# block that really did break out comes back truncated, and a truncated
# block contains no angle bracket to find. Truncation instead shows up as
# invalid JSON, which is the thing a browser would choke on too.
def test_jsonld_survives_a_script_tag_in_the_content():
    import json, re
    post = _post(title="Closing </script> in a title")
    post.body = "Code:\n\n```\n</script> and <all files>\n```\n"
    page = post_page(post, _site())
    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
    assert len(blocks) == 2          # BreadcrumbList + BlogPosting
    for block in blocks:
        json.loads(block)            # raises if the element closed early

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

    # Pagination nav is same-origin navigation, so root-relative -- see
    # test_pagination_nav_links_are_root_relative below.
    assert '<a class="prev"' not in p1
    assert '<a class="next" href="/posts/page/2/">' in p1

    assert '<a class="prev" href="/posts/">' in p2
    assert '<a class="next" href="/posts/page/3/">' in p2

    assert '<a class="prev" href="/posts/page/2/">' in p3
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

# docs/hugo-quirks.md quirk 13. Hugo emitted no JSON-LD at all on term and
# taxonomy pages -- its schema_json.html guard is `(or .IsPage .IsSection)`,
# and neither Kind satisfies it. A section listing got a BreadcrumbList, so
# this was an oversight rather than a decision.
def _breadcrumbs(page: str) -> list[tuple[int, str, str]]:
    import json, re
    out = []
    for b in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', page, re.S):
        doc = json.loads(b)
        if doc.get("@type") == "BreadcrumbList":
            out += [(i["position"], i["name"], i["item"])
                    for i in doc["itemListElement"]]
    return out

def test_term_page_has_a_two_step_breadcrumb():
    trail = _breadcrumbs(term_page("Elm", [_post()], 1, 1, _site()))
    assert trail == [(1, "Tags", "https://example.com/tags/"),
                     (2, "Elm", "https://example.com/tags/elm/")]

def test_terms_index_is_a_direct_child_of_home():
    assert _breadcrumbs(terms_index({"elm": 1}, _site())) == [
        (1, "Tags", "https://example.com/tags/")]

# /categories/ comes through the same code path. Deriving the root label
# from the page's own base_path rather than assuming "tags" is what stops
# this reading "Tags -> Categories".
def test_categories_index_is_not_labelled_tags():
    assert _breadcrumbs(categories_index(_site())) == [
        (1, "Categories", "https://example.com/categories/")]

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

def test_term_page_has_exactly_one_json_ld_block():
    # A BreadcrumbList and nothing else: a term listing is not an article,
    # so it gets no BlogPosting the way a real page does.
    page = term_page("Elm", [], 1, 1, _site())
    assert page.count("application/ld+json") == 1
    assert "BlogPosting" not in page

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

def test_terms_index_has_exactly_one_json_ld_block():
    page = terms_index([], _site())
    assert page.count("application/ld+json") == 1
    assert "BlogPosting" not in page

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


# --- same-origin links are root-relative, off-origin metadata stays absolute
#
# The nav bar used to point at site.base_url even when the dev server is
# browsed under a different origin (see docs/hugo-quirks.md's "Deliberate
# deviations" entry) -- Hugo/PaperMod's absLangURL exists for multilingual
# sites injecting a language prefix, which this single-language site never
# needs. Same-origin navigation/assets are now root-relative; anything
# consumed off-origin (canonical, og:url, hreflang, JSON-LD) still needs the
# real absolute URL and must keep it.

def test_nav_favicon_and_footer_links_are_root_relative():
    page = post_page(_post(), _site())
    assert 'href="/archives/"' in page
    assert 'href="/consulting/"' in page
    assert 'href="/cv/"' in page
    assert 'href="/rss/index.xml"' in page
    assert 'href="/"' in page  # logo and footer copyright link
    assert 'href="/favicons/favicon.ico"' in page
    assert 'href="/favicons/site.webmanifest"' in page

def test_post_tag_links_are_root_relative():
    post = _post()
    post.tags = ["testing"]
    page = post_page(post, _site())
    assert '<li><a href="/tags/testing/">Testing</a></li>' in page

def test_active_nav_entry_still_matches_after_href_became_relative():
    # The regression this guards against: making the href relative while
    # leaving the "active" comparison mismatched (one side absolute, one
    # relative) would silently drop this highlight -- see _header's own
    # docstring/comment for why the comparison still needs both sides
    # absolute even though the href itself doesn't.
    page = archives_page([], _site())
    assert '<span class="active">Archive</span>' in page

def test_list_entry_and_pagination_links_are_root_relative():
    site = _site()
    posts = [_post()]
    page = list_page(posts, 2, 3, "/posts/", site)
    assert 'aria-label="post link to' in page
    idx = page.index('aria-label="post link to')
    assert 'href="/posts/dangerous-title/"' in page[idx:idx + 200]
    assert '<a class="prev" href="/posts/">' in page
    assert '<a class="next" href="/posts/page/3/">' in page

def test_terms_index_entry_links_are_root_relative():
    tags = group_posts_by_tag([_post()])
    page = terms_index(tags, _site())
    assert 'href="/tags/testing/"' in page

def test_archive_entry_links_are_root_relative():
    page = archives_page([_post()], _site())
    assert 'aria-label="post link to' in page
    idx = page.index('aria-label="post link to')
    assert 'href="/posts/dangerous-title/"' in page[idx:idx + 200]

def test_home_page_nav_favicon_and_listing_links_are_root_relative():
    site = _site()
    site.posts = [_post()]
    page = home_page(site)
    assert 'href="/archives/"' in page
    assert 'href="/favicons/favicon.ico"' in page
    assert 'href="/index.xml"' in page
    assert 'href="/rss/index.xml"' in page
    assert 'href="/posts/dangerous-title/"' in page

def test_canonical_og_url_hreflang_and_jsonld_stay_absolute():
    # The off-origin/metadata exceptions -- these are broken or meaningless
    # if made relative, so they must keep repeating site.base_url.
    page = post_page(_post(), _site())
    assert '<link rel="canonical" href="https://example.com/posts/dangerous-title/">' in page
    assert '<meta property="og:url" content="https://example.com/posts/dangerous-title/">' in page
    assert '<link rel="alternate" hreflang="en" href="https://example.com/posts/dangerous-title/">' in page
    assert '"@id": "https://example.com/posts/dangerous-title/"' in page
    assert '"item": "https://example.com/posts/"' in page
    assert '"logo": {\n      "@type": "ImageObject",\n      "url": "https://example.com/favicons/favicon.ico"' in page


# --- cv_page / consulting_page / not_found_page / categories_index --------

def _cv_front_matter() -> dict:
    return {"title": "", "linktitle": "CV", "menu": "main",
            "hidePageTitle": True, "weight": 10}

def test_cv_page_renders_a_real_link_from_the_toml_content():
    # content/cv.toml's own GitHub profile entry, rendered through cv.render
    # -- must land as a real <a>, not escaped markup.
    cv_data = cv.load(Path("content/cv.toml"))
    page = cv_page(_site(), _cv_front_matter(), cv_data)
    assert '<a href="https://github.com/allanderek" class="cv-profile-link">GitHub</a>' in page

def test_cv_page_has_a_signature_block():
    cv_data = cv.load(Path("content/cv.toml"))
    page = cv_page(_site(), _cv_front_matter(), cv_data)
    assert '<aside class="signature"' in page

def test_cv_page_has_no_nested_document():
    # The bug this whole redesign fixes: content/cv.html used to be a full
    # HTML document (its own <!DOCTYPE>/<html>/<head>) inserted verbatim,
    # so the built page carried two of each. cv.render's own output has
    # none of those tags, so the page should carry exactly one.
    cv_data = cv.load(Path("content/cv.toml"))
    page = cv_page(_site(), _cv_front_matter(), cv_data)
    assert page.count("<!DOCTYPE") == 1
    assert page.count("<html") == 1

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
    # Was byte-exact against Hugo's own alias template. The refresh target is
    # now root-relative -- a deliberate divergence, so a dev server does not
    # bounce the reader to production. <title> and canonical stay absolute:
    # canonical must be. The <title> was Hugo's bare target URL and now says
    # what the page is doing, since it shows in a tab before the redirect.
    stub = alias_stub("/posts/", _site())
    assert stub == (
        '<!DOCTYPE html>\n'
        '<html lang="en-us">\n'
        '\t<head>\n'
        '\t\t<title>Redirecting to /posts/</title>\n'
        '\t\t<link rel="canonical" href="https://example.com/posts/">\n'
        '\t\t<meta charset="utf-8">\n'
        '\t\t<meta http-equiv="refresh" content="0; url=/posts/">\n'
        '\t</head>\n'
        '</html>\n'
    )
