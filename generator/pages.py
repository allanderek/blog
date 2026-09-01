"""Assembles a single post page, matching Hugo/PaperMod's rendering of this
site element for element. `/tmp/target-post.html` (Hugo's own rendering of
the "dsls" post, captured with `hugo --destination /tmp/target`) is the
spec this was built against; the PaperMod-derived templates this repo keeps
under `layouts/` (read-only for this task) are the second source of truth
for anything the one captured page doesn't exercise -- front matter options
no post in this corpus actually sets (cover images, ShowToc, canonicalURL,
...) are left out rather than guessed at.
"""
from __future__ import annotations
import html as _html_std
import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from . import html, markdown
from .content import Post

if TYPE_CHECKING:
    from .site import SiteContext

# TEMPORARY: like SiteContext.stylesheet_href, this is a fingerprinted
# resources.Get(...).Resize(...) output that only assets.py (Task 11) can
# compute for real. Captured from Hugo's own build; every post uses the
# same signature image, so one constant covers all of them until then.
_SIGNATURE_AVATAR = "/images/portrait_hu_6510263e774a9def.png"

_MENU = [
    ("Archive", "/archives/"),
    ("Consulting", "/consulting/"),
    ("CV", "/cv/"),
    ("RSS Feed", "/rss/index.xml"),
]

_ISO_OFFSET = "%Y-%m-%dT%H:%M:%S+00:00"   # article:published_time / modified_time
_ISO_Z = "%Y-%m-%dT%H:%M:%SZ"             # JSON-LD datePublished / dateModified
_GO_STRING = "%Y-%m-%d %H:%M:%S +0000"    # time.Time's default String() form, zone appended separately
_HUMAN = "%B {day}, %Y"                     # PaperMod's default "January 2, 2006"

def _go_string_zone(post: Post) -> str:
    """The zone text Go's time.Time.String() appends after the numeric
    offset. A bare front-matter date or a "Z" suffix parses to Go's named
    "UTC" `time.Location`, which String()s as "+0000 UTC". An explicit
    numeric offset ("+00:00") instead produces an unnamed fixed-offset
    Location, whose String() has no name to print and just repeats the
    offset instead: "+0000 +0000". Confirmed against Hugo's own output
    built with this site's real deploy environment
    (`TZ=America/Los_Angeles`, from .github/workflows/hugo.yaml) -- LA is
    never at UTC+0 in any season, so this is deterministic, unlike
    building under this sandbox's own local zone (Europe/London), which
    intermittently resolves the same unnamed offset to "GMT" every winter."""
    return "UTC" if post.date_zone_named else "+0000"

_ANCHOR_RE = re.compile(r'(<h[1-6] id="([^"]+)".+)(</h[1-6]>)')

