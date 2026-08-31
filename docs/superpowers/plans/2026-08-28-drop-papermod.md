# Drop PaperMod Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the PaperMod theme submodule so the site owns every template and
stylesheet it renders, with byte-identical output.

**Architecture:** Copy the theme's templates, CSS and i18n into the site first,
where Hugo's lookup order makes them shadow the theme harmlessly. Only then
detach from the theme and delete it. Every step is verified by diffing the built
site against a baseline captured before any change.

**Tech Stack:** Hugo 0.165.0 (extended), bash. No test framework; the existing
`check-site.sh`, `check-links-internal.sh`, and a full output diff are the tests.

**Spec:** `docs/superpowers/specs/2026-08-28-drop-papermod-design.md`

## Global Constraints

- **Do not run `git commit`.** Allan commits his own work. End each task by
  reporting what changed and stopping. Suggested commit messages are given for
  him to use.
- **Output must not change.** The only accepted difference is the footer credit
  (Task 6). Any other diff is a defect: stop and explain it rather than
  accepting it.
- The baseline diff must always ignore the RSS build timestamp, which changes
  every build: use `diff -r -I '<updated>'`.
- Run every `hugo` command through `direnv exec .` so the devenv Hugo (0.165.0)
  is used, not whatever is on the ambient PATH.
- Never overwrite an existing file in `layouts/`. Four files exist in both
  `layouts/` and the theme, and ours must win: `_default/baseof.html`,
  `partials/head.html`, `partials/templates/schema_json.html`,
  `partials/templates/twitter_cards.html`. `cp -rn` (no-clobber) enforces this.

## File Structure

- `layouts/` — gains 38 templates copied from the theme. Already holds 8 of ours.
- `assets/css/` — gains `core/`, `common/`, `includes/` from the theme.
  `assets/css/extended/` (ours) is untouched.
- `i18n/en.yaml` — new. Supplies the pagination labels.
- `hugo.toml` — loses `theme`, gains `capitalizeListTitles`.
- `themes/` — deleted entirely, along with both `.gitmodules` entries.

## Why these three non-obvious steps exist

All three were found by rehearsing this migration and diffing the output. Do not
skip them; each causes a silent, visible regression.

1. **`i18n/en.yaml` must be copied.** Without it, pagination renders
   `&nbsp;&nbsp;»` instead of `Next&nbsp;&nbsp;»`. The theme supplies the
   `next_page`/`prev_page` strings.
2. **`capitalizeListTitles = true` must be set explicitly.** Without it the tags
   index renders `elm` instead of `Elm` for every tag.
3. **The `LLMs` tag must be normalised first.** The tag is spelled `llms` in five
   posts and `LLMs` in one. Hugo merges them into one term and picks a display
   name in a way that changes when the theme is removed. Normalising to `LLMs`
   everywhere keeps the URL `/tags/llms/` and the display `LLMs`.

---

### Task 1: Capture the baseline and normalise the tag

**Files:**
- Modify: `content/posts/empire-ai-water-usage.md`, `content/posts/llms-and-code-reuse.md`, `content/posts/llms-and-files-as-modules.md`, and any other post whose `tags:` line contains lowercase `llms`

**Interfaces:**
- Produces: `/tmp/baseline` — the reference build every later task diffs against. Do not delete it until the plan is finished.

- [ ] **Step 1: Confirm the tree is clean before starting**

```bash
git status --short
```

Expected: no modified tracked files. If there are any, stop and ask Allan — the
diff-based verification needs a known starting point.

- [ ] **Step 2: Normalise the tag spelling to `LLMs`**

Only the `tags:` line is touched, so prose mentioning "llms" is left alone.

```bash
sed -i -E 's/(^tags:.*)\bllms\b/\1LLMs/' content/posts/*.md
grep -h '^tags:' content/posts/*.md | grep -i llms
```

Expected: every printed line spells it `LLMs`, none lowercase.

- [ ] **Step 3: Verify the tag URL and display are unchanged**

