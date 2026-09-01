# Replace Hugo with a Python static site generator

## Goal

Generate the site from a small Python program in this repository, and remove
Hugo from the toolchain. The blog's published output should be unchanged apart
from an agreed, written-down list of typographic differences and the contents of
syntax-highlighted code blocks.

## Why

The PaperMod removal (2026-08-28) took the theme out but left the larger
dependency in place. Hugo still supplies markdown rendering, syntax
highlighting, taxonomy and pagination logic, feeds, the asset pipeline and the
dev server — and it still imposes Go's template language, which is the thing
this blog's own post on domain specific languages argues against: a language
used too infrequently to stay fluent in, relearned from scratch each time.

The concrete cost has already been paid once. Upgrading Hugo to 0.165 broke the
build outright (`.Site.Author` removed), and left three deprecation warnings, two
of which could not be fixed locally until the theme was vendored. A generator we
own has no such upgrades.

This is the second half of a plan whose first half is complete. All 45 templates
and the whole stylesheet are already owned locally, so the remaining work is
translating them, not designing them.

## Non-goals

- No redesign. The site should look the same.
- No new features: no search, no comments, no tags beyond what exists.
- No incremental rebuild, no live reload. A full rebuild takes Hugo about 0.6s
  for 328 pages; Python will be slower but a few seconds is acceptable for a
  personal blog, and the author has explicitly said live reload is not needed.
- Not a general-purpose static site generator. It generates this site.

## Success criteria

Byte-identical output is not achievable, because syntax highlighting cannot be
reproduced exactly (see Highlighting below). Instead:

1. **Prose HTML must match exactly**, outside the accepted-drift allow-list.
2. **Accepted drift is enumerated** in `compare.py` and nowhere else. Anything
   not on that list must be a zero diff.
3. **Code-block contents are excluded** from the automated diff and reviewed by
   eye across a sample of languages before Hugo is deleted.
4. `check-site.sh` (46 checks) and `check-links-internal.sh` (347 links) pass
   against the generator's output. They assert on rendered HTML and are
   generator-agnostic, so they serve as a second, independent gate.

## Evidence: the markdown fidelity probe

Run 2026-09-01 against all 176 posts, comparing Hugo's rendered post body with
`markdown-it-py`'s, code blocks excluded. This was the one question that could
have made the project a bad idea.

**135 of 176 posts already render byte-identically.** The remaining 41 differ by
roughly 70 instances across nine causes, every one of them configuration or a
few lines of code:

| Count | Cause | Disposition |
|-------|-------|-------------|
| 46 | Smart-quote direction (`'` → `’` always, vs directional `‘…’`) | Accept as drift |
| 9 | Heading-ID slugification (Hugo keeps `_`, collapses `--` differently) | Match — affects URLs |
| 6 | Image handling | Match — port the render hook |
| 3 | `<s>` vs `<del>` for strikethrough | Match — see Decisions |
| 2 | Over-linking: `coverage.py` became a link (`.py` read as a TLD) | Match — tune linkify |
| 2 | En-dash conversion (`--` → `–`) | Accept as drift |
| 1 | A `mailto:` autolink Hugo makes | Match — tune linkify |
| 1 | Definition list (`<dl>/<dt>/<dd>`) in one post | Match — add deflist plugin |
| 1 | Ellipsis spacing | Accept as drift |

The probe is throwaway. Its category-report approach is not: `compare.py`
inherits it.

## Decisions

1. **Python**, using `markdown-it-py` and Pygments. `markdown-it-py` implements
   CommonMark+GFM, the same standard as Goldmark, which is why the probe came
   back as well as it did. Pygments is the closest analogue to Chroma and has an
   Elm lexer, which matters: 331 of the site's 517 code blocks are Elm.
2. **Plain Python functions, no template language.** Each page type is a
   function returning HTML, composed from small helpers in `html.py`. Swapping
   Go templates for Jinja templates would leave the original complaint intact.
3. **The CV is an opaque static artifact.** It is authored outside this
   repository and copied in. `pages.py` reads the HTML file and inserts it
   without parsing or templating. It is expected to be replaced later — it looks
   dated and does not work in the dark theme — and that is out of scope here.
4. **Highlighting stays inline-styled Monokai**, matching Chroma's current
   output shape, isolated behind one function in `highlight.py`. Switching to
   class-based highlighting later then touches one module and a stylesheet
   rather than the generator. Note the `.chroma` rules already in the bundled
   CSS are currently dead — nothing uses them, because Hugo emits inline styles.
5. **Match Hugo on `<del>`.** No CSS targets either element, so it is visually
   irrelevant, but it is a different element in the output, matching costs one
   line, and it keeps the diff gate tight for free. Two posts are affected.
6. **Accepted drift is limited to typography**: smart-quote direction, dashes,
   ellipsis. Nothing structural, and nothing affecting a URL, is ever accepted —
   heading IDs are matched precisely for that reason.
7. **Build in parallel, converge, then delete Hugo.** Both generators run
   throughout; Hugo is removed only once the gate is green. This is the approach
   that worked for the PaperMod migration, where continuous diffing caught three
   real defects — including one in the plan itself — that a single check at the
   end would have surfaced far too late.

