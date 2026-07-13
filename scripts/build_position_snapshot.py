#!/usr/bin/env python3
"""Generate a redacted, traceable commercial-position snapshot."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from robofox_truth.position import build_and_write  # noqa: E402
from robofox_truth.validation import TruthStoreError  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("product", help="lowercase kebab-case product slug")
    parser.add_argument("--workspace", help="private workspace path")
    parser.add_argument("--as-of", help="timezone-aware ISO-8601 position time")
    parser.add_argument("--stdout", action="store_true", help="also print the JSON snapshot")
    args = parser.parse_args(argv)
    try:
        snapshot, json_path, markdown_path = build_and_write(args.workspace, args.product, as_of=args.as_of)
    except (TruthStoreError, OSError) as exc:
        print(f"POSITION SNAPSHOT: FAIL\n- {exc}", file=sys.stderr)
        return 1
    if args.stdout:
        print(json.dumps(snapshot, indent=2, ensure_ascii=False))
    print(json.dumps({"json": str(json_path), "markdown": str(markdown_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
