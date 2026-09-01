"""Tests for generator/assets.py: the fingerprinted stylesheet bundle
(`_bundle_text`/`build_stylesheet`) and the resized signature portrait
(`resize_portrait`).

`build_stylesheet`/`resize_portrait` deliberately do NOT reproduce Hugo's
own CSS minifier or Go's PNG encoder byte-for-byte -- see assets.py's own
module docstring for the recorded deviation -- so these tests pin down
what this generator's own build actually guarantees (concatenation order,
a stable/self-consistent fingerprint, correct image dimensions), not a
byte-for-byte match against Hugo's output, which `compare.py`'s own
full-tree comparison already confirmed is out of scope here.
"""
from __future__ import annotations
import base64
import hashlib
from pathlib import Path

from PIL import Image

from generator import assets


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def _css_fixture(root: Path) -> None:
    """A minimal but complete assets/css tree, built from scratch rather
    than pointed at the real repo tree: one distinctive marker string per
    file, with no separators of their own, so a wrong concatenation order
    shows up as markers out of byte sequence, not as a subtler content
    difference somewhere inside real CSS. Two files each in `common/` and
    `extended/` (deliberately NOT alphabetical on disk -- "z-first"/
    "a-second") so a missing `sorted()` on either glob also fails loudly."""
    _write(root / "core" / "license.css", "LICENSE")
    _write(root / "core" / "theme-vars.css", "THEME-VARS")
    _write(root / "core" / "reset.css", "RESET")
    _write(root / "common" / "a-first.css", "COMMON-A")
    _write(root / "common" / "z-last.css", "COMMON-Z")
    _write(root / "includes" / "chroma-styles.css", "CHROMA-STYLES")
    _write(root / "includes" / "chroma-mod.css", "CHROMA-MOD")
    _write(root / "includes" / "scroll-bar.css", "SCROLL-BAR")
    _write(root / "core" / "zmedia.css", "ZMEDIA")
    _write(root / "extended" / "a-first.css", "EXTENDED-A")
    _write(root / "extended" / "z-last.css", "EXTENDED-Z")


# head.html's own order: license, then core (theme-vars, reset,
# common/*.css SORTED BY FILENAME -- "COMMON-A" is z-first.css, sorted
# first -- chroma-styles, chroma-mod, the includes group, zmedia), then
# extended/*.css sorted. "COMMON-A"/"EXTENDED-A" are the fixture's own
# marker names, not the alphabetical winners -- see `_css_fixture`.
_MARKERS_IN_ORDER = [
    "LICENSE", "THEME-VARS", "RESET", "COMMON-A", "COMMON-Z",
    "CHROMA-STYLES", "CHROMA-MOD", "SCROLL-BAR", "ZMEDIA",
    "EXTENDED-A", "EXTENDED-Z",
]


def test_bundle_text_concatenation_order(tmp_path: Path):
    _css_fixture(tmp_path)
    bundle = assets._bundle_text(tmp_path)
    positions = [bundle.index(marker) for marker in _MARKERS_IN_ORDER]
    assert positions == sorted(positions), \
        list(zip(_MARKERS_IN_ORDER, positions))

def test_bundle_text_includes_group_is_blank_resource_then_scroll_bar(tmp_path: Path):
    # head.html builds the includes group as `$includes | append (blank)`
    # (Hugo's `append`, piped, appends its argument onto the END of the
    # piped collection: [blank]) then, unless disabled,
    # `append $ScrollStyle $includes` (the same function called directly,
    # so $includes is now the collection argument: ScrollStyle appended
    # onto the end of [blank]) -- [blank, ScrollStyle], not the other way
    # around. The blank resource is a single space with no marker of its
    # own, so this checks its exact position the only way possible: the
    # literal byte between the two neighbouring markers.
    _css_fixture(tmp_path)
    bundle = assets._bundle_text(tmp_path)
    assert "CHROMA-MOD SCROLL-BAR" in bundle

def test_bundle_text_disables_scroll_bar_style_when_configured(tmp_path: Path):
    _css_fixture(tmp_path)
    assets._DISABLE_SCROLL_BAR_STYLE = True
    try:
        bundle = assets._bundle_text(tmp_path)
    finally:
        assets._DISABLE_SCROLL_BAR_STYLE = False
    assert "SCROLL-BAR" not in bundle
    assert "CHROMA-MOD ZMEDIA" in bundle  # blank resource, no scroll-bar, then zmedia


def test_build_stylesheet_filename_and_integrity_agree_on_one_digest(tmp_path: Path):
    css_root, out = tmp_path / "css", tmp_path / "out"
    _css_fixture(css_root)
    href, integrity = assets.build_stylesheet(css_root, out)

    bundle_path = next((out / "assets" / "css").glob("stylesheet.*.css"))
    digest = hashlib.sha256(bundle_path.read_bytes()).digest()

    # The filename carries the HEX digest; `integrity` the BASE64 form of
    # the exact same bytes -- not two independently-computed hashes that
    # merely happen to agree.
    assert href == f"/assets/css/stylesheet.{digest.hex()}.css"
    assert integrity == "sha256-" + base64.b64encode(digest).decode("ascii")

def test_build_stylesheet_is_stable_across_builds(tmp_path: Path):
    # An unstable hash would churn every page's stylesheet URL on every
    # build, even with no CSS source changed at all.
    css_root = tmp_path / "css"
    _css_fixture(css_root)
    href1, integrity1 = assets.build_stylesheet(css_root, tmp_path / "out1")
    href2, integrity2 = assets.build_stylesheet(css_root, tmp_path / "out2")
    assert href1 == href2
    assert integrity1 == integrity2

def test_build_stylesheet_changes_with_the_source(tmp_path: Path):
    css_root = tmp_path / "css"
    _css_fixture(css_root)
    href1, _ = assets.build_stylesheet(css_root, tmp_path / "out1")
    (css_root / "extended" / "z-first.css").write_text("EXTENDED-A-CHANGED")
    href2, _ = assets.build_stylesheet(css_root, tmp_path / "out2")
    assert href1 != href2


def test_resize_portrait_dimensions_and_mode(tmp_path: Path):
    src = tmp_path / "portrait.png"
    Image.new("RGBA", (192, 192), (10, 20, 30, 255)).save(src)
    out = tmp_path / "out"

    href = assets.resize_portrait(src, out, 112)

    assert href == "/images/portrait_hu_6510263e774a9def.png"
    dest = out / "images" / "portrait_hu_6510263e774a9def.png"
    with Image.open(dest) as im:
        assert im.size == (112, 112)
        # consulting-signature.html's own spec is "112x png" -- an RGB
        # PNG, not the RGBA the fixture source starts as.
        assert im.mode == "RGB"

def test_resize_portrait_honours_a_different_width(tmp_path: Path):
    src = tmp_path / "portrait.png"
    Image.new("RGB", (192, 192), (0, 0, 0)).save(src)
    out = tmp_path / "out"

    assets.resize_portrait(src, out, 56)

    with Image.open(out / "images" / "portrait_hu_6510263e774a9def.png") as im:
        assert im.size == (56, 56)
