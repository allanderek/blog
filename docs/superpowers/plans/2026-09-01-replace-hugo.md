# Replace Hugo With a Python Generator — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate this blog from a Python program in `generator/`, and remove Hugo
from the toolchain, with published output unchanged apart from an agreed list of
typographic differences and the contents of highlighted code blocks.

**Architecture:** A Python package of single-responsibility modules. Pages are plain
Python functions returning HTML — no template language. Hugo keeps working
throughout; a comparison tool diffs the two output trees continuously, and Hugo is
deleted only once the gate is green.

**Tech Stack:** Python 3, `markdown-it-py` (CommonMark+GFM, same standard as
Goldmark), `mdit-py-plugins` (deflist), Pygments (highlighting), Pillow (image
resize), pytest (unit tests). All pinned in `devenv.nix`.

**Spec:** `docs/superpowers/specs/2026-09-01-replace-hugo-design.md`

## Global Constraints

- Hugo remains installed and working until Task 12. Never break the Hugo build.
- The generator writes to its own output directory until Task 12. It must NOT
  write to `public/` before then.
- Prose HTML must match Hugo exactly, except for the accepted-drift allow-list:
  smart-quote direction, en-dash conversion, ellipsis spacing. Nothing structural
  and nothing affecting a URL is ever accepted as drift.
- Code-block *contents* are excluded from the automated diff; the surrounding
  `<pre>`/`<code>` structure is not.
- Run Hugo via `direnv exec . hugo` so version 0.165.0 is used. A bare `hugo` is
  0.146.7 and produces different output.
- Python dependencies must be added to `devenv.nix`. They are currently only
  present because this machine happens to have them; CI installs nothing.
- Do not run `git commit` unless the executing skill directs otherwise — Allan
  commits his own work. End each task by reporting what changed.
- Three Hugo deprecation WARNs (`languageCode`, `.Language.LanguageDirection`,
  `.Language.LanguageCode`) are pre-existing and expected.
- `check-site.sh` must stay at 46/46 throughout.

## File Structure

    generator/
      __init__.py
      __main__.py      CLI: build, serve
      content.py       front matter parsing, Post model, filtering, ordering
      slugs.py         Hugo-compatible heading slugs, with per-document dedupe
      markdown.py      configured markdown-it-py; heading IDs; image hook
      highlight.py     Pygments wrapper emitting Chroma-shaped output
      html.py          escaping and element helpers (the template-language substitute)
      pages.py         one function per page type
      feeds.py         RSS and Atom
      assets.py        CSS concat/minify/fingerprint; portrait resize
      site.py          orchestration
    tests/
      test_slugs.py
      test_content.py
      test_markdown.py
    compare.py         dev tool: diff Hugo's tree against the generator's

## Reference Data (measured 2026-09-01, do not re-derive)

- 176 posts in `content/posts/`. Front matter keys in use, and no others:
  `title` (176), `date` (176), `tags` (174), `featured` (11), `featuredWeight`
  (11), `featuredBlurb` (11), `description` (4). No post currently sets `draft`,
  but the key must still be honoured.
- Date formats in use: `2026-08-28` (10 chars), `2017-04-15T14:40:31Z` (20),
  `2026-08-13T11:23:43+00:00` (25).
- 517 code blocks: 492 labelled, 25 unlabelled. Languages: elm 331, python 80,
  Python 11, bash 13, shell 9, diff 7, haskell 7, sql 4, make 4, javascript 4, c 4.
- Hugo emits 413 files and 328 pages.
- 70 pagination alias stubs (`/posts/page/1/` plus 69 `/tags/<tag>/page/1/`).
- No post uses a front-matter `aliases` key.

---

### Task 1: Environment, package skeleton, and the Post model

**Files:**
- Modify: `devenv.nix`
- Create: `generator/__init__.py`, `generator/content.py`, `tests/test_content.py`

**Interfaces:**
- Produces: `content.Post` dataclass with fields `slug: str`, `title: str`,
  `date: datetime`, `tags: list[str]`, `body: str`, `featured: bool`,
  `featured_weight: int`, `featured_blurb: str | None`, `description: str | None`,
  `draft: bool`. Also `content.load_posts(root: Path) -> list[Post]`, returning
  posts sorted newest-first, with drafts and future-dated posts excluded.

- [ ] **Step 1: Add the Python dependencies to devenv.nix**

Edit the `packages` list so it reads:

```nix
  packages = [
    pkgs.git
    pkgs.hugo
    pkgs.fd
    pkgs.sd
    pkgs.lychee   # used by ./check-links-external.sh
    (pkgs.python3.withPackages (ps: [
      ps.markdown-it-py
      ps.mdit-py-plugins
      ps.pygments
      ps.pillow
      ps.pytest
    ]))
  ];
```

- [ ] **Step 2: Verify the environment provides them**

```bash
direnv exec . python3 -c "import markdown_it, mdit_py_plugins, pygments, PIL, pytest; print('all present')"
```

Expected: `all present`. If direnv has not picked up the change, re-enter the
shell. Do not proceed until this passes — every later task depends on it.

- [ ] **Step 3: Write the failing tests**

Create `tests/test_content.py`:

