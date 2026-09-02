# Hugo quirks the Python generator reproduces

This document exists because the Hugo → Python migration (branch
`python-generator`, plan `docs/superpowers/plans/2026-09-01-replace-hugo.md`)
targeted **byte-identical output**, which meant faithfully copying a number of
Hugo/Go/goldmark behaviours that nobody would have chosen if designing a
generator from scratch — some are outright bugs in Hugo's own templates or in
Go's standard library, some are Go-template escaping artifacts, and some are
just surprising. They were discovered empirically during the migration (task
reports and reviews in `.superpowers/sdd/2026-09-01-replace-hugo/`, now
scheduled for deletion) and are recorded here so the decision of what to keep
survives past that deletion.

Read this together with the code: each entry names the file and function that
implements the behaviour today.

For "Recommendation", the underlying question is always the same: now that
Hugo is no longer part of this project's toolchain, is there any reason left
to be bug-compatible with it? "Keep" means yes (URL stability, genuine user
value, or the cost of change exceeds the benefit); "stop" means no.

---

## 1. The `htmlUnescape`-before-strip content-drop bug (JSON-LD `articleBody`/`wordCount`)

**What Hugo does.** The JSON-LD `articleBody`/`wordCount` fields come from
Hugo's `.Content | safeJS | htmlUnescape | plainify` pipeline — it decodes
HTML entities **before** stripping tags. If a fenced code block contains
literal text that, once its `&lt;`/`&gt;` are decoded, looks like an HTML tag
(e.g. `<all source files>` or an Apache `<Directory ...>` config), Go's own
tag-stripper (`html/template`'s `stripTags`, which is really a `context.Context`
state machine driven by `htmlTag`/`htmlTagName`/... states) silently deletes
that text — and if a decoded fragment puts the stripper into `stateError`
(e.g. an attribute-like token containing `'`, `"`, or `<`), it stops emitting
output **entirely** for the rest of the document.

