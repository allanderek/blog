"""Discover and parse posts. Front matter is a known, small YAML subset."""
from __future__ import annotations
import csv
import io
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
    # "short" or "long": which of the home page's two recommendation lists
    # a featured post belongs in. Editorial rather than measured -- it is
    # about whether a post is a coffee-break read or a weekend one, which a
    # word count only approximates, and a threshold would let a post change
    # category because a paragraph was added.
    featured_length: str = "long"
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

def _parse_list(raw: str) -> list[str]:
    """Split a flat, flow-style YAML list, respecting quoted commas."""
    inner = raw.strip()[1:-1]
    if not inner.strip():
        return []
    row = next(csv.reader(io.StringIO(inner), skipinitialspace=True))
    return [item.strip().strip("'") for item in row if item.strip()]

def _parse_scalar(raw: str):
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        return _parse_list(raw)
    if raw.lower() in ("true", "false"):
        return raw.lower() == "true"
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    return raw.strip('"').strip("'")

def _parse_front_matter(text: str) -> tuple[dict, str]:
    """The front-matter block (as a plain dict, keys/values parsed via
    `_parse_scalar`) and the body that follows it, lstripped of the blank
    line(s) `---` normally leaves behind. Shared by `parse_post` (which
    additionally requires a `date:` key) and `load_front_matter` (which
    doesn't -- `content/cv.md`/`content/consulting.md` have none)."""
    if not text.startswith("---"):
        raise ValueError("no front matter")
    end = text.index("\n---", 3)
    front, body = text[3:end], text[end + 4:].lstrip("\n")
    meta: dict = {}
    for line in front.splitlines():
        if not line.strip() or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = _parse_scalar(value)
    return meta, body

def load_front_matter(path: Path) -> dict:
    """Front matter only, for a page with no `date:` (so it can't go
    through `parse_post`, which requires one) whose metadata is still
    needed -- `feeds.py`'s root RSS item for `content/cv.md`/
    `content/consulting.md`, which Hugo's `.RegularPages` includes
    alongside every post (see feeds.py's module docstring)."""
    return load_page(path)[0]

def load_page(path: Path) -> tuple[dict, str]:
    """Front matter AND body, for a page with no `date:` whose own body
    needs rendering too -- `content/consulting.md` (real markdown prose;
    `pages.consulting_page` renders it exactly like a post's own body).
    `content/cv.md`'s own body is empty -- the CV's actual content lives in
    `content/cv.toml`, parsed by `cv.load` (see `pages.cv_page`) -- so only
    its front matter is ever needed; callers that only need that use
    `load_front_matter` above."""
    try:
        meta, body = _parse_front_matter(path.read_text(encoding="utf-8"))
    except ValueError as e:
        raise ValueError(f"{path}: {e}") from e
    return meta, body

def parse_post(path: Path) -> Post:
    text = path.read_text(encoding="utf-8")
    try:
        meta, body = _parse_front_matter(text)
    except ValueError as e:
        raise ValueError(f"{path}: {e}") from e
    raw_date = str(meta["date"])
    return Post(
        slug=path.stem,
        title=str(meta.get("title", "")),
        date=_parse_date(raw_date),
        body=body,
        tags=meta.get("tags") or [],
        featured=bool(meta.get("featured", False)),
        featured_weight=int(meta.get("featuredWeight", 999)),
        featured_blurb=meta.get("featuredBlurb"),
        description=meta.get("description"),
        draft=bool(meta.get("draft", False)),
        featured_length=_featured_length(meta, path),
    )

_FEATURED_LENGTHS = ("short", "long")

def _featured_length(meta: dict, path: Path) -> str:
    """`featuredLength: short` / `long`, defaulting to long.

    An unrecognised value raises rather than quietly defaulting: a typo
    would otherwise file the post under the wrong heading with nothing to
    show for it, and a build that stops with a clear message is the same
    treatment a malformed `date:` already gets.
    """
    raw = meta.get("featuredLength")
    if raw is None:
        return "long"
    value = str(raw).strip().strip('"').strip("'").lower()
    if value not in _FEATURED_LENGTHS:
        raise ValueError(
            f"{path}: featuredLength is {raw!r}; expected one of "
            f"{' or '.join(_FEATURED_LENGTHS)}")
    return value

def load_posts(root: Path, now: datetime | None = None) -> list[Post]:
    now = now or datetime.now(timezone.utc)
    posts = [parse_post(p) for p in sorted(Path(root).glob("*.md"))]
    posts = [p for p in posts if not p.draft and p.date <= now]
    posts.sort(key=lambda p: p.date, reverse=True)
    return posts

# A slug becomes a permanent URL, so this is validated rather than
# normalised: a stray capital or space is worth refusing before the post is
# written, not silently rewriting into something the author did not choose.
_SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")

# The newest posts carry a full timestamp rather than a bare date, so two
# posts written on the same day still order against each other.
_NEW_POST_DATE = "%Y-%m-%dT%H:%M:%S+00:00"

def title_from_slug(slug: str) -> str:
    """"my-new-post" -> "My new post". Sentence case, matching the corpus;
    a starting point to type over, not a guess to live with."""
    words = slug.replace("-", " ")
    return words[:1].upper() + words[1:]

def new_post(root: Path, slug: str, title: str | None = None,
             now: datetime | None = None) -> Path:
    """Write an empty post at `root/<slug>.md` and return its path.

    Refuses to touch an existing file: this is a convenience for starting
    something, never a way to lose a draft.
    """
    if not _SLUG_RE.match(slug):
        raise ValueError(
            f"{slug!r} is not a usable slug. A slug becomes the post's URL, "
            "so it must be lowercase letters, digits and single hyphens -- "
            f"try {slug.strip().lower().replace(' ', '-')!r}")
    path = Path(root) / f"{slug}.md"
    if path.exists():
        raise FileExistsError(f"{path} already exists")
    stamp = (now or datetime.now(timezone.utc)).strftime(_NEW_POST_DATE)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'---\ntitle: "{title or title_from_slug(slug)}"\n'
        f"tags: []\ndate: {stamp}\n---\n\n",
        encoding="utf-8")
    return path

def load_index_body(path: Path) -> str:
    """content/_index.md carries the home page's intro prose, but -- unlike
    every real post -- it has no `date:` key, so it cannot go through
    parse_post (which does `meta["date"]` and is meant to raise on exactly
    that). Strip the front matter the same way parse_post does and hand
    back the raw markdown body only; pages.py renders it."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path}: no front matter")
    end = text.index("\n---", 3)
    return text[end + 4:].lstrip("\n")