```python
from datetime import datetime
from pathlib import Path
from generator.content import Post, load_posts, parse_post

def test_parses_all_three_date_formats(tmp_path):
    for name, raw in [
        ("a", "2026-08-28"),
        ("b", "2017-04-15T14:40:31Z"),
        ("c", "2026-08-13T11:23:43+00:00"),
    ]:
        (tmp_path / f"{name}.md").write_text(
            f'---\ntitle: "T"\ndate: {raw}\ntags: [x]\n---\n\nBody\n')
    posts = {p.slug: p for p in load_posts(tmp_path)}
    assert len(posts) == 3
    assert posts["a"].date.year == 2026
    assert posts["b"].date.year == 2017

def test_body_excludes_front_matter(tmp_path):
    (tmp_path / "p.md").write_text(
        '---\ntitle: "T"\ndate: 2020-01-01\n---\n\nHello *world*\n')
    post = parse_post(tmp_path / "p.md")
    assert post.body.strip() == "Hello *world*"
    assert "title:" not in post.body

def test_drafts_are_excluded(tmp_path):
    (tmp_path / "keep.md").write_text('---\ntitle: "K"\ndate: 2020-01-01\n---\nx\n')
    (tmp_path / "skip.md").write_text(
        '---\ntitle: "S"\ndate: 2020-01-01\ndraft: true\n---\nx\n')
    assert [p.slug for p in load_posts(tmp_path)] == ["keep"]

def test_future_posts_are_excluded(tmp_path):
    (tmp_path / "old.md").write_text('---\ntitle: "O"\ndate: 2020-01-01\n---\nx\n')
    (tmp_path / "future.md").write_text('---\ntitle: "F"\ndate: 2999-01-01\n---\nx\n')
    assert [p.slug for p in load_posts(tmp_path)] == ["old"]

def test_sorted_newest_first(tmp_path):
    for name, d in [("old", "2020-01-01"), ("new", "2021-01-01")]:
        (tmp_path / f"{name}.md").write_text(f'---\ntitle: "T"\ndate: {d}\n---\nx\n')
    assert [p.slug for p in load_posts(tmp_path)] == ["new", "old"]

def test_featured_defaults(tmp_path):
    (tmp_path / "p.md").write_text('---\ntitle: "T"\ndate: 2020-01-01\n---\nx\n')
    post = parse_post(tmp_path / "p.md")
    assert post.featured is False
    assert post.featured_weight == 999
    assert post.tags == []

def test_real_corpus_loads(tmp_path):
    posts = load_posts(Path("content/posts"))
    assert len(posts) == 176
    assert all(p.title for p in posts)
    assert posts == sorted(posts, key=lambda p: p.date, reverse=True)
```

- [ ] **Step 4: Run the tests and watch them fail**

```bash
direnv exec . python3 -m pytest tests/test_content.py -v
```

Expected: collection error, `ModuleNotFoundError: No module named 'generator'`.

- [ ] **Step 5: Implement content.py**

Front matter is a small, known YAML subset — do not add a YAML dependency. Only
the seven keys in Reference Data appear, values are scalars or flat lists.

```python
"""Discover and parse posts. Front matter is a known, small YAML subset."""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

@dataclass
class Post:
    slug: str
    title: str
    date: datetime
    body: str
    tags: list[str] = field(default_factory=list)
    featured: bool = False
    featured_weight: int = 999
    featured_blurb: str | None = None
    description: str | None = None
    draft: bool = False

def _parse_date(raw: str) -> datetime:
    raw = raw.strip().strip('"').strip("'")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def _parse_scalar(raw: str):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        items = [i.strip().strip('"').strip("'") for i in raw[1:-1].split(",")]
        return [i for i in items if i]
    if raw.lower() in ("true", "false"):
        return raw.lower() == "true"
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    return raw.strip('"').strip("'")

def parse_post(path: Path) -> Post:
    text = path.read_text()
    if not text.startswith("---"):
        raise ValueError(f"{path}: no front matter")
    end = text.index("\n---", 3)
    front, body = text[3:end], text[end + 4:].lstrip("\n")
    meta: dict = {}
    for line in front.splitlines():
        if not line.strip() or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = _parse_scalar(value)
    return Post(
        slug=path.stem,
        title=str(meta.get("title", "")),
        date=_parse_date(str(meta["date"])),
        body=body,
        tags=meta.get("tags") or [],
        featured=bool(meta.get("featured", False)),
        featured_weight=int(meta.get("featuredWeight", 999)),
        featured_blurb=meta.get("featuredBlurb"),
        description=meta.get("description"),
        draft=bool(meta.get("draft", False)),
    )

def load_posts(root: Path, now: datetime | None = None) -> list[Post]:
    now = now or datetime.now(timezone.utc)
    posts = [parse_post(p) for p in sorted(Path(root).glob("*.md"))]
    posts = [p for p in posts if not p.draft and p.date <= now]
    posts.sort(key=lambda p: p.date, reverse=True)
    return posts
```

Also create an empty `generator/__init__.py`.

- [ ] **Step 6: Run the tests until they pass**

```bash
direnv exec . python3 -m pytest tests/test_content.py -v
```

Expected: 7 passed. `test_real_corpus_loads` asserting exactly 176 is the one
that proves this works on real data, not just fixtures.

- [ ] **Step 7: Confirm Hugo is untouched**

```bash
./check-site.sh 2>&1 | tail -3
```

Expected: `46 checks: 46 passed, 0 failed`.

- [ ] **Step 8: Report and stop**

Suggested message: `generator: content model and front matter parsing`

---

### Task 2: Hugo-compatible heading slugs

Slugs decide heading anchor URLs, so they must match Hugo exactly. Three
behaviours are easy to get wrong, and all three were observed in this corpus.

**Files:**
- Create: `generator/slugs.py`, `tests/test_slugs.py`

**Interfaces:**
- Produces: `slugs.Slugger` — a per-document class. `Slugger().slug(text: str) -> str`.
  A fresh `Slugger` is created for each document; calling `.slug()` repeatedly on
  the same instance applies the dedupe suffixes.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_slugs.py`. Every case below is a real heading from this repo.

```python
from generator.slugs import Slugger

def test_lowercases_and_hyphenates_spaces():
    assert Slugger().slug("Green Party") == "green-party"

def test_underscores_are_preserved_backticks_removed():
    # source: "## Setting `cert_loc`" -> Hugo emits id="setting-cert_loc"
    assert Slugger().slug("Setting `cert_loc`") == "setting-cert_loc"

