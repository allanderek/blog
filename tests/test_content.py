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
    assert len(posts) == 176
    assert all(p.title for p in posts)
    assert posts == sorted(posts, key=lambda p: p.date, reverse=True)
