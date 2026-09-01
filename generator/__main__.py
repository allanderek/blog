"""CLI entry point: `python3 -m generator build --out DIR` /
`python3 -m generator serve [--port 8080]`."""
from __future__ import annotations
import argparse
from pathlib import Path

from . import site

def serve(port: int = 8080) -> None:
    """Builds into a scratch directory, then serves it with the stdlib's
    own `http.server` -- no live reload: re-run this command after
    editing anything (content, templates-equivalent Python, CSS)."""
    import functools
    import http.server
    import socketserver

    out = Path("/tmp/blog-dev")
    site.build(out)
    handler = functools.partial(http.server.SimpleHTTPRequestHandler,
                                 directory=str(out))
    print(f"serving {out} at http://localhost:{port}")
    socketserver.TCPServer(("", port), handler).serve_forever()

def main() -> None:
    parser = argparse.ArgumentParser(prog="generator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build the site")
    build_parser.add_argument("--out", required=True, type=Path)

    serve_parser = subparsers.add_parser("serve", help="Build, then serve over HTTP")
    serve_parser.add_argument("--port", default=8080, type=int)

    args = parser.parse_args()
    if args.command == "build":
        site.build(args.out)
    elif args.command == "serve":
        serve(args.port)

if __name__ == "__main__":
    main()