def _minimal_html_escape(s: str) -> str:
    """Goldmark's own text-node escaping, NOT Go html/template's wider
    attribute-context table (`html.esc`, applied separately where that's
    the real context, e.g. <meta name="description">) and NOT quotes --
    confirmed against real JSON-LD "description" fields built from a
    front-matter `description:` value (pure prose, e.g. "...for Elm's
    type parameters...", the apostrophe surviving raw) that "+" and a
    straight quote are never escaped here. A straight quote *inside a
    fenced code block* embedded in an auto-summary DOES get escaped (see
    markdown.py's `_block_html`, which escapes a fence's own content --
    the right layer for that, since it's specific to code, not to this
    whole-description pass)."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

_JS_ESCAPES = {
    "\\": "\\\\", '"': '\\"',
    "&": "\\u0026", "<": "\\u003c", ">": "\\u003e",
    "\n": "\\n", "\r": "\\r", "\t": "\\t",
}
_JS_ESCAPE_RE = re.compile("|".join(re.escape(c) for c in _JS_ESCAPES))

# The JSON-LD script isn't built with encoding/json at all: Go's
# html/template auto-detects that these `{{ }}` placeholders sit inside a
# <script type="application/ld+json"> element and runs its own JS-context
# escaper on them instead -- confirmed by "&rsquo;" coming out as
# "&rsquo;" (the literal entity text's own "&" getting the SAME &
# treatment a real JSON encoder would never apply to already-encoded text).
#
# Two distinct forms of that escaper are used, matching how each field is
# written in schema_json.html:
#   - most fields interpolate with no surrounding quotes in the template
#     source (`"headline": {{ .Title | plainify}},`) -- Go supplies the
#     quotes itself and, needing nothing more than valid JSON, does not
#     bother escaping an apostrophe or a bare "/". That's `_js_value`.
#   - exactly one field, BlogPosting's own "name", is written INSIDE
#     literal quotes already present in the template source
#     (`"name": "{{ .Title | plainify }}",`) -- Go's escaper for use
#     inside an *existing* string is more conservative, additionally
#     escaping both. Confirmed against one title containing an apostrophe
#     ("Link: python's..." -> unescaped in "headline", "\u0027" in "name")
#     and another containing "/" ("Dynamically/Statically..." -> unescaped
#     in "headline", "\/" in "name"). That's `_js_string_inner`.
def _js_string_inner(s: str) -> str:
    escaped = _JS_ESCAPE_RE.sub(lambda m: _JS_ESCAPES[m.group(0)], s)
    return escaped.replace("'", "\\u0027").replace("/", "\\/")

def _js_value(s: str) -> str:
    return '"' + _JS_ESCAPE_RE.sub(lambda m: _JS_ESCAPES[m.group(0)], s) + '"'

_TAG_WORD_START_RE = re.compile(r"(^|[ -])([a-zA-Z])")

def _tag_title(tag: str) -> str:
    """Hugo's taxonomy term title: capitalise the first letter after a
    space OR a hyphen, leave the rest untouched -- "SQLite"/"LLMs" survive,
    "dead code" becomes "Dead Code", "language-design" becomes
    "Language-Design"."""
    return _TAG_WORD_START_RE.sub(lambda m: m.group(1) + m.group(2).upper(), tag)

def _tag_slug(tag: str) -> str:
    return tag.lower().replace(" ", "-")

def _anchor_headings(content: str) -> str:
    return _ANCHOR_RE.sub(
        lambda m: f'{m.group(1)}<a hidden class="anchor" aria-hidden="true" '
                  f'href="#{m.group(2)}">#</a>{m.group(3)}',
        content,
    )

_INLINE_MD_P_RE = re.compile(r"\A<p>(.*)</p>\n?\Z", re.S)

def _render_inline_markdown(text: str) -> str:
    """A featured post's blurb (home.html: `{{ . | markdownify }}`) is
    written to sit directly inside a `<p class="home-blurb">` the template
    supplies itself, so -- unlike `markdown.render` -- a single-paragraph
    result must come back without its own wrapping `<p>...</p>`. Real
    corpus blurbs are always exactly one paragraph; nothing here handles
    more than one."""
    rendered = markdown.render(text)
    m = _INLINE_MD_P_RE.match(rendered)
    return m.group(1) if m else rendered

def _description_text(post: Post) -> str:
    """<meta name="description"> and twitter:description: Hugo interpolates
    `.Description` (a plain string) or `.Summary` (a `template.HTML` value)
    straight into a quoted attribute. Go escapes the two differently -- see
    `_head`, which picks the escaper -- so return the text only."""
    return post.description or markdown.summary(post.body)

def _og_description_text(description: str | None, body: str) -> str:
    # opengraph.html: `or .Description .Summary | plainify | htmlUnescape
    # | chomp`. htmlUnescape is what makes this form differ from the raw one
    # above: the entities goldmark baked in are decoded back to real
    # characters here (and `chomp` is a trailing-newline rstrip). Takes the
    # description/body pair directly rather than a Post so the home page
    # (whose "page" is content/_index.md, not a Post -- see
    # content.load_index_body) can share it: home has no `.Description`
    # front-matter field at all, so it always falls through to `.Summary`.
    source = description or markdown.extract_summary(markdown.render_entities(body))
    return _html_std.unescape(markdown.plainify(source)).rstrip("\r\n")

def _jsonld_description_text(post: Post) -> str:
    # schema_json.html: `.Description | plainify` or `.Summary | plainify`
    # -- the same pipeline as og:description but with NO htmlUnescape and no
    # chomp, so this one keeps both the entities and any trailing newline.
    if post.description:
        return markdown.plainify(post.description)
    return markdown.summary_description(post.body)

# The parts of <head> that carry no per-page data at all, or only site-wide
# data -- identical on every page kind this generator has built so far
# (posts and, as of this function's second caller, the home page). Split out
# so `_head` (posts) and `_head_home` can share them instead of the two
# copies silently drifting apart.
_META_TOP = """<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
<meta name="robots" content="index, follow">"""

def _feed_and_analytics(site: SiteContext) -> str:
    return f"""<link rel="alternate" type="application/rss+xml" title="{html.esc(site.title)} RSS Feed" href="{site.base_url}/rss/index.xml">
<link rel="alternate" type="application/atom+xml" title="{html.esc(site.title)} Atom Feed" href="{site.base_url}/rss/index.xml">
<script data-goatcounter="https://poleprediction.goatcounter.com/count"
        async src="//gc.zgo.at/count.js"></script>"""

def _favicons_block(site: SiteContext) -> str:
    return f"""<link rel="icon" href="{site.base_url}/favicons/favicon.ico">
