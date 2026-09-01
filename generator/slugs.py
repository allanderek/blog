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
        self._counts: dict[str, int] = {}
        self._emitted: set[str] = set()

    def slug(self, text: str) -> str:
        base = _TAG.sub("", text).strip().lower()
        base = _KEEP.sub("", base).replace(" ", "-")
        if not base:
            base = "heading"          # Hugo's fallback for an empty slug
        n = self._counts.get(base, 0)
        self._counts[base] = n + 1
        candidate = base if n == 0 else f"{base}-{n}"
        # A literal heading can collide with a generated numbered form, so keep
        # suffixing until the id is genuinely free.
        suffix_n = 0
        while candidate in self._emitted:
            suffix_n += 1
            candidate = f"{candidate}-{suffix_n}"
        self._emitted.add(candidate)
        return candidate
