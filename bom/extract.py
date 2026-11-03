#!/usr/bin/env python3
"""
Extract per-symbol component data from the KiCad schematic hierarchy.

Parses the .kicad_sch s-expressions directly so we get one record per
reference designator, including the bare (dnp) and (exclude_from_bom)
tokens which kicad-cli's BOM exporter folds away.

Outputs bom/symbols.json
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Every sheet in the hierarchy, INCLUDING the root. The root sheet carries the
# 23-way edge connectors (J1/J2/J3) and the mounting holes, so leaving it out
# silently drops parts from the BOM.
SHEETS = [
    "controller.kicad_sch",
    "power.kicad_sch",
    "lpt.kicad_sch",
    "grbl-interface.kicad_sch",
    "conn.kicad_sch",
]

FIELDS = [
    "Reference", "Value", "Footprint", "Datasheet", "Description",
    "E14MFR#", "E14PART", "E14MOQ", "Marking",
    "JLCPART", "JLCMFR#", "JLCMOQ", "LCSC", "LCSCMFR#",
]


def unescape(s: str) -> str:
    return s.replace('\\"', '"').replace("\\\\", "\\")


def parse_schematic(path: Path) -> list[dict]:
    """Split a .kicad_sch into top-level symbol instance blocks."""
    text = path.read_text(encoding="utf-8")

    # Top-level symbol instances start with a line consisting of 2 tabs + "(symbol"
    # Sub-units inside lib_symbols are nested deeper, so this reliably isolates
    # placed instances.
    chunks = re.split(r"\n\t\(symbol\n", text)

    prop_re = re.compile(r'\(property "([^"]*)" "((?:[^"\\]|\\.)*)"')
    out = []

    for chunk in chunks[1:]:
        # The block ends at the next top-level close; being generous is fine
        # since we only harvest properties and bare tokens.
        block = chunk.split("\n\t(symbol\n")[0]

        props = {k: unescape(v) for k, v in prop_re.findall(block)}
        ref = props.get("Reference", "")
        if not ref or not re.match(r"^[A-Za-z]+\d", ref):
            continue

        rec = {f: props.get(f, "") for f in FIELDS}
        rec["Ref"] = ref
        rec["sheet"] = path.name
        # KiCad 10 uses (dnp yes/no) / (in_bom yes/no) / (on_board yes/no)
        rec["dnp"] = bool(re.search(r"^\s*\(dnp yes\)", block, re.M))
        rec["exclude_from_bom"] = bool(
            re.search(r"^\s*\(in_bom no\)", block, re.M)
        )
        rec["on_board"] = not bool(re.search(r"^\s*\(on_board no\)", block, re.M))
        out.append(rec)

    return out


def main() -> int:
    symbols: list[dict] = []
    for sheet in SHEETS:
        p = ROOT / sheet
        if not p.exists():
            print(f"!! missing sheet: {sheet}", file=sys.stderr)
            continue
        symbols.extend(parse_schematic(p))

    def sort_key(r: dict) -> tuple:
        m = re.match(r"^([A-Za-z]+)(\d+)", r["Ref"])
        if not m:
            return (r["Ref"], 0)
        return (m.group(1), int(m.group(2)))

    symbols.sort(key=sort_key)

    dst = ROOT / "bom" / "symbols.json"
    dst.write_text(json.dumps(symbols, indent=2))

    print(f"{len(symbols)} symbols -> {dst.relative_to(ROOT)}")

    dnp = [s["Ref"] for s in symbols if s["dnp"]]
    xbom = [s["Ref"] for s in symbols if s["exclude_from_bom"]]
    print(f"  dnp:              {len(dnp):>3}  {' '.join(dnp)}")
    print(f"  exclude_from_bom: {len(xbom):>3}  {' '.join(xbom)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