def test_punctuation_is_deleted_not_replaced():
    # backticks vanish rather than becoming separators
    assert Slugger().slug("Switch the `if` and `else` branches") == \
        "switch-the-if-and-else-branches"

def test_consecutive_spaces_are_not_collapsed():
    # source: "## First a  point of terminology" (two spaces)
    # Hugo emits id="first-a--point-of-terminology"
    assert Slugger().slug("First a  point of terminology") == \
        "first-a--point-of-terminology"

def test_duplicates_get_numeric_suffixes():
    # one post has four "### Detection" headings
    s = Slugger()
    assert [s.slug("Detection") for _ in range(4)] == \
        ["detection", "detection-1", "detection-2", "detection-3"]

def test_dedupe_is_per_document():
    assert Slugger().slug("Detection") == "detection"
    assert Slugger().slug("Detection") == "detection"

def test_strips_inline_html():
    assert Slugger().slug("A <em>word</em> here") == "a-word-here"
```

- [ ] **Step 2: Run the tests and watch them fail**

```bash
direnv exec . python3 -m pytest tests/test_slugs.py -v
```

Expected: `ModuleNotFoundError: No module named 'generator.slugs'`.

- [ ] **Step 3: Implement slugs.py**

```python
"""Heading slugs matching Hugo's github-style autoHeadingID.

Three behaviours matter, all observed in this repo's content:
  - punctuation is DELETED, not replaced ("`cert_loc`" -> "cert_loc")
  - underscores and hyphens survive; other punctuation does not
  - consecutive spaces are NOT collapsed ("a  point" -> "a--point")
Duplicate slugs within one document get -1, -2, ... suffixes.
"""
from __future__ import annotations
import re

_TAG = re.compile(r"<[^>]+>")
_KEEP = re.compile(r"[^\w\s-]", re.UNICODE)

class Slugger:
    def __init__(self) -> None:
        self._seen: dict[str, int] = {}

    def slug(self, text: str) -> str:
        s = _TAG.sub("", text).strip().lower()
        s = _KEEP.sub("", s)          # delete punctuation; \w keeps underscore
        s = s.replace(" ", "-")       # one hyphen per space, no collapsing
        n = self._seen.get(s, 0)
        self._seen[s] = n + 1
        return s if n == 0 else f"{s}-{n}"
```

Note `\w` in Python includes the underscore, which is exactly the behaviour
required, and `_KEEP` deliberately does not include a `+` quantifier collapse.

- [ ] **Step 4: Run the tests until they pass**

```bash
direnv exec . python3 -m pytest tests/test_slugs.py -v
```

Expected: 7 passed.

- [ ] **Step 5: Verify against every heading Hugo actually generated**

This is the real test — the unit tests above cover cases we know about, this
covers all of them.

```bash
direnv exec . hugo --destination /tmp/slugcheck >/dev/null 2>&1
direnv exec . python3 - <<'PY'
import re, pathlib
from generator.slugs import Slugger
bad = 0; checked = 0
for built in pathlib.Path("/tmp/slugcheck/posts").glob("*/index.html"):
    src = pathlib.Path("content/posts") / (built.parent.name + ".md")
    if not src.exists(): continue
    hugo_ids = re.findall(r'<h[2-6] id="([^"]+)"', built.read_text())
    s = Slugger()
    mine = [s.slug(re.sub(r'`', '', m.group(2)))
            for m in re.finditer(r'^(#{2,6})\s+(.*)$', src.read_text(), re.M)]
    for h, m in zip(hugo_ids, mine):
        checked += 1
        if h != m:
            bad += 1
            if bad <= 10: print(f"{built.parent.name}: hugo={h!r} mine={m!r}")
print(f"checked {checked} headings, {bad} mismatched")
PY
```

Expected: `0 mismatched`. If any mismatch appears, fix `slugs.py` — do not adjust
the test to accept it, because these strings are live anchor URLs.

- [ ] **Step 6: Report and stop**

Suggested message: `generator: Hugo-compatible heading slugs`

---

### Task 3: Markdown rendering

**Files:**
- Create: `generator/markdown.py`, `tests/test_markdown.py`

**Interfaces:**
- Consumes: `slugs.Slugger`
- Produces: `markdown.render(text: str) -> str`, returning the HTML body of one
  post, with heading IDs applied and images carrying `loading="lazy"`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_markdown.py`. These encode the four differences the fidelity
probe found that we decided to MATCH, plus the drift we decided to ACCEPT.

```python
from generator.markdown import render

def test_headings_get_ids():
    assert 'id="green-party"' in render("## Green Party")

def test_strikethrough_uses_del_not_s():
    # Goldmark emits <del>; markdown-it-py's default is <s>
    out = render("~~gone~~")
    assert "<del>gone</del>" in out
    assert "<s>" not in out

def test_bare_domain_is_not_linkified():
    # "coverage.py" must stay text: .py is not a TLD we accept
    assert "<a href" not in render("I used coverage.py for this.")

def test_real_url_is_still_linkified():
    assert '<a href="https://example.com/x">' in render("See https://example.com/x")

def test_definition_lists_render():
    out = render("Term\n:   Definition\n")
    assert "<dl>" in out and "<dt>" in out and "<dd>" in out

def test_images_are_lazy():
    out = render("![alt](/img/x.png)")
    assert 'loading="lazy"' in out
    assert 'src="/img/x.png"' in out
    assert 'alt="alt"' in out

def test_accepted_drift_directional_quotes():
    # we deliberately do NOT match Goldmark here; it makes every ' into a right
    # quote, we produce proper directional quotes
    assert "‘then’" in render("'then'")

def test_code_block_structure_preserved():
    out = render("```elm\nx = 1\n```")
    assert "<pre" in out and "</pre>" in out
```

- [ ] **Step 2: Run the tests and watch them fail**

```bash
direnv exec . python3 -m pytest tests/test_markdown.py -v
```

