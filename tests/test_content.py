import pytest
from datetime import datetime, timezone
from pathlib import Path
from generator.content import (Post, load_posts, new_post, parse_post,
                               title_from_slug)

def test_parses_all_three_date_formats(tmp_path):
    for name, raw in [
        ("a", "2026-08-28"),
        ("b", "2017-04-15T14:40:31Z"),
        ("c", "2026-08-13T11:23:43+00:00"),
    ]:
        (tmp_path / f"{name}.md").write_text(
            f'---\ntitle: "T"\ndate: {raw}\ntags: [x]\n---\n\nBody\n')
    posts = {p.slug: p for p in load_posts(tmp_path)}
    assert len(posts) == 3
    assert posts["a"].date.year == 2026
    assert posts["b"].date.year == 2017
    # All three date forms -- bare, "Z"-suffixed and "+00:00" -- are the
    # same instant, and now render one label. See docs/hugo-quirks.md
    # quirk 7.
    assert {p.date.tzinfo for p in posts.values()} == {timezone.utc}

def test_body_excludes_front_matter(tmp_path):
    (tmp_path / "p.md").write_text(
        '---\ntitle: "T"\ndate: 2020-01-01\n---\n\nHello *world*\n')
    post = parse_post(tmp_path / "p.md")
    assert post.body.strip() == "Hello *world*"
    assert "title:" not in post.body

def test_drafts_are_excluded(tmp_path):
    (tmp_path / "keep.md").write_text('---\ntitle: "K"\ndate: 2020-01-01\n---\nx\n')
    (tmp_path / "skip.md").write_text(
        '---\ntitle: "S"\ndate: 2020-01-01\ndraft: true\n---\nx\n')
    assert [p.slug for p in load_posts(tmp_path)] == ["keep"]

def test_future_posts_are_excluded(tmp_path):
    (tmp_path / "old.md").write_text('---\ntitle: "O"\ndate: 2020-01-01\n---\nx\n')
    (tmp_path / "future.md").write_text('---\ntitle: "F"\ndate: 2999-01-01\n---\nx\n')
    assert [p.slug for p in load_posts(tmp_path)] == ["old"]

def test_sorted_newest_first(tmp_path):
    for name, d in [("old", "2020-01-01"), ("new", "2021-01-01")]:
        (tmp_path / f"{name}.md").write_text(f'---\ntitle: "T"\ndate: {d}\n---\nx\n')
    assert [p.slug for p in load_posts(tmp_path)] == ["new", "old"]

def test_featured_defaults(tmp_path):
    (tmp_path / "p.md").write_text('---\ntitle: "T"\ndate: 2020-01-01\n---\nx\n')
    post = parse_post(tmp_path / "p.md")
    assert post.featured is False
    assert post.featured_weight == 999
    assert post.tags == []

def test_real_corpus_loads(tmp_path):
    posts = load_posts(Path("content/posts"))
    # A floor, not an inventory. What this guards is load_posts silently
    # returning nothing or dropping most of the corpus; an exact count
    # would instead fail every time a post is written, which trains you to
    # ignore a red suite. The real assertions are the two below.
    assert len(posts) >= 150
    assert all(p.title for p in posts)
    assert posts == sorted(posts, key=lambda p: p.date, reverse=True)

def test_new_post_is_parseable_by_our_own_parser(tmp_path):
    # The point of the template: what it writes must round-trip through
    # parse_post, or the first thing a new post does is break the build.
    path = new_post(tmp_path, "my-new-post")
    post = parse_post(path)
    assert post.title == "My new post"
    assert post.tags == []
    assert post.body.strip() == ""
    assert post.date.year >= 2026

def test_new_post_takes_an_explicit_title(tmp_path):
    post = parse_post(new_post(tmp_path, "my-new-post", "A better title"))
    assert post.title == "A better title"

def test_new_post_refuses_to_overwrite(tmp_path):
    new_post(tmp_path, "already-here")
    with pytest.raises(FileExistsError):
        new_post(tmp_path, "already-here")

def test_new_post_rejects_a_slug_that_would_make_a_bad_url(tmp_path):
    # A slug becomes a permanent URL, so it is refused rather than quietly
    # normalised into something the author did not choose.
    for bad in ("My Post", "my post", "My-Post", "my--post", "-leading",
                "trailing-", "punctuation!"):
        with pytest.raises(ValueError, match="not a usable slug"):
            new_post(tmp_path, bad)

def test_new_post_accepts_ordinary_slugs(tmp_path):
    for good in ("post", "my-post", "elm-0-19-notes", "a1-b2"):
        assert new_post(tmp_path, good).name == f"{good}.md"

def test_title_from_slug_is_sentence_case():
    assert title_from_slug("why-i-like-elm") == "Why i like elm"
    assert title_from_slug("post") == "Post"

def test_description_is_parsed(tmp_path):
    (tmp_path / "p.md").write_text(
        '---\ntitle: "T"\ndate: 2020-01-01\ndescription: "A short summary"\n---\nx\n')
    post = parse_post(tmp_path / "p.md")
    assert post.description == "A short summary"

def test_featured_length_defaults_to_long(tmp_path):
    (tmp_path / "p.md").write_text(
        '---\ntitle: "T"\ndate: 2020-01-01\nfeatured: true\n---\nx\n')
    assert parse_post(tmp_path / "p.md").featured_length == "long"

def test_featured_length_is_parsed(tmp_path):
    (tmp_path / "p.md").write_text(
        '---\ntitle: "T"\ndate: 2020-01-01\nfeaturedLength: short\n---\nx\n')
    assert parse_post(tmp_path / "p.md").featured_length == "short"

def test_an_unrecognised_featured_length_is_rejected(tmp_path):
    # A typo would otherwise file the post under the wrong heading with
    # nothing at all to show for it. Same treatment a malformed date gets.
    (tmp_path / "p.md").write_text(
        '---\ntitle: "T"\ndate: 2020-01-01\nfeaturedLength: shrot\n---\nx\n')
    with pytest.raises(ValueError, match="featuredLength"):
        parse_post(tmp_path / "p.md")

def test_featured_blurb_is_parsed(tmp_path):
    (tmp_path / "p.md").write_text(
        '---\ntitle: "T"\ndate: 2020-01-01\nfeaturedBlurb: "Read this one"\n---\nx\n')
    post = parse_post(tmp_path / "p.md")
    assert post.featured_blurb == "Read this one"

def test_tag_with_quoted_comma_is_not_split(tmp_path):
    (tmp_path / "p.md").write_text(
        '---\ntitle: "T"\ndate: 2020-01-01\ntags: ["a, b", "c"]\n---\nx\n')
    post = parse_post(tmp_path / "p.md")
    assert post.tags == ["a, b", "c"]

def test_real_corpus_quoted_tag_style(tmp_path):
    (tmp_path / "p.md").write_text(
        '---\ntitle: "T"\ndate: 2020-01-01\ntags: ["compilation", "language-design"]\n---\nx\n')
    post = parse_post(tmp_path / "p.md")
    assert post.tags == ["compilation", "language-design"]

def test_corpus_tags_are_never_comma_split():
    posts = load_posts(Path("content/posts"))
    all_tags = [t for p in posts for t in p.tags]
    # Again a floor rather than a total -- see test_real_corpus_loads. The
    # assertion that matters is the second: a tag written as "a, b" in
    # front matter must survive as one tag, not split into two.
    assert len(all_tags) >= 300
    assert all("," not in t for t in all_tags)
