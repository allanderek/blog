"""Site-wide context and the build entry point."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

from .content import Post, load_posts, load_index_body
from .pages import home_page, post_page

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
    # The home page's own intro prose (content/_index.md, front matter
    # stripped) -- see content.load_index_body for why it can't go through
    # parse_post like a real post.
    home_intro: str = ""
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
    # TEMPORARY: like the two above, this is what the installed Hugo
    # version actually injects into the home page (`disableHugoGeneratorInject`
    # is unset in hugo.toml) -- Hugo's own doing, not a template call, and
    # only the home page gets it (confirmed absent from every other page
    # kind). `pkgs.hugo` in devenv.nix isn't pinned, so nixpkgs bumping it
    # would move this string; nothing downstream should assume it's
    # permanent, same as the two fields above.
    hugo_generator: str = "Hugo 0.165.0"

def _default_site(posts: list[Post], home_intro: str = "") -> SiteContext:
    return SiteContext(
        title="Allanderek's blog",
        base_url="https://blog.poleprediction.com",
        posts=posts,
        home_intro=home_intro,
    )

def build(out: Path) -> None:
    posts = load_posts(CONTENT_ROOT / "posts")
    home_intro = load_index_body(CONTENT_ROOT / "_index.md")
    site = _default_site(posts, home_intro)
    for post in posts:
        page_dir = out / "posts" / post.slug
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(post_page(post, site))
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(home_page(site))
