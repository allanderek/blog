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

Both site-wide feeds deliberately take only `site.posts`: Hugo's real
`/index.xml` also lists two non-post pages (`/cv/` and `/consulting/`,
`.RegularPages` on the home page is every regular page, not just posts),
which neither page exists to render yet (Task 11). Tracked as a known,
expected gap -- see the task-10 report -- not something `rss()` tries to
special-case.
"""
from __future__ import annotations
import re
from datetime import datetime
from typing import TYPE_CHECKING

from . import html, markdown
from .content import Post

if TYPE_CHECKING:
    from .site import SiteContext

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


def _rss_item(post: Post, site: SiteContext) -> str:
    permalink = f"{site.base_url}/posts/{post.slug}/"
    # No <author>: site.Params.author is a plain string, not a map, so
    # rss.xml's `$authorEmail` (from `.email`) is always "" here and every
    # block gated on `{{ with $authorEmail }}` -- <managingEditor>,
    # <webMaster>, and this per-item <author> -- never fires. Confirmed
    # against real output: zero <author> tags anywhere in any RSS feed.
    return f"""    <item>
      <title>{html.esc(post.title)}</title>
      <link>{permalink}</link>
      <pubDate>{post.date.strftime(_RFC1123Z)}</pubDate>
      <guid>{permalink}</guid>
      <description>{_rss_item_description(post, site)}</description>
    </item>"""


def rss(posts: list[Post], site: SiteContext, base_path: str = "/",
        title: str | None = None) -> str:
    """One RSS 2.0 channel: `posts` newest-first, already the FULL set for
    `base_path` (a section or term's own RSS gets every one of its posts,
    never just one pagination page -- confirmed against real output:
    `/posts/index.xml` has all 176, `/tags/programming/index.xml` all 106,
    despite `PAGER_SIZE` capping the HTML listing at 100). `title` is the
    page's real display title; omitted only by the home-page caller, which
    passes `site.title` explicitly instead (see this module's docstring)."""
    if title is None:
        title = site.title
    permalink = f"{site.base_url}{base_path}"
    self_href = f"{permalink}index.xml"
    # rss.xml: `{{ (index $pages.ByLastmod.Reverse 0).Lastmod.Format ... }}`
    # -- the newest post's own date, not a build clock (confirmed
    # deterministic across two real builds seconds apart; see the task-10
    # report). `posts` is already sorted newest-first.
    last_build = posts[0].date.strftime(_RFC1123Z) if posts else ""
    items = "\n".join(_rss_item(post, site) for post in posts)
    return f"""<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{html.esc(_channel_title(title, site))}</title>
    <link>{permalink}</link>
    <description>{html.esc(_channel_description(title, site))}</description>
    <generator>Hugo -- 0.165.0</generator>
    <language>en-us</language>
    <lastBuildDate>{last_build}</lastBuildDate>
    <atom:link href="{self_href}" rel="self" type="application/rss+xml" />
{items}
  </channel>
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
