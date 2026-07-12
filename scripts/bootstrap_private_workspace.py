#!/usr/bin/env python3
"""Create a local private workspace outside the public engine."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=os.getenv("ROBOFOX_GTM_WORKSPACE", "~/private/robofox-gtm-workspace"))
    args = parser.parse_args()
    root = Path(args.path).expanduser().resolve()
    engine = Path(__file__).resolve().parents[1]
    try:
        root.relative_to(engine)
        raise SystemExit("Refusing to create the private workspace inside the public engine.")
    except ValueError:
        pass

    for directory in ("products", "markets", "customers", "evidence", "experiments", "decisions", "outcomes", "snapshots", "drafts", "audit"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    (root / ".gitignore").write_text(".env\nsecrets/\ncredentials/\n*.log\n", encoding="utf-8")
    (root / "workspace.json").write_text(json.dumps({
        "classification": "INTERNAL",
        "public_repo": False,
        "timezone": "Asia/Kolkata",
        "external_execution": False,
        "customer_identifiers_enabled": False,
    }, indent=2) + "\n", encoding="utf-8")
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
