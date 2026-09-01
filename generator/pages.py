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

def _description_text(post: Post) -> str:
    """<meta name="description"> and twitter:description: Hugo interpolates
    `.Description` (a plain string) or `.Summary` (a `template.HTML` value)
    straight into a quoted attribute. Go escapes the two differently -- see
    `_head`, which picks the escaper -- so return the text only."""
    return post.description or markdown.summary(post.body)

def _og_description_text(post: Post) -> str:
    # opengraph.html: `or .Description .Summary | plainify | htmlUnescape
    # | chomp`. htmlUnescape is what makes this form differ from the raw one
    # above: the entities goldmark baked in are decoded back to real
    # characters here (and `chomp` is a trailing-newline rstrip).
    source = post.description or markdown.extract_summary(markdown.render_entities(post.body))
    return _html_std.unescape(markdown.plainify(source)).rstrip("\r\n")

def _jsonld_description_text(post: Post) -> str:
    # schema_json.html: `.Description | plainify` or `.Summary | plainify`
    # -- the same pipeline as og:description but with NO htmlUnescape and no
    # chomp, so this one keeps both the entities and any trailing newline.
    if post.description:
        return markdown.plainify(post.description)
    return markdown.summary_description(post.body)

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

    return f"""<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
<meta name="robots" content="index, follow">

<link rel="alternate" type="application/rss+xml" title="{html.esc(site.title)} RSS Feed" href="{site.base_url}/rss/index.xml">
<link rel="alternate" type="application/atom+xml" title="{html.esc(site.title)} Atom Feed" href="{site.base_url}/rss/index.xml">
<script data-goatcounter="https://poleprediction.goatcounter.com/count"
        async src="//gc.zgo.at/count.js"></script>
<title>{title}</title>
<meta name="keywords" content="{keywords}">
<meta name="description" content="{desc_attr}">
<meta name="author" content="{html.esc(site.author)}">
<link rel="canonical" href="{permalink}">
<link crossorigin="anonymous" href="{site.stylesheet_href}" integrity="{site.stylesheet_integrity}" rel="preload stylesheet" as="style">
<link rel="icon" href="{site.base_url}/favicons/favicon.ico">
<link rel="icon" type="image/png" sizes="16x16" href="{site.base_url}/favicons/favicon-16x16.png">
<link rel="icon" type="image/png" sizes="32x32" href="{site.base_url}/favicons/favicon-32x32.png">
<link rel="apple-touch-icon" href="{site.base_url}/favicons/apple-touch-icon.png">
<link rel="manifest" href="{site.base_url}/favicons/site.webmanifest">
<meta name="theme-color" content="#2e2e33">
<meta name="msapplication-TileColor" content="#2e2e33">
<link rel="alternate" hreflang="en" href="{permalink}">
<noscript>
    <style>
        #theme-toggle,
        .top-link {{
            display: none;
        }}

    </style>
    <style>
        @media (prefers-color-scheme: dark) {{
            :root {{
                --theme: rgb(29, 30, 32);
                --entry: rgb(46, 46, 51);
                --primary: rgb(218, 218, 219);
                --secondary: rgb(155, 156, 157);
                --tertiary: rgb(65, 66, 68);
                --content: rgb(196, 196, 197);
                --code-block-bg: rgb(46, 46, 51);
                --code-bg: rgb(55, 56, 62);
                --border: rgb(51, 51, 51);
            }}

            .list {{
                background: var(--theme);
            }}

            .list:not(.dark)::-webkit-scrollbar-track {{
                background: 0 0;
            }}

            .list:not(.dark)::-webkit-scrollbar-thumb {{
                border-color: var(--theme);
            }}
        }}

    </style>
</noscript><meta property="og:url" content="{permalink}">
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

def _schema_json(post: Post, site: SiteContext, permalink: str, jsonld_description: str) -> str:
    # Hugo's `.Content` carries goldmark's typographic entities, and both
    # `articleBody` (which decodes them) and `.WordCount` are computed
    # from it.
    content_html = markdown.render_entities(post.body)
    plain = markdown.plain(content_html)
    word_count = markdown.word_count(content_html)
    published_z = post.date.strftime(_ISO_Z)
    keywords = ", ".join(_js_value(t) for t in post.tags)

    breadcrumbs = f"""<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{
      "@type": "ListItem",
      "position":  1 ,
      "name": "Posts",
      "item": "{site.base_url}/posts/"
    }},
    {{
      "@type": "ListItem",
      "position":  2 ,
      "name": {_js_value(post.title)},
      "item": "{permalink}"
    }}
  ]
}}
</script>"""

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

def _signature(site: SiteContext) -> str:
    return f"""<aside class="signature" aria-label="About the author">
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

def _post_meta(post: Post, site: SiteContext) -> str:
    go_string = post.date.strftime(_GO_STRING) + " " + _go_string_zone(post)
    human = post.date.strftime(_HUMAN.format(day=post.date.day))
    # Trailing "\n\n" mirrors post_meta.html's own trailing partial calls
    # (translation_list/edit_post/post_canonical), which all render empty
    # for this corpus but still leave whitespace before "</div>".
    return (f"<span title='{go_string}'>{human}</span>"
            f"&nbsp;·&nbsp;{html.esc(site.author)}\n\n")

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
    og_description = _og_description_text(post)
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