Expected: `ModuleNotFoundError: No module named 'generator.markdown'`.

- [ ] **Step 3: Implement markdown.py**

```python
"""Markdown rendering configured to match Goldmark where it matters.

Matched deliberately: heading IDs, <del> over <s>, lazy images, definition
lists, and linkify tuning. Accepted drift: smart-quote direction, en-dashes,
ellipsis spacing — see the spec's accepted-drift list.
"""
from __future__ import annotations
import re
from markdown_it import MarkdownIt
from mdit_py_plugins.deflist import deflist_plugin
from .slugs import Slugger
from .highlight import highlight

def _make_parser() -> MarkdownIt:
    md = MarkdownIt("gfm-like", {"typographer": True, "html": True,
                                 "highlight": highlight})
    md.use(deflist_plugin)
    md.enable(["replacements", "smartquotes"])
    # Goldmark does not linkify bare domains like "coverage.py"; only schemes.
    md.options["linkify"] = False
    return md

_MD = _make_parser()
_HEADING = re.compile(r"<h([2-6])>(.*?)</h\1>", re.S)
_S_TAG = re.compile(r"<(/?)s>")
_IMG = re.compile(r"<img ")

def render(text: str) -> str:
    html = _MD.render(text)
    slugger = Slugger()

    def add_id(m: re.Match) -> str:
        level, inner = m.group(1), m.group(2)
        return f'<h{level} id="{slugger.slug(inner)}">{inner}</h{level}>'

    html = _HEADING.sub(add_id, html)
    html = _S_TAG.sub(r"<\1del>", html)            # Goldmark emits <del>
    html = _IMG.sub('<img loading="lazy" ', html)  # the render hook's job
    return html
```

- [ ] **Step 4: Run the tests until they pass**

```bash
direnv exec . python3 -m pytest tests/test_markdown.py -v
```

Expected: 8 passed. If `test_real_url_is_still_linkified` fails because linkify
was disabled wholesale, note that markdown-it-py still renders explicit
autolinks and bare schemed URLs through its `linkify` rule only — if a bare
`https://` URL in this corpus stops being a link, re-enable linkify and instead
restrict it with `md.linkify.set({"fuzzy_link": False})`, which turns off
schemeless matching (the `coverage.py` case) while keeping real URLs.

- [ ] **Step 5: Report and stop**

Suggested message: `generator: markdown rendering`

---

### Task 4: Syntax highlighting

The spec calls this the largest unverified area: 492 of 517 code blocks are
highlighted, 331 of them Elm. Pygments will not tokenise identically to Chroma,
so this task's gate is a human looking at the output.

**Files:**
- Create: `generator/highlight.py`

**Interfaces:**
- Produces: `highlight.highlight(code: str, lang: str, attrs: str) -> str`,
  matching markdown-it-py's `highlight` callback signature and returning a
  complete `<pre>…</pre>` block. Returns `""` for an unknown or empty language,
  which tells markdown-it-py to fall back to its own escaping.

- [ ] **Step 1: Implement highlight.py**

```python
"""Pygments highlighting shaped like Chroma's output.

Hugo emits inline styles (Monokai), not CSS classes — the .chroma rules in the
bundled stylesheet are currently dead. We match that shape so the stylesheet
question can be revisited independently later.

An unlabelled block must NEVER be guessed at: 25 blocks have no language and
must stay unhighlighted.
"""
from __future__ import annotations
from pygments import highlight as _pyg_highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound

_FORMATTER = HtmlFormatter(style="monokai", noclasses=True, nowrap=False)

def highlight(code: str, lang: str, attrs: str = "") -> str:
    if not lang:
        return ""          # unlabelled: let markdown-it escape it plainly
    try:
        lexer = get_lexer_by_name(lang.lower())
    except ClassNotFound:
        return ""          # unknown language: plain, never guessed
    return _pyg_highlight(code, lexer, _FORMATTER)
```

- [ ] **Step 2: Confirm every language in the corpus resolves to a lexer**

An unresolved name degrades silently to no highlighting, which is exactly the
failure this step exists to catch.

```bash
direnv exec . python3 - <<'PY'
from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
langs = ["elm","python","Python","bash","shell","diff","haskell",
         "sql","make","javascript","c"]
for l in langs:
    try:
        print(f"  ok   {l:12} -> {get_lexer_by_name(l.lower()).name}")
    except ClassNotFound:
        print(f"  FAIL {l:12} -> no lexer")
PY
```

Expected: every line `ok`. `python` and `Python` must both resolve — the corpus
uses both spellings.

- [ ] **Step 3: Confirm unlabelled blocks stay unhighlighted**

```bash
direnv exec . python3 -c "
from generator.highlight import highlight
assert highlight('x = 1', '') == '', 'unlabelled block was highlighted'
assert highlight('x = 1', 'nosuchlang') == '', 'unknown language was guessed'
print('unlabelled and unknown correctly left alone')"
```

- [ ] **Step 4: Render one block per language for human review**

```bash
direnv exec . python3 - <<'PY'
import pathlib, re
from generator.markdown import render
out = ["<html><body style='background:#222'>"]
seen = set()
for p in sorted(pathlib.Path("content/posts").glob("*.md")):
    for m in re.finditer(r"^```([a-zA-Z]+)\n(.*?)^```", p.read_text(), re.M|re.S):
        lang = m.group(1)
        if lang in seen: continue
        seen.add(lang)
        out.append(f"<h2 style='color:#fff'>{lang} ({p.stem})</h2>")
        out.append(render(f"```{lang}\n{m.group(2)}```"))
out.append("</body></html>")
pathlib.Path("/tmp/highlight-sample.html").write_text("\n".join(out))
print("wrote /tmp/highlight-sample.html covering:", ", ".join(sorted(seen)))
PY
```

- [ ] **Step 5: Compare against Hugo's rendering of the same blocks, by eye**