<link rel="icon" type="image/png" sizes="16x16" href="{site.base_url}/favicons/favicon-16x16.png">
<link rel="icon" type="image/png" sizes="32x32" href="{site.base_url}/favicons/favicon-32x32.png">
<link rel="apple-touch-icon" href="{site.base_url}/favicons/apple-touch-icon.png">
<link rel="manifest" href="{site.base_url}/favicons/site.webmanifest">
<meta name="theme-color" content="#2e2e33">
<meta name="msapplication-TileColor" content="#2e2e33">"""

_NOSCRIPT_BLOCK = """<noscript>
    <style>
        #theme-toggle,
        .top-link {
            display: none;
        }

    </style>
    <style>
        @media (prefers-color-scheme: dark) {
            :root {
                --theme: rgb(29, 30, 32);
                --entry: rgb(46, 46, 51);
                --primary: rgb(218, 218, 219);
                --secondary: rgb(155, 156, 157);
                --tertiary: rgb(65, 66, 68);
                --content: rgb(196, 196, 197);
                --code-block-bg: rgb(46, 46, 51);
                --code-bg: rgb(55, 56, 62);
                --border: rgb(51, 51, 51);
            }

            .list {
                background: var(--theme);
            }

            .list:not(.dark)::-webkit-scrollbar-track {
                background: 0 0;
            }

            .list:not(.dark)::-webkit-scrollbar-thumb {
                border-color: var(--theme);
            }
        }

    </style>
</noscript>"""

def _head(post: Post, site: SiteContext, permalink: str, description: str,
          og_description: str, jsonld_description: str) -> str:
    title = f"{html.esc(post.title)} | {html.esc(site.title)}" if post.title else html.esc(site.title)
    keywords = ", ".join(html.esc(t) for t in post.tags)
    # `.Description` is a plain string (Go escapes "&" too); `.Summary` is
    # `template.HTML`, which Go escapes with its normalising table instead,
    # leaving goldmark's own entities intact.
    desc_attr = html.esc(description) if post.description else html.esc_norm(description)
    og_desc_attr = html.esc(og_description)
    published = post.date.strftime(_ISO_OFFSET)

    tag_metas = "\n".join(
        f'    <meta property="article:tag" content="{html.esc(_tag_title(t))}">'
        for t in post.tags[:6]
    )

    return f"""{_META_TOP}

{_feed_and_analytics(site)}
<title>{title}</title>
<meta name="keywords" content="{keywords}">
<meta name="description" content="{desc_attr}">
<meta name="author" content="{html.esc(site.author)}">
<link rel="canonical" href="{permalink}">
<link crossorigin="anonymous" href="{site.stylesheet_href}" integrity="{site.stylesheet_integrity}" rel="preload stylesheet" as="style">
{_favicons_block(site)}
<link rel="alternate" hreflang="en" href="{permalink}">
{_NOSCRIPT_BLOCK}<meta property="og:url" content="{permalink}">
  <meta property="og:site_name" content="{html.esc(site.title)}">
  <meta property="og:title" content="{html.esc(post.title)}">
  <meta property="og:description" content="{og_desc_attr}">
  <meta property="og:locale" content="en-us">
  <meta property="og:type" content="article">
    <meta property="article:section" content="posts">
    <meta property="article:published_time" content="{published}">
    <meta property="article:modified_time" content="{published}">
{tag_metas}
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{html.esc(post.title)}">
<meta name="twitter:description" content="{desc_attr}">


{_schema_json(post, site, permalink, jsonld_description)}"""

def _head_home(site: SiteContext, permalink: str, description_attr: str,
               og_description_attr: str) -> str:
    """<head> for the home page (Kind "home"): its own title/description/
    og/twitter rules (see layouts/home.html and layouts/partials/head.html,
    read-only references for this task) and an Organization JSON-LD block
    instead of a post's BreadcrumbList + BlogPosting -- see
    `_schema_json_home`. `description_attr`/`og_description_attr` arrive
    pre-escaped: unlike a post, the home page's plain <meta name="description">
    and its og:description are two genuinely different values (site-wide
    description vs. a summary of content/_index.md), each escaped once by
    its caller rather than picked between here."""
    return f"""\t<meta name="generator" content="{site.hugo_generator}">
{_META_TOP}

{_feed_and_analytics(site)}
<title>{html.esc(site.title)}</title>

