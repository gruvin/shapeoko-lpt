#!/usr/bin/env python3
"""
Generate a PCBWay-format BOM spreadsheet from the resolved BOM.

Reads bom/controller-bom.csv (produced by resolve.py) and writes
bom/controller-PCBWay.xlsx using PCBWay's own sample workbook as a template, so
their logo, title, header styling, column widths and instruction footer are all
preserved. Only the data rows are replaced.

    python3 bom/make_pcbway_bom.py                 # 62 rows
    python3 bom/make_pcbway_bom.py --boards 10     # also puts "10PCS" in the title
    python3 bom/make_pcbway_bom.py --tht omit      # leave THT lines out entirely

Requires openpyxl (Homebrew python: pip install --break-system-packages openpyxl).
"""

import argparse
import copy
import csv
import json
import re
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
BOM = ROOT / "bom"
TEMPLATE = Path.home() / "Desktop" / "a-sample-of-PCBWay-BOM.xlsx"
OUT = BOM / "controller-PCBWay.xlsx"

# Data occupies these rows in the sample; the styled footer starts after them.
FIRST_DATA_ROW = 7
SAMPLE_DATA_ROWS = 15   # data rows 7..21 in the sample
NCOLS = 9

# footprint -> short package label, checked in order. First match wins.
PKG_RULES: list[tuple[str, str]] = [
    (r"_(\d{4})_\d{4}Metric", r"\1"),
    (r"C_(\d{4})_\d{4}Metric", r"\1"),
    (r"CP_Elec_([\d.]+)x([\d.]+)", r"Elec \1x\2"),
    (r"VQFN-(\d+)", r"VQFN-\1"),
    (r"TQFP-(\d+)", r"TQFP-\1"),
    (r"LQFP-(\d+)", r"LQFP-\1"),
    (r"SOIC-(\d+W?)", r"SOIC-\1"),
    (r"SO-(\d+)", r"SO-\1"),
    (r"SOT-(\d+-\d+|23)", r"SOT-\1"),
    (r"SOD-(\d+)", r"SOD-\1"),
    (r"D_SMA", "SMA"),
    (r"D_SMB", "SMB"),
    (r"SMA_DOT", "SMA"),
    (r"TO-(\d+-\d+)", r"TO-\1"),
    (r"TO-(\d+)", r"TO-\1"),
    (r"L_(\d+)x(\d+)mm", r"\1x\2"),
    (r"L_(\d{4})_", r"\1"),
    (r"R_Array_Convex_4x(\d{4})", r"4x\1"),
    (r"R_Array_Convex_(\d+)x(\d+)", r"\1x\2"),
    (r"PinHeader_(\d+)x(\d+)_P([\d.]+)mm", r"\1x\2 P\3"),
    (r"PinSocket_(\d+)x(\d+)_P([\d.]+)mm", r"\1x\2 P\3"),
    (r"CFPX-\d+-4Pin_([\d.]+)x([\d.]+)mm", r"\1x\2 4pin"),
    (r"USB_Mini-B", "USB Mini-B"),
    (r"KYCON_KPJX-(\w+)", r"KPJX-\1"),
    (r"Molex_Micro-Fit_3\.0_43045-\d+_(\d+x\d+)", r"Micro-Fit \1"),
    (r"Molex_KK-254_\S+_(\d+x\d+)", r"KK254 \1"),
    (r"DSUB-(\d+)", r"DSUB-\1"),
    (r"Relay_SPST_OJS", "OJS relay"),
    (r"SW_Push_1P1T_NO_XUNPU_\S+", "3.9x3.0mm tact"),
    (r"ISP_SMD_100mil", "2x03 2.54 SMD"),
    (r"LED_(\d{4})_DOT", r"\1"),
    (r"NetTie-2_SMD_Pad", "nettie"),
    (r"TerminalBlock_Phoenix_MPT-0,5-(\d+)-([\d.]+)", r"MPT 1x\1 P\2"),
    (r"TerminalBlock_Phoenix_MKDS-1,5-(\d+)-([\d.]+)", r"MKDS 1x\1 P\2"),
]

# Lines sourced outside element14 get a note so PCBWay can match or consign them.
SUPPLIER_NOTES = {
    "DigiKey": "Consigned - DigiKey {sku}",
    "LCSC": "LCSC {sku}",
}


def package_label(footprint: str) -> str:
    fp = footprint.split(":")[-1]
    for pat, rep in PKG_RULES:
        m = re.search(pat, fp)
        if m:
            return m.expand(rep.replace(r"\1", r"\g<1>").replace(r"\g<1>", r"\1"))
    return fp[:24]


def expand_refs(row: dict, by_range: dict[str, list[str]]) -> list[str]:
    refs = by_range.get(row["refs"])
    if refs:
        return refs
    return [r.strip() for r in row["refs"].split(",") if r.strip()]