```bash
rm -rf /tmp/tagcheck && direnv exec . hugo --destination /tmp/tagcheck >/dev/null
grep -o 'tags/llms/">[^<]*' /tmp/tagcheck/tags/index.html | head -1
```

Expected exactly: `tags/llms/">LLMs`

The URL must still be `/tags/llms/`. If it changed, the tag pages moved and
inbound links break — stop.

- [ ] **Step 4: Capture the baseline**

```bash
rm -rf /tmp/baseline && direnv exec . hugo --destination /tmp/baseline
find /tmp/baseline -type f | wc -l
```

Expected: 410 files, no ERROR lines. Three deprecation WARNs are expected and
unrelated.

- [ ] **Step 5: Confirm the existing checks pass**

```bash
./check-site.sh; ./check-links-internal.sh
```

Expected: `46 checks: 46 passed, 0 failed` and `0 broken`.

- [ ] **Step 6: Stop for review**

Suggested message: `content: normalise the LLMs tag spelling`

---

### Task 2: Copy the theme's templates, CSS and i18n into the site

Hugo prefers `layouts/` over `themes/*/layouts/`, so after this task the site
renders entirely from its own files while the theme is still present. That makes
this step reversible and independently verifiable.

**Files:**
- Create: 38 files under `layouts/`
- Create: `assets/css/core/`, `assets/css/common/`, `assets/css/includes/`
- Create: `i18n/en.yaml`

**Interfaces:**
- Consumes: `/tmp/baseline` from Task 1
- Produces: a `layouts/` tree that renders the site without the theme's `layouts/`

- [ ] **Step 1: Copy templates, refusing to clobber ours**

```bash
cp -rn themes/papermod/layouts/. layouts/
```

- [ ] **Step 2: Verify our four overrides survived**

```bash
for f in _default/baseof.html partials/head.html \
         partials/templates/schema_json.html partials/templates/twitter_cards.html; do
  if diff -q "layouts/$f" "themes/papermod/layouts/$f" >/dev/null 2>&1; then
    echo "CLOBBERED: $f"
  else
    echo "ours intact: $f"
  fi
done
```

Expected: all four report `ours intact`. If any says `CLOBBERED`, restore it with
`git checkout -- layouts/<file>` and re-run using `cp -rn`.

- [ ] **Step 3: Copy the CSS and i18n**

```bash
cp -rn themes/papermod/assets/css assets/
mkdir -p i18n && cp themes/papermod/i18n/en.yaml i18n/
ls assets/css/
```

Expected: `common  core  extended  includes`.

- [ ] **Step 4: Rebuild and diff against the baseline**

```bash
rm -rf /tmp/out && direnv exec . hugo --destination /tmp/out
diff -r -I '<updated>' /tmp/baseline /tmp/out | head -20
diff -r -I '<updated>' /tmp/baseline /tmp/out | wc -l
```

Expected: `0`. Anything else means a file was missed or clobbered — investigate
before continuing.

- [ ] **Step 5: Stop for review**

Suggested message: `layouts: vendor PaperMod templates, css and i18n`

---

### Task 3: Delete the dead search block from head.html

**Files:**
- Modify: `layouts/partials/head.html` (the `{{- /* Search */}}` block)

- [ ] **Step 1: Confirm the block is genuinely dead**

```bash
grep -rn 'layout.*search' content/ || echo "no page uses layout: search"
```

Expected: `no page uses layout: search`. The block is guarded by
`{{- if (eq .Layout `search`) -}}`, so it never executes — which is why the site
ships no JS despite the block referencing three JS files.

- [ ] **Step 2: Delete the block**

```bash
python3 - <<'PY'
import pathlib
p = pathlib.Path("layouts/partials/head.html")
s = p.read_text()
start = s.index("{{- /* Search */}}")
end = s.index("{{- end -}}", s.index("{{- if (eq .Layout `search`)")) + len("{{- end -}}")
p.write_text(s[:start] + s[end:])
print("removed", end - start, "characters")
PY
```

- [ ] **Step 3: Verify no JS references remain**

```bash
grep -n 'js/' layouts/partials/head.html || echo "no js references left"
```

Expected: `no js references left`.

- [ ] **Step 4: Rebuild and diff**

