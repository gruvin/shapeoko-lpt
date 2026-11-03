#!/usr/bin/env python3
"""
Write the resolved BOM data back into the KiCad schematics.

This is the "never do this by hand again" step: after resolve.py has settled on
a part for every line, push it back into the symbol fields so the schematic is
the source of truth.

Fields written (his existing per-distributor convention, plus a few additions):

    E14MFR#      manufacturer part number   (always)
    E14PART      element14 order code       (element14 lines)
    E14MOQ       element14 MOQ              (element14 lines)
    MFR          brand / manufacturer name  (always)          [new]
    Description  part description           (always)
    Datasheet    datasheet URL              (always, when known)
    DKPART       DigiKey part number        (DigiKey lines)    [new]
    ALT          alternate source, if any   (rare)             [new]

Value is deliberately NOT touched: it is the functional label used for
silkscreen and netlist meaning ("YELLOW", "RESET", "DB25_PINS_MountingHoles"),
not a part number.

Usage:
    python3 apply_fields.py --dry-run     # show what would change
    python3 apply_fields.py               # write
"""

import csv
import json
import re
import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOM = ROOT / "bom"

SHEETS = ["controller.kicad_sch", "power.kicad_sch", "lpt.kicad_sch",
          "grbl-interface.kicad_sch", "conn.kicad_sch"]

# Order matters only for insertion position: new fields are appended after the
# last existing one, so they end up in a predictable place.
FILL_IF_EMPTY = {"Datasheet", "Description"}

# Metadata is for the BOM, not for the drawing. These are forced hidden so a
# long element14 description never lands on top of the schematic.
HIDE_ALWAYS = {"E14MFR#", "E14PART", "E14MOQ", "MFR", "DKPART", "ALT",
               "LCSC", "LCSCMFR#", "Description", "Datasheet"}

HIDDEN_TEMPLATE = """\t\t(property "{name}" "{value}"
\t\t\t(at {x} {y} 0)
\t\t\t(hide yes)
\t\t\t(show_name no)
\t\t\t(do_not_autoplace no)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t)
\t\t)
"""


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def build_updates() -> dict[str, dict[str, str]]:
    """ref -> {field: value} from the resolved BOM.

    The BOM's `refs` column is a compressed range ("R25-R29,R31-R32"), so the
    individual designators are taken from groups.json, which has the expanded
    list per line. Splitting the compressed string would silently skip whole
    groups.
    """
    rows = list(csv.DictReader((BOM / "controller-bom.csv").open()))
    groups = json.loads((BOM / "groups.json").read_text())["groups"]
    refs_by_range = {g["ref_range"]: g["refs"] for g in groups}
    out: dict[str, dict[str, str]] = {}
    for r in rows:
        if not r["mpn"]:
            continue
        fields: dict[str, str] = {}
        fields["E14MFR#"] = r["mpn"]
        fields["MFR"] = r["brand"]
        fields["Description"] = r["desc"]
        # Always write ALT, even when empty, so a superseded note cannot linger.
        # DKPART likewise: only a DigiKey line should carry one.
        fields["ALT"] = r.get("alternates") or ""
        fields["DKPART"] = ""
        if r["supplier"] == "element14":
            fields["E14PART"] = r["sku"]
            if r["moq"]:
                fields["E14MOQ"] = r["moq"]
        elif r["supplier"] == "DigiKey":
            fields["DKPART"] = r["sku"]
            fields["ALT"] = r.get("alternates") or ""
            fields["E14PART"] = ""      # not an element14 part
            fields["E14MOQ"] = ""
        elif r["supplier"] == "LCSC":
            fields["LCSC"] = r["sku"]
            fields["LCSCMFR#"] = r["mpn"]
            fields["E14PART"] = ""
            fields["E14MOQ"] = ""
        if r.get("alternates"):
            fields["ALT"] = r["alternates"]
        refs = refs_by_range.get(r["refs"], [])
        if not refs:                      # fall back for anything unmapped
            refs = [x.strip() for x in r["refs"].split(",") if x.strip()]
        for ref in refs:
            out[ref] = dict(fields)
    # datasheets are per-MPN, fetched from the cache
    ds = datasheets()
    for ref, f in out.items():
        url = ds.get(f.get("E14MFR#", ""))
        if url:
            f["Datasheet"] = url
    return out