<meta name="description" content="{description_attr}">
<meta name="author" content="{html.esc(site.author)}">
<link rel="canonical" href="{permalink}">
<link crossorigin="anonymous" href="{site.stylesheet_href}" integrity="{site.stylesheet_integrity}" rel="preload stylesheet" as="style">
{_favicons_block(site)}
<link rel="alternate" type="application/rss+xml" href="{site.base_url}/index.xml">
<link rel="alternate" type="application/atom+xml" href="{site.base_url}/rss/index.xml">
<link rel="alternate" hreflang="en" href="{permalink}">
{_NOSCRIPT_BLOCK}<meta property="og:url" content="{permalink}">
  <meta property="og:site_name" content="{html.esc(site.title)}">
  <meta property="og:title" content="{html.esc(site.title)}">
  <meta property="og:description" content="{og_description_attr}">
  <meta property="og:locale" content="en-us">
  <meta property="og:type" content="website">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="">
<meta name="twitter:description" content="{description_attr}">


{_schema_json_home(site)}"""

def _head_section(site: SiteContext, permalink: str, title: str, base_path: str) -> str:
    """<head> for a section's list page (Kind "section", e.g. /posts/):
    head.html's non-`.IsHome` branch (title suffixed with " | {site.Title}",
    an empty <meta name="keywords"> since a section carries no front-matter
    tags of its own, and the ".Summary | default (printf \"%s - %s\"
    .Title site.Title)" description fallback -- .Summary is always empty
    here, since no content/<section>/_index.md exists to give a section
    real body content) and opengraph.html/twitter_cards.html/schema_json.html's
    shared `.IsSection` behaviour: the site-wide description for
    og/twitter (a section has no `.Summary` to fall back to there either),
    `og:type` "website" like the home page, and a BreadcrumbList with no
    BlogPosting -- see `_schema_json_section`. Confirmed identical across
    every page of a paginated section (`/tmp/t8-hugo/posts/index.html` vs.
    `.../posts/page/2/index.html`): Hugo's paginator keeps the same
    underlying section Page for every page it renders, so nothing here
    varies with `page_num`/`total_pages`, only the caller's post list and
    pagination nav do."""
    desc_attr = html.esc(f"{title} - {site.title}")
    og_desc_attr = html.esc(site.description)
    return f"""{_META_TOP}

{_feed_and_analytics(site)}
<title>{html.esc(title)} | {html.esc(site.title)}</title>
<meta name="keywords" content="">
<meta name="description" content="{desc_attr}">
<meta name="author" content="{html.esc(site.author)}">
<link rel="canonical" href="{permalink}">
<link crossorigin="anonymous" href="{site.stylesheet_href}" integrity="{site.stylesheet_integrity}" rel="preload stylesheet" as="style">
{_favicons_block(site)}
<link rel="alternate" type="application/rss+xml" href="{site.base_url}{base_path}index.xml">
<link rel="alternate" hreflang="en" href="{permalink}">
{_NOSCRIPT_BLOCK}<meta property="og:url" content="{permalink}">
  <meta property="og:site_name" content="{html.esc(site.title)}">
  <meta property="og:title" content="{html.esc(title)}">
  <meta property="og:description" content="{og_desc_attr}">
  <meta property="og:locale" content="en-us">
  <meta property="og:type" content="website">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{html.esc(title)}">
<meta name="twitter:description" content="{og_desc_attr}">


{_schema_json_section(title, permalink)}"""

def _breadcrumb_list(items: list[tuple[str, str]]) -> str:
    """schema_json.html's `BreadcrumbList` block -- the composable piece
    shared by `_schema_json` (a post: two entries, "Posts" then the post
    itself) and `_schema_json_section` (a section list page like /posts/:
    one self-referencing entry; taxonomy pages in a later task add a
    third shape built from the same helper -- "Tags" then the term).
    `items` is (name, url) pairs in position order; `name` must already be
    a JSON-ready value (`_js_value(...)` -- see that function's docstring
    for why the BlogPosting's own "name" field needs `_js_string_inner`
    instead, a distinction no breadcrumb name needs since none is ever
    written inside pre-existing literal quotes)."""
    entries = ",\n".join(f"""    {{
      "@type": "ListItem",
      "position":  {position} ,
      "name": {name},
      "item": "{url}"
    }}""" for position, (name, url) in enumerate(items, start=1))
    return f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
{entries}
  ]
}}
</script>"""

