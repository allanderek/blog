"""Site-wide context and the build entry point."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

from .content import Post, load_posts
from .pages import post_page

CONTENT_ROOT = Path(__file__).resolve().parent.parent / "content"

@dataclass
class SiteContext:
    title: str
    base_url: str
    posts: list[Post] = field(default_factory=list)
    author: str = "Allan Clark"
    description: str = (
        "The thoughts of a programmer, heavily slanted towards development "
        "in Elm, but occasionally more general programming."
    )
    # TEMPORARY: assets.py (Task 11) will compute these from the real,
    # fingerprinted CSS bundle. Hardcoded here so post pages can reach a
    # byte-for-byte match against Hugo *now* -- captured from Hugo's own
    # build of this repo (`direnv exec . hugo --destination /tmp/target`).
    # Task 11 replaces both with values computed by assets.py; nothing
    # downstream should assume these particular strings are permanent.
    stylesheet_href: str = (
        "/assets/css/stylesheet.9adc48ca951744ce8f6b0c8854fdd76fa8e68bfeafc106e171df63787f1e19c5.css"
    )
    stylesheet_integrity: str = "sha256-mtxIypUXRM6PawyIVP3Xb6jmi/6vwQbhcd9jeH8eGcU="

def _default_site(posts: list[Post]) -> SiteContext:
    return SiteContext(
        title="Allanderek's blog",
        base_url="https://blog.poleprediction.com",
        posts=posts,
    )

def build(out: Path) -> None:
    posts = load_posts(CONTENT_ROOT / "posts")
    site = _default_site(posts)
    for post in posts:
        page_dir = out / "posts" / post.slug
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(post_page(post, site))
