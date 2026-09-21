"""CLI entry point: `python3 -m generator build --out DIR` /
`python3 -m generator serve [--port 8080] [--no-watch]`."""
from __future__ import annotations
import argparse
import http.server
import shutil
import sys
import tempfile
import threading
import time
from pathlib import Path

from . import content, site

# Everything a build reads. Split in two because a change to each needs a
# different response: content can be rebuilt in place, but the generator is
# already imported into this process and a rebuild would silently keep using
# the old code -- so that case asks for a restart rather than pretending.
_CONTENT_DIRS = (Path("content"), Path("css"), Path("static"))
_CODE_DIRS = (Path("generator"),)

_POLL_SECONDS = 0.5


def _fingerprint(dirs: tuple[Path, ...]) -> dict[str, tuple[float, int]]:
    """Path -> (mtime, size) for every file under `dirs`.

    Polling beats a watchdog dependency here: a few hundred stat calls twice
    a second is nothing next to a 0.4s rebuild, and it has no platform
    quirks. Size is included because mtime alone has coarse resolution on
    some filesystems, and an editor can write twice within one tick.
    """
    out: dict[str, tuple[float, int]] = {}
    for root in dirs:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.is_file() and "__pycache__" not in path.parts:
                stat = path.stat()
                out[str(path)] = (stat.st_mtime, stat.st_size)
    return out


def _build_into_fresh_dir() -> Path:
    """Build into a brand-new directory and return it.

    Deliberately NOT a rebuild in place. `site.build` writes files but never
    removes them, so building over a previous run would leave the page of a
    post you just deleted sitting there being served -- and an internal link
    to it would keep passing locally while breaking on production, which
    rebuilds from nothing. A fresh directory each time gives the dev server
    the same from-blank semantics as the real build.
    """
    out = Path(tempfile.mkdtemp(prefix="blog-dev-"))
    site.build(out)
    return out


def serve(port: int = 8080, watch: bool = True) -> None:
    """Build, then serve over HTTP, rebuilding when anything changes.

    A rebuild is a FULL rebuild into a fresh directory, not a patch of the
    page you touched. That is affordable because the render caches make a
    warm rebuild take about 0.4s (see markdown.py's "Render caching"), and
    it is what keeps the dev server honest: no incremental-update bugs, and
    no stale page surviving a deletion.
    """
    current = _build_into_fresh_dir()

    class Handler(http.server.SimpleHTTPRequestHandler):
        # Read the directory per request rather than binding it once, so a
        # rebuild can swap in a new tree between requests.
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(current), **kwargs)

        def log_message(self, fmt, *args):
            pass  # a request log per asset drowns out the rebuild messages

    # ThreadingHTTPServer, not socketserver.TCPServer: it sets
    # allow_reuse_address, without which sockets left in TIME_WAIT on the
    # port block a rebind for about a minute after a Ctrl-C -- reported as
    # "Address already in use" while `lsof -i:8080` shows nothing, because a
    # TIME_WAIT socket has no owning process. Threading also stops one
    # browser keep-alive connection stalling every other request.
    try:
        httpd = http.server.ThreadingHTTPServer(("", port), Handler)
    except OSError as exc:
        # Bind first, announce second. The old code printed "serving ..."
        # before binding, so a failure looked like a server that had started
        # and then died.
        print(f"Cannot listen on port {port}: {exc}", flush=True)
        print(f"Something else may be using it: try `ss -tlnp 'sport = :{port}'`,", flush=True)
        print("or run with a different --port.", flush=True)
        raise SystemExit(1)

    def swap(new_dir: Path) -> None:
        nonlocal current
        previous, current = current, new_dir
        shutil.rmtree(previous, ignore_errors=True)

    print(f"serving {current} at http://localhost:{port}", flush=True)
    if watch:
        print(f"watching {', '.join(str(d) for d in _CONTENT_DIRS)} "
              f"-- edit and save, then reload the page", flush=True)
        threading.Thread(target=_watch, args=(swap,), daemon=True).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        httpd.server_close()
        shutil.rmtree(current, ignore_errors=True)


def _watch(swap) -> None:
    """Poll for changes; rebuild content, ask for a restart on code."""
    content_seen = _fingerprint(_CONTENT_DIRS)
    code_seen = _fingerprint(_CODE_DIRS)
    warned_about_code = False

    while True:
        time.sleep(_POLL_SECONDS)

        code_now = _fingerprint(_CODE_DIRS)
        if code_now != code_seen:
            code_seen = code_now
            if not warned_about_code:
                print("generator/ changed -- restart the dev server to pick "
                      "it up (this process already imported the old code)", flush=True)
                warned_about_code = True
            continue

        content_now = _fingerprint(_CONTENT_DIRS)
        if content_now == content_seen:
            continue
        changed = _describe(content_seen, content_now)
        content_seen = content_now

        started = time.time()
        try:
            new_dir = _build_into_fresh_dir()
        except Exception as exc:
            # Keep serving the last good build. A half-typed front matter
            # block should not take the site down until the next save.
            print(f"{changed}: build FAILED, still serving the previous one", flush=True)
            print(f"  {type(exc).__name__}: {exc}", flush=True)
            continue
        swap(new_dir)
        print(f"{changed}: rebuilt in {time.time() - started:.1f}s", flush=True)


def _describe(before: dict, after: dict) -> str:
    """A short "what changed" for the rebuild line."""
    added = set(after) - set(before)
    removed = set(before) - set(after)
    modified = {p for p in set(before) & set(after) if before[p] != after[p]}
    for label, paths in (("deleted", removed), ("added", added), ("changed", modified)):
        if paths:
            first = sorted(paths)[0]
            extra = f" (+{len(paths) - 1} more)" if len(paths) > 1 else ""
            return f"{first} {label}{extra}"
    return "changed"


def new(slug: str, title: str | None) -> None:
    """Create an empty post and print its path.

    The path is the ONLY thing on stdout, so the command composes:
    `$EDITOR $(./new-post.sh my-post)` in bash, `e (./new-post.sh my-post)`
    in fish. Anything friendly goes to stderr, where a command
    substitution will not pick it up.
    """
    try:
        path = content.new_post(Path("content/posts"), slug, title)
    except (ValueError, FileExistsError) as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
    print(f"created {path}", file=sys.stderr)
    print(path)

def main() -> None:
    parser = argparse.ArgumentParser(prog="generator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build the site")
    build_parser.add_argument("--out", required=True, type=Path)

    serve_parser = subparsers.add_parser("serve", help="Build, then serve over HTTP")
    serve_parser.add_argument("--port", default=8080, type=int)
    serve_parser.add_argument("--no-watch", action="store_true",
                              help="Do not rebuild when files change")

    new_parser = subparsers.add_parser("new", help="Create an empty post")
    new_parser.add_argument("slug", help="lowercase-hyphenated; becomes the URL")
    new_parser.add_argument("title", nargs="?", default=None,
                            help="defaults to the slug, sentence-cased")

    args = parser.parse_args()
    if args.command == "build":
        site.build(args.out)
    elif args.command == "serve":
        serve(args.port, watch=not args.no_watch)
    elif args.command == "new":
        new(args.slug, args.title)


if __name__ == "__main__":
    main()
