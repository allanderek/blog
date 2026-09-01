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
