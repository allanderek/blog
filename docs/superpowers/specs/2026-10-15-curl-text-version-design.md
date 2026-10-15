# A terminal-readable version of the site

**Status:** design, awaiting implementation
**Date:** 2026-10-15

## Goal

Serve every page of the blog as ANSI-styled plain text, so that

    curl https://blog.poleprediction.com/posts/some-post/index.txt

renders that post legibly in a terminal. The PDF CV stays a PDF.

## Intent and constraints

The idea came from <https://nytpu.com/gemlog/2026-03-18>, where the site
detects a `curl` User-Agent and serves text instead of HTML.

**That approach is not available here.** This site is served by GitHub
Pages, which is a static file host: it cannot branch on a request header.
Confirmed by inspection — responses carry `server: GitHub.com`, DNS is at
Namecheap with `blog.poleprediction.com` a CNAME to
`allanderek.github.io`, and there is no CDN in front. The referenced
author uses Nginx.

Getting User-Agent detection would mean moving the site behind something
that can run code at the edge. That was considered and rejected: it adds a
dependency, a second place for the site to break, and a thing to pay for,
all to avoid typing five characters.

So the text version is **generated as files at build time**, one beside
each page. This keeps hosting exactly as it is. It is also a prerequisite
for User-Agent detection rather than an alternative to it: were an edge
layer ever added, it would serve these same files.

Success looks like: every page readable in a terminal, syntax
highlighting intact, links both clickable and copy-pasteable, and no way
for the text version to silently drift from the HTML one.

## Architecture

A new module, `generator/text.py`, exporting one function:

```python
def render(html: str, *, permalink: str, base_url: str) -> str
```

It takes a complete built page and returns the terminal text. It parses
with `html.parser` from the standard library — **no new dependency** — and
carries an element stack so nesting is handled uniformly rather than
case by case.

### Rendering from HTML, not from markdown

The alternative was a second rendering backend over markdown-it tokens.
Rejected for two reasons.

**Most pages are not markdown.** Only posts have a markdown source. The
home page, `/archives/`, `/posts/`, all 71 tag pages, `/tags/`, and the
CV (built from `content/cv.toml`) are generated HTML. A markdown backend
would cover 187 pages of 266 and need a bespoke path for each of the
rest.

**Embedded HTML would fail silently.** The author writes markdown, but
markdown permits raw HTML, and markdown-it hands it through as opaque
`html_block` / `html_inline` tokens. A markdown backend would meet a
`<table>` it could not interpret and either emit the tags literally or
drop the content, with nothing to signal it. Checked: with fenced code
excluded, **no post currently contains raw HTML**, so this would not
break anything today — but the failure is silent, which makes it a bad
thing to build in. Reading from HTML makes the whole category
unrepresentable, because embedded HTML *is* the input.

The inverse risk — an element the text renderer does not recognise — is
handled by failing loudly; see *Unknown elements* below.

### Hook into the build

`generator/site.py` currently repeats

```python
(page_dir / "index.html").write_text(page_html, encoding="utf-8")
```

at ten call sites. Replace those with one helper:

```python
def _write_page(out: Path, path: Path, page_html: str, site: SiteContext) -> None
```

which writes the HTML and then the `.txt` beside it. The page's permalink
is derived from its output path, which *is* its URL path:
`out/posts/foo/index.html` → `/posts/foo/` → `base_url + "/posts/foo/"`.
Mechanical and exact, with no permalink plumbing through `pages.py`.

(Every page also carries `<link rel="canonical">`, so the permalink could
be read back out of the markup instead. Deriving it from the path is
preferred: it needs no parsing and cannot be defeated by a page that
forgets the tag.)

## Scope

Every page that gets an `index.html`, **except** the `/posts/page/1/`
and `/tags/*/page/1/` alias stubs, which are redirects with no content.

A full build writes 338 `index.html` files, 72 of them stubs, so that is
**266 text files**:

| | count |
|---|---|
| posts | 187 |
| tag pages | 71 |
| paginated continuations (`page/2/` onward) | 2 |
| `/`, `/posts/`, `/tags/`, `/archives/`, `/cv/`, `/consulting/` | 6 |
| **total** | **266** |