Open `/tmp/highlight-sample.html` and a real post from a Hugo build side by side:

```bash
direnv exec . hugo --destination /tmp/hl-hugo >/dev/null 2>&1
echo "Hugo:  /tmp/hl-hugo/posts/dsls/index.html"
echo "Mine:  /tmp/highlight-sample.html"
```

This step needs a person. Report what differs — colours, whether strings and
comments are picked out, whether Elm in particular looks right, since it is 64%
of all highlighted blocks. Differences in exact token boundaries are expected and
acceptable; a language rendering as undifferentiated grey is not.

- [ ] **Step 6: Report and stop**

Suggested message: `generator: syntax highlighting`

---

### Task 5: The comparison harness

Built now, before any page rendering, because every remaining task is verified
with it. It is the plan's gate.

**Files:**
- Create: `compare.py`

**Interfaces:**
- Produces: `python3 compare.py <hugo-dir> <generator-dir>` — prints differences
  grouped by category and exits non-zero if any difference falls outside the
  accepted-drift allow-list.

- [ ] **Step 1: Implement compare.py**

```python
"""Diff Hugo's output tree against the generator's, by category.

The allow-list below is the single written record of what we deliberately let
differ. Anything not on it must be zero. Report by category, never as a wall of
lines: the categorised report is what makes this usable day to day.
"""
from __future__ import annotations
import html as htmlmod
import re, sys, collections, difflib
from pathlib import Path

# Accepted drift, per the spec. Applied to BOTH sides before comparison, so a
# difference of this kind cannot reach the report.
def normalise(text: str) -> str:
    text = re.sub(r"<pre.*?</pre>", "@@CODE@@", text, flags=re.S)
    text = htmlmod.unescape(text)                 # &rsquo; == '’'
    text = text.replace("‘", "'").replace("’", "'")   # quote direction
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("–", "--").replace("—", "---")  # dashes
    text = text.replace("…", "...")          # ellipsis
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def categorise(a: str, b: str) -> str:
    if 'id="' in a and 'id="' in b:      return "heading id"
    if "<a href" in b and "<a href" not in a: return "extra link (over-linkify)"
    if "<a href" in a and "<a href" not in b: return "missing link"
    if "src=" in a or "src=" in b:       return "image"
    if "@@CODE@@" in a or "@@CODE@@" in b: return "code block placement"
    return "other"

def main(hugo_dir: str, gen_dir: str) -> int:
    hugo, gen = Path(hugo_dir), Path(gen_dir)
    hugo_files = {p.relative_to(hugo) for p in hugo.rglob("*") if p.is_file()}
    gen_files = {p.relative_to(gen) for p in gen.rglob("*") if p.is_file()}

    missing = sorted(hugo_files - gen_files)
    extra = sorted(gen_files - hugo_files)
    cats: collections.Counter = collections.Counter()
    examples: dict = {}

    for rel in sorted(hugo_files & gen_files):
        if rel.suffix not in (".html", ".xml"):
            continue
        a = normalise((hugo / rel).read_text(errors="replace"))
        b = normalise((gen / rel).read_text(errors="replace"))
        if a == b:
            continue
        sm = difflib.SequenceMatcher(None, a.split(), b.split())
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            x = " ".join(a.split()[i1:i2])[:70]
            y = " ".join(b.split()[j1:j2])[:70]
            c = categorise(x, y)
            cats[c] += 1
            examples.setdefault(c, (str(rel), x, y))

    print(f"files: hugo {len(hugo_files)}, generator {len(gen_files)}")
    if missing:
        print(f"\nMISSING from generator ({len(missing)}):")
        for m in missing[:20]: print(f"  {m}")
    if extra:
        print(f"\nEXTRA in generator ({len(extra)}):")
        for e in extra[:20]: print(f"  {e}")
    if cats:
        print("\nCONTENT DIFFERENCES by category:")
        for c, n in cats.most_common():
            rel, x, y = examples[c]
            print(f"  {n:5}  {c}")
            print(f"         e.g. {rel}")
            print(f"           hugo: {x!r}")
            print(f"           mine: {y!r}")
    ok = not missing and not extra and not cats
    print("\nCLEAN" if ok else "\nDIFFERENCES PRESENT")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
```

- [ ] **Step 2: Prove the tool reports rather than stays silent**

Compare a Hugo build against a deliberately incomplete copy of itself. A
comparison tool that cannot fail is worthless, so verify it fails first.

```bash
direnv exec . hugo --destination /tmp/cmp-a >/dev/null 2>&1
cp -r /tmp/cmp-a /tmp/cmp-b
rm -rf /tmp/cmp-b/tags
sed -i 's|<h2 id="green-party">|<h2 id="wrong-slug">|' \
  /tmp/cmp-b/posts/scottish-local-election-2017/index.html
direnv exec . python3 compare.py /tmp/cmp-a /tmp/cmp-b; echo "exit=$?"
```

Expected: reports the missing `tags/` files AND a `heading id` category, exits 1.

- [ ] **Step 3: Prove it passes on identical trees**

```bash
rm -rf /tmp/cmp-c && cp -r /tmp/cmp-a /tmp/cmp-c
direnv exec . python3 compare.py /tmp/cmp-a /tmp/cmp-c; echo "exit=$?"
```

Expected: `CLEAN`, exit 0.

- [ ] **Step 4: Report and stop**

Suggested message: `compare: output comparison harness`

---

### Task 6: HTML helpers and the single post page

**Files:**
- Create: `generator/html.py`, `generator/pages.py`, `generator/site.py`,
  `generator/__main__.py`