def _schema_json(post: Post, site: SiteContext, permalink: str, jsonld_description: str) -> str:
    # Hugo's `.Content` carries goldmark's typographic entities, and both
    # `articleBody` (which decodes them) and `.WordCount` are computed
    # from it.
    content_html = markdown.render_entities(post.body)
    plain = markdown.plain(content_html)
    word_count = markdown.word_count(content_html)
    published_z = post.date.strftime(_ISO_Z)
    keywords = ", ".join(_js_value(t) for t in post.tags)

    breadcrumbs = _breadcrumb_list([
        (_js_value("Posts"), f"{site.base_url}/posts/"),
        (_js_value(post.title), permalink),
    ])

    blog_posting = f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": {_js_value(post.title)},
  "name": "{_js_string_inner(post.title)}",
  "description": {_js_value(jsonld_description)},
  "keywords": [
    {keywords}
  ],
  "articleBody": {_js_value(plain)},
  "wordCount" : "{word_count}",
  "inLanguage": "en",
  "datePublished": "{published_z}",
  "dateModified": "{published_z}",
  "author":{{
    "@type": "Person",
    "name": {_js_value(site.author)}
  }},
  "mainEntityOfPage": {{
    "@type": "WebPage",
    "@id": "{permalink}"
  }},
  "publisher": {{
    "@type": "Organization",
    "name": {_js_value(site.title)},
    "logo": {{
      "@type": "ImageObject",
      "url": "{site.base_url}/favicons/favicon.ico"
    }}
  }}
}}
</script>"""

    return breadcrumbs + "\n" + blog_posting

def _schema_json_home(site: SiteContext) -> str:
    # schema_json.html's `.IsHome` branch: an Organization, not a
    # BreadcrumbList/BlogPosting pair. Every field here sits in the
    # no-literal-quotes template position (`"name": {{ site.Title }},`), so
    # `_js_value` -- not `_js_string_inner` -- is the right escaper for all
    # of them; see that function's docstring for the distinction.
    #
    # site.Params.description is also piped through Hugo's `truncate 180`,
    # not reproduced here: this site's real description is 116 characters,
    # well under that limit, so the pipe stage is a no-op for the only value
    # it is ever applied to.
    return f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": {_js_value(site.title)},
  "url": {_js_value(site.base_url + "/")},
  "description": {_js_value(site.description)},
  "logo": {_js_value(site.base_url + "/favicons/favicon.ico")},
  "sameAs": [

  ]
}}
</script>"""

def _schema_json_section(name: str, permalink: str) -> str:
    """schema_json.html's `.IsSection` branch (`.IsSection` without
    `.IsPage`): just the `_breadcrumb_list`, no BlogPosting. `/posts/` is
    the only section this generator builds yet, and its own `$bc_list` (a
    direct child of Home) is always a single self-referencing entry --
    confirmed against `/tmp/t8-hugo/posts/index.html`'s own JSON-LD."""
    return _breadcrumb_list([(_js_value(name), permalink)])

def _theme_init_script() -> str:
    return """<script>
    if (localStorage.getItem("pref-theme") === "dark") {
        document.body.classList.add('dark');
    } else if (localStorage.getItem("pref-theme") === "light") {
        document.body.classList.remove('dark')
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        document.body.classList.add('dark');
    }

</script>"""

def _header(site: SiteContext) -> str:
    menu_items = "\n".join(
        f"""            <li>
                <a href="{site.base_url}{path}" title="{html.esc(name)}">
                    <span>{html.esc(name)}</span>
                </a>
            </li>"""
        for name, path in _MENU
    )
    return f"""<header class="header">
    <nav class="nav">
        <div class="logo">
            <a href="{site.base_url}/" accesskey="h" title="{html.esc(site.title)} (Alt + H)">{html.esc(site.title)}</a>
            <div class="logo-switches">
                <button id="theme-toggle" accesskey="t" title="(Alt + T)">
                    <svg id="moon" xmlns="http://www.w3.org/2000/svg" width="24" height="18" viewBox="0 0 24 24"
                        fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                        stroke-linejoin="round">
                        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                    </svg>
                    <svg id="sun" xmlns="http://www.w3.org/2000/svg" width="24" height="18" viewBox="0 0 24 24"
                        fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                        stroke-linejoin="round">
                        <circle cx="12" cy="12" r="5"></circle>
                        <line x1="12" y1="1" x2="12" y2="3"></line>
                        <line x1="12" y1="21" x2="12" y2="23"></line>
                        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                        <line x1="1" y1="12" x2="3" y2="12"></line>
                        <line x1="21" y1="12" x2="23" y2="12"></line>
                        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                    </svg>
                </button>
            </div>
        </div>
        <ul id="menu">
{menu_items}
        </ul>
    </nav>
</header>"""

