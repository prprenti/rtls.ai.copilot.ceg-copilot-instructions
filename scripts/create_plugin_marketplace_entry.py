#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from validate_plugin_metadata import (
    RunResult,
    apply_local_plugin_requirements,
    build_marketplace_entry,
    detect_repo_mode,
    resolve_repo_root,
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Emit marketplace JSON for a single plugin repository.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=argparse.SUPPRESS,
        help=(
            "single-plugin repository root containing a root-level plugin.json; if omitted, "
            "search upward from the current directory and the script location"
        ),
    )
    parser.add_argument(
        "--repo",
        default="OWNER/REPO",
        help="owner/repo source to include in the emitted marketplace entry",
    )
    parser.add_argument(
        "--ref",
        default="",
        help="branch, tag, or commit to include in the emitted marketplace entry",
    )
    parser.add_argument(
        "--path",
        default="",
        help="plugin root path within the source repository",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        root = resolve_repo_root(getattr(args, "repo_root", None), Path(__file__))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if detect_repo_mode(root) != "plugin":
        print(
            (
                f"{root}: create_plugin_marketplace_entry.py requires a single-plugin repository root "
                "with a root-level plugin.json. Use --repo-root to point at the plugin repository or plugin directory."
            ),
            file=sys.stderr,
        )
        return 1

    result = RunResult()
    try:
        manifest = apply_local_plugin_requirements(root, apply=False, result=result)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if result.violations:
        for violation in result.violations:
            print(f"{violation.path}: {violation.message}", file=sys.stderr)
        return 1

    try:
        entry = build_marketplace_entry(manifest, repo=args.repo, ref=args.ref, path=args.path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(entry, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))