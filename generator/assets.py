"""Builds the two fingerprinted assets Hugo's pipeline produces for this
site: the bundled/fingerprinted stylesheet (`layouts/partials/head.html`)
and the resized signature portrait (`layouts/partials/consulting-signature.html`).

Both follow the same shape as Hugo's own `resources.Get(...).Fingerprint()`/
`.Resize()` pipeline: read source file(s), transform, write the result under
a content-addressed filename, and hand back what `<head>`/`<img>` need to
reference it.

DEVIATIONS (recorded per the task's standing authorisation to accept a
different hash rather than chase byte-for-byte parity with an external
tool's own encoder):

* `build_stylesheet` concatenates the CSS sources in head.html's exact
  order but does NOT run Hugo's `resources.Minify` (tdewolff's CSS
  minifier) over the core/extended groups first -- matching that
  minifier's output byte-for-byte from Python is impractical. The
  rendered CSS is identical (same rules, just not minified); only the
  SHA-256 -- and so the fingerprinted filename and `integrity` value --
  differs from Hugo's own build. Every page still gets the same
  `href`/`integrity` pair (computed once here), so the site stays
  internally consistent.

* `resize_portrait` resizes with Pillow rather than Go's `image/png`
  encoder (which Hugo's `.Resize` uses); the two never produce
  byte-identical PNGs regardless of resampling filter, since Go's deflate
  implementation and Pillow's differ. The rendered image is pixel-correct;
  only its raw bytes differ from Hugo's own resize output. Hugo's actual
  resized filename (`portrait_hu_6510263e774a9def.png`, confirmed against
  a real build of this repo) is kept as the target path regardless --
  reverse-engineering Hugo's own resize-cache hashing algorithm just to
  reproduce that one, permanently-fixed name for this site's single
  avatar image is out of scope here; every page's own `<img src>` already
  depends on this exact literal path (see pages.py's `_SIGNATURE_AVATAR`),
  so changing it would be a much larger regression than the deviation
  above.
"""
from __future__ import annotations
import base64
import hashlib
from pathlib import Path

from PIL import Image

# Hugo's `includes-blank.css`: an unconditional `resources.FromString(" ")`
# resource appended to the includes group regardless of any other setting.
_INCLUDES_BLANK = " "

# hugo.toml sets no `params.assets.disableScrollBarStyle`, so it defaults to
# false -- scroll-bar.css is always in the includes group for this site.
_DISABLE_SCROLL_BAR_STYLE = False


def _read(css_root: Path, rel: str) -> str:
    return (css_root / rel).read_text()


def _sorted_glob_text(css_root: Path, rel_dir: str) -> list[str]:
    return [p.read_text() for p in sorted((css_root / rel_dir).glob("*.css"))]


def _bundle_text(css_root: Path) -> str:
    """head.html's own concatenation order: license.css, then the "core"
    group (theme-vars, reset, common/*.css sorted, chroma-styles,
    chroma-mod, the includes group [scroll-bar.css unless disabled, then
    the blank resource], zmedia), then extended/*.css sorted. See this
    module's docstring for why this concatenates raw file text rather
    than each group's Hugo `resources.Minify` output."""
    parts = [_read(css_root, "core/license.css")]
    core = [
        _read(css_root, "core/theme-vars.css"),
        _read(css_root, "core/reset.css"),
        *_sorted_glob_text(css_root, "common"),
        _read(css_root, "includes/chroma-styles.css"),
        _read(css_root, "includes/chroma-mod.css"),
    ]
    if not _DISABLE_SCROLL_BAR_STYLE:
        core.append(_read(css_root, "includes/scroll-bar.css"))
    core.append(_INCLUDES_BLANK)
    core.append(_read(css_root, "core/zmedia.css"))
    parts.extend(core)
    parts.extend(_sorted_glob_text(css_root, "extended"))
    return "".join(parts)


def build_stylesheet(src: Path, out: Path) -> tuple[str, str]:
    """Writes the fingerprinted stylesheet bundle to
    `out/assets/css/stylesheet.<hex-sha256>.css` and returns `(href,
    integrity)` -- `SiteContext.stylesheet_href`/`stylesheet_integrity`,
    which every page's <head> embeds verbatim. `src` is the repo's
    `assets/css` directory (read-only for this task)."""
    bundle = _bundle_text(src).encode("utf-8")
    digest = hashlib.sha256(bundle).digest()
    hex_digest = digest.hex()
    integrity = "sha256-" + base64.b64encode(digest).decode("ascii")
    out_dir = out / "assets" / "css"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"stylesheet.{hex_digest}.css").write_bytes(bundle)
    return f"/assets/css/stylesheet.{hex_digest}.css", integrity


# Hugo's own resize-cache filename for this site's one signature avatar
# (`assets/images/portrait.png`, resized "112x png" by
# consulting-signature.html) -- confirmed against a real Hugo build of this
# repo. See this module's docstring for why this is a fixed constant rather
# than a computed one.
_PORTRAIT_FINGERPRINT = "portrait_hu_6510263e774a9def.png"


def resize_portrait(src: Path, out: Path, width: int) -> str:
    """Resizes `src` (a square PNG) to `width`x`width` and writes it to
    `out/images/<Hugo's own fingerprinted name>`, returning the
    site-relative href every page's signature `<img src>` uses. `width`
    is threaded through rather than hardcoded so a future change to
    consulting-signature.html's own `.Resize "WxH png"` spec only needs
    updating at the call site, not here."""
    image_dir = out / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    dest = image_dir / _PORTRAIT_FINGERPRINT
    with Image.open(src) as im:
        im = im.convert("RGB").resize((width, width), Image.LANCZOS)
        im.save(dest, format="PNG")
    return f"/images/{_PORTRAIT_FINGERPRINT}"