def build_rows(include_tht: bool) -> tuple[list[list], dict]:
    rows = list(csv.DictReader((BOM / "controller-bom.csv").open()))
    groups = json.loads((BOM / "groups.json").read_text())["groups"]
    by_range = {g["ref_range"]: g["refs"] for g in groups}

    out, stats = [], {"SMD": 0, "thru-hole": 0, "skipped": 0}
    for r in rows:
        if r["assembly"] == "THT":
            if not include_tht:
                stats["skipped"] += 1
                continue
            kind = "thru-hole"
        else:
            kind = "SMD"

        refs = expand_refs(r, by_range)
        notes = ""
        tmpl = SUPPLIER_NOTES.get(r["supplier"])
        if tmpl:
            notes = tmpl.format(sku=r["sku"] or r["mpn"])

        out.append([
            len(out) + 1,
            ",".join(refs),
            int(r["qty"]),
            r["brand"],
            r["mpn"],
            r["desc"] or r["value"],
            package_label(r["footprint"]),
            kind,
            notes,
        ])
        stats[kind] += 1
    return out, stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boards", type=int, default=1,
                    help="assembled board quantity for the title (default 1 - this is "
                         "the assembly BOM; the bare-PCB order is a separate 5-off run)")
    ap.add_argument("--tht", choices=["mark", "omit"], default="mark",
                    help="include THT lines marked 'thru-hole' (default) or omit")
    ap.add_argument("--title", default="Shapeoko LPT Controller")
    ap.add_argument("--template", type=Path, default=TEMPLATE)
    ap.add_argument("-o", "--output", type=Path, default=OUT)
    args = ap.parse_args()

    if not args.template.exists():
        print(f"template not found: {args.template}")
        return 1

    rows, stats = build_rows(args.tht == "mark")

    wb = openpyxl.load_workbook(args.template)
    ws = wb["Sheet1"]

    # keep the styling of the sample's first data row, column by column
    proto = [copy.copy(ws.cell(FIRST_DATA_ROW, c)._style) for c in range(1, NCOLS + 1)]
    proto_height = ws.row_dimensions[FIRST_DATA_ROW].height

    # Snapshot everything below the sample's data block (the instruction footer,
    # including its hyperlinks) so it can be re-emitted after our own rows.
    # Deleting/inserting rows with openpyxl silently strands cells that carry a
    # hyperlink, so the tail is rebuilt rather than shifted.
    tail = []
    markup_start = FIRST_DATA_ROW + SAMPLE_DATA_ROWS
    for r in range(markup_start, ws.max_row + 1):
        cells = []
        for c in range(1, NCOLS + 1):
            cell = ws.cell(r, c)
            cells.append((cell.value, copy.copy(cell._style),
                          cell.hyperlink.target if cell.hyperlink else None))
        tail.append((ws.row_dimensions[r].height, cells))

    # Merged ranges are NOT moved by delete_rows/insert_rows, so the footer's
    # A:I merges would still sit over the data rows and swallow every write to
    # columns B..I. Unmerge anything below the header, remembering which footer
    # rows to re-merge once they are rewritten.
    span_merged: set[int] = set()
    for m in list(ws.merged_cells.ranges):
        if m.min_row < FIRST_DATA_ROW:
            continue                      # keep the title / logo merges
        if m.min_col == 1 and m.max_col == NCOLS:
            for r in range(m.min_row, m.max_row + 1):
                span_merged.add(r - markup_start)
        ws.unmerge_cells(str(m))

    # wipe everything below the header and lay our own block out from scratch
    ws.delete_rows(FIRST_DATA_ROW, ws.max_row - FIRST_DATA_ROW + 1)

    for i, values in enumerate(rows):
        r = FIRST_DATA_ROW + i
        for c, val in enumerate(values, start=1):
            cell = ws.cell(r, c)
            cell.value = val
            cell._style = copy.copy(proto[c - 1])
        if proto_height:
            ws.row_dimensions[r].height = proto_height

    # re-emit the footer immediately after the data
    for j, (height, cells) in enumerate(tail):
        r = FIRST_DATA_ROW + len(rows) + j
        for c, (val, style, link) in enumerate(cells, start=1):
            cell = ws.cell(r, c)
            cell.value = val
            cell._style = copy.copy(style)
            if link:
                cell.hyperlink = link
        if height:
            ws.row_dimensions[r].height = height
        if j in span_merged:
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=NCOLS)

    title = args.title
    if args.boards:
        title += f" {args.boards}PCS BOM"
    else:
        title += " BOM"
    ws.cell(2, 4).value = title

    args.output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(args.output)

    print(f"{args.output.relative_to(ROOT)}: {len(rows)} rows "
          f"({stats['SMD']} SMD, {stats['thru-hole']} thru-hole"
          + (f", {stats['skipped']} THT omitted" if stats["skipped"] else "") + ")")
    print(f"  title: {title}")

    # required-field check
    bad = [(v[1], col) for v in rows
           for col, val in (("Designator", v[1]), ("Qty", v[2]),
                            ("Mfg Part #", v[4]), ("Package", v[6]))
           if val in (None, "")]
    if bad:
        print(f"  WARNING: {len(bad)} rows with a blank required field:")
        for refs, col in bad[:8]:
            print(f"    {refs}: {col}")
        return 1
    print("  all required fields populated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