def datasheets() -> dict[str, str]:
    """mpn -> datasheet URL, harvested from the cached API responses."""
    out: dict[str, str] = {}
    for f in (BOM / "cache").glob("*.json"):
        try:
            data = json.loads(f.read_text())
        except Exception:  # noqa: BLE001
            continue
        for w in data.values() if isinstance(data, dict) else []:
            if not isinstance(w, dict):
                continue
            for p in w.get("products") or []:
                mpn = p.get("translatedManufacturerPartNumber")
                dss = p.get("datasheets") or []
                if mpn and dss and mpn not in out:
                    url = dss[0].get("url") or ""
                    if url.startswith("http"):
                        out[mpn] = url
    return out


def unesc(s: str) -> str:
    return s.replace('\\"', '"').replace("\\\\", "\\")


def _close_paren(text: str, i: int) -> int:
    """Index just past the ')' that closes the '(' at position i."""
    depth = 0
    while i < len(text):
        c = text[i]
        if c == '"':                      # skip over strings
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


PROP_RE = re.compile(r'\t\t\(property "([^"]*)" "((?:[^"\\]|\\.)*)"')


def update_block(block: str, fields: dict[str, str]) -> tuple[str, list[str]]:
    """Set the given properties inside one symbol block.

    All replacements are collected against the ORIGINAL string and applied
    right-to-left, so earlier edits cannot shift later offsets. (Doing it
    left-to-right in place silently corrupts the file when a new value is a
    different length to the old one.)
    """
    changes: list[str] = []
    repls: list[tuple[int, int, str]] = []

    for m in PROP_RE.finditer(block):
        name = m.group(1)
        if name not in fields:
            continue
        want = fields[name]
        have = unesc(m.group(2))
        if have == want:
            continue
        if name in FILL_IF_EMPTY and have.strip():
            continue                  # keep what is already there
        repls.append((m.start(2), m.end(2), esc(want)))
        changes.append(f"{name}: {have!r} -> {want!r}")

    for a, b, text in sorted(repls, key=lambda r: r[0], reverse=True):
        block = block[:a] + text + block[b:]

    # append any properties that do not exist yet
    existing = {m.group(1) for m in PROP_RE.finditer(block)}
    # Never create an empty property: an empty value here means "clear this
    # field if it exists", not "add a blank field to every symbol".
    missing = [k for k in fields if k not in existing and fields[k] != ""]
    if missing:
        matches = list(PROP_RE.finditer(block))
        if not matches:
            return block, changes
        last = matches[-1]
        close = _close_paren(block, block.rfind("(property \"", 0, last.end()))
        geo = re.search(r"\(at ([\-\d.]+) ([\-\d.]+)", block[last.start():close])
        x, y = (geo.group(1), geo.group(2)) if geo else ("0", "0")
        add = "".join(
            HIDDEN_TEMPLATE.format(name=k, value=esc(fields[k]), x=x, y=y)
            for k in missing
        )
        for k in missing:
            changes.append(f"{k}: (new) -> {fields[k]!r}")
        block = block[:close] + "\n" + add.rstrip("\n") + block[close:]
    return block, changes


def ensure_hidden(block: str, names: set[str]) -> tuple[str, list[str]]:
    """Add (hide yes) to the named properties where it is missing."""
    out: list[str] = []
    changes: list[str] = []
    pos = 0
    while True:
        m = re.search(r'\t\t\(property "([^"]*)"', block[pos:])
        if not m:
            break
        start = pos + m.start()
        name = m.group(1)
        close = _close_paren(block, start + 2)
        piece = block[start:close]
        if name in names and "(hide yes)" not in piece:
            am = re.search(r"\(at [^)]*\)\n", piece)
            if am:
                piece = piece[:am.end()] + "\t\t\t(hide yes)\n" + piece[am.end():]
                changes.append(f"{name}: shown -> hidden")
        out.append(block[pos:start])
        out.append(piece)
        pos = close
    out.append(block[pos:])
    return "".join(out), changes