def _footer(site: SiteContext) -> str:
    year = datetime.now(timezone.utc).year
    return f"""<footer class="footer">
        <span>&copy; {year} <a href="{site.base_url}/">{html.esc(site.title)}</a></span> ·

    <span>
        Powered by
        <a href="https://gohugo.io/" rel="noopener noreferrer" target="_blank">Hugo</a>
    </span>
</footer>
<a href="#top" aria-label="go to top" title="Go to Top (Alt + G)" class="top-link" id="top-link" accesskey="g">
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 6" fill="currentColor">
        <path d="M12 6H0l6-6z" />
    </svg>
</a>

<script>
    let menu = document.getElementById('menu')
    if (menu) {{
        menu.scrollLeft = localStorage.getItem("menu-scroll-position");
        menu.onscroll = function () {{
            localStorage.setItem("menu-scroll-position", menu.scrollLeft);
        }}
    }}

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
        anchor.addEventListener("click", function (e) {{
            e.preventDefault();
            var id = this.getAttribute("href").substr(1);
            if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {{
                document.querySelector(`[id='${{decodeURIComponent(id)}}']`).scrollIntoView({{
                    behavior: "smooth"
                }});
            }} else {{
                document.querySelector(`[id='${{decodeURIComponent(id)}}']`).scrollIntoView();
            }}
            if (id === "top") {{
                history.replaceState(null, null, " ");
            }} else {{
                history.pushState(null, null, `#${{id}}`);
            }}
        }});
    }});

</script>
<script>
    var mybutton = document.getElementById("top-link");
    window.onscroll = function () {{
        if (document.body.scrollTop > 800 || document.documentElement.scrollTop > 800) {{
            mybutton.style.visibility = "visible";
            mybutton.style.opacity = "1";
        }} else {{
            mybutton.style.visibility = "hidden";
            mybutton.style.opacity = "0";
        }}
    }};

</script>
<script>
    document.getElementById("theme-toggle").addEventListener("click", () => {{
        if (document.body.className.includes("dark")) {{
            document.body.classList.remove('dark');
            localStorage.setItem("pref-theme", 'light');
        }} else {{
            document.body.classList.add('dark');
            localStorage.setItem("pref-theme", 'dark');
        }}
    }})

</script>"""

def _signature(site: SiteContext, inline: bool = False) -> str:
    # consulting-signature.html: an extra "signature-inline" class when
    # rendered inside <main> by a layout -- only the home page does that
    # (see home_page); every post gets the default, non-inline position.
    css_class = "signature signature-inline" if inline else "signature"
    return f"""<aside class="{css_class}" aria-label="About the author">
    <img class="signature-avatar" src="{_SIGNATURE_AVATAR}" alt="" width="56" height="56">
    <div class="signature-body">
        <p class="signature-text">
            <strong>Allan Clark</strong> &mdash; I write this blog, and I&rsquo;m available for
            hire: Elm contract development, and code review of existing codebases in most languages.
        </p>
        <p class="signature-link">
            See <a href="/consulting/">consulting.</a>
        </p>
    </div>
</aside>"""

def _post_meta_core(post: Post, site: SiteContext) -> str:
    """post_meta.html's own `<span title=...>...</span>&nbsp;·&nbsp;author`
    -- shared by a post's `<div class="post-meta">` (`_post_meta`, below)
    and a list page's `<footer class="entry-footer">` (`_list_entry`),
    which uses the identical partial but without the trailing blank-line
    partial calls only the post layout leaves room for."""
    go_string = post.date.strftime(_GO_STRING) + " " + _go_string_zone(post)
    human = post.date.strftime(_HUMAN.format(day=post.date.day))
    return (f"<span title='{go_string}'>{human}</span>"
            f"&nbsp;·&nbsp;{html.esc(site.author)}")

def _post_meta(post: Post, site: SiteContext) -> str:
    # Trailing "\n\n" mirrors post_meta.html's own trailing partial calls
    # (translation_list/edit_post/post_canonical), which all render empty
    # for this corpus but still leave whitespace before "</div>".
    return _post_meta_core(post, site) + "\n\n"

def _post_tags(post: Post, site: SiteContext) -> str:
    items = "\n".join(
        f'      <li><a href="{site.base_url}/tags/{html.esc(_tag_slug(t))}/">{html.esc(_tag_title(t))}</a></li>'
        for t in post.tags
    )
    return f"""    <ul class="post-tags">
{items}
    </ul>"""