**Interfaces:**
- Consumes: `content.Post`, `markdown.render`
- Produces: `html.esc(s) -> str`, `html.attrs(**kw) -> str`, `html.tag(name, inner, **kw) -> str`;
  `pages.post_page(post: Post, site: SiteContext) -> str`;
  `site.SiteContext` carrying `title`, `base_url`, `posts`, `stylesheet_href`,
  `stylesheet_integrity`; `site.build(out: Path) -> None`;
  CLI `python3 -m generator build --out DIR`.

- [ ] **Step 1: Capture the exact target HTML**

Do not invent the page structure — copy it. Extract Hugo's rendering of one post
and keep it beside you while writing `post_page`:

```bash
direnv exec . hugo --destination /tmp/target >/dev/null 2>&1
cp /tmp/target/posts/dsls/index.html /tmp/target-post.html
wc -l /tmp/target-post.html
```

The generator's job in this task is to reproduce that file for every post,
byte for byte outside the accepted drift.

- [ ] **Step 2: Implement html.py**

```python
"""Minimal helpers for building HTML. This is the substitute for a template
language: plain functions, real Python, a debugger that works."""
from __future__ import annotations
import html as _html

def esc(s: object) -> str:
    return _html.escape(str(s), quote=True)

def attrs(**kw: object) -> str:
    out = []
    for k, v in kw.items():
        if v is None or v is False:
            continue
        k = k.rstrip("_").replace("_", "-")
        out.append(k if v is True else f'{k}="{esc(v)}"')
    return (" " + " ".join(out)) if out else ""

def tag(name: str, inner: str = "", **kw: object) -> str:
    return f"<{name}{attrs(**kw)}>{inner}</{name}>"
```

- [ ] **Step 3: Implement pages.post_page, site.py and the CLI**

**`/tmp/target-post.html` is the specification for this step.** It is a complete,
exact example of the required output, and is more precise than prose could be —
read it and reproduce it, element by element, rather than writing what you think
a post page should contain.

Build the page from `html.py` helpers and `markdown.render(post.body)`.
`site.build` writes each post to `<out>/posts/<slug>/index.html`. `__main__.py`
exposes `python3 -m generator build --out DIR`.

Parts of that file that are easy to overlook because nothing breaks without them:
the `<head>` metadata block, the signature `<aside>` after the article, the
favicon and manifest links, and — most importantly — the seven inlined
`<script>` blocks carrying the theme toggle and scroll-to-top behaviour. Copy
them verbatim; they are not generated from anything.

Work iteratively against the target: render one post, diff it against
`/tmp/target-post.html`, fix, repeat. Do not move on until that single file
matches.

- [ ] **Step 4: Verify one post matches exactly**

```bash
direnv exec . python3 -m generator build --out /tmp/gen
diff <(direnv exec . python3 -c "
import sys, html, re
print(open('/tmp/target/posts/dsls/index.html').read())") \
     /tmp/gen/posts/dsls/index.html | head -20
```

Then the authoritative check, which applies the accepted-drift rules:

```bash
mkdir -p /tmp/one-hugo/posts/dsls /tmp/one-gen/posts/dsls
cp /tmp/target/posts/dsls/index.html /tmp/one-hugo/posts/dsls/
cp /tmp/gen/posts/dsls/index.html /tmp/one-gen/posts/dsls/
direnv exec . python3 compare.py /tmp/one-hugo /tmp/one-gen
```

Expected: `CLEAN`.

- [ ] **Step 5: Verify ALL 176 post pages**

```bash
rm -rf /tmp/all-hugo && mkdir -p /tmp/all-hugo
cp -r /tmp/target/posts /tmp/all-hugo/
rm -rf /tmp/all-gen && mkdir -p /tmp/all-gen && cp -r /tmp/gen/posts /tmp/all-gen/
direnv exec . python3 compare.py /tmp/all-hugo /tmp/all-gen
```

Expected: `CLEAN`. If categories appear, fix `pages.py` or `markdown.py` — do not
widen the allow-list in `compare.py`.

Then assert the behavioural JavaScript survived. `compare.py` would catch its
absence, but only as an unhelpful "other" category, and this is the single most
likely thing to be silently lost:

```bash
direnv exec . python3 - <<'PYCHECK'
import pathlib
h = pathlib.Path("/tmp/gen/posts/dsls/index.html").read_text()
for needle, what in [("theme-toggle", "theme toggle button"),
                     ("localStorage", "theme persistence"),
                     ("prefers-color-scheme", "system theme detection"),
                     ("top-link", "scroll-to-top button"),
                     ("scrollTo", "scroll-to-top behaviour")]:
    print(("ok   " if needle in h else "MISSING ") + what)
n = h.count("<script")
print(f"script blocks: {n} (expected 7)")
PYCHECK
```

Expected: five `ok` lines and 7 script blocks. The allow-list changes only by an explicit
decision recorded in the spec.

- [ ] **Step 6: Report and stop**

Suggested message: `generator: post pages`

---

### Task 7: Home page

**Files:**
- Modify: `generator/pages.py`, `generator/site.py`

**Interfaces:**
- Produces: `pages.home_page(site: SiteContext) -> str`

- [ ] **Step 1: Capture the target and note the ordering rules**

```bash
cp /tmp/target/index.html /tmp/target-home.html
grep -c 'class="home-featured-item"' /tmp/target-home.html
grep -c 'class="home-recent-item"' /tmp/target-home.html
```

Expected: 11 featured items, 8 recent items.

Rules that must hold, each currently asserted by `check-site.sh`:
- Featured posts sort by `featured_weight` ascending; equal weights fall back to
  date descending; posts without a weight use 999 and therefore sort last.
- Recent shows exactly the 8 newest posts.
- The signature block appears once, with class `signature signature-inline`, and
  before `id="start-here"`.
- The intro prose comes from `content/_index.md`, rendered as markdown.

- [ ] **Step 2: Implement home_page and wire it into site.build**

- [ ] **Step 3: Verify against Hugo**

