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
    description: str | None = None
    draft: bool = False
    # Did the front-matter date have an explicit numeric UTC offset
    # ("+00:00"), or was it left implicit (a bare date, or a "Z" suffix)?
    # Both parse to the same instant, but Hugo's Go runtime resolves them to
    # two different `time.Location`s: bare/"Z" dates get the named "UTC"
    # zone, while an explicit numeric offset gets an unnamed fixed-offset
    # zone. That distinction is invisible on `date` (both end up tzinfo=UTC
    # here) but visible in Go's default time.Time formatting -- see
    # pages.py's `_go_string_zone`.
    date_zone_named: bool = True

_EXPLICIT_OFFSET_RE = re.compile(r"[+-]\d{2}:?\d{2}$")

def _parse_date(raw: str) -> datetime:
    raw = raw.strip().strip('"').strip("'")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

def _date_zone_named(raw: str) -> bool:
    raw = raw.strip().strip('"').strip("'")
    return not _EXPLICIT_OFFSET_RE.search(raw)

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
    `content/cv.md`'s own body is just the `{{< cv >}}` shortcode call,
    of no use to a renderer (see `pages.cv_page`, which reads
    `content/cv.html` directly instead) -- callers that only need the
    front matter use `load_front_matter` above."""
    try:
        meta, body = _parse_front_matter(path.read_text())
    except ValueError as e:
        raise ValueError(f"{path}: {e}") from e
    return meta, body

def parse_post(path: Path) -> Post:
    text = path.read_text()
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
        date_zone_named=_date_zone_named(raw_date),
    )

def load_posts(root: Path, now: datetime | None = None) -> list[Post]:
    now = now or datetime.now(timezone.utc)
    posts = [parse_post(p) for p in sorted(Path(root).glob("*.md"))]
    posts = [p for p in posts if not p.draft and p.date <= now]
    posts.sort(key=lambda p: p.date, reverse=True)
    return posts

def load_index_body(path: Path) -> str:
    """content/_index.md carries the home page's intro prose, but -- unlike
    every real post -- it has no `date:` key, so it cannot go through
    parse_post (which does `meta["date"]` and is meant to raise on exactly
    that). Strip the front matter the same way parse_post does and hand
    back the raw markdown body only; pages.py renders it."""
    text = path.read_text()
    if not text.startswith("---"):
        raise ValueError(f"{path}: no front matter")
    end = text.index("\n---", 3)
    return text[end + 4:].lstrip("\n")