def post_page(post: Post, site: SiteContext) -> str:
    permalink = f"{site.base_url}/posts/{post.slug}/"
    description = _description_text(post)
    og_description = _og_description_text(post.description, post.body)
    jsonld_description = _jsonld_description_text(post)
    content_html = _anchor_headings(markdown.render(post.body))

    description_div = (
        f'\n    <div class="post-description">\n      {html.esc(post.description)}\n    </div>'
        if post.description else ""
    )

    header = f"""<header class="post-header">

    <h1 class="post-title entry-hint-parent">
      {html.esc(post.title)}
    </h1>{description_div}
    <div class="post-meta">{_post_meta(post, site)}</div>
  </header>"""

    article = f"""<article class="post-single">
  {header}
  <div class="post-content">{content_html}
  </div>

  <footer class="post-footer">
{_post_tags(post, site)}
  </footer>
</article>"""

    body = f"""<body class="" id="top">
{_theme_init_script()}

{_header(site)}
<main class="main">

{article}
    </main>
{_signature(site)}

{_footer(site)}
</body>"""

    return f"""<!DOCTYPE html>
<html lang="en" dir="auto">

<head>
{_head(post, site, permalink, description, og_description, jsonld_description)}
</head>

{body}

</html>
"""

def _featured_item(post: Post) -> str:
    blurb_line = (
        f'\n      <p class="home-blurb">{_render_inline_markdown(post.featured_blurb)}</p>'
        if post.featured_blurb else ""
    )
    return f"""    <li class="home-featured-item">
      <a href="/posts/{post.slug}/">{html.esc(post.title)}</a>{blurb_line}
    </li>"""

def _recent_item(post: Post) -> str:
    day = post.date.strftime("%Y-%m-%d")
    return f"""    <li class="home-recent-item">
      <time datetime="{day}">{day}</time>
      <a href="/posts/{post.slug}/">{html.esc(post.title)}</a>
    </li>"""

def home_page(site: SiteContext) -> str:
    """The home page (Kind "home"): layouts/home.html, a project override
    of PaperMod's own home layout, kept here (read-only for this task) as
    the second source of truth alongside `/tmp/target-home.html` (Hugo's
    own rendering of this site, captured with
    `TZ=America/Los_Angeles hugo --destination /tmp/target`)."""
    permalink = f"{site.base_url}/"
    intro_html = markdown.render(site.home_intro)
    # Unlike a post, the home page's <meta name="description">/twitter:description
    # and its og:description are two genuinely different values -- the raw
    # site-wide description, and a plainified/htmlUnescaped/chomped summary
    # of content/_index.md -- so each is escaped once here rather than one
    # value with two possible escapers (contrast `_head`'s desc_attr).
    description_attr = html.esc(site.description)
    og_description_attr = html.esc(_og_description_text(None, site.home_intro))

    # Start here: hand-picked posts, ranked by featuredWeight ascending. A
    # post with no featuredWeight reads as 999 (content.parse_post's own
    # default) so it sorts last. site.posts is already newest-first, and
    # Python's sort is stable, so equal weights keep that date-descending
    # order -- matching home.html's own two-step sort (rank $featured.ByDate.Reverse
    # by weight) without needing to re-sort by date here.
    featured = sorted((p for p in site.posts if p.featured), key=lambda p: p.featured_weight)
    featured_section = ""
    if featured:
        items = "\n".join(_featured_item(p) for p in featured)
        featured_section = f"""<section class="home-section" id="start-here">
  <h2>Start here</h2>
  <ul class="home-featured">
{items}
  </ul>
</section>
"""

    # Recent: the 8 newest posts. site.posts is already newest-first.
    recent = site.posts[:8]
    recent_section = ""
    if recent:
        items = "\n".join(_recent_item(p) for p in recent)
        recent_section = f"""<section class="home-section" id="recent">
  <h2>Recent</h2>
  <ul class="home-recent">
{items}
  </ul>
  <p class="home-all-posts">
    <a href="/archives/">All {len(site.posts)} posts &rarr;</a>
  </p>
</section>
"""

    main = f"""<article class="home-intro">
  {intro_html}
</article>
{_signature(site, inline=True)}

{featured_section}{recent_section}"""

    body = f"""<body class="list" id="top">
{_theme_init_script()}

{_header(site)}
<main class="main">
{main}
    </main>

{_footer(site)}
</body>"""

    return f"""<!DOCTYPE html>
<html lang="en" dir="auto">

<head>
{_head_home(site, permalink, description_attr, og_description_attr)}
</head>

{body}

</html>
"""