```bash
rm -rf /tmp/out && direnv exec . hugo --destination /tmp/out
diff -r -I '<updated>' /tmp/baseline /tmp/out | wc -l
```

Expected: `0`.

- [ ] **Step 5: Stop for review**

Suggested message: `head: drop the dead search block`

---

### Task 4: Detach the site from the theme

The theme directory stays on disk here, so this step isolates the config change
from the deletion. If the diff breaks, the cause is unambiguous.

**Files:**
- Modify: `hugo.toml`

- [ ] **Step 1: Remove the theme setting and add the list-title setting**

`capitalizeListTitles` must be a top-level key. Inserting at line 2 keeps it
above the first `[table]` header; appending to the end of the file would place it
inside `[outputs]`, where it is silently ignored.

```bash
sed -i "/^theme = /d" hugo.toml
sed -i "2i capitalizeListTitles = true" hugo.toml
head -4 hugo.toml
```

Expected: `capitalizeListTitles = true` on line 2, and no `theme =` line
anywhere.

- [ ] **Step 2: Rebuild and diff**

```bash
rm -rf /tmp/out && direnv exec . hugo --destination /tmp/out
diff -r -I '<updated>' /tmp/baseline /tmp/out | wc -l
```

Expected: `0`.

If the tags index shows `elm` instead of `Elm`, `capitalizeListTitles` landed in
the wrong place — check it is on line 2, not inside a table.

- [ ] **Step 3: Confirm pagination labels survived**

```bash
grep -o 'class="next"[^<]*' /tmp/out/posts/index.html | head -1
```

Expected to contain `Next&nbsp;&nbsp;»`. If `Next` is missing, `i18n/en.yaml`
was not copied in Task 2.

- [ ] **Step 4: Stop for review**

Suggested message: `config: stop using the papermod theme`

---

### Task 5: Delete both theme submodules

`themes/mini` is also a submodule and is not referenced by `hugo.toml` at all. It
goes at the same time.

**Files:**
- Delete: `themes/`
- Modify: `.gitmodules` (emptied)

- [ ] **Step 1: Deinitialise and remove both submodules**

```bash
git submodule deinit -f themes/papermod
git submodule deinit -f themes/mini
git rm -f themes/papermod themes/mini
rm -rf themes .git/modules/themes
```

- [ ] **Step 2: Verify .gitmodules is empty and remove it if so**

```bash
cat .gitmodules 2>/dev/null || echo "(gone)"
```

If the file still exists and is empty, `git rm -f .gitmodules`. If it still lists
a submodule, remove that entry by hand — do not leave a stale entry.

- [ ] **Step 3: Rebuild and diff**

```bash
rm -rf /tmp/out && direnv exec . hugo --destination /tmp/out
diff -r -I '<updated>' /tmp/baseline /tmp/out | wc -l
```

Expected: `0`. This is the moment the theme is genuinely gone, so a clean diff
here is the plan's central claim.

- [ ] **Step 4: Run both checkers**

```bash
./check-site.sh; ./check-links-internal.sh
```

Expected: `46 checks: 46 passed, 0 failed` and `0 broken`.

- [ ] **Step 5: Stop for review**

Suggested message: `themes: remove the papermod and mini submodules`

---

### Task 6: Correct the footer credit

The only intended visible change in this plan. The footer credits PaperMod, which
the site no longer uses.

**Files:**
- Modify: `layouts/partials/footer.html`

- [ ] **Step 1: Find the credit**

```bash
grep -n 'PaperMod' layouts/partials/footer.html
```

- [ ] **Step 2: Show Allan the surrounding markup and agree the wording**

```bash
sed -n "$(grep -n 'Powered by' layouts/partials/footer.html | cut -d: -f1),+6p" layouts/partials/footer.html
```

Do not invent replacement wording. Keeping the Hugo credit and dropping only the
PaperMod half is the obvious default, but the text is Allan's to choose. Ask,
then apply his wording.

- [ ] **Step 3: Rebuild and confirm the diff is the credit alone**

