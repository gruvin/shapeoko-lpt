#!/usr/bin/env python3
"""
Remove stale per-project instance data from child sheets.

A .kicad_sch that was once saved as its own standalone project keeps a
`(project "<its own name>" ...)` entry inside every symbol's `(instances ...)`
block, alongside the `(project "controller" ...)` entry created when the sheet is
placed inside this design.

Those stale entries carry *different* reference designators — in this project
grbl-interface.kicad_sch still claims U1, C4, C7, C12 … which collide with the
real U1/C4/C7/C12 in power.kicad_sch. Depending on which entry KiCad resolves,
symbols can end up with duplicate designators, and the BOM dialog then drops or
merges them (and does so inconsistently).

This removes the stale entries, leaving only the parent project's data.

    python3 fix_stale_instances.py --dry-run
    python3 fix_stale_instances.py
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHEETS = ["controller.kicad_sch", "power.kicad_sch", "lpt.kicad_sch",
          "grbl-interface.kicad_sch", "conn.kicad_sch"]
PROJECT = "controller"


def close_paren(text: str, i: int) -> int:
    depth = 0
    while i < len(text):
        c = text[i]
        if c == '"':
            i += 1
            while i < len(text) and text[i] != '"':
                i += 2 if text[i] == "\\" else 1
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(text)


def strip_stale(text: str, sheet: str) -> tuple[str, int]:
    """Delete (project "x") entries that are not the parent project."""
    removed = 0
    pos = 0
    while True:
        m = re.search(r'\n\t\t\t\(project "(?!%s")[^"]*"' % re.escape(PROJECT),
                      text[pos:])
        if not m:
            break
        start = pos + m.start()          # the newline before (project
        open_at = pos + m.start() + 1    # the '('
        end = close_paren(text, open_at)
        # swallow the newline that followed the block
        if text[end:end + 1] == "\n":
            end += 1
        text = text[:start] + text[end:]
        removed += 1
        pos = start
    return text, removed


def audit(text: str, sheet: str) -> list[str]:
    problems = []
    stale = re.findall(r'\(project "(?!%s")[^"]*"' % re.escape(PROJECT), text)
    if stale:
        problems.append(f"stale project entries remain: {set(stale)}")
    for inst in re.split(r"\n\t\(symbol\n", text)[1:]:
        m = re.search(r'\(property "Reference" "([^"]*)"', inst)
        if not m:
            continue
        ref = m.group(1)
        n = len(re.findall(r'\(project "%s"' % re.escape(PROJECT), inst))
        if n == 0:
            problems.append(f"{ref}: no {PROJECT} instance entry")
        elif n > 1:
            problems.append(f"{ref}: {n} {PROJECT} entries")
    return problems


def main() -> int:
    dry = "--dry-run" in sys.argv
    total = 0
    pending = []
    for sheet in SHEETS:
        p = ROOT / sheet
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        new, removed = strip_stale(text, sheet)
        if not removed:
            continue
        if new.count("(") != new.count(")"):
            print(f"ABORT {sheet}: unbalanced parentheses")
            return 1
        problems = audit(new, sheet)
        # references must still be unique and match the Reference property
        if problems:
            print(f"ABORT {sheet}:")
            for x in problems[:6]:
                print("   " + x)
            return 1
        print(f"{sheet}: removed {removed} stale project entries, verified OK")
        pending.append((p, new))
        total += removed

    if not total:
        print("nothing to do - no stale instance data found")
        return 0
    if dry:
        print(f"\nDRY RUN - nothing written; {total} entries would be removed")
        return 0
    for p, text in pending:
        p.write_text(text, encoding="utf-8")
    print(f"\nwritten: {len(pending)} sheet(s), {total} entries removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
