# Home page redesign

Date: 2026-08-12
Status: approved design, not yet implemented

## Goal

Replace the current home page — a bare paginated list of all 169 posts — with a
landing page that introduces Allan, points readers at his best writing, and
still gets them to the full archive in one click.

## Decisions

| Question | Decision |
|---|---|
| Home page shape | Hand-built landing page: intro, "Start here", "Recent", archive link |
| Full post list | `/archives/` only (PaperMod's year-grouped layout). `/posts/` still generated, not linked in the nav |
| How "best posts" are chosen | `featured: true` in post front matter, with `featuredBlurb` and `featuredWeight` |
| Featured ordering | `featuredWeight` ascending; posts without a weight sort after those with one, by date descending |
| Intro purpose | Context for readers, plus an explicit availability line and a visible CV link |
| Availability wording | Placeholder for now; Allan is available for consulting and the right permanent roles |
| Links in intro | GitHub (`github.com/allanderek`), email (`allan.clark@gmail.com`), CV (`/cv.pdf`), RSS (`/rss/index.xml`), Pole Prediction (`poleprediction.com`), football-analysis (`allanderek.github.io/football-analysis`) |
| Social links | None. The CV lists no Mastodon/Bluesky/X account, and none were supplied |
| Intro prose lives in | `content/_index.md` as markdown, so it can be edited without touching templates |

## Prerequisite: local production builds fail

This is pre-existing and unrelated to the redesign. Nothing Allan currently does
hits it, but it blocks verification of this work, so it is fixed here.

`themes/papermod` (v8.0-15-ga020be2, Feb 2025) calls two partials by a
`partials/`-prefixed name:

- `layouts/partials/templates/twitter_cards.html:9`
- `layouts/partials/templates/schema_json.html:88`

Both do `partial "partials/templates/_funcs/get-page-images"`. Hugo removed the
double lookup that made this resolve in 0.146.0.

`layouts/partials/head.html` invokes both templates only inside
`{{- if hugo.IsProduction | or (eq site.Params.env "production") }}`, so the
failure appears only in production builds. Measured:

| Command | Hugo | Environment | Result |
|---|---|---|---|
| `./debug.sh` (`hugo server`) | 0.146.7 | development | exit 0, 0 errors |
| `hugo` | 0.146.7 | production | **exit 1, 4 errors** |
| GitHub Actions | 0.139.0 | production | exit 0 (0.139 still double-looks-up) |

So the deployed site is fine and the dev server is fine. Two reasons to fix it
anyway: verifying this work requires inspecting `public/index.html` from a
production build, and raising `HUGO_VERSION` past 0.146 in CI would break the
deploy with no warning.

### Fix

Vendor the two partials into the project with the prefix removed. This is the
same pattern the repo already uses for `layouts/partials/head.html`, works under
both 0.139.0 and 0.146.7, and touches neither the submodule nor CI.

```
layouts/partials/templates/twitter_cards.html   # copy of theme file, prefix removed
layouts/partials/templates/schema_json.html     # copy of theme file, prefix removed
```

Verified: with these two files in place, `hugo` completes with exit 0 and a full
build.

### Explicitly not done here

Updating the PaperMod submodule, or aligning the CI and devenv Hugo versions, is
the proper long-term fix but is a separate decision with its own risk (a newer
PaperMod may require a newer Hugo than CI pins). Left alone deliberately.

## Files changed

| File | Change |
|---|---|
| `layouts/home.html` | **new** — the home page layout |
| `layouts/partials/templates/twitter_cards.html` | **new** — build fix, see above |
| `layouts/partials/templates/schema_json.html` | **new** — build fix, see above |
| `content/_index.md` | **new** — intro prose and links |
| `content/archives.md` | **new** — three lines of front matter, enables `/archives/` |
| `assets/css/extended/home.css` | **new** — styles the new sections |
| `hugo.toml` | add `[params]`, move `mainSections` into it, add archive menu entry |
| 10 post files | add `featured` / `featuredBlurb` / `featuredWeight` |
| `layouts/_defaults/` | **delete** — empty directory, misspelled (`_defaults` vs `_default`), does nothing |

## Page structure

```
┌────────────────────────────────────────────┐
│ Allanderek's blog     archive · cv · rss   │  PaperMod header, unchanged
├────────────────────────────────────────────┤
│ Allan Clark                                │  ─┐
│                                            │   │ content/_index.md
│ I'm a programmer in Edinburgh. PhD on…     │   │ (markdown, freely editable)
│ Co-founded Pakk Software 2019–2025.        │   │
│ AVAILABILITY PLACEHOLDER                   │  ─┘
│                                            │
│ GitHub · Email · CV (PDF) · RSS            │  ─┐ links
│ Pole Prediction · Football analysis        │  ─┘
├────────────────────────────────────────────┤
│ Start here                                 │  featured posts by
│  Ladybird overtakes Servo: Why?            │  featuredWeight, blurb
│    A C++ browser engine is outpacing a     │  under each. Section
│    Rust one…                               │  omitted if none.
│  …                                         │
├────────────────────────────────────────────┤
│ Recent                                     │  latest 8, date + title
│  2026-08-10  Link: Danluu.pl…              │
│  …                                         │
│                    All 169 posts →         │  → /archives/
└────────────────────────────────────────────┘
```

## Template behaviour

`layouts/home.html` defines `main` (PaperMod's `baseof.html` expects that block).
Hugo 0.146.7 resolves `layouts/home.html` for the home page's HTML output.

1. Render `.Content` from `content/_index.md`.
2. **Start here**: `where site.RegularPages "Params.featured" true`, sorted by
   `featuredWeight` ascending then `Date` descending. A post with no
   `featuredWeight` sorts as if it were `999`, so it lands after the weighted
   ones; use `default 999` when reading the value rather than relying on how
   Hugo orders a missing key. Each entry is a linked title plus `featuredBlurb`
   if present. The whole section is omitted when the collection is empty.
3. **Recent**: `where site.RegularPages "Type" "in" site.Params.mainSections`,
   `first 8`. Date and linked title only, no summaries.
4. Archive link to `/archives/`. Its label carries a live count — the "169" is
   computed from the page collection, not hardcoded, so it stays correct as
   posts are added.

Use `site.Params.mainSections`, matching the theme. This resolves correctly
today via Hugo's auto-detection; moving the key under `[params]` in `hugo.toml`
makes it explicit rather than incidental.

## Featured posts

Ten posts, `featuredWeight` 10–100 (gaps of 10, so posts can be inserted later
without renumbering).

| Weight | Post | Blurb |
|---|---|---|
| 10 | `ladybird-and-strong-static-typing` | A C++ browser engine is outpacing a Rust one. I believe stronger guarantees make you more productive — so I listed ten ways to explain this away, and talked myself out of all of them. |
| 20 | `small-functions-and-elm` | Function length is the wrong proxy for the thing we actually want. And no, I'm not going to give you a rule to replace it. |
| 30 | `weak-typing` | I think weakly typed languages are useless. So I spent a post trying to build the best case for one. |
| 40 | `dynamically-typed-statically-typed-metaprogramming` | Why you can write a generic admin panel in Python and not in Elm — explained down at the level of what's actually in memory. |
| 50 | `time-extra-posix-to-parts-great-laxy-example` | What laziness is actually for — and it isn't efficiency or infinite lists. |
| 60 | `stacks-and-laziness` | The follow-up where laziness loses: space leaks that grow with the number of operations, not the size of your data. |
| 70 | `structural-custom-types` | Extensible union types are the wrong framing. The real question is structural versus nominal — and answering it gets you opaque types for records and primitives too. |
| 80 | `scoring-orders` | Our F1 prediction scoring let a randomly-generated guess beat a nearly-correct one. Here's the system I built to fix it. |
| 90 | `legal-standing-proposal-standing` | Before proposing a feature, show standing: real code that is harmed, not a hypothetical. |
| 100 | `mo-gawdat-diary-of-a-ceo` | A careful, quote-by-quote look at what happens when "by definition" and "as a matter of fact" are doing all the argumentative work. |

Front matter added to each, e.g.:

```yaml
featured: true
featuredWeight: 10
featuredBlurb: "A C++ browser engine is outpacing a Rust one. …"
```

Runners-up considered and left out, recorded so the decision isn't relitigated:
`prog-lang-websites`, `dynamically-typed-languages-why`, `foldl-and-foldr`,
`splitting-up-update`, `immutabilit-bugs`, `where-is-all-the-shovelware`.

## Out of scope

- **Tag-case inconsistency.** 68 posts tag `elm`, 6 tag `Elm`, producing two tag
  pages. Worth fixing, but the home page does not display tags, so it is not
  part of this work.
- **`.Site.Author` in `layouts/index.atom.xml`.** The feed's author element reads
  the deprecated `[author]` config table, not `[params] author`, so it will keep
  falling back to the site title even after `[params] author` is added. A
  one-line fix, but in a file this work does not otherwise touch.
- Search, comments, or any other PaperMod feature not named above.
- Updating the theme submodule or the CI Hugo version (see above).

## Verification

1. `hugo` exits 0 with no `ERROR` lines. Run the production build, not the dev
   server: `hugo server` skips the production-only templates and so proves less.
   Check Hugo's own exit status — do not pipe it through another command and
   read that one's status.
2. `public/index.html` contains: the intro text, all ten featured titles, all
   ten blurbs, and a link to `/archives/`.
3. `public/archives/index.html` exists and lists all 169 posts.
4. `public/index.xml` and `public/rss/index.xml` still generate, with the same
   entries as a pre-change build. Compare ignoring the top-level `<updated>`
   element, which contains `now` and therefore differs on every build.
5. `/posts/` still builds and paginates.
6. Home page renders sensibly at mobile width.