## Architecture

A Python package at `generator/`. Each module has one responsibility and is
testable without the others.

| Module | Responsibility |
|--------|----------------|
| `content.py` | Discover posts, parse front matter, build `Post` objects, filter drafts and future dates |
| `slugs.py` | Hugo-compatible heading slugs, with per-document dedupe |
| `markdown.py` | The configured `markdown-it-py` instance: heading IDs, image hook, deflist, linkify tuning |
| `highlight.py` | Pygments wrapper emitting Chroma-shaped output |
| `html.py` | Escaping, attributes, element helpers — the substitute for a template language |
| `pages.py` | One function per page type, returning HTML |
| `feeds.py` | RSS and Atom |
| `assets.py` | CSS concat, minify, fingerprint; portrait resize |
| `site.py` | Orchestration: walk content, call renderers, write the output tree |
| `__main__.py` | CLI: `build`, `serve` |

Page types to cover, each currently a Hugo template: home, single post, list
(`/posts/` with pagination), taxonomy term (`/tags/<tag>/`), taxonomy index
(`/tags/`), archives, CV, consulting, 404.

Other behaviour that must be carried across, each of which is invisible until it
is missing:

- Pagination alias stubs. `hugo.toml` sets `[pagination] disableAliases =
  false`, which emits a `/page/1/` `http-equiv="refresh"` redirect for every
  paginated listing — 69 tag pages plus `/posts/`, 70 files, 17% of the output
  tree. No post uses a front-matter `aliases` key, so per-post alias support is
  NOT needed. Nothing in `check-site.sh` asserts these stubs exist, so a
  generator that omitted them would pass every existing check while breaking
  inbound links; the comparison tool is the only thing that would catch it.
- The signature block: inline on the home page, between main and footer
  elsewhere, absent on the consulting page.
- Featured posts ordered by `featuredWeight` ascending, missing weight sorting
  last.
- `loading="lazy"` on images, from the render hook.
- The theme-toggle and scroll-to-top JavaScript, inlined into every page.
- Fingerprinted CSS bundle with an `integrity` attribute.

## Verification

`compare.py`, a development tool, not part of the generator:

1. Build with Hugo into one tree, the generator into another.
2. Normalise both: exclude code-block contents, decode HTML entities, apply the
   accepted-drift allow-list.
3. Diff, and report **by category** rather than as a wall of lines.

The categorised report is what made the probe useful and is the daily working
tool. The allow-list is the specification's most important artifact: it is the
written record of what was deliberately allowed to differ, so that any new
difference is a real regression rather than something lost in noise.

`check-site.sh` and `check-links-internal.sh` run against the generator's output
as a second gate.

## Phasing

Each phase ends with the comparison tool green for what it covers.

0. Package scaffolding, `content.py`, `markdown.py`; verify rendered post bodies
   against Hugo's, reproducing the probe as a real test.
1. Single post pages, end to end.
2. Home, list with pagination, taxonomy term, taxonomy index, archives.
3. Feeds.
4. Assets: CSS bundle and fingerprint, portrait resize.
5. CV, consulting, 404, pagination alias stubs.
6. Dev server.
7. Switch over: generator writes to `public/`, Hugo removed from `devenv.nix`
   and the CI workflow, `check-site.sh` pointed at the new build.

## Risks

1. **Syntax highlighting is the largest unverified area, and it covers almost
   everything.** The probe deliberately excluded it. Of 517 code blocks, **492
   are labelled and therefore highlighted** — 331 Elm, 91 Python (80 `python`
   plus 11 `Python`), 22 shell (`bash`/`shell`), 7 diff, 7 Haskell, and four
   each of sql, make, javascript and c. Only 25 blocks are unlabelled. So 95% of
   code blocks pass through the highlighter, and Pygments' lexers will not
   tokenise identically to Chroma's. This is the most likely source of a visible
   regression and needs eyeball review across every language above, not a
   sample of one or two.
2. **Pagination and taxonomy ordering** are logic Hugo currently supplies for
   free. Ordering bugs are quiet: the page still renders, just wrongly.
   `check-site.sh` covers some of this and should be leaned on.
3. **The asset pipeline's fingerprint** must produce a stable hash across
   rebuilds, or every build churns the stylesheet URL.
4. **Reproducibility of the Python environment.** `markdown-it-py`, Pygments and
   the image library must be pinned in `devenv.nix`, not merely present on the
   system as they are today. CI installs nothing implicitly.
5. **The 25 unlabelled code blocks** must stay unhighlighted. Pygments will
   happily guess a lexer if asked to; it must not be asked.
6. **Language labels are inconsistent** — `python` appears 80 times and `Python`
   11 times. Pygments resolves lexer names case-insensitively, so this should be
   harmless, but it must be confirmed rather than assumed, since an unresolved
   name is the kind of thing that silently falls back to no highlighting.

## Out of scope

- Redesigning the CV.
- Fixing the two remaining Hugo deprecation warnings — they leave with Hugo.
- Search, comments, or any feature the site does not have today.
- Incremental builds and live reload.
- Removing the `.chroma` dead CSS rules, unless the highlighting decision is
  revisited.