def verify(sheet: str, text: str, updates: dict[str, dict[str, str]]) -> list[str]:
    """Read the fields back out of the new text and confirm they took."""
    problems: list[str] = []
    for chunk in re.split(r"\n\t\(symbol\n", text)[1:]:
        m = re.search(r'\(property "Reference" "([^"]*)"', chunk)
        if not m or m.group(1) not in updates:
            continue
        ref = m.group(1)
        for field, want in updates[ref].items():
            fm = re.search(r'\(property "%s" "((?:[^"\\]|\\.)*)"' % re.escape(field), chunk)
            got = unesc(fm.group(1)) if fm else None
            if want == "" and got is None:
                continue          # absent is the desired state for a cleared field
            if got != want and not (field in FILL_IF_EMPTY and got):
                problems.append(f"{sheet}:{ref}.{field} = {got!r} (wanted {want!r})")
    return problems


def main() -> int:
    dry = "--dry-run" in sys.argv
    updates = build_updates()
    print(f"{len(updates)} references to update, "
          f"{len({f['E14MFR#'] for f in updates.values()})} distinct parts\n")

    if not dry and "--backup" in sys.argv:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        bak = BOM / f"schematic-backup-{stamp}"
        bak.mkdir(parents=True, exist_ok=True)
        for s in SHEETS:
            if (ROOT / s).exists():
                shutil.copy2(ROOT / s, bak / s)
        print(f"backed up to {bak.name}\n")

    # Pass 1: compute and verify everything, touching nothing yet.
    pending: list[tuple[Path, str]] = []
    total = 0
    for sheet in SHEETS:
        path = ROOT / sheet
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        chunks = re.split(r"(\n\t\(symbol\n)", text)
        touched = 0
        for k, chunk in enumerate(chunks):
            if chunk != "\n\t(symbol\n":
                continue
            body = chunks[k + 1] if k + 1 < len(chunks) else ""
            m = re.search(r'\(property "Reference" "([^"]*)"', body)
            ref = m.group(1) if m else None
            new_body, changes = (body, [])
            if ref and ref in updates:
                new_body, changes = update_block(body, updates[ref])
            # hide metadata on EVERY symbol, including DNP ones we do not
            # otherwise touch, so nothing long lands on the drawing
            new_body, hidden = ensure_hidden(new_body, HIDE_ALWAYS)
            changes = changes + hidden
            if changes:
                touched += len(changes)
                chunks[k + 1] = new_body
        if not touched:
            continue
        new_text = "".join(chunks)

        if new_text.count("(") != new_text.count(")"):
            print(f"ABORT: {sheet} would end with unbalanced parentheses")
            return 1
        # Only placed instances matter; lib_symbols definitions (3+ tabs) keep
        # their own Description fields, which are not drawn on the sheet.
        strays = []
        for inst in re.split(r"\n\t\(symbol\n", new_text)[1:]:
            for m in re.finditer(r'\t\t\(property "([^"]*)"', inst):
                if m.group(1) in HIDE_ALWAYS and "(hide yes)" not in inst[
                        m.start():_close_paren(inst, m.start() + 2)]:
                    strays.append(m.group(1))
        if strays:
            print(f"ABORT: {sheet} has visible metadata fields: {sorted(set(strays))}")
            return 1
        probs = verify(sheet, new_text, updates)
        if probs:
            print(f"ABORT: {sheet} has {len(probs)} unverified fields")
            for x in probs[:8]:
                print("   " + x)
            return 1
        pending.append((path, new_text))
        total += touched
        print(f"{sheet}: {touched} field changes, verified OK")

    if dry:
        print(f"\nDRY RUN - nothing written; {total} field changes total")
        return 0

    # Pass 2: everything checked out, so write.
    for path, text in pending:
        path.write_text(text, encoding="utf-8")
    print(f"\nwritten: {len(pending)} sheets, {total} field changes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
