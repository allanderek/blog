# Drop PaperMod, keep Hugo

## Goal

Remove the PaperMod theme submodule and own every template and stylesheet the
site renders, while keeping Hugo as the generator and producing byte-comparable
output.

## Why

Two of the three deprecation warnings raised by the Hugo 0.158 upgrade live
inside PaperMod (`.Language.LanguageCode` in `opengraph.html` and `rss.xml`).
They cannot be fixed without patching or updating someone else's theme. The
same upgrade broke the build outright via `.Site.Author`, which was ours to fix
and took minutes; the theme's share is the part with no local remedy.

The site also uses almost none of what the theme provides (see Measurements),
so the theme is mostly carrying conditionals for features that are switched
off.

This is deliberately a step that stands on its own. It is also the prerequisite
for any later move off Hugo entirely: that work needs the HTML owned locally
first, so doing this now is not wasted either way.

## Measurements

Taken 2026-08-28 against Hugo 0.165.0. These justify the scope; re-check if the
site changes substantially before this is executed.

A built post page contains **none** of: breadcrumbs, table of contents, share
icons, edit-post link, comments, cover image, post-nav links, translation list,
code-copy buttons. Only anchored headings are present.

- Theme ships 39 HTML templates and 18 CSS files (136K of source).
- The site ships **one 24K CSS bundle** and **zero JS files**.
- 119 lines of JS are inlined into every page (theme toggle, scroll-to-top).
- One shortcode is used across all content: our own `cv`. All six theme
  shortcodes are unused.
- No search page exists, so the theme's search machinery is entirely dead.
- Three markdown images exist, all affected by the theme's image render hook.
- There are **two** theme submodules. `themes/mini` is not referenced by
  `hugo.toml` and is entirely unused; it can go at the same time.

## Decisions

1. **Keep Hugo.** Only the theme is removed. No change to content, front
   matter, config semantics, or the build command.
2. **Copy the theme's CSS rather than freeze the compiled bundle.** Our own
   `layouts/partials/head.html` already contains the whole CSS pipeline
   (`resources.Get "css/core/theme-vars.css"`, `resources.Match
   "css/common/*.css"`, concat, minify, fingerprint). Copying
   `themes/papermod/assets/css` to `assets/css` keeps that pipeline working
   unchanged, now reading files we own. Freezing the minified bundle instead
   would leave an unmaintainable 24K blob.
3. **Port templates one at a time, verifying after each.** Not a single
   cut-over.
4. **Preserve current rendered output.** This is a refactor. Any visible change
   is a defect, with one accepted exception: the footer's "Powered by Hugo &
   PaperMod" credit, which becomes inaccurate once the theme is gone.
5. **Prune only what is provably unused**, and only after the port is verified
   green. Deleting unused CSS is a separate, later step.

## Templates to vendor

Originally scoped as "write seven templates from scratch". Rehearsing the
migration on 2026-08-28 showed that **copying the theme's templates verbatim
into `layouts/` produces byte-identical output**, which is strictly safer than
rewriting them, and reversible. Rewriting or simplifying them is optional
follow-up work, not part of this change.

Hugo prefers `layouts/` over `themes/*/layouts/`, so the copy can be made and
verified while the theme is still installed. `cp -rn` (no-clobber) copies the 38
theme templates we do not already have, and refuses to touch the 4 we override.

Three additional things must be carried across. Each was found by diffing the
rehearsal against a baseline, and each causes a silent visible regression if
missed:

1. **`themes/papermod/i18n/en.yaml` → `i18n/en.yaml`.** Supplies `next_page` and
   `prev_page`. Without it, pagination renders `&nbsp;&nbsp;»` with no "Next".
2. **`capitalizeListTitles = true` in `hugo.toml`,** as a top-level key. Without
   it the tags index renders `elm` rather than `Elm` for every tag. It must sit
   above the first `[table]` header; appended to the end of the file it lands
   inside `[outputs]` and is silently ignored.
3. **`layouts/_default/_markup/render-image.html`,** the image render hook,
   which adds `loading="lazy"`. Included in the `cp -rn`, but verify it by hand
   since nothing errors when it is missing.

## Prerequisite: normalise the LLMs tag

