#!/usr/bin/env python3
"""Fail when a repository Markdown link points to a missing local target."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "tel:", "data:", "#")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    errors: list[str] = []
    checked = 0
    for document in sorted(root.rglob("*.md")):
        if ".git" in document.parts:
            continue
        text = document.read_text(encoding="utf-8")
        for match in LINK.finditer(text):
            raw = match.group(1).strip()
            if raw.startswith(SKIP_PREFIXES):
                continue
            if raw.startswith("<") and raw.endswith(">"):
                raw = raw[1:-1]
            raw = raw.split("#", 1)[0]
            if not raw:
                continue
            target = Path(unquote(raw))
            resolved = target if target.is_absolute() else document.parent / target
            checked += 1
            if not resolved.exists():
                line = text.count("\n", 0, match.start()) + 1
                errors.append(f"{document.relative_to(root)}:{line}: missing {raw}")
    if errors:
        print("\n".join(errors))
        raise SystemExit(1)
    print(f"Markdown local links: PASS ({checked} targets checked)")


if __name__ == "__main__":
    sys.exit(main())
