"""Parses `content/cv.toml` and renders it into the CV page's own content
markup (`<div class="post-content">`'s inner HTML, in `pages.cv_page`).

Kept separate from `content.py`, which is entirely about blog posts: a CV
is not a `Post` (no date, no tags, no slug) and its content is structured
data -- four fixed section shapes -- rather than a single markdown body.

Every section holds exactly one of three kinds of body: `items` (a flat
list of markdown strings, for `kind == "list"` or `"prose"`), `entries` (a
list of `Item`, summary + optional detail, for `kind == "expandable"`), or
`subsections` (a list of `Subsection`, each itself a `list`/`prose` body,
for `kind == "subsections"`). `load()` never mixes them: a TOML file that
sets e.g. both `items` and `[[section.item]]` on the same `[[section]]`
still parses (whichever `render()` doesn't look at for that `kind` is
simply ignored), matching every other place in this generator that trusts
its own content directory rather than validating it defensively.
"""
from __future__ import annotations
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import html, markdown


@dataclass
class Profile:
    name: str
    url: str


@dataclass
class Item:
    """One `expandable` entry: a `<li>` on its own (`detail is None`) or a
    `<details><summary>` (`detail` is the markdown revealed on expansion)."""
    summary: str
    detail: str | None = None


@dataclass
class Subsection:
    title: str
    kind: str            # "list" | "prose"
    items: list[str] = field(default_factory=list)


@dataclass
class Section:
    title: str
    kind: str             # "expandable" | "list" | "subsections" | "prose"
    items: list[str] = field(default_factory=list)
    entries: list[Item] = field(default_factory=list)
    subsections: list[Subsection] = field(default_factory=list)


@dataclass
class Cv:
    name: str
    address: list[str]
    pdf: str
    headlines: list[str]
    profiles: list[Profile]
    sections: list[Section]


def _parse_item(raw: dict) -> Item:
    return Item(summary=str(raw["summary"]), detail=raw.get("detail"))


def _parse_subsection(raw: dict) -> Subsection:
    return Subsection(title=str(raw["title"]), kind=str(raw["kind"]),
                       items=[str(i) for i in raw.get("items", [])])


def _parse_section(raw: dict) -> Section:
    return Section(
        title=str(raw["title"]),
        kind=str(raw["kind"]),
        items=[str(i) for i in raw.get("items", [])],
        entries=[_parse_item(i) for i in raw.get("item", [])],
        subsections=[_parse_subsection(s) for s in raw.get("subsection", [])],
    )


def load(path: Path) -> Cv:
    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    return Cv(
        name=str(raw["name"]),
        address=[str(a) for a in raw.get("address", [])],
        pdf=str(raw["pdf"]),
        headlines=[str(h) for h in raw.get("headlines", [])],
        profiles=[Profile(name=str(p["name"]), url=str(p["url"]))
                  for p in raw.get("profile", [])],
        sections=[_parse_section(s) for s in raw.get("section", [])],
    )


# --- Rendering ---------------------------------------------------------------
#
# Every markdown-typed field (`summary`, `detail`, a `list`/`prose` item) goes
# through `markdown.render`/`render_inline` -- never through `html.esc` --
# so the CV's own links (PEPA, SBSI, ipclib, the football-analysis blog, ...)
# come out as real `<a>` tags. Plain data (`name`, `address`, `headlines`,
# a profile's `name`) is escaped, not rendered as markdown: none of it is
# meant to carry markup, and escaping is the narrower, safer default.

def _list_items(items: list[str]) -> str:
    lis = "".join(f"<li>{markdown.render_inline(item)}</li>" for item in items)
    return f'<ul class="cv-list">{lis}</ul>'


def _prose_items(items: list[str]) -> str:
    return "".join(markdown.render(item) for item in items)


def _body(kind: str, items: list[str]) -> str:
    if kind == "list":
        return _list_items(items)
    if kind == "prose":
        return _prose_items(items)
    raise ValueError(f"unknown list/prose kind: {kind!r}")


def _render_entries(entries: list[Item]) -> str:
    parts = []
    for entry in entries:
        summary_html = markdown.render_inline(entry.summary)
        if entry.detail is None:
            parts.append(f"<li>{summary_html}</li>")
        else:
            parts.append(
                f"<li><details class=\"cv-details\">"
                f"<summary>{summary_html}</summary>"
                f"{markdown.render(entry.detail)}"
                f"</details></li>"
            )
    return f'<ul class="cv-expandable">{"".join(parts)}</ul>'


def _render_subsections(subsections: list[Subsection]) -> str:
    parts = []
    for sub in subsections:
        parts.append(f'<h3 class="cv-sub-heading">{html.esc(sub.title)}</h3>')
        parts.append(_body(sub.kind, sub.items))
    return "".join(parts)


def _render_section(section: Section) -> str:
    heading = f'<h2 class="cv-heading">{html.esc(section.title)}</h2>'
    if section.kind == "expandable":
        body = _render_entries(section.entries)
    elif section.kind == "subsections":
        body = _render_subsections(section.subsections)
    else:
        body = _body(section.kind, section.items)
    return f'<div class="cv-section">{heading}{body}</div>'


def render(cv: Cv) -> str:
    address_html = "<br>".join(html.esc(line) for line in cv.address)
    profiles_html = "".join(
        f'<li><a href="{html.esc(p.url)}" class="cv-profile-link">{html.esc(p.name)}</a></li>'
        for p in cv.profiles
    )
    headlines_html = "".join(f"<li>{html.esc(h)}</li>" for h in cv.headlines)
    sections_html = "".join(_render_section(s) for s in cv.sections)

    return f"""<div class="cv">
<div class="cv-header">
<h2 class="cv-name">{html.esc(cv.name)}</h2>
<div class="cv-address">{address_html}</div>
<ul class="cv-profiles">{profiles_html}</ul>
</div>
<ul class="cv-headlines">{headlines_html}</ul>
<p class="cv-pdf-note">You can download a PDF version of this CV <a href="{html.esc(cv.pdf)}">here</a>.</p>
{sections_html}
</div>"""