def _list_entry(post: Post, site: SiteContext) -> str:
    """list.html's `<article class="post-entry">` for one post in a
    listing: title, `.Summary` (list.html always reads `.Summary`
    directly -- unlike the meta `<meta name="description">` above, it
    never falls back to a front-matter `description:`), the same
    post-meta line a post page's own header uses (`_post_meta_core`), and
    the entry-level permalink."""
    summary_text, truncated = markdown.entry_summary(post.body)
    summary_html = html.esc(summary_text) + ("..." if truncated else "")
    title = html.esc(post.title)
    permalink = f"{site.base_url}/posts/{post.slug}/"
    return f"""<article class="post-entry"> 
  <header class="entry-header">
    <h2 class="entry-hint-parent">{title}
    </h2>
  </header>
  <div class="entry-content">
    <p>{summary_html}</p>
  </div>
  <footer class="entry-footer">{_post_meta_core(post, site)}</footer>
  <a class="entry-link" aria-label="post link to {title}" href="{permalink}"></a>
</article>"""

_PAGINATION_PREV = """    <a class="prev" href="{url}">
      «&nbsp;Prev&nbsp;
    </a>"""

_PAGINATION_NEXT = """    <a class="next" href="{url}">Next&nbsp;&nbsp;»
    </a>"""

def _pagination_footer(prev_url: str | None, next_url: str | None) -> str:
    """list.html's `<footer class="page-footer">` pagination nav, only
    emitted at all when `$paginator.TotalPages > 1` -- callers pass both
    URLs as None for a single-page listing, which this returns as ""."""
    if prev_url is None and next_url is None:
        return ""
    links = []
    if prev_url is not None:
        links.append(_PAGINATION_PREV.format(url=prev_url))
    if next_url is not None:
        links.append(_PAGINATION_NEXT.format(url=next_url))
    nav = "\n".join(links)
    return f"""<footer class="page-footer">
  <nav class="pagination">
{nav}
  </nav>
</footer>"""

def _list_title(base_path: str) -> str:
    """The list page's own auto Title (list.html's <h1>, and the source
    for "<title>Title | site.Title</title>"/the description fallback/
    og:title/twitter:title in `_head_section`) -- for a section with no
    content/<section>/_index.md, Hugo's default section Title is simply
    the capitalised section name. `/posts/` is the only section this
    generator builds yet."""
    return base_path.strip("/").rsplit("/", 1)[-1].capitalize()

def list_page(posts: list[Post], page_num: int, total_pages: int, base_path: str,
              site: SiteContext) -> str:
    """.../_default/list.html for one page of a paginated section listing
    (Kind "section", e.g. /posts/ and /posts/page/2/). `base_path` is the
    section's own bare, absolute-from-root path ("/posts/"); `posts` is
    already the slice this particular page renders (`pagerSize`-many,
    newest-first); `page_num`/`total_pages` drive only the prev/next
    pagination nav -- see `_head_section`'s docstring for why nothing else
    in <head> varies by page number."""
    permalink = f"{site.base_url}{base_path}"
    title = _list_title(base_path)

    entries = "\n\n".join(_list_entry(post, site) for post in posts)
    prev_url = (permalink if page_num == 2
                else f"{site.base_url}{base_path}page/{page_num - 1}/" if page_num > 2
                else None)
    next_url = (f"{site.base_url}{base_path}page/{page_num + 1}/"
                if page_num < total_pages else None)
    pagination = _pagination_footer(prev_url, next_url) if total_pages > 1 else ""

    main = f"""<header class="page-header">
  <h1>
    {title}
  </h1>
</header>

{entries}""" + (f"\n{pagination}" if pagination else "")

    body = f"""<body class="list" id="top">
{_theme_init_script()}

{_header(site)}
<main class="main"> 
{main}
    </main>
{_signature(site)}

{_footer(site)}
</body>"""

    return f"""<!DOCTYPE html>
<html lang="en" dir="auto">

<head>
{_head_section(site, permalink, title, base_path)}
</head>

{body}

</html>
"""

def alias_stub(target_url: str, site: SiteContext) -> str:
    """A `disableAliases = false` pagination alias: Hugo's own built-in
    alias template, emitted for every paginated listing's implicit
    "/page/1/" URL, redirecting it to the listing's own bare URL.
    `target_url` is that bare, absolute-from-root path (e.g. "/posts/");
    the stub's <title>/canonical/refresh all repeat the absolute URL it
    redirects to -- captured verbatim from `/tmp/t8-hugo/posts/page/1/index.html`."""
    absolute = f"{site.base_url}{target_url}"
    return f"""<!DOCTYPE html>
<html lang="en-us">
\t<head>
\t\t<title>{absolute}</title>
\t\t<link rel="canonical" href="{absolute}">
\t\t<meta charset="utf-8">
\t\t<meta http-equiv="refresh" content="0; url={absolute}">
\t</head>
</html>
"""
