#!/usr/bin/env python3
"""Print the project entry and the v4 using-memory rules without writing files."""

import argparse
from pathlib import Path
import re


def context(readme, entry_only=False):
    text = readme.read_text(encoding="utf-8")
    yield f"# Project entry: {readme}\n\n{text}"
    if entry_only:
        return
    front = re.match(r"\A---\s*\n(.*?)\n---(?:\s*\n|$)", text, re.S)
    formats = re.findall(r"(?m)^ssot_format:([^\n]*)$", front[1]) if front else []
    if len(formats) != 1 or not re.fullmatch(
            r"[ \t]*(?:4|'4'|\"4\")[ \t]*(?:#.*)?", formats[0]):
        return
    model = Path(__file__).resolve().parents[2] / "references/memory-model.md"
    yield f"# Using-memory rules: {model}"
    sections = re.split(r"(?m)(?=^## \d+\. )", model.read_text(encoding="utf-8"))
    for number in (1, 3, 5):
        section = next(s for s in sections if s.startswith(f"## {number}. "))
        if number == 3:
            section = section.split("### Human-decision evidence", 1)[0]
        yield section.rstrip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("readme", type=Path, nargs="?", default=Path("SSOT/README.md"))
    parser.add_argument("--entry-only", action="store_true",
                        help="Refresh the entry when using-memory rules remain in context")
    args = parser.parse_args()
    print("\n\n".join(context(args.readme, args.entry_only)))