**Where we reproduce it.** `generator/markdown.py`: `plain()`, `word_count()`,
`plainify()`, `strip_tags()` are direct transcriptions of Hugo v0.165.0's Go
source (`resources/page/page_markup.go`, `tpl/template.go`), not
approximations — see the module's own comment block starting `# --- Hugo's
.Summary, .Plain and .WordCount ---`. The transcription includes the
`stateError` give-up behaviour, confirmed exact (`176/176`) against a
throwaway Hugo build that prints `.Summary`/`.Plain`/`.WordCount` directly.

**Why it is odd.** A genuine Hugo bug (or at least an unintended consequence of
reusing `html/template`'s HTML-escaping state machine for plain-text
extraction) — it silently corrupts SEO/JSON-LD metadata, invisible to a reader
because the *visible* `<pre>` block is unaffected; only `articleBody` and
`wordCount` in the `<script type="application/ld+json">` block lose text.

**Evidence.** `posts/dsls` (loses the phrase `<all source files>` from its own
`articleBody`, `wordCount` off by one); `posts/setting-up-nextcloud` (an
Apache `<Directory ...>` block puts the stripper into `stateError` and drops
most of the rest of the article from `articleBody`); `posts/tailwind-critique`
and `posts/templating` also affected. Full mechanism and the throwaway-Hugo-site
probe are in `task-6-report.md`'s fix rounds 4–5.

**Recommendation.** **Stop.** This is pure content loss with no reader-facing
benefit — it exists only because Hugo happens to reuse an escaper's error
state for plain-text extraction. Once nothing needs to diff against Hugo's
`articleBody`, extract plain text with a normal, non-lossy tag-strip (decode
entities *after* stripping tags, not before) so `dsls` and
`setting-up-nextcloud` get correct JSON-LD again.

---

## 2. JSON-LD isn't built with `encoding/json` — two different escaping strengths

**What Hugo does.** The JSON-LD `<script type="application/ld+json">` block is
built by interpolating Go template values into text, not via
`encoding/json.Marshal`. Go's `html/template` auto-detects the `<script>`
context and runs its own JS-string escaper — but at **two different
strengths** depending on whether the template source already wraps the
placeholder in literal quotes. Confirmed by a real title containing a `/`:
it comes out as `\/` in exactly one field but not others.

**Where we reproduce it.** `generator/pages.py`: two escaper flavours,
`_js_value` and `_js_string_inner`, applied depending on which JSON-LD field is
being built (see `task-6-report.md`, Step 3).

**Why it is odd.** A Go-template artifact — the templates were never written
against a real JSON serializer, so the escaping strength is whatever
`html/template`'s auto-escaper happened to infer from surrounding quote
characters, not a deliberate choice.

**Evidence.** `task-6-report.md`, Step 3 ("The JSON-LD script itself isn't
built with `encoding/json` at all"). No specific post named beyond the general
title-with-`/` and title-with-apostrophe probes.

**Recommendation.** **Stop.** Replace both escaper flavours with a single,
standard JSON string escaper (e.g. `json.dumps`-equivalent quoting) for every
JSON-LD field. There is no reason to keep two inconsistent escaping strengths
once nothing needs to match Hugo's specific auto-escaper output byte-for-byte.

---

## 3. The auto-summary truncation algorithm

**What Hugo does.** `.Summary`/`.Description`/JSON-LD `description` truncate at
~70 words (`summaryLength`, Hugo's default), but "words" are **not** prose
words — Hugo walks the *rendered HTML*, splits each `</p>`-delimited chunk on
whitespace, and counts one token per whitespace-separated piece **except**
that a token matching `^</?[A-Za-z]+>?$` (`<a`, `</em>`), a token matching
`^[A-Za-z]+=["']` (`href="...`), and the bare token `>` all count **zero**.
Two further details are load-bearing: the inner loop's final-rune case drops
the chunk's last character, and the outer loop advances by `len("</p")`, so
every chunk after the first begins on the `>` of the previous `</p>` (which
itself scores zero). On top of the word count, there's a separate rule for
*where* the cut is allowed to land: once the running total reaches 70, a
paragraph or a blockquote is a valid stopping point (stop immediately); a
heading or a fence is not (pull in exactly one more block, necessarily a
paragraph). A blockquote containing its own nested sub-blocks is walked
recursively for this purpose, not treated as one atomic unit.

**Where we reproduce it.** `generator/markdown.py`: `extract_summary()`
(the block-walking rule, `# --- Hugo's ExtractSummaryFromHTML ---`),
`plainify()`/`strip_tags()`/`plain()`/`word_count()` (the tag/attribute
zero-scoring word count). `highlight.py`'s `_wrap_lines` also matters here:
Chroma's per-line `<span style="display:flex;"><span>` wrapper is read as text
by this same word-count pipeline, so getting the highlighter's line-wrapping
markup exactly right was a precondition for getting the summary boundary
right on posts with code blocks.

**Why it is odd.** This is not a template bug so much as an algorithm nobody
would design on purpose — it counts HTML markup tokens, not words, and its
edge cases (an attribute value literally eating the next word; a link as the
very first token costing nothing because `<p><a` isn't a bare tag) only make
sense once you've read Hugo's Go source (`resources/page/page_markup.go`,
v0.165.0). Four rounds of black-box inference from rendered prose alone failed
to reconstruct it exactly; it was only nailed down by building a throwaway
Hugo site that prints `.Summary`/`.Plain`/`.WordCount` as JSON and reading the
Go source directly (`task-6-report.md`, fix round 4).

**Evidence.** Verified `176/176` exact against a throwaway-Hugo-site probe
(`task-6-report.md`, fix round 4: "summary exact: 176 / 176 bad: []"). The
specific posts that exposed each piece of the rule: `llms-and-code-reuse` and
`polymorphism-blind-spot` (crossing inside a fence → runs on),
`minor-refactorings` (initially unreconciled — needed the final HTML-token
rule, not a prose-word rule, to resolve), `clients-as-a-pitfall` (crossing
inside a blockquote → stops immediately), `needless-do-notation` (crossing
inside a nested blockquote sub-block → recursion needed),
`dynamically-typed-statically-typed-metaprogramming` (crossing inside a
heading → runs on).

**Recommendation.** **Stop.** The mechanism (counting HTML tokens with
special-cased zero-scoring rules) is far more complex than the value it
produces (an approximately-70-word summary) warrants. Keep the *intent* —
truncate long posts to a short auto-summary around a paragraph boundary — but
replace the mechanism with a plain prose-word count over the extracted text.
The exact cut point will shift slightly on some posts; that's fine once
nothing needs to match Hugo's output.

---

## 4. Goldmark typographer quirks needed for byte-exact entities

**What Hugo does.** Goldmark's typographer extension has two rules a naive
smart-quote/ellipsis implementation won't have: (a) an opening single quote
immediately followed by `t`/`e`/`n`/`l` is treated as an apostrophe
(`'twas`, `'em`, `'net`, `'love`), not an open quote; (b) an ellipsis is
**exactly three dots** — a four-dot run (`....`) keeps a trailing literal
period rather than folding into one `…` entity.

**Where we reproduce it.** `generator/markdown.py`: a second parser path
(`render_entities()`) that substitutes single-character sentinels (not
multi-character replacements — markdown-it-py's own smartquotes extension
mis-tracks offsets with a longer replacement, confirmed by "Specifically"
corrupting to "Spec'fically" corpus-wide when tried) which become the right
entities in one pass; see the module comment starting `# "'test first'" comes
out &lsquo;...&rsquo; where Hugo has`.

**Why it is odd.** Not a bug — a deliberate Goldmark typography choice — but
surprising enough that a from-scratch implementation would not reproduce it
without reading Goldmark's source (`extension/typographer.go`).

**Evidence.** Six posts use the `'twas`/`'em`/`'net`/`'love` apostrophe form
(`task-6-report.md`, fix round 4, "Five further problems this exposed"
item 2). The `....` four-dot case: one corpus instance, first found in Task 3
(`progress.md`'s Task 3 ruling) and finally resolved as goldmark's
exactly-three-dots rule in Task 6's fix round 4, item 3.

**Recommendation.** **Keep.** These are genuine typographic conveniences
(correctly distinguishing an apostrophe from an open quote, a proper ellipsis
character) that read better for any reader, independent of matching Hugo —
not compatibility cruft.

---

## 5. The heading-anchor slug algorithm (a real Hugo bug)

**What Hugo does.** Confirmed empirically with a probe post (`progress.md`,
Task 2 ruling):

```
## Detection   -> detection
## Detection   -> detection-1
## Detection 1 -> detection-1-1   (candidate already emitted, suffixed again)
## Detection   -> detection-2
## ???         -> heading
## !!!         -> heading-1
```

Hugo keeps a per-base counter (so a second `## Detection` becomes
`detection-1`, a third `detection-2`, ...) **and** re-suffixes a candidate id
that happens to collide with an id already emitted by a different heading
(so a literal `## Detection 1` heading, which would naturally slugify to
`detection-1`, gets bumped to `detection-1-1` because that string was already
taken) — and a heading whose text normalises to nothing (`## ???`, `## !!!`)
falls back to the literal string `"heading"`, itself subject to the same
counter/collision rules.

**Where we reproduce it.** `generator/slugs.py`: `Slugger.slug()`.

**Why it is odd.** A genuine Hugo bug, not a deliberate design — the original
plan for this migration supplied a simpler (wrong) slug algorithm verbatim,
and the reviewer caught the discrepancy against real Hugo output. Re-suffixing
an already-emitted candidate rather than just incrementing a counter is not
something anyone would design on purpose.

**Evidence.** The probe post transcribed above (`progress.md`, Task 2
ruling: "PLAN DEFECT — the `slugs.py` algorithm I supplied verbatim in the
plan is wrong in two ways"). Not observed to affect any heading in the current
176-post corpus (no post mixes a repeated heading with a literal numbered
one), but the collision is real and reachable.

**Recommendation.** **Keep.** Heading anchor ids are URL fragments — other
sites, search results, or bookmarks may already link to `#detection-1` on a
specific post. Changing the slug algorithm now (even to something more
sensible) risks silently breaking those existing deep links. The bug is
harmless unless a post is edited to introduce a genuine collision, at which
point it just produces a slightly odd-looking id, not a broken page.

---

## 6. `<h1>` headings get anchor ids too, not just `<h2>`–`<h6>`

**What Hugo does.** Every heading level, including a body-level `<h1>`
produced by a post's own `#` heading, gets an `id="..."` anchor — not only
`<h2>`–`<h6>`.

**Where we reproduce it.** `generator/markdown.py`'s heading-id rule (the
character class covers `h1`–`h6`).

**Why it is odd.** Easy to miss by inspection: most posts' only `<h1>` is the
post title itself (which Hugo's template sets separately, no id needed), so a
quick look at a handful of posts suggests only `h2`–`h6` ever need ids. The
original migration plan made exactly this assumption (`_HEADING =
re.compile(r"<h([2-6])>...")`) and it went unnoticed by Task 2's own corpus
check, because that check also only inspected `h2`–`h6`.

**Evidence.** `progress.md`, Task 3 ruling: "my plan's `_HEADING` ... excludes
h1, so body-level `#` headings get no id on 20 of 176 posts. Confirmed Hugo
emits `<h1 id="conclusion">`."

**Recommendation.** **Keep.** This isn't really "bug compatibility" so much as
correct behaviour — removing ids from `h1` headings would break any existing
deep link to one of those 20 posts' `h1`-level anchors for no benefit.

---

## 7. Post-meta date tooltip: zone text depends on the date's own format, not the reader's or the build machine's timezone

**What Hugo does (the trap, and the actual rule).** The `<span
title="...">` tooltip on each post's date renders Go's `time.Time` zone as
text. A **bare** date (`date: 2021-02-26`) or a `...Z`-suffixed date parses to
Go's named `UTC` location → the tooltip reads `"... +0000 UTC"`. An **explicit
numeric offset** (`...+00:00`, this corpus's only other form) parses to an
*unnamed* fixed-offset location, which Go prints by repeating the offset
instead of naming it → `"... +0000 +0000"`. The trap: this looks
timezone-dependent at first, because testing under a machine whose local zone
is `Europe/London` makes GMT (its winter name) intermittently coincide with a
UTC+0 offset — but that's an artifact of the *testing* environment, not of
Hugo's actual logic, which depends only on how the date string itself was
written, not on the build machine's `TZ` at all. (Separately, the real
production build **is** pinned via `TZ=America/Los_Angeles` in
`.github/workflows/hugo.yaml`, which was necessary to get a correct baseline
to compare against in the first place.)

**Where we reproduce it.** `generator/content.py`: `Post.date_zone_named:
bool` (set by `_date_zone_named()` from the raw date string's own format —
not from the build machine's `TZ`). `generator/pages.py`: `_go_string_zone()`,
used by `_post_meta_core()`.

**Why it is odd.** Surprising rather than a bug — it's a faithful (if
initially confusing) consequence of Go's `time.Time` distinguishing a named
`time.Location` from an unnamed fixed-offset one, and it took two fix rounds
in Task 6 to separate "depends on the date string's format" (real) from
"depends on the build machine's timezone" (a testing artifact).

**Evidence.** `progress.md`'s Task 6 TZ-correction ruling and
`task-6-report.md`'s fix rounds 1–2 (initial hardcoded-`"UTC"` bug, then the
mis-diagnosed three-form/two-form confusion, resolved by rebuilding the
baseline under `TZ=America/Los_Angeles`).

**Recommendation.** **Stop.** Both textual forms mean exactly the same
instant in UTC; the distinction conveys no information to a reader and exists
only because Go's `time.Time` happens to print named and unnamed zero-offset
locations differently. Simplify to one consistent zone label for every post.

---

## 8. RSS double-escapes a front-matter `description`, but not the auto-summary fallback

**What Hugo does.** The RSS item description template is `{{ with
.Description | html }}{{ . }}{{ else }}...{{ .Summary | html }}...{{ end
}}`. When a post has an explicit front-matter `description:`, that inner `{{
. }}` is a *second*, separate interpolation that Go's contextual auto-escaper
escapes **again** — only a pipeline ending directly in a recognised escaper
(as `.Summary | html` is, printed with no intervening `with`/reprint) is
exempted from the redundant pass. Confirmed against `underscore-type-param`
(`description: "...Elm's type parameters..."`): the RSS item reads
`Elm&amp;#39;s` (double-escaped), while that same page's own `<meta
name="description">` (one escaping pass, different template) reads
`Elm&#39;s`.

**Where we reproduce it.** `generator/feeds.py`: `_rss_item_description()` —
applies `html.esc_text` twice for the `post.description` branch, once for the
`.Summary` fallback branch.

**Why it is odd.** A Go `html/template` contextual-auto-escaping artifact:
whether a value gets escaped once or twice depends on how many template
"prints" it passes through on the way to output, not on anything about the
value itself. Two posts using different front-matter shapes for equivalent
content (`description:` vs. relying on the auto-summary) end up differently
escaped in the exact same feed.

**Evidence.** `underscore-type-param` (task-10-report.md, "RSS `<description>`
double-escapes a front-matter `description:`").

**Recommendation.** **Stop.** This is a rendering bug with no reader-facing
value — a feed reader shows a literal `&#39;` instead of an apostrophe for any
post using front-matter `description:`. Escape every RSS description exactly
once.

---

## 9. RSS absolutises internal links; Atom does not

**What Hugo does.** Every root-relative `href`/`src` inside an **RSS**
`<description>` is rewritten to a fully-qualified URL
(`href="https://blog.poleprediction.com/posts/other/"`), but the same link
inside the **Atom** feed's `<content>` is left relative
(`href="/posts/other/"`). Traced to Hugo's auto-absolutisation being keyed to
its own built-in `"rss"` output format specifically; this site's `ATOM` output
format is user-defined in `hugo.toml` and doesn't get the same treatment.

**Where we reproduce it.** `generator/feeds.py`: `rss()` calls
`_absolutize()` on description/content text; `atom()` does not.

**Why it is odd.** A Go-template/Hugo-internals artifact (built-in vs.
user-defined output format) rather than a deliberate per-format design choice
— there's no reason a feed reader consuming Atom needs relative links any
less than one consuming RSS.

**Evidence.** `task-10-report.md`, "Link absolutisation in RSS, but not Atom"
— confirmed against a real in-body link to another post, both feed forms.

**Recommendation.** **Keep the RSS absolutisation** (a feed reader has no "this
site" to resolve a relative link against — genuinely necessary, not just
Hugo-compatibility). Consider **extending it to Atom too**, since the current
asymmetry serves no purpose — this is closer to an inconsistency worth fixing
than a Hugo behaviour worth preserving.

---

## 10. Root RSS sort order: weight, then date, then case-insensitive `LinkTitle`

**What Hugo does.** The root `/index.xml` feed's item order is Hugo's actual
default page sort (`resources/page/pagesort.go`), applied to a wider page set
than "all posts" — see #12 below. The rule: sort by **weight ascending**,
except a page with **no explicit weight (literal `0`)** always sorts *after*
any page that sets a weight (not "0 is the smallest weight" — a page's weight
is compared numerically against literal `0`); pages sharing a weight sort by
**date, newest first**; pages sharing both weight and date sort by
**`LinkTitle`, ascending, case-insensitively**.

**Where we reproduce it.** `generator/feeds.py`: `_hugo_page_less()`, used by
both `rss()` (root feed) and `sitemap.xml`'s ordering.

**Why it is odd.** Not a bug — legitimate Hugo behaviour — but non-obvious:
the case-insensitive tiebreak in particular was only discovered while
building the sitemap, where same-weight/same-date ties are common (multiple
tag term pages sharing the newest post's date).

**Evidence.** `progress.md`, Task 10: `cv.md`'s `weight: 10` is the only
reason it sorts first in the root feed; `consulting.md` (weight 0 like every
post, but `.Date` zero — the oldest possible date) sorts dead last among the
weight-0 group under "newest first". Tag terms "Gren"/"Programming"/"Syntax"
(identical `pubDate`, same newest post carries all three tags) confirmed to
list in `LinkTitle` order in `/tags/index.xml`.

**Recommendation.** **Keep.** A sensible, working sort order for the feed;
nothing about it is Hugo-specific baggage worth removing.

---

## 11. The CV item's empty `<title></title>` and `pubDate` of year 0001 in the root RSS

**What Hugo does.** The root RSS feed (`/index.xml`) includes not just posts
but every `Kind: "page"` content file site-wide — `content/cv.md` and
`content/consulting.md` too (178 items total: 176 posts + these 2; see #12).
Neither `cv.md` nor `consulting.md` sets `date:` in front matter, so both get
Go's zero `time.Time` → `<pubDate>Mon, 01 Jan 0001 00:00:00 +0000</pubDate>`.
`cv.md`'s `title: ""` front matter produces a literal, empty
`<title></title>` element.

**Where we reproduce it.** `generator/feeds.py`: `_load_root_extras()` builds
these two `_RssEntry` values directly from front matter (not by rendering the
`{{< cv >}}` shortcode).

**Why it is odd.** Not a Hugo bug exactly, but a side effect no one would
choose: an RSS reader displaying "Jan 1, year 1" for an item, or an item with
no visible title at all, is confusing/broken-looking to a human reading the
feed, purely because two content files happen not to set `title`/`date` for
reasons unrelated to their RSS presence (they're meant to be rendered as
standalone pages, not read as feed items).

**Evidence.** `task-10-report.md`, "Gap 2: the rule for what the root RSS
includes" — confirmed the literal `<pubDate>Mon, 01 Jan 0001 00:00:00
+0000</pubDate>` and `<title></title>` against real Hugo output.

**Recommendation.** **Stop.** Give the CV item a real title (its own page
heading, e.g. "Curriculum Vitae") and either a sensible `pubDate` (e.g. the
site's launch date, or omit `pubDate` entirely — RSS 2.0 allows it) or drop
`pubDate` rather than emit a nonsensical year-1 date. Purely presentational,
no downside to changing it.

---

## 12. The root RSS feed includes `cv.md` and `consulting.md`, not just posts — and excludes `archives.md`

**What Hugo does.** `layouts/_default/rss.xml`'s page set is `.RegularPages`
on `.IsHome` — every `Kind: "page"` content file site-wide, filtered by
`{{- if and (ne .Layout "search") (ne .Layout "archives") }}`. That's why
`content/archives.md` (a real regular page, `layout: "archives"`) is the one
page absent from the feed despite otherwise qualifying, while `cv.md` and
`consulting.md` (no special layout) are included.

**Where we reproduce it.** `generator/feeds.py`: `rss()`'s
`include_site_pages=True` flag (root feed only — every section/term feed's
own `.Pages` is genuinely just its own posts); `_load_root_extras()`.

**Why it is odd.** Surprising rather than buggy — a `layout:` front-matter
value doing double duty as an RSS-inclusion filter is not something the
template's author likely set out to design; it's an incidental consequence of
one generic guard.

**Evidence.** `task-10-report.md`, "Gap 2" — 178 = 176 posts + `cv.md` +
`consulting.md`, confirmed by item count against real Hugo output;
`archives.md`'s absence confirmed by its `layout: "archives"` value.

**Recommendation.** **Keep**, but revisit content: whether the CV and
consulting pages genuinely belong in a blog-post RSS feed is a judgement call
independent of Hugo-compatibility — likely worth a deliberate decision rather
than defaulting to what Hugo happened to include.

---

## 13. Taxonomy (term) pages emit no JSON-LD at all

**What Hugo does.** `/tags/<slug>/` (a tag's own term page) and `/tags/` (the
terms index) get **zero** `<script type="application/ld+json">` blocks —
confirmed `grep -c application/ld+json` is `0` for both. Neither Kind
("term"/"taxonomy") satisfies `schema_json.html`'s `(or .IsPage .IsSection)`
guard. By contrast, `content/archives.md` (Kind "page", so `.IsPage` is true)
*does* get the full `BreadcrumbList` + `BlogPosting` pair.

**Where we reproduce it.** `generator/pages.py`: `_head_taxonomy()` /
`list_page(taxonomy=True)` path emits no JSON-LD; contrast with
`_schema_json`/`_schema_json_section`/`_blog_posting_json` used elsewhere.

**Why it is odd.** Almost certainly an oversight in Hugo's own template, not
a deliberate decision — `schema_json.html`'s guard was seemingly written
before term/taxonomy pages existed as a case to consider, and nothing about a
tag page makes structured data less appropriate than a section listing (which
*does* get a `BreadcrumbList`).

**Evidence.** `task-9-report.md`, "Zero JSON-LD on term/taxonomy pages" —
explicitly notes this contradicted the task dispatcher's own paraphrase
("BreadcrumbList without a BlogPosting for these"), and the implementer
trusted the real Hugo output over that paraphrase.

**Recommendation.** **Stop.** Add a `BreadcrumbList` (matching what section
pages already get) to tag/taxonomy pages — there's a clear SEO/consistency
benefit and no reason to preserve what looks like an unintentional gap in
Hugo's own templates.

---

## 14. `page/1` alias stubs emitted even for single-page listings

**What Hugo does.** Every paginated section (`/posts/`) and every tag term
page gets a `page/1/` alias stub — a minimal HTML file containing only a
`<meta http-equiv="refresh">` redirect back to the un-paginated URL — **even
when that listing has only one page** (fits entirely within `PAGER_SIZE=100`
and would never itself produce a `page/2/`). 70 such stubs exist in the real
corpus: `/posts/page/1/` plus one per tag (69 tags), regardless of how many
posts each tag has.

**Where we reproduce it.** `generator/pages.py`: `alias_stub()`.
`generator/site.py`: `_write_section()` writes it unconditionally, confirmed
by `tests/test_site.py::test_page_1_alias_stub_is_written_even_for_a_single_page_listing`.

**Why it is odd.** Not incorrect, just unconditional in a way that looks
redundant at a glance — Hugo's paginator always creates a `page/1/` alias for
consistency (so `/posts/page/1/` is never a 404 even if `/posts/page/2/`
doesn't exist), rather than only when genuine multi-page pagination exists.

**Evidence.** `task-8-report.md`, Step 1: `find /tmp/t8-hugo -path
'*/page/1/index.html' | wc -l` → 70 (`/posts/page/1/` + 69 tag stubs).

**Recommendation.** **Keep.** Cheap, harmless, and avoids a 404 for anyone
who has ever bookmarked or linked to `/tags/<tag>/page/1/` — no reason to
remove a working redirect.

---

## 15. `/tags/index.xml` and `/categories/index.xml` are feeds of *terms*, not posts

**What Hugo does.** `/tags/index.xml` looks like a normal RSS feed but its
`<item>`s are one per **tag** (title/link/pubDate/guid), not one per post —
`<description>` is always empty, and there is no post content anywhere in the
file. `/categories/index.xml` is structurally identical but has zero
`<item>`s, because no post in the corpus ever sets `categories:` — the
category taxonomy exists in the template system but is completely unused.

**Where we reproduce it.** `generator/feeds.py`: `terms_rss()`.

**Why it is odd.** Surprising rather than buggy: a feed titled and shaped like
a content feed that actually just lists term *names* is an unusual reading of
"feed" — easy to build a generator that skips it entirely, assuming (wrongly)
that `feeds.rss(posts, site)` covers every `.xml` file in the corpus.

**Evidence.** `task-10-report.md`: full `<item>` example for `/tags/index.xml`
("Gren" tag, empty `<description>`); `/categories/index.xml`'s full empty
channel is quoted in the same report.

**Recommendation.** **Stop maintaining `/categories/index.xml`/`.html`
entirely** — the category taxonomy has zero posts using it; it's pure dead
weight kept alive only because Hugo emits it unconditionally. **Keep
`/tags/index.xml`** — low value, but it's a real catalog of the site's tags
and cheap to keep serving.

---

## 16. CSS comments inside `cv.html`'s `<style>` block collapse to a single space

**What Hugo does.** `layouts/shortcodes/cv.html` (the CV page's markup,
inserted as an "opaque artifact" — never parsed as markdown) is **not**
byte-identical between its source file and Hugo's rendered `.Content` for the
CV page: every `/* ... */` CSS comment inside the one `<style>` block becomes
a single space in Hugo's real output. Confirmed by diffing a real build's
rendered `<div class="post-content">` against the source file: thirteen
comments, each replaced by exactly one space, nothing else in the 23KB
document touched.

**Where we reproduce it.** `generator/pages.py`: `strip_style_comments()`
(applied narrowly, only inside `<style>` tags) — used by `cv_page()` and by
the root RSS feed's CV item `<description>` (`generator/feeds.py`).

**Why it is odd.** A markdown/goldmark rendering side effect on what's meant
to be raw HTML passthrough — the CV shortcode's HTML apparently still runs
through some sanitization/rendering pass that strips CSS comments, which is
not documented behaviour and wouldn't be expected of "insert this HTML
verbatim."

**Evidence.** `task-11-report.md`, "A genuine discovery (not a deviation):
`<style>` comment stripping" — thirteen comments confirmed stripped in the
real 23KB rendered document.

**Recommendation.** **Stop.** There's no reader-facing or functional reason
to strip CSS comments from the CV page's own stylesheet — it only matched
Hugo's incidental rendering-pipeline side effect. Leave the comments intact;
they're harmless and can help a future maintainer reading page source.

---

## 17. Code blocks: an unlabelled fence and a *labelled-but-unknown-language* fence render structurally differently

**What Hugo does.** A fenced code block with **no** language label gets
Hugo's plain, unstyled form: `<pre tabindex="0"><code>...</code></pre>`, no
wrapper, no `class`. A fenced code block **with** a language label — even one
neither Chroma nor Pygments can lex (MoonBit, in this corpus) — gets the full
highlighted structure: `<div class="highlight">` + a styled `<pre
tabindex="0" ...>` (dark Monokai background, `tab-size`, etc.) +
`<code class="language-X" data-lang="X">`, just with the *token colouring*
missing (plain, unhighlighted text inside real `<span>`-free markup). The
distinguishing factor is only whether the fence declared a language, not
whether that language could actually be highlighted.

**Where we reproduce it.** `generator/highlight.py`: `highlight()` returns
`None` only for the true "no language" case, and returns the full wrapped
structure with unhighlighted text for "labelled, but lexer unavailable."
`generator/markdown.py`'s fence rule branches on that three-way contract.

**Why it is odd.** Not a bug, but easy to get wrong by assuming "no
highlighting" is a single case — the CSS class `div.highlight` is genuinely
styled (`assets/css/common/main.css`), so getting this wrong is a visible
regression (an unstyled code block where every other one is dark), not just a
diff artifact.

**Evidence.** `progress.md`, Task 6 ruling ("for a LABELLED code block whose
language Pygments does not know, emit Hugo's highlighted structure... with
unhighlighted text"); `posts/prog-lang-websites` (the MoonBit post) is the one
corpus example, confirmed via probe: `unlabelled block -> <pre tabindex="0">
<code>` vs. `moonbit block -> <div class="highlight"><pre styled><code
class="language-moonbit" data-lang="moonbit">`.

**Recommendation.** **Keep.** Genuinely useful, Hugo-independent behaviour —
keeps every labelled code block visually consistent (same dark background,
same structure) even when a specific language can't be coloured, which is a
better reading experience than falling back to an unstyled block.

---

## 18. Chroma's specific "monokai" hex palette, not Pygments' own

**What Hugo does.** Chroma's Monokai style uses specific hex values that
differ from Pygments 2.20's own bundled "monokai" style in several places:
`Operator`/`Keyword.Namespace`/`Name.Tag`/`Generic.Deleted`/`Generic.Prompt`
(`#f92672` vs. Pygments' `#ff4689`), `Comment`/`Generic.Subheading`
(`#75715e` vs. `#959077`), `Error`'s foreground (`#960050` vs. `#ed007e`).
Pygments also uppercases hex colours (`#F92672`) where Chroma always writes
lowercase.

**Where we reproduce it.** `generator/highlight.py`: colour substitutions
applied after Pygments' `HtmlFormatter` runs, confirmed against the entire
real corpus that none of the three Pygments-specific colours appear anywhere
in genuine Hugo output, and all three Chroma colours already do.

**Why it is odd.** Not a bug, just a fact worth writing down so a future
maintainer doesn't wonder why hardcoded hex overrides exist instead of
Pygments' built-in `style="monokai"` — the two libraries' "monokai" have
simply drifted apart over time.

**Evidence.** `task-10-report.md`, "What I fixed in highlight.py" items 1–2.

**Recommendation.** **Keep.** Purely a colour-scheme choice, independent of
Hugo — changing it now would just be a cosmetic redesign of every code block
on the site, not a Hugo-compatibility question.

---

## Deliberate deviations from Hugo

These are places the generator does **not** match Hugo, on purpose. Recorded
here for the opposite reason from the quirks above: someone may notice output
differing from an old Hugo build and wonder if something is broken. It isn't.

### The CSS bundle is unminified, so its fingerprinted filename differs

`generator/assets.py`'s `build_stylesheet()` concatenates the CSS sources in
`head.html`'s exact order (license, core group, extended group sorted) but
does **not** run Hugo's `resources.Minify` (the `tdewolff` minifier) first —
matching that minifier byte-for-byte from Python was judged impractical.
Rendered CSS is functionally identical to Hugo's (confirmed after normalising
minification artifacts, `task-11-report.md` fix round 1), just larger
(26,622 vs. Hugo's 17,900 bytes) and unminified, so its SHA-256 — and
therefore the fingerprinted filename and the `integrity` attribute on every
page's `<link>` — differs from Hugo's
(`stylesheet.9adc48ca951744ce8f6b0c8854fdd76fa8e68bfeafc106e171df63787f1e19c5.css`
vs. `stylesheet.78a811c31f5443b4286b806ccb2e9a27c09c5cd16c56a49525ae45c13cb8db90.css`).
Explicitly pre-authorised by Allan (`progress.md`'s Task 11 CSS-minification
ruling) as an accepted escape hatch. Whether to add real minification later is
a separate, optional decision, not a defect.

### The resized portrait PNG differs in bytes

`generator/assets.py`'s `resize_portrait()` uses Pillow, not Go's `image/png`
encoder (which Hugo's `.Resize` uses internally) — the two never produce
byte-identical PNGs even from the same source and target dimensions. Verified
same dimensions and colour mode (112×112, RGB) as Hugo's output; only the
compressed bytes differ (16,629 vs. Hugo's 18,608 bytes — ours is actually
smaller). Hugo's real fingerprinted filename
(`portrait_hu_6510263e774a9def.png`) is kept as a fixed target path regardless
of the deviation, since every page's `<img src>` already depends on that
literal string. Not pre-authorised in advance (unlike the CSS one); flagged to
Allan explicitly in `task-11-report.md`'s Deviations section and accepted as
the same class of difference — a different implementation's encoder producing
a visually equivalent asset.

### Accepted typographic drift: smart-quote direction, dashes, ellipsis

`compare.py`'s `_TYPOGRAPHIC` allow-list (and the `‘’“”–—…` character
normalisation next to it) treats these as equivalent between the two builds,
never reported as a difference:

- `&rsquo;`/`&lsquo;` (and the literal `’`/`‘` characters) both fold to `'`
- `&ldquo;`/`&rdquo;` (and `“`/`”`) both fold to `"`
- `&ndash;`/`&mdash;` (and `–`/`—`) fold to `--`/`---`
- `&hellip;` (and `…`) folds to `...`

This is a deliberate spec-level decision (`compare.py`'s own comment: "Only
these entities are typographic equivalences on the accepted-drift
allow-list... Everything else — crucially `&lt; &gt; &amp; &quot; &#39;` — is
structural markup/escaping and must stay untouched"), not an oversight: it
absorbs cosmetic differences between markdown-it-py's and goldmark's
typographer extensions (direction-tracking for quotes, dash-run handling) that
have no bearing on document structure or URLs. Two specific corpus cases ride
on this same allow-list rather than being individually special-cased: a
four-dot run (`....`) where goldmark keeps a trailing literal period but
markdown-it-py folds all four into `…` (both sides normalise to `...`), and an
unflanked `--` run that goldmark converts to an en-dash but markdown-it-py
leaves literal (both sides normalise to `--`) — see `progress.md`'s Task 3
ruling and `compare.py`'s own comment beside `_TYPOGRAPHIC`.

### `posts/prog-lang-websites`: one JSON-LD difference from the MoonBit lexer gap

Chroma (Hugo's highlighter) has a MoonBit lexer; Pygments (the generator's
highlighter) does not. The one fenced MoonBit block in the corpus therefore
renders with real token `<span>` boundaries in Hugo but as one contiguous
unhighlighted run in the generator (see quirk #17 above for the structural
handling of this case). That boundary difference is invisible on the page
itself (both render as plain-looking text once accepted colouring drift is
factored in) but becomes a **content** difference in the JSON-LD
`articleBody`: Hugo's `htmlUnescape`-before-strip pipeline (quirk #1) decodes
Chroma's `&lt;` span-wrapped separately from the following `</span>`'s `<`,
so they don't combine into what looks like an HTML tag; without those span
boundaries, the generator's decoded text has `&lt;Zero =&gt;` as one
contiguous run, which the tag-stripper reads as a tag and deletes. Root cause
fully proven in `task-6-report.md`'s fix round 5 (`plain(Hugo's own .Content)
== Hugo's articleBody: True`; `plain(our .Content) == Hugo's articleBody:
False`, isolated to exactly this mechanism). Closing this would require a
Pygments MoonBit lexer whose token boundaries agree with Chroma's — judged out
of scope for the migration and not attempted, to avoid a hand-fitted lexer
built only to make one file compare equal.
