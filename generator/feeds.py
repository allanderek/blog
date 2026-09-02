"""The site's RSS and Atom feeds.

`rss()` renders `layouts/_default/rss.xml` (read-only reference for this
task, quoted piecemeal in the comments below) for three different Kinds
that all go through the same template: the home page (`/index.xml`), a
section (`/posts/index.xml`), and a taxonomy term (`/tags/<slug>/index.xml`,
one per tag). Which Kind is which is selected entirely by `base_path`/
`title`/`posts`, matching the caller's own convention in
`pages.list_page`/`site._write_section`: `title` is the page's real display
title (already-resolved, e.g. `tag_title(name)`), defaulting to
`site.title` for the home page.

`atom()` renders Hugo's embedded default Atom template, which this repo has
no local override for -- reverse-engineered from `hugo --destination`
output rather than transcribed from source (no local copy of Hugo's
embedded template exists to read). It is the site's only Atom feed: Hugo's
`[outputs] home = [..., "ATOM"]` is the only Kind in hugo.toml with ATOM in
its output formats, so, unlike `rss()`, there is only ever one of these.

Neither function's title is ever rewritten to Hugo's title-fallback form
when `title == site.title` (`check-site.sh` asserts this for both feeds) --
that IS the fallback form; it only fires the OTHER way; see `_channel_title`.

The root RSS feed (only the root one -- every section/term feed's `.Pages`
is genuinely just its own posts) additionally lists two non-post pages,
`/cv/` and `/consulting/`: Hugo's home-page RSS uses `.RegularPages`, every
Kind-"page" content file site-wide, not `mainSections`-filtered posts (that
filtering is Atom-only -- see `_atom_entry`'s docstring for why the two
formats diverge). `_load_root_extras` builds those two entries straight
from `content/cv.md`/`content/consulting.md`'s own front matter -- reading
front matter, not rendering either page in full -- and `rss()` merges them
into `posts` for the root feed only, ordered by Hugo's actual default page
sort. See `_load_root_extras` for how the CV item's own `<description>`
(which needs `.Summary` of `{{< cv >}}`'s rendered content, not just front
matter) is built once `pages.cv_page` exists to share that same summary
logic with, and the task-10 report for how all of this was found.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from . import html, markdown
from .content import Post, load_front_matter
from .pages import strip_style_comments, tag_title

if TYPE_CHECKING:
    from .site import SiteContext

_CONTENT_ROOT = Path(__file__).resolve().parent.parent / "content"

_CV_SHORTCODE = _CONTENT_ROOT / "cv.html"

# Hugo's default RSS/Atom date layouts (`time.Time.Format`, Go reference
# time). Posts are always UTC in this Post model (content.py normalises
# every front-matter date's tzinfo to UTC), so both are hardcoded to the
# zero offset rather than computed -- same trick pages.py's `_ISO_OFFSET`
# already relies on for the same reason.
_RFC1123Z = "%a, %d %b %Y %H:%M:%S %z"          # RSS <pubDate>/<lastBuildDate>
_ISO_OFFSET = "%Y-%m-%dT%H:%M:%S+00:00"          # Atom <published>/<updated>

ATOM_ENTRY_LIMIT = 20   # check-site.sh asserts this count.

# A feed reader has no notion of "this site" to resolve a root-relative URL
# against, so Hugo rewrites every `href`/`src` that starts with a bare "/"
# (never "//", a protocol-relative URL, which is already absolute enough)
# in feed HTML to a fully-qualified one -- confirmed against real output: a
# post page keeps `href="/posts/other-post/"` verbatim, but that same link
# reads `href="https://blog.poleprediction.com/posts/other-post/"` in every
# feed it appears in (RSS description, Atom content, on any post's own
# in-body links to another post). Applied to the raw HTML BEFORE
# `html.esc_text`, not after: matching plain `href="..."` quotes is far
# simpler than matching the escaped `href=&#34;...&#34;` form, and running
# first doesn't change the escaped result either way.
_LOCAL_URL_RE = re.compile(r'\b(href|src)="(/(?!/)[^"]*)"')


def _absolutize(fragment: str, site: SiteContext) -> str:
    return _LOCAL_URL_RE.sub(
        lambda m: f'{m.group(1)}="{site.base_url}{m.group(2)}"', fragment)


def _channel_title(title: str, site: SiteContext) -> str:
    # rss.xml: `{{ if eq .Title site.Title }}{{ site.Title }}{{ else }}
    # {{ with .Title }}{{ . }} on {{ end }}{{ site.Title }}{{ end }}`.
    return site.title if title == site.title else f"{title} on {site.title}"


def _channel_description(title: str, site: SiteContext) -> str:
    # rss.xml: `Recent content {{ if ne .Title site.Title }}
    # {{ with .Title }}in {{ . }} {{ end }}{{ end }}on {{ site.Title }}`.
    if title == site.title:
        return f"Recent content on {site.title}"
    return f"Recent content in {title} on {site.title}"


# Go's zero time.Time, formatted through Hugo's own RFC1123Z-ish layout --
# what `content/cv.md`/`content/consulting.md` get for `<pubDate>`, since
# neither sets a `date:` (confirmed against real output). Not computed via
# `.strftime`: Python's "%Y" doesn't zero-pad year 1 to four digits the way
# Go's "2006" does ("Mon, 01 Jan 1 00:00:00 +0000" vs. Hugo's real
# "Mon, 01 Jan 0001 00:00:00 +0000"), so this is the one literal exception
# to computing every other date in this module.
_ZERO_PUBDATE = "Mon, 01 Jan 0001 00:00:00 +0000"
_ZERO_DATE = datetime.min.replace(tzinfo=timezone.utc)   # Go's zero time.Time


@dataclass
class _RssEntry:
    """One RSS `<item>`, already resolved down to exactly what the item
    template needs -- built either from a `Post` (`_post_entry`) or from
    `content/cv.md`/`content/consulting.md`'s own front matter
    (`_load_root_extras`), so `_rss_item` itself never has to know which.
    `weight`/`sort_date` exist only to feed `_hugo_page_order`; `pub_date`
    is the already-formatted `<pubDate>` string (a `Post`'s real date, or
    the literal `_ZERO_PUBDATE`), kept separate from `sort_date` because
    Hugo's own sort key -- `.Date`, zero for both extras -- and its
    `<pubDate>` -- `.PublishDate`, which prints as the same zero -- happen
    to coincide here but are conceptually two different fields."""
    title: str
    permalink: str
    pub_date: str
    description: str          # already fully escaped, ready to insert as-is
    weight: int = 0
    sort_date: datetime = _ZERO_DATE


def _post_entry(post: Post, site: SiteContext) -> _RssEntry:
    permalink = f"{site.base_url}/posts/{post.slug}/"
    return _RssEntry(
        title=html.esc(post.title), permalink=permalink,
        pub_date=post.date.strftime(_RFC1123Z),
        description=_rss_item_description(post, site),
        weight=0, sort_date=post.date,
    )


def _load_root_extras(site: SiteContext) -> list[_RssEntry]:
    """`content/cv.md` and `content/consulting.md`: the two non-post
    `.RegularPages` Hugo's root RSS includes alongside every post (see
    this module's docstring). Both set no `date:`, so both get
    `_ZERO_PUBDATE` and sort last among same-weight entries -- cv.md's own
    `weight: 10` is what actually puts it first overall; see
    `_hugo_page_order`.

    The CV item's own `<description>` is `.Summary` of `{{< cv >}}`'s
    FULLY RENDERED page (confirmed against real output: the escaped text
    starts `&lt;!DOCTYPE html&gt;...`, the CV page's own literal markup,
    not prose) -- `markdown.extract_summary` applied to
    `pages.strip_style_comments(cv.html)` (Hugo's own `.Content` for this
    page -- see that function's docstring for why the raw shortcode text
    alone isn't quite right), the same computation `pages.cv_page` does
    for its own `<meta name="description">`, then absolutized and escaped
    exactly like a real post's own RSS summary (`_rss_item_description`'s
    `.Summary | html` pipeline) since it is still raw, tag-intact HTML at
    this point, not the tag-stripped form `<meta name="description">`
    needs.
    """
    cv_meta = load_front_matter(_CONTENT_ROOT / "cv.md")
    consulting_meta = load_front_matter(_CONTENT_ROOT / "consulting.md")
    cv_content = strip_style_comments(_CV_SHORTCODE.read_text())
    cv_summary = markdown.extract_summary(cv_content)
    cv = _RssEntry(
        title=html.esc(cv_meta.get("title", "")),
        permalink=f"{site.base_url}/cv/",
        pub_date=_ZERO_PUBDATE,
        description=html.esc_text(_absolutize(cv_summary, site)),
        weight=int(cv_meta.get("weight", 0)),
    )
    consulting_url = consulting_meta.get("url", "/consulting/")
    consulting = _RssEntry(
        title=html.esc(consulting_meta.get("title", "")),
        permalink=f"{site.base_url}{consulting_url}",
        pub_date=_ZERO_PUBDATE,
        # `summary:` front matter overrides Hugo's auto-extracted
        # `.Summary` outright (a real Hugo feature) -- plain prose, one
        # escaping pass, same as any other already-`template.HTML` value
        # (`.Summary | html`, not `.Description | html`'s doubled one).
        description=html.esc_text(consulting_meta.get("summary", "")),
        weight=int(consulting_meta.get("weight", 0)),
    )
    return [cv, consulting]


def _hugo_page_less(a: tuple, b: tuple) -> bool:
    """Hugo's actual default page sort (`resources/page/pagesort.go`,
    transcribed, not guessed) as a `<` predicate over `(weight, date,
    linktitle)` triples: weight ascending, EXCEPT a page with no explicit
    weight (0) always sorts after one that sets any -- not "0 is the
    smallest weight", a page's own weight compared numerically against 0
    -- pages sharing a weight sort by date (newest first), and pages
    sharing BOTH sort by LinkTitle, ascending. `date=_ZERO_DATE` stands in
    for Hugo's zero `time.Time` (no `date:` front matter): the oldest
    possible date, so "newest first" puts a page carrying it dead last
    among its tied group, not first, whatever its small weight number
    might otherwise suggest.

    Confirmed against real output twice, at two different scales:
    `content/cv.md`'s `weight: 10` sorts it before all 176 (weight-0)
    posts, and zero-dated `content/consulting.md` (weight 0, like every
    post) sorts after every one of them, in the root RSS feed
    (`_hugo_page_order`, `rss()`'s `include_site_pages`); and, site-wide,
    in `sitemap()` -- e.g. "Gren"/"Programming"/"Syntax" (identical
    weight, identical pubDate: the same newest post carries all three
    tags) list in exactly LinkTitle-ascending order, and the whole
    zero-weight/zero-date tail (`/archives/`, `/categories/`,
    `/consulting/`) sorts "Archive" < "Categories" < "Consulting"."""
    aw, ad, at = a
    bw, bd, bt = b
    if aw == bw:
        if ad == bd:
            # Case-INSENSITIVE, confirmed against real output: the tag
            # "Agents" sorts before the post "AI agent programming and
            # files as  modules" (same date) in the real sitemap, which a
            # raw/byte comparison gets backwards -- 'I' (0x49) sorts
            # before 'g' (0x67) in a case-SENSITIVE comparison, putting
            # "AI..." first, the opposite of Hugo's real order.
            return at.lower() < bt.lower()
        return ad > bd
    if bw == 0:
        return True
    if aw == 0:
        return False
    return aw < bw


def _hugo_page_order(entries: list[_RssEntry]) -> list[_RssEntry]:
    import functools
    key = lambda e: (e.weight, e.sort_date, e.title)  # noqa: E731
    cmp = lambda a, b: -1 if _hugo_page_less(key(a), key(b)) else (  # noqa: E731
        1 if _hugo_page_less(key(b), key(a)) else 0)
    return sorted(entries, key=functools.cmp_to_key(cmp))


def _rss_item_description(post: Post, site: SiteContext) -> str:
    # rss.xml: `{{ with .Description | html }}{{ . }}{{ else }}
    # {{ .Summary | html }}{{ end -}}`. `.Description` is a plain
    # front-matter string (never has HTML markup to absolutize a link
    # inside); `.Summary` is already-rendered HTML (goldmark's own entity
    # form, kept verbatim -- see markdown.py's `render_entities`
    # docstring) truncated at 70 words. Either way the explicit `| html`
    # pipe is Go's plain `html/template.HTMLEscapeString`, not the wider
    # contextual attribute escaper -- `html.esc_text`, not `html.esc`; see
    # that function's docstring.
    if post.description:
        # Doubly escaped, not a typo: `.Description` is a plain string (not
        # `template.HTML`, unlike `.Summary`), and the template's
        # `{{ with .Description | html }}{{ . }}` prints it through a
        # SECOND, separate `{{ . }}` action -- which Go's contextual
        # auto-escaper treats as its own bare text-node interpolation and
        # escapes again, since only a pipeline ending in a recognised
        # escaper (as `.Summary | html` below, printed directly with no
        # `with`/reprint in between) is exempted. Confirmed against real
        # output: a front-matter `description: "...Elm's..."` -- a real
        # apostrophe, one escaping pass elsewhere on the very same page's
        # own `<meta name="description">` -- comes out `Elm&amp;#39;s`
        # here, not `Elm&#39;s`.
        return html.esc_text(html.esc_text(post.description))
    summary = markdown.extract_summary(markdown.render_entities(post.body))
    return html.esc_text(_absolutize(summary, site))


def _rss_item(entry: _RssEntry) -> str:
    # No <author>: site.Params.author is a plain string, not a map, so
    # rss.xml's `$authorEmail` (from `.email`) is always "" here and every
    # block gated on `{{ with $authorEmail }}` -- <managingEditor>,
    # <webMaster>, and this per-item <author> -- never fires. Confirmed
    # against real output: zero <author> tags anywhere in any RSS feed.
    return f"""    <item>
      <title>{entry.title}</title>
      <link>{entry.permalink}</link>
      <pubDate>{entry.pub_date}</pubDate>
      <guid>{entry.permalink}</guid>
      <description>{entry.description}</description>
    </item>"""


def rss(posts: list[Post], site: SiteContext, base_path: str = "/",
        title: str | None = None, include_site_pages: bool = False) -> str:
    """One RSS 2.0 channel: `posts` newest-first, already the FULL set for
    `base_path` (a section or term's own RSS gets every one of its posts,
    never just one pagination page -- confirmed against real output:
    `/posts/index.xml` has all 176, `/tags/programming/index.xml` all 106,
    despite `PAGER_SIZE` capping the HTML listing at 100). `title` is the
    page's real display title; omitted only by the home-page caller, which
    passes `site.title` explicitly instead (see this module's docstring).
    `include_site_pages` is that same home-page caller's own signal to
    merge in `_load_root_extras`'s two non-post entries -- every
    section/term feed's own `.Pages` is genuinely just its own posts, so
    this must default off for them."""
    if title is None:
        title = site.title
    permalink = f"{site.base_url}{base_path}"
    self_href = f"{permalink}index.xml"
    entries = [_post_entry(post, site) for post in posts]
    if include_site_pages:
        entries = _hugo_page_order(entries + _load_root_extras(site))
    # rss.xml: `{{ (index $pages.ByLastmod.Reverse 0).Lastmod.Format ... }}`
    # `{{ if not .Date.IsZero }}` guards the whole element -- omitted
    # entirely, not printed empty, when there is nothing to report a date
    # for (confirmed against real output: the empty `categories`
    # taxonomy's own feed has no `<lastBuildDate>` line at all). The
    # newest of `entries`' own dates either way, not a build clock -- see
    # the task-10 report for how that was established -- computed from
    # `sort_date` (not `pub_date`, a string) so the two zero-dated site
    # pages this can include never register as "newest".
    dated = [e for e in entries if e.sort_date > _ZERO_DATE]
    last_build = (f"    <lastBuildDate>{max(e.sort_date for e in dated).strftime(_RFC1123Z)}</lastBuildDate>\n"
                  if dated else "")
    items = "\n".join(_rss_item(e) for e in entries)
    if items:
        items += "\n"
    return f"""<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{html.esc(_channel_title(title, site))}</title>
    <link>{permalink}</link>
    <description>{html.esc(_channel_description(title, site))}</description>
    <generator>Hugo -- 0.165.0</generator>
    <language>en-us</language>
{last_build}    <atom:link href="{self_href}" rel="self" type="application/rss+xml" />
{items}  </channel>
</rss>
"""


def terms_rss(tags: list[tuple[str, str, list[Post]]], site: SiteContext,
               base_path: str, title: str) -> str:
    """A taxonomy's OWN listing feed (`/tags/index.xml`, `/categories/
    index.xml`) -- structurally its own thing, not `rss()` with a
    different `posts` list: its `<item>`s are the TERMS themselves (one
    per tag, title/link/pubDate, no post content -- `<description>` is
    always empty), not posts. `tags` is `pages.group_posts_by_tag`'s own
    (display_name, slug, that tag's posts) triples; unlike that function's
    own alphabetical-by-slug order (which `/tags/`'s HTML listing wants),
    Hugo's taxonomy-list RSS sorts its term-pages by Hugo's own default
    page sort -- every term's implicit weight is 0, so this collapses to
    date descending, then (Hugo's own third tiebreaker, LinkTitle
    ascending) `tag_title` ascending for a tie -- confirmed against real
    output: "Gren"/"Programming"/"Syntax" (identical pubDate, the same
    newest post carries all three tags) list in exactly that alphabetical
    order. A term's own "date" is the newest of its own posts' dates, the
    same value its own per-tag feed's `<lastBuildDate>` uses (`rss()`,
    called separately per tag). `categories` (this site's other taxonomy,
    always empty -- no post ever sets `categories:`) reuses this with
    `tags=[]`, matching Hugo's real, itemless `/categories/index.xml`
    exactly (confirmed against real output: `<channel>` with no `<item>`
    and, per the same `.Date.IsZero` guard `rss()` documents, no
    `<lastBuildDate>` either)."""
    permalink = f"{site.base_url}{base_path}"
    self_href = f"{permalink}index.xml"
    # Case-insensitive tiebreak, matching `_hugo_page_less`'s own (see
    # there for why a raw comparison gets a real corpus case backwards).
    ordered = sorted(
        tags, key=lambda t: (-max(p.date for p in t[2]).timestamp(), tag_title(t[0]).lower()))
    last_build = ""
    if ordered:
        newest = max(p.date for _, _, posts in ordered for p in posts)
        last_build = f"    <lastBuildDate>{newest.strftime(_RFC1123Z)}</lastBuildDate>\n"
    items = "\n".join(f"""    <item>
      <title>{html.esc(tag_title(name))}</title>
      <link>{site.base_url}/tags/{slug}/</link>
      <pubDate>{max(p.date for p in tag_posts).strftime(_RFC1123Z)}</pubDate>
      <guid>{site.base_url}/tags/{slug}/</guid>
      <description></description>
    </item>""" for name, slug, tag_posts in ordered)
    if items:
        items += "\n"
    return f"""<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{html.esc(_channel_title(title, site))}</title>
    <link>{permalink}</link>
    <description>{html.esc(_channel_description(title, site))}</description>
    <generator>Hugo -- 0.165.0</generator>
    <language>en-us</language>
{last_build}    <atom:link href="{self_href}" rel="self" type="application/rss+xml" />
{items}  </channel>
</rss>
"""


def _atom_entry(post: Post, site: SiteContext) -> str:
    permalink = f"{site.base_url}/posts/{post.slug}/"
    when = post.date.strftime(_ISO_OFFSET)
    # The <content> is the FULL post, not a summary (unlike RSS's
    # <description>): Hugo's embedded atom template has no word-count
    # limit. Same entity-form render and `| html`-style escaping as the
    # RSS description (see its docstring) -- `render_entities`, not
    # `render`: a literal "&rsquo;" in the raw HTML must double-escape to
    # "&amp;rsquo;" the same way a live "&" would, which only holds if the
    # typographer's substitutions are already entity text rather than real
    # Unicode curly-quote characters.
    # Unlike RSS's <description> (see `_rss_item_description`), Atom's
    # <content> does NOT get its internal links absolutized: confirmed
    # against real output -- the same in-body link to another post reads
    # `href="/posts/other-post/"` here but
    # `href="https://blog.poleprediction.com/posts/other-post/"` in every
    # RSS feed. Hugo's automatic link-absolutizing is keyed to its own
    # built-in "rss" output format specifically; ATOM here is a
    # user-defined format in hugo.toml (`[outputFormats.ATOM]`), so it
    # never gets that treatment even though `layouts/_default/rss.xml`
    # itself is shared across every RSS-kind page (home/section/term).
    content = html.esc_text(markdown.render_entities(post.body))
    lines = [
        "  <entry>",
        f"    <title>{html.esc(post.title)}</title>",
        f'    <link href="{permalink}"/>',
        f"    <id>{permalink}</id>",
        f"    <published>{when}</published>",
        f"    <updated>{when}</updated>",
        f"    <author><name>{html.esc(site.author)}</name></author>",
        f'    <content type="html">{content}</content>',
    ]
    # Two whitespace-only lines before the first <category>, one between
    # each subsequent pair, and two more before </entry> -- reproduced
    # literally for the same reason as atom()'s own preamble; see there.
    if post.tags:
        lines.append("    ")
        lines.append("    ")
        for i, tag in enumerate(post.tags):
            if i:
                lines.append("    ")
            lines.append(f'    <category term="{html.esc(tag)}"/>')
        lines.append("    ")
    lines.append("    ")
    lines.append("  </entry>")
    return "\n".join(lines)


def atom(posts: list[Post], site: SiteContext) -> str:
    """The site's one Atom feed (`/rss/index.xml`): the `ATOM_ENTRY_LIMIT`
    newest posts (`check-site.sh` asserts the count) -- `posts` need not
    already be trimmed; slicing here mirrors Hugo's own template doing it
    internally rather than expecting a pre-limited caller. The feed-level
    `<updated>` is the one genuine build clock in either feed (see the
    task-10 report for how that was established) -- `datetime.now()`
    picks up whatever zone the process runs under, same as Hugo's own
    `now`."""
    entries = posts[:ATOM_ENTRY_LIMIT]
    updated = datetime.now().astimezone().isoformat(timespec="seconds")
    entries_xml = "\n  \n".join(_atom_entry(post, site) for post in entries)
    # The blank-looking lines below are NOT empty: Hugo's own output pads
    # each with the indentation of its surrounding block ("  " or "    "),
    # a leftover of `{{ with }}` blocks that produced no text of their own.
    # Reproduced literally (rather than as bare blank lines) so a raw
    # `diff` against real Hugo output -- not just compare.py's
    # whitespace-normalised one -- comes back clean; see the task-10
    # report.
    return "\n".join([
        '<?xml version="1.0" encoding="utf-8"?>',
        '<feed xmlns="http://www.w3.org/2005/Atom">',
        f"  <title>{html.esc(site.title)}</title>",
        f'  <link href="{site.base_url}/rss" rel="self"/>',
        f'  <link href="{site.base_url}/"/>',
        f"  <updated>{updated}</updated>",
        f"  <id>{site.base_url}/</id>",
        "  ",
        "  <author>",
        f"    <name>{html.esc(site.author)}</name>",
        "    ",
        "  </author>",
        "  <generator>Hugo -- gohugo.io</generator>",
        "  ",
        entries_xml,
        "  ",
        "</feed>",
        "",
    ])


def _link_title(meta: dict) -> str:
    # Hugo's own LinkTitle fallback: `linktitle:` front matter if set,
    # else `title:` -- confirmed against `content/cv.md`, which sets
    # both distinctly (`title: ""`, `linktitle: "CV"`) precisely so its
    # nav-menu entry reads "CV" while its own page carries no title.
    return str(meta.get("linktitle") or meta.get("title", ""))


def sitemap(posts: list[Post], tags: list[tuple[str, str, list[Post]]],
            site: SiteContext) -> str:
    """`/sitemap.xml`: every Kind Hugo puts in it -- every post, the home
    page, the `/posts/` section, the `/tags/` taxonomy list, every tag's
    own term page, and `content/archives.md`/`categories` (empty, no
    `_index.md`)/`consulting.md`/`cv.md` -- ordered by the SAME default
    page sort `rss()`'s `include_site_pages` already established
    (`_hugo_page_less`), just applied site-wide instead of to two extra
    root-feed items. Confirmed against real output: 252 `<url>` entries,
    matching this exact membership one-for-one (176 posts + 1 home +
    1 section + 1 taxonomy list + 69 terms + 4 standalone pages), in this
    exact order -- no pagination page gets its own entry. A page's own
    `<lastmod>` is its `.Date` (the same "newest of its own content" value
    used throughout this module for `<lastBuildDate>`), entirely omitted,
    not printed empty, for the four pages with none. Reading `content/
    archives.md`'s own front matter is the only new thing this needs
    beyond what `_load_root_extras` already reads for cv/consulting --
    `pages.archives_page` (Task 9) renders the page itself; this only
    needs its `<loc>`/`<lastmod>`/sort position, not its body."""
    max_date = max((p.date for p in posts), default=None)
    entries: list[tuple[int, datetime, str, str]] = []  # (weight, date, linktitle, loc)
    entries.append((0, max_date or _ZERO_DATE, site.title, f"{site.base_url}/"))
    for post in posts:
        entries.append((0, post.date, post.title, f"{site.base_url}/posts/{post.slug}/"))
    entries.append((0, max_date or _ZERO_DATE, tag_title("posts"), f"{site.base_url}/posts/"))
    entries.append((0, max_date or _ZERO_DATE, tag_title("tags"), f"{site.base_url}/tags/"))
    for name, slug, tag_posts in tags:
        entries.append((0, max(p.date for p in tag_posts), tag_title(name),
                         f"{site.base_url}/tags/{slug}/"))
    archives_meta = load_front_matter(_CONTENT_ROOT / "archives.md")
    entries.append((int(archives_meta.get("weight", 0)), _ZERO_DATE,
                     _link_title(archives_meta), f"{site.base_url}/archives/"))
    entries.append((0, _ZERO_DATE, tag_title("categories"), f"{site.base_url}/categories/"))
    consulting_meta = load_front_matter(_CONTENT_ROOT / "consulting.md")
    entries.append((int(consulting_meta.get("weight", 0)), _ZERO_DATE,
                     _link_title(consulting_meta),
                     f"{site.base_url}{consulting_meta.get('url', '/consulting/')}"))
    cv_meta = load_front_matter(_CONTENT_ROOT / "cv.md")
    entries.append((int(cv_meta.get("weight", 0)), _ZERO_DATE,
                     _link_title(cv_meta), f"{site.base_url}/cv/"))

    import functools
    key = lambda e: (e[0], e[1], e[2])  # noqa: E731
    cmp = lambda a, b: -1 if _hugo_page_less(key(a), key(b)) else (  # noqa: E731
        1 if _hugo_page_less(key(b), key(a)) else 0)
    ordered = sorted(entries, key=functools.cmp_to_key(cmp))

    urls = "".join(
        f"<url>\n    <loc>{loc}</loc>\n"
        + (f"    <lastmod>{date.strftime(_ISO_OFFSET)}</lastmod>\n" if date > _ZERO_DATE else "")
        + "  </url>"
        for _, date, _, loc in ordered
    )
    return f"""<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
  xmlns:xhtml="http://www.w3.org/1999/xhtml">
  {urls}
</urlset>
"""
