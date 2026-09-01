"""CLI entry point: `python3 -m generator build --out DIR`."""
from __future__ import annotations
import argparse
from pathlib import Path

from . import site

def main() -> None:
    parser = argparse.ArgumentParser(prog="generator")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build the site")
    build_parser.add_argument("--out", required=True, type=Path)

    args = parser.parse_args()
    if args.command == "build":
        site.build(args.out)

if __name__ == "__main__":
    main()