```bash
direnv exec . python3 -m generator build --out /tmp/gen
mkdir -p /tmp/h-hugo /tmp/h-gen
cp /tmp/target/index.html /tmp/h-hugo/; cp /tmp/gen/index.html /tmp/h-gen/
direnv exec . python3 compare.py /tmp/h-hugo /tmp/h-gen
```

Expected: `CLEAN`.

- [ ] **Step 4: Report and stop**

Suggested message: `generator: home page`

---

### Task 8: List pages, pagination, and the alias stubs

The 70 alias stubs are 17% of the output tree and **nothing in `check-site.sh`
asserts they exist** — a generator that omitted them would pass every existing
check while breaking published URLs. `compare.py` is the only thing that catches
it, which is why this task exists as its own gate.

**Files:**
- Modify: `generator/pages.py`, `generator/site.py`

**Interfaces:**
- Produces: `pages.list_page(posts, page_num, total_pages, base_path, site) -> str`;
  `pages.alias_stub(target_url: str, site) -> str`

- [ ] **Step 1: Capture the targets**

```bash
cat /tmp/target/posts/page/1/index.html
ls /tmp/target/posts/page/
```

The stub is a complete small document: `<title>` and `<link rel="canonical">`
both holding the absolute target URL, plus
`<meta http-equiv="refresh" content="0; url=…">`.

- [ ] **Step 2: Implement list_page and alias_stub**

Pagination: `pagerSize` is 100, so `/posts/` holds the 100 newest and
`/posts/page/2/` the remainder. Every paginated listing also gets a
`page/1/index.html` stub redirecting to its bare URL.

- [ ] **Step 3: Verify, including the stub count**

```bash
direnv exec . python3 -m generator build --out /tmp/gen
find /tmp/gen -path '*/page/1/index.html' | wc -l
```

Expected at this stage: 1 (only `/posts/`; the 69 tag stubs arrive in Task 9).

```bash
mkdir -p /tmp/l-hugo /tmp/l-gen
cp -r /tmp/target/posts /tmp/l-hugo/; cp -r /tmp/gen/posts /tmp/l-gen/
direnv exec . python3 compare.py /tmp/l-hugo /tmp/l-gen
```

Expected: `CLEAN`.

- [ ] **Step 4: Report and stop**

Suggested message: `generator: list pages and pagination`

---

### Task 9: Taxonomies and archives

**Files:**
- Modify: `generator/pages.py`, `generator/site.py`

**Interfaces:**
- Produces: `pages.term_page(tag, posts, site) -> str`;
  `pages.terms_index(tags, site) -> str`; `pages.archives_page(posts, site) -> str`

- [ ] **Step 1: Note the tag rules**

Tag URLs are lowercased (`/tags/elm/`), while display text preserves the
front-matter spelling (`Elm`). Tag spellings were normalised in an earlier
migration precisely so this is unambiguous — do not re-derive display names by
title-casing, take them from the front matter.

```bash
ls /tmp/target/tags | wc -l
grep -o 'tags/elm/">[^<]*' /tmp/target/tags/index.html | head -1
```

Expected: 69 tag directories, and display `Elm`.

- [ ] **Step 2: Implement the three page types, plus a page/1 stub per tag**

- [ ] **Step 3: Verify**

```bash
direnv exec . python3 -m generator build --out /tmp/gen
find /tmp/gen -path '*/page/1/index.html' | wc -l
```

Expected: 70.

```bash
mkdir -p /tmp/t-hugo /tmp/t-gen
cp -r /tmp/target/tags /tmp/target/archives /tmp/t-hugo/
cp -r /tmp/gen/tags /tmp/gen/archives /tmp/t-gen/
direnv exec . python3 compare.py /tmp/t-hugo /tmp/t-gen
```

Expected: `CLEAN`.

- [ ] **Step 4: Report and stop**

Suggested message: `generator: taxonomies and archives`

---

### Task 10: Feeds

**Files:**
- Create: `generator/feeds.py`
- Modify: `generator/site.py`

**Interfaces:**
- Produces: `feeds.atom(posts, site) -> str`, `feeds.rss(posts, site) -> str`

- [ ] **Step 1: Note the constraints**

- Atom lives at `/rss/index.xml`, RSS at `/index.xml`.
- Atom contains exactly 20 entries; `check-site.sh` asserts this.
- The feed's `<updated>` is a build timestamp and will always differ — this is
  the one difference `compare.py` cannot resolve, so exclude it when comparing.
- The Atom author is `Allan Clark`, from `site.Params.author`. Neither feed's
  `<title>` may be rewritten to `"X on Allanderek's blog"`; `check-site.sh`
  asserts this too.

- [ ] **Step 2: Implement feeds.py and wire it in**

- [ ] **Step 3: Verify, ignoring only the build clock**

```bash
direnv exec . python3 -m generator build --out /tmp/gen
diff <(sed '/<updated>/d' /tmp/target/rss/index.xml) \
     <(sed '/<updated>/d' /tmp/gen/rss/index.xml) | head -20
diff <(sed '/<lastBuildDate>/d' /tmp/target/index.xml) \
     <(sed '/<lastBuildDate>/d' /tmp/gen/index.xml) | head -20
```

Expected: no output from either. Note the Atom entry `<updated>` values are per
post, not build times — only the feed-level one is a clock, so a `sed` that
removes all of them would hide real differences. If the diff is empty only
because every `<updated>` was stripped, tighten the filter to the feed-level
element and re-run.

- [ ] **Step 4: Report and stop**

Suggested message: `generator: RSS and Atom feeds`

---

### Task 11: Assets, remaining pages, and the dev server

**Files:**
- Create: `generator/assets.py`
- Modify: `generator/pages.py`, `generator/site.py`, `generator/__main__.py`

**Interfaces:**
- Produces: `assets.build_stylesheet(src: Path, out: Path) -> tuple[str, str]`
  returning `(href, integrity)`; `assets.resize_portrait(src, out, width) -> str`;
  `pages.cv_page`, `pages.consulting_page`, `pages.not_found_page`;
  CLI `python3 -m generator serve [--port 8080]`