The tag is spelled `llms` in five posts and `LLMs` in one. Hugo merges them into
a single term and derives a display name in a way that changes when the theme is
removed, so the migration surfaces this as a spurious diff.

Normalise every `tags:` line to `LLMs` **before** capturing the baseline. This
keeps the URL `/tags/llms/` and the display `LLMs`, both unchanged. Normalising
the other way would display `Llms`, which is wrong for an acronym.

Only the `tags:` lines are touched; prose is left alone.

Separately, `llm` (3 posts) and `llms` (6 posts) are distinct terms with distinct
pages. Merging them is a content decision, and is out of scope here.

## Already owned

No work needed; listed so the remaining scope is clear.

`layouts/_default/baseof.html`, `layouts/partials/head.html`,
`layouts/home.html`, `layouts/index.atom.xml`,
`layouts/partials/consulting-signature.html`,
`layouts/partials/templates/schema_json.html`,
`layouts/partials/templates/twitter_cards.html`,
`layouts/shortcodes/cv.html`, `assets/css/extended/*.css`,
`assets/images/portrait.png`.

## Files changed

- Added: 38 templates copied from the theme, including the render hook.
- Added: `i18n/en.yaml`.
- Added: `assets/css/` gains `core/`, `common/`, `includes/` copied from the
  theme. `assets/css/extended/` is untouched.
- Removed: `themes/papermod` and `themes/mini` submodules, plus both
  `.gitmodules` entries.
- Changed: `hugo.toml` loses `theme = 'papermod'` and gains
  `capitalizeListTitles = true`.
- Changed: six posts, to normalise the `LLMs` tag spelling.
- Changed: `layouts/partials/head.html`, to drop the two theme partial calls
  and delete the dead search block.
- Unchanged: the four templates we already override, which `cp -rn` must not
  clobber.
- Unchanged: all content, `check-site.sh`, both link checkers, CI workflow.

## Risks

1. **The 119 lines of inlined JS.** Theme toggle (localStorage plus
   `prefers-color-scheme`) and scroll-to-top, currently emitted from the
   theme's `footer.html`. This is the most likely thing to be silently lost,
   because nothing fails if it disappears; the page just stops toggling. Carry
   it across deliberately and test the toggle by hand.
2. **The image render hook**, as above. Silent when missing.
3. **Theme-toggle CSS coupling.** The toggle sets classes the CSS keys off.
   Taking the CSS wholesale should preserve this, but it is the first thing to
   check if dark mode misbehaves.
4. **Pagination.** `/posts/page/2/` exists and is asserted by `check-site.sh`.
   The list template must keep it working, and the i18n file must be present for
   its labels.
5. **Clobbering our own overrides.** Four files exist in both trees. `cp -r`
   without `-n` would silently overwrite months of customisation, including
   `baseof.html` and `head.html`. Always `cp -rn`, and verify afterwards.

## Out of scope

- Moving off Hugo. A separate decision, informed by how this goes.
- Fixing the two remaining deprecation warnings. Once the theme's copies are
  ours, `.Language.LanguageCode` becomes fixable, but changing it here would
  confound the "output is unchanged" check. Do it immediately afterwards.
- Pruning unused CSS (`search.css`, `profile-mode.css`).
- Any redesign. Output should be indistinguishable.
- Adding a search page.

## Verification

The existing checks are the regression harness and must stay green throughout:

- `./check-site.sh` — 46 assertions against built output, including the
  signature block, feeds, pagination, and the archive.
- `./check-links-internal.sh` — 344 links, expected 0 broken.

Those assert specific facts. To catch everything else, capture a full baseline
before starting:

    direnv exec . hugo --destination /tmp/baseline

and after each step diff the built tree against it, ignoring the RSS build
timestamp, which changes on every build:

    diff -r -I '<updated>' /tmp/baseline /tmp/out

The rehearsal reached a zero-line diff, so anything non-zero is a real defect,
not noise. Expected differences by the end: the footer credit line only.

Manual checks that no script covers:

- Dark/light toggle works and persists across a reload.
- Scroll-to-top button appears and works.
- A post with images renders them with `loading="lazy"`.
- `/posts/page/2/` loads.