```bash
rm -rf /tmp/out && direnv exec . hugo --destination /tmp/out
diff -r -I '<updated>' /tmp/baseline /tmp/out | grep '^[<>]' | sort -u | head
```

Expected: only lines from the footer credit. Every page changes, but they should
all differ in the same way.

- [ ] **Step 4: Stop for review**

Suggested message: `footer: drop the PaperMod credit`

---

### Task 7: Manual verification

No script covers these. They are the behaviours most likely to break silently,
because nothing errors when they do.

- [ ] **Step 1: Start the dev server**

```bash
./debug.sh
```

- [ ] **Step 2: Check the theme toggle**

Click it. The page must switch between light and dark, and the choice must
survive a reload. This exercises the 119 lines of JS inlined from
`footer.html` — the single most likely casualty of this migration.

- [ ] **Step 3: Check scroll-to-top**

Open a long post, scroll down, confirm the button appears and works.

- [ ] **Step 4: Check images still lazy-load**

Open `/posts/generic-components/` and confirm in devtools that both images carry
`loading="lazy"`. This comes from `layouts/_default/_markup/render-image.html`,
copied in Task 2.

- [ ] **Step 5: Check pagination**

Visit `/posts/page/2/`. It must load, and the Prev/Next labels must read as
words, not bare arrows.

- [ ] **Step 6: Spot-check the pages that use distinct templates**

Visit `/`, a post, `/tags/`, `/tags/elm/`, `/archives/`, `/cv/`, `/consulting/`,
and a URL that does not exist (for the 404). Each uses a different template.

- [ ] **Step 7: Stop for review**

Report anything that looks wrong. Do not fix and continue silently.

---

### Task 8: Prune provably-unused files

Deliberately last. Doing it earlier would confound the "output is unchanged"
check with deletions.

**Files:**
- Delete: `layouts/_default/search.html`, `assets/js/`, `assets/css/common/search.css`, `assets/css/common/profile-mode.css`

- [ ] **Step 1: Confirm each is unreferenced**

```bash
grep -rn 'search\.css\|profile-mode\.css' layouts/ assets/css/ || echo "no css references"
grep -rn 'js/' layouts/ || echo "no js references"
ls assets/js 2>/dev/null || echo "(no assets/js — nothing to delete)"
```

Both CSS files are picked up by `resources.Match "css/common/*.css"` rather than
by name, so "no css references" is the expected result and does not mean they are
already excluded — deleting them removes them from that glob.

- [ ] **Step 2: Delete them**

```bash
rm -f layouts/_default/search.html
rm -rf assets/js
rm -f assets/css/common/search.css assets/css/common/profile-mode.css
```

- [ ] **Step 3: Rebuild and diff**

```bash
rm -rf /tmp/out && direnv exec . hugo --destination /tmp/out
diff -r -I '<updated>' /tmp/baseline /tmp/out | grep '^[<>]' | sort -u | head
```

Expected: still only the footer credit from Task 6. The CSS bundle is
fingerprinted, so its filename changes when its contents change; if the
stylesheet link differs, confirm the only cause is the removed rules and that no
page lost styling.

- [ ] **Step 4: Run both checkers a final time**

```bash
./check-site.sh; ./check-links-internal.sh
```

Expected: `46 checks: 46 passed, 0 failed` and `0 broken`.

- [ ] **Step 5: Stop for review**

Suggested message: `assets: drop unused search and profile-mode files`

---

## Notes for the implementer

- If a diff is non-empty and you cannot explain it, stop. Do not "fix" it by
  editing the baseline or by loosening the diff.
- `/tmp/baseline` is deleted by a reboot. If it disappears mid-plan, recreate it
  from a clean checkout of the commit made at the end of Task 1 — not from the
  current working tree, which already contains changes.
- The three deprecation WARNs are pre-existing and out of scope. Two of them
  (`.Language.LanguageCode`) become fixable once the theme's files are ours, but
  fixing them here would confound the diff. That is deliberate follow-up work.
- The tags `llm` (3 posts) and `llms` (6 posts) are separate terms with separate
  pages. Merging them is a content decision for Allan and is not part of this
  plan.