Paginated pages from `page/2/` onward **are** included, so that the
`Next »` link works for a reader navigating by curl.

Not included: `404.html` (see *Known limitations*), feeds, the sitemap,
images, the stylesheet, the favicon, the web manifest, and `cv.pdf`.
`/cv.pdf` remains a PDF, as requested.

GitHub Pages already serves `.txt` as `text/plain; charset=utf-8`. No
configuration change is needed.

## What is rendered

`render` walks into `<main>` and renders its contents. Everything outside
is site chrome and is dropped: `<header class="header">` and its nav,
`<aside class="signature">`, `<footer class="footer">`, the back-to-top
link, and all `<script>` and `<style>` blocks.

Dropping the site footer also drops its copyright year, which is
generated from the current date — the same reason the CV PDF fingerprint
excludes it (`cv-pdf-inputs.py`).

A rendered post is therefore: title, date, body, tags, then the link
footnotes, then the pointer to the HTML version.

### Element table

This covers every element that appears inside `<main>` on any page,
inventoried from a full build. Counts are occurrences across the whole
site.

**Transparent containers** — recurse into children, no decoration, one
blank line between consecutive blocks:
`div` (1909), `header` (829), `footer` (757), `article` (754),
`nav` (4), `section` (3), `aside` (1).

**Headings**

| element | count | rendering |
|---|---|---|
| `h1` | 290 | bold, followed by a `━` rule the width of the text |
| `h2` | 841 | bold, followed by a `─` rule the width of the text |
| `h3` | 286 | bold |
| `h4` | 4 | underlined |
| `h5` | 0 | italic |
| `h6` | 0 | italic, dimmed |

Every heading gets a blank line before and after.

`h5` and `h6` appear nowhere in the corpus today and are whitelisted
deliberately: a nested heading is a reasonable thing to reach for while
writing, and it should not stop a build. They sit below `h4` on the
ladder, so the six levels stay distinguishable.

The ladder descends by weight — rule, rule, bold, underline, italic,
dim — and uses **only** attributes the reader's terminal resolves, never
a colour. An earlier draft of this spec gave `h2`, `h3` and `h4` the same
plain bold, which would have rendered three levels identically.

**Blocks**

| element | count | rendering |
|---|---|---|
| `p` | 2897 | children, then a blank line |
| `pre` | 567 | Monokai block — see *Syntax highlighting* |
| `blockquote` | 192 | children with every line prefixed `│ `, dimmed |
| `ul` / `ol` / `li` | 268 / 51 / 847 | `• ` and `1. ` markers, indented two spaces per nesting level |
| `dl` / `dt` / `dd` | 1 / 7 / 7 | `dt` bold on its own line, `dd` indented four spaces |
| `table` and friends | 12 | see *Tables* |
| `details` / `summary` | 7 / 7 | `summary` bold on its own line, remaining children indented two spaces — **always expanded**, as a terminal has no disclosure widget |

**Inline**

| element | count | rendering |
|---|---|---|
| `a` | 2085 | OSC 8 hyperlink plus `[n]` — see *Links* |
| `span` | 20926 | transparent, except inside `pre` where its colour is read |
| `code` | 2010 | cyan (inline only; inside `pre` handled by the code-block path) |
| `em` | 500 | `\x1b[3m` italic |
| `strong` | 432 | `\x1b[1m` bold |
| `del` | 2 | `\x1b[9m` strikethrough |
| `sup` | 184 | inline, undecorated, so `3<sup>rd</sup>` reads `3rd` |
| `time` | 8 | its text |
| `br` | 2 | a newline |
| `img` | 4 | `[image: ALT]` plus a footnote to the source; **`alt=""` renders nothing at all** |

One class-based exception: `sup.archive-count` holds a post count beside
a year or month heading on `/archives/`, where bare juxtaposition would
read as `2026 28`. It renders as ` (28)`.

`alt=""` is html's way of marking an image decorative -- it is why a
screen reader passes over the signature avatar -- so the text version
passes over it too, rather than announcing `[image]` and footnoting a
portrait on every page carrying one. A *missing* `alt` attribute is
different: it says nothing about the image, so the reader is told one is
there and given its url.

