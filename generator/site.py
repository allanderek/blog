"""Site-wide context and the build entry point."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

from . import feeds
from .content import Post, load_posts, load_index_body
from .pages import (alias_stub, archives_page, group_posts_by_tag, home_page,
                     list_page, post_page, tag_title, terms_index)

CONTENT_ROOT = Path(__file__).resolve().parent.parent / "content"

# hugo.toml [pagination] pagerSize -- also the trigger for the 176-post
# /posts/ listing to need a second page and a `/posts/page/2/`.
PAGER_SIZE = 100

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

def _write_section(out: Path, base_path: str, posts: list[Post], site: SiteContext,
                    title: str | None = None, taxonomy: bool = False) -> None:
    """Writes every page of a paginated listing (`base_path`, e.g.
    "/posts/" or "/tags/elm/"): the bare page (the newest `PAGER_SIZE`
    posts, newest-first since `posts` already is), a `page/N/` page for
    each page after that (a tag can need one too -- "programming" alone
    has 106 posts, one over `PAGER_SIZE`), and the `page/1/` alias stub
    Hugo's `disableAliases = false` emits for every paginated listing --
    even for a single-page one, matching Hugo (see `pages.alias_stub`) --
    nothing in check-site.sh asserts that stub exists, so it is easy to
    silently drop; `compare.py` is what catches it. `title` is threaded
    straight through to `list_page` -- see its docstring for why a tag
    listing must pass its real front-matter spelling here rather than
    leaving it to derive one. `taxonomy` is also threaded straight
    through, selecting `list_page`'s taxonomy <head>/entry-class
    behaviour for a tag's own listing."""
    total_pages = max(1, -(-len(posts) // PAGER_SIZE))  # ceil division
    section_dir = out / base_path.strip("/")
    section_dir.mkdir(parents=True, exist_ok=True)
    for page_num in range(1, total_pages + 1):
        page_posts = posts[(page_num - 1) * PAGER_SIZE: page_num * PAGER_SIZE]
        page_html = list_page(page_posts, page_num, total_pages, base_path, site,
                               title=title, taxonomy=taxonomy)
        page_dir = section_dir if page_num == 1 else section_dir / "page" / str(page_num)
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(page_html)
    stub_dir = section_dir / "page" / "1"
    stub_dir.mkdir(parents=True, exist_ok=True)
    (stub_dir / "index.html").write_text(alias_stub(base_path, site))
    # One RSS feed per section/term, at its own bare `base_path` only --
    # never per pagination page (Hugo emits no `page/N/index.xml`; the
    # feed always lists every one of `posts`, not just one page's slice --
    # see feeds.rss's docstring). `title` defaults the same way
    # `list_page` does when the caller (the `/posts/` case) leaves it
    # unset: `tag_title` on the last path segment of `base_path`.
    (section_dir / "index.xml").write_text(
        feeds.rss(posts, site, base_path,
                  title=title if title is not None
                  else tag_title(base_path.strip("/").rsplit("/", 1)[-1])))

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
    # The site-wide feeds. Deliberately built from `posts` alone, not
    # every Hugo `RegularPage` -- see feeds.py's module docstring for why
    # Hugo's own `/index.xml` (which also lists `/cv/` and `/consulting/`)
    # is not fully reproducible yet.
    (out / "index.xml").write_text(feeds.rss(posts, site, title=site.title))
    rss_dir = out / "rss"
    rss_dir.mkdir(parents=True, exist_ok=True)
    (rss_dir / "index.xml").write_text(feeds.atom(posts, site))
    _write_section(out, "/posts/", posts, site)

    tags = group_posts_by_tag(posts)
    for name, slug, tag_posts in tags:
        _write_section(out, f"/tags/{slug}/", tag_posts, site,
                        title=tag_title(name), taxonomy=True)
    tags_dir = out / "tags"
    tags_dir.mkdir(parents=True, exist_ok=True)
    (tags_dir / "index.html").write_text(terms_index(tags, site))

    archives_dir = out / "archives"
    archives_dir.mkdir(parents=True, exist_ok=True)
    (archives_dir / "index.html").write_text(archives_page(posts, site))