- [ ] **Step 1: Note the fingerprint format**

Hugo's filename uses the **hex** SHA-256 of the bundle; the `integrity`
attribute uses the **base64** encoding of the same digest:

```
href="/assets/css/stylesheet.9adc48ca951744ce8f6b0c8854fdd76fa8e68bfeafc106e171df63787f1e19c5.css"
integrity="sha256-mtxIypUXRM6PawyIVP3Xb6jmi/6vwQbhcd9jeH8eGcU="
```

Concatenation order is fixed and must be reproduced exactly, from
`layouts/partials/head.html`: `license.css`, then core (`theme-vars`, `reset`,
`common/*.css` sorted, `chroma-styles`, `chroma-mod`, includes, `zmedia`), then
`extended/*.css` sorted.

- [ ] **Step 2: Implement assets.py**

Minification must match Hugo's, or the hash differs and every page's stylesheet
URL churns. If matching Hugo's minifier proves impractical, concatenate without
minifying and accept a different hash — record that as a deliberate deviation,
since it changes only the asset filename and not the rendered CSS.

- [ ] **Step 3: Implement the CV, consulting and 404 pages**

The CV is an opaque artifact authored outside this repo. Read
`layouts/shortcodes/cv.html` and insert it verbatim — do not parse or template
it.

- [ ] **Step 4: Implement the dev server**

```python
# in __main__.py
def serve(port: int = 8080) -> None:
    import functools, http.server, socketserver
    out = Path("/tmp/blog-dev")
    build(out)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                directory=str(out))
    print(f"serving {out} at http://localhost:{port}")
    socketserver.TCPServer(("", port), handler).serve_forever()
```

There is deliberately no live reload; re-run the command after editing.

- [ ] **Step 5: Full-tree verification**

```bash
direnv exec . hugo --destination /tmp/final-hugo >/dev/null 2>&1
direnv exec . python3 -m generator build --out /tmp/final-gen
direnv exec . python3 compare.py /tmp/final-hugo /tmp/final-gen
```

Expected: `CLEAN`, or differences confined to the stylesheet filename and
`integrity` if Step 2's deviation was taken. Any other category is a defect.

- [ ] **Step 6: Run the site checks against the generator's output**

```bash
find /tmp/final-gen -type f | wc -l
```

Expected: 413.

Re-assert the inlined JavaScript across the whole tree, not just one post, since
it is emitted per page:

```bash
direnv exec . python3 - <<'PYCHECK'
import pathlib
pages = list(pathlib.Path("/tmp/final-gen").rglob("*.html"))
missing = [p for p in pages
           if "page/1" not in str(p)
           and ("theme-toggle" not in p.read_text() or "top-link" not in p.read_text())]
print(f"{len(pages)} html files, {len(missing)} missing the inlined JS")
for m in missing[:10]: print("  ", m)
PYCHECK
```

Expected: 0 missing. The `page/1` alias stubs are excluded because they are bare
redirect documents with no chrome.

- [ ] **Step 7: Report and stop**

Suggested message: `generator: assets, remaining pages, dev server`

---

### Task 12: Switch over and remove Hugo

Only start this once Task 11 reports CLEAN.

**Files:**
- Modify: `check-site.sh`, `debug.sh`, `devenv.nix`,
  `.github/workflows/hugo.yaml`
- Delete: `layouts/`, `assets/`, `i18n/`, `hugo.toml`, `archetypes/`

- [ ] **Step 1: Point the checkers at the generator**

In `check-site.sh`, replace the build line

```bash
if hugo --destination "$OUT" >"$OUT/build.log" 2>&1; then
```

with

```bash
if python3 -m generator build --out "$OUT" >"$OUT/build.log" 2>&1; then
```

- [ ] **Step 2: Run both checkers**

```bash
./check-site.sh 2>&1 | tail -5
./check-links-internal.sh 2>&1 | tail -3
```

Expected: `46 checks: 46 passed, 0 failed`, and `0 broken`. These now run against
the generator, so they are the standing regression suite from here on.

- [ ] **Step 3: Update debug.sh**

```sh
#!/bin/sh

python3 -m generator serve --port 8080
```

- [ ] **Step 4: Update CI**

In `.github/workflows/hugo.yaml`, remove the Hugo install step, the dart-sass
step, the `HUGO_VERSION` env var, and `submodules: recursive`. Replace the build
step with the generator invocation, using the same Python packages pinned in
`devenv.nix`. Keep the artifact upload and deploy steps unchanged, and keep the
output directory as `./public`.

- [ ] **Step 5: Remove Hugo**

```bash
git rm -r layouts assets i18n hugo.toml archetypes
sed -i '/pkgs.hugo/d' devenv.nix
```

Note `assets/images/portrait.png` is needed by the generator — move it somewhere
the generator owns before deleting `assets/`, and update `assets.py`.

- [ ] **Step 6: Final verification from a clean state**

```bash
rm -rf public && python3 -m generator build --out public
find public -type f | wc -l
./check-site.sh 2>&1 | tail -3
./check-links-internal.sh 2>&1 | tail -3
```

Expected: 413 files, 46/46, 0 broken.

- [ ] **Step 7: Report and stop**

Suggested message: `build: replace Hugo with the Python generator`

---

## Notes for the implementer

- The allow-list in `compare.py` is the project's most important artifact. Widen
  it only by an explicit decision recorded in the spec — never to make a diff go
  away.
- If a task's comparison will not come clean and you cannot explain why, stop and
  report rather than adjusting the comparison.
- Hugo must keep working until Task 12. If a change breaks the Hugo build, that
  is a defect in the change.
- The spec's out-of-scope list stands: no redesign, no search, no live reload, and
  the CV is taken as-is.