### No line wrapping

Text is **not** wrapped. A static file cannot know the reader's terminal
width, and the terminal already wraps. A paragraph is emitted as one long
line.

Two places still need a width, and both use a *locally* known one rather
than a guessed terminal width: code blocks pad to the longest line in
that block, and tables pad to the widest cell in each column.

### Tables

Columns are padded to the widest cell in each column. Cells are separated
by ` │ `, and a `─` rule separates `thead` from `tbody`. Twelve tables in
the corpus, all narrow; no overflow handling.

## Where `base_url` comes from

`generator/site.py:57` hardcodes

```python
base_url="https://blog.poleprediction.com"
```

in `_default_site`, and 39 call sites across the generator read
`site.base_url`.

### Development mode

This matters more for this feature than for anything built before it. A
built page already carries seven production URLs — the canonical link,
`og:url` and the JSON-LD — and that is conventional and harmless, because
those are declarations about where the page lives, not navigation.

Footnotes and the curl pointer **are** navigation. Left as-is, every
footnote on a page served from `localhost:8080` would point at the live
site: following one would silently leave the local build, and
curl-navigation — the whole point of the feature — could not be tested
locally at all.

Making same-origin footnotes root-relative would dodge this, but is not
available: **an OSC 8 hyperlink requires an absolute URL**, because the
terminal has no document base to resolve against. Clickability forces
absolute URLs, so the base URL has to be right.

**Resolution.** Add a `--base-url` option to both subcommands:

- `build` defaults to `https://blog.poleprediction.com`
- `serve` defaults to `http://localhost:<port>`, which it already knows

`check-site.sh` and both link checkers invoke `build`, so they continue
to see production URLs and are unaffected.

Accepted side effect: in `serve`, the canonical link, `og:url` and
JSON-LD also become localhost. This is harmless — dev output is never
published — and makes a local build internally consistent. The
alternative, a second `SiteContext` field for navigational URLs only, was
rejected: two base URLs in one context is a confusing thing to leave
behind for a problem this small.

### Moving the domain

Changing `site.py:57` is necessary but **not sufficient**. There is no
`CNAME` file in the repository, so the custom domain is configured in the
GitHub Pages settings for the repo, and `blog.poleprediction.com` is a
CNAME record at Namecheap pointing to `allanderek.github.io`. A move
needs all three changed together; the in-repo constant alone would
produce a site whose links all pointed at a domain that no longer served
it.

## Syntax highlighting

`generator/highlight.py` builds code blocks with Pygments'
`noclasses=True`, so the colours are **inline hex, not CSS classes**:

```html
<pre tabindex="0" style="color:#f8f8f2;background-color:#272822;...">
<code class="language-elm" data-lang="elm"><span style="display:flex;"><span><span style="color:#66d9ef">type</span> ...
```

The hex is already in the markup, so translating to ANSI truecolor is a
direct conversion:

```python
def _ansi_fg(hex6: str) -> str:
    r, g, b = (int(hex6[i:i + 2], 16) for i in (1, 3, 5))
    return f"\x1b[38;2;{r};{g};{b}m"
```

Two details:

**Nesting.** `highlight.py`'s `_wrap_lines` puts two structural spans
round every source line, and token spans sit inside them. A `</span>`
must therefore restore the *enclosing* colour, not blanket-reset. The
element stack the renderer already maintains carries the current colour,
so this is a push and a pop.

Spans are distinguished by their style attribute: `color:#xxxxxx` sets a
colour, `display:flex` is structural and sets none.

**An unlabelled fence has no inline style at all.** highlight.py emits
Hugo's bare `<pre tabindex="0"><code>` for a fence with no language,
because a block with no language must never be guessed at -- 25 blocks
in this corpus. There is therefore no colour to read, and such a block
would render as undecorated prose, indistinguishable from the paragraph
above it. It falls back to the theme's own default foreground and
background, published from highlight.py as `DEFAULT_COLOUR` and
`BACKGROUND_COLOUR` so that changing `_STYLE_NAME` moves the html and
the text together.

