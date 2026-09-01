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
