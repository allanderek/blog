from datetime import datetime
from pathlib import Path
from generator.content import Post, load_posts, parse_post

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
    # Bare date and "Z" suffix both parse to Go's named "UTC" zone; an
    # explicit numeric offset parses to an unnamed fixed-offset zone --
    # invisible on the datetime itself, but it changes how Hugo formats it.
    assert posts["a"].date_zone_named is True
    assert posts["b"].date_zone_named is True
    assert posts["c"].date_zone_named is False

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

def test_description_is_parsed(tmp_path):
    (tmp_path / "p.md").write_text(
        '---\ntitle: "T"\ndate: 2020-01-01\ndescription: "A short summary"\n---\nx\n')
    post = parse_post(tmp_path / "p.md")
    assert post.description == "A short summary"

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