**The background is painted.** Monokai's default foreground is
`#f8f8f2`, near-white; without its `#272822` background, unhighlighted
code would be invisible on a light terminal. Each line of the block is
padded with spaces to the width of the longest line in that block, with
foreground and background set from the `<pre>`'s own inline style, so the
block renders as a filled rectangle. This is what makes the dark theme
safe without knowing the terminal width.

### Palette policy

Code blocks use **truecolor**, because they are deliberately reproducing
a specific palette and paint their own background, so they are
self-consistent.

Everything else — headings, inline code, blockquotes, footnote markers —
uses only **bold, dim, italic, strikethrough and the eight standard ANSI
colours**. Those are resolved by the reader's own terminal theme, so the
page stays legible on light and dark alike. No site colour is hardcoded
into prose styling.

## Links

Each `<a href>` renders as its text wrapped in an OSC 8 hyperlink,
followed by a dim `[n]`:

    \x1b]8;;URL\x1b\\link text\x1b]8;;\x1b\\[n]

Footnotes are listed under a `Links` heading at the foot of the page.
A URL repeated within a page gets one number, reused.

Three rules:

- **Footnote URLs are absolute.** `/posts/foo/index.txt` cannot be pasted
  into a terminal; the `base_url` form can.
- **Same-origin links point at the `.txt`.** `/posts/foo/` becomes
  `https://blog.poleprediction.com/posts/foo/index.txt`, so a reader can
  curl their way around the site. External links are unchanged.
- **An empty `href` is not a link.** A markdown `[words]()` whose url
  was never pasted in produces `<a href="">`, which is invisible in a
  browser (it merely re-links the current page) and can sit unnoticed in
  a post for a long time. It renders as its words, with no footnote, so
  the Links section never carries a blank entry. One such slip already
  exists in the corpus; see *Found during implementation*.
