"""Site-wide context and the build entry point."""
from __future__ import annotations
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from . import assets, feeds
from .content import Post, load_front_matter, load_page, load_posts, load_index_body
from .pages import (alias_stub, archives_page, categories_index, cv_page,
                     consulting_page, group_posts_by_tag, home_page,
                     list_page, not_found_page, post_page, tag_title,
                     terms_index)

REPO_ROOT = Path(__file__).resolve().parent.parent
CONTENT_ROOT = REPO_ROOT / "content"
STATIC_ROOT = REPO_ROOT / "static"
CSS_ROOT = REPO_ROOT / "css"
PORTRAIT_SRC = REPO_ROOT / "images" / "portrait.png"

# consulting-signature.html: `resources.Get("images/portrait.png").Resize
# ("112x png")` -- the source is square, so this is both the resized
# width and height.
PORTRAIT_WIDTH = 112

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
    # Computed by `assets.build_stylesheet`/`assets.resize_portrait` in
    # `build()`, below, before any page is rendered -- every page's <head>
    # (stylesheet_href/stylesheet_integrity) or signature block
    # (avatar_href) embeds these verbatim. The defaults here are never the
    # real values in a `build()`-produced site; they only matter to a
    # caller (a test) that builds a `SiteContext` directly without also
    # running asset generation.
    stylesheet_href: str = ""
    stylesheet_integrity: str = ""
    avatar_href: str = ""

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

def _copy_static(out: Path) -> None:
    """Hugo copies `static/` into the output root verbatim, file for
    file (favicons, `cv.pdf`, `img/*`, ...) -- implemented generically
    here, rather than naming each file, so a future addition under
    `static/` ships without this function needing an edit."""
    if not STATIC_ROOT.is_dir():
        return
    for src in STATIC_ROOT.rglob("*"):
        if src.is_dir():
            continue
        dest = out / src.relative_to(STATIC_ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)

def build(out: Path) -> None:
    posts = load_posts(CONTENT_ROOT / "posts")
    home_intro = load_index_body(CONTENT_ROOT / "_index.md")
    site = _default_site(posts, home_intro)
    site.stylesheet_href, site.stylesheet_integrity = assets.build_stylesheet(CSS_ROOT, out)
    site.avatar_href = assets.resize_portrait(PORTRAIT_SRC, out, PORTRAIT_WIDTH)
    _copy_static(out)
    for post in posts:
        page_dir = out / "posts" / post.slug
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(post_page(post, site))
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(home_page(site))
    # The site-wide feeds. `include_site_pages` merges in `/cv/`/
    # `/consulting/` (every other feed's `.Pages` is genuinely just its
    # own posts) -- see feeds.py's module docstring for the one field of
    # the CV item this still can't reproduce.
    (out / "index.xml").write_text(
        feeds.rss(posts, site, title=site.title, include_site_pages=True))
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
    (tags_dir / "index.xml").write_text(
        feeds.terms_rss(tags, site, "/tags/", tag_title("tags")))
    # /categories/: an unused taxonomy (no post ever sets `categories:`),
    # so its own terms page (`categories_index`) always renders the
    # zero-terms case -- Hugo still emits both an (empty) HTML page and an
    # (empty but real) feed regardless. `terms_rss` with an empty `tags`
    # list already matches Hugo's real, itemless feed output; see its own
    # docstring.
    categories_dir = out / "categories"
    categories_dir.mkdir(parents=True, exist_ok=True)
    (categories_dir / "index.html").write_text(categories_index(site))
    (categories_dir / "index.xml").write_text(
        feeds.terms_rss([], site, "/categories/", tag_title("categories")))

    archives_dir = out / "archives"
    archives_dir.mkdir(parents=True, exist_ok=True)
    (archives_dir / "index.html").write_text(archives_page(posts, site))

    # content/cv.md and content/consulting.md: the two non-post Kind
    # "page" content files -- see pages.cv_page/consulting_page's own
    # docstrings. Read straight from disk rather than threaded through
    # `posts` (they are not `Post`s -- see content.load_front_matter's
    # own docstring, which `feeds._load_root_extras` already relies on
    # for the same two files).
    cv_meta = load_front_matter(CONTENT_ROOT / "cv.md")
    cv_html = (CONTENT_ROOT / "cv.html").read_text()
    cv_dir = out / "cv"
    cv_dir.mkdir(parents=True, exist_ok=True)
    (cv_dir / "index.html").write_text(cv_page(site, cv_meta, cv_html))

    consulting_meta, consulting_body = load_page(CONTENT_ROOT / "consulting.md")
    consulting_url = str(consulting_meta.get("url", "/consulting/")).strip("/")
    consulting_dir = out / consulting_url
    consulting_dir.mkdir(parents=True, exist_ok=True)
    (consulting_dir / "index.html").write_text(
        consulting_page(site, consulting_meta, consulting_body))

    (out / "404.html").write_text(not_found_page(site))

    (out / "sitemap.xml").write_text(feeds.sitemap(posts, tags, site))