- **Dead links keep their marking.** The `dead:` scheme
  (`markdown.py`'s `DEAD_LINK_SCHEME`) emits an `<a>` with no `href`, a
  `class="dead-link"` and a title. In text these render dimmed and
  struck through with **no footnote**, since there is nothing to link to.
  Seven pages use this. If the feature did not survive into text it would
  quietly stop meaning anything there.

## The two pointers

Each version points at the other.

**In the HTML**, a line in the site footer on every page:

> This page in your terminal: `curl https://blog.poleprediction.com/posts/foo/index.txt`

A full command rather than a bare URL: copy-pasteable, and
self-explanatory to a reader who has never considered doing this. Placing
it in the footer means one implementation in `pages.py` covers the home
page and every post alike.

**In the text**, at the foot, below the `Links` section:

> Full HTML version: https://blog.poleprediction.com/posts/foo/

That url is itself an OSC 8 hyperlink, so it is clickable as well as
copy-pasteable, like every other url on the page.

### Neither pointer is inherited

The naive version of this feature is circular. If the HTML says "get the
text version at …/index.txt", and the text is rendered *from* that HTML,
then the text version inherits the line and tells the reader to fetch the
thing they are already reading.

So **each side's pointer is generated by the code that owns that side**.
`pages.py` writes the HTML-side line. `text.py` generates its own
back-pointer from `permalink` and never reads one out of the markup —
and because the HTML-side line lives in the site footer, which is outside
`<main>`, the text renderer never sees it at all.

No marker classes, no element special-casing, no circularity.

## Unknown elements

**An element inside `<main>` that is not in the table above raises at
build time.** `script`, `style` and `svg` are explicitly dropped; nothing
else is tolerated.

This is the same choice `content.py`'s `_featured_length` makes for an
unrecognised front-matter value, and for the same reason: the failure
mode it replaces is silent. Without it, adding a new element to a
template would quietly delete that content from 266 text files, and
nothing would say so. With it, the build breaks.

## Testing

### Unit tests — `tests/test_text.py`

Built entirely from **synthetic HTML fixtures**, not from real posts. Real
posts get edited, and a test that asserts a sentence or a count from one
turns an edit into a CI failure.

- one test per element in the table
- nesting: lists in lists, inline inside blocks, spans inside `pre`
- code blocks: colour translation, the nesting push/pop, background padding
- footnote numbering, and deduplication of a repeated URL
- same-origin rewriting to `.txt`; external URLs untouched
- dead links: marked, and absent from the footnotes
- the HTML back-pointer is generated, not inherited
- the six heading levels render distinguishably from one another, `h5`
  and `h6` included, even though no real page uses those two yet
- `--base-url` is honoured: footnotes, the OSC 8 targets and the
  back-pointer all use the given base, so a `serve` build's links stay
  inside the local site and never point at production
- an unknown element raises

### Build-wide invariants

These are the tests most likely to catch a real regression.

- every `index.html` has an `index.txt` beside it, except the `page/1/`
  stubs, and there are 266 of them
- no `.txt` contains an HTML entity such as `&amp;` or `&nbsp;` —
  verified to have no false positives: no code block in the corpus
  contains a literal entity in its source text
- **no `.txt` contains a leaked tag.** This assertion needed THREE
  qualifiers before it held, each found by running it:

  1. *Not inside a fenced code block.* Twelve posts legitimately show
     html in fenced code (`tailwind-critique`, `dsls`,
     `setting-up-nextcloud` among them), so their text versions really do
     contain `<div ...>`. Those lines are identified by the background
     the renderer paints behind them.
  2. *Not inside inline code.* `<usize>`, `<i32>`, `<expr>` and
     `<VirtualHost *:80>` are real inline code in real posts, and inline
     code has only a foreground colour, no background to spot it by. The
     cyan runs are cut out by their own escape sequences.
  3. *Only element names the renderer handles.* `let <def-list> in
     <expr>` is plain prose in one post -- angle brackets written as
     text, in no code markup at all. So angle brackets alone cannot be
     the signal. The pattern is built from the renderer's own element
     tables, which both excludes prose like that and extends itself to
     any element added later.

  What a leak actually looks like is `<p>` or `<span style=...>`, and the
  check was verified against those rather than assumed to work: a
  deliberately leaked tag of each shape is caught, and all six of the
  legitimate cases above pass through.
- a code block's `.txt` contains an ANSI colour sequence
- every footnote URL is absolute
- no assertion on the number of posts, and no assertion on text taken
  from a real post

### `check-site.sh` tripwires

- the HTML footer pointer is present, and names that page's own `.txt`
- the `.txt` back-pointer is present, and names that page's own HTML URL
- following a page's `.txt` back-pointer reaches that page

## Known limitations

**A missing `.txt` serves HTML.** GitHub Pages returns `404.html` for any
unknown path, so curling a `.txt` that does not exist produces a page of
HTML rather than a text error. Unavoidable on a static host; not worth
moving hosting for.

**ANSI in a browser looks like garbage.** These files carry escape
sequences, so opening one in a browser shows the sequences literally.
This is accepted: the files exist for terminals, and the HTML version is
one click away via the pointer.

**Italics vary by terminal.** `\x1b[3m` is widely but not universally
supported; where it is missing the text renders unstyled, which is
harmless.

## Out of scope

- User-Agent detection, and any change of host
- line wrapping, and any attempt to detect terminal width
- a text version of the feeds, the sitemap or `404.html`
- a plain-ASCII variant alongside the ANSI one
- Gemini or Gopher


## Found during implementation

**`content/posts/gmail-and-spam.md:21` has an empty link.** The prose
reads `A few weeks ago I [linked to]() an excellent post asking`, so the
built page carries `<a href="">`. In a browser this is invisible: it
re-links the current page and looks like ordinary text. Rendering the
page as text is what surfaced it, because it produced a numbered
footnote pointing at nothing.

The post has since been corrected, and an empty link is now a **build
failure** rather than something to be found by accident: `markdown.py`'s
`link_open` rule raises on an empty url, quoting the link's own words
(an empty url gives nothing to grep for) and naming the `dead:` scheme
as the deliberate alternative, since the two look identical in the
source. `site.build` catches it per post and prefixes
`content/posts/<slug>.md`, so the message names the file among 187.

The text renderer still treats an empty `href` as no link, so a page
built by any other route degrades gracefully rather than emitting a
blank footnote.
