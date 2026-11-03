#!/usr/bin/env python3
"""
Packaging audit: make sure no BOM line is a full reel or a multi-pack.

Bryan needs *individual parts*. element14 signals packaging three ways, and
they do not always agree:

  * SKU suffix  - "RL" on the end usually means a full reel
  * `reeling`   - boolean in the API response, the authoritative flag
  * `packSize`  - units per ordered item (e.g. 500 for a reel "each")
  * `unitOfMeasure` - free text, e.g. "EACH (SUPPLIED ON CUT TAPE)"

A high MOQ is the practical symptom: you end up buying 500 of a 7-off part.

Read-only. Writes bom/packaging-audit.csv and prints offenders.
"""

import csv
import re
from pathlib import Path

from e14 import E14, moq_of

ROOT = Path(__file__).resolve().parent.parent
BOM = ROOT / "bom"

# Beyond this many units for a handful of parts, something is wrong.
MOQ_ALARM = 50


def main() -> int:
    api = E14()
    rows = list(csv.DictReader((BOM / "controller-bom.csv").open()))

    out = []
    for r in rows:
        sku = (r.get("sku") or "").strip()
        rec = {
            "refs": r["refs"], "qty": r["qty"], "value": r["value"],
            "mpn": r["mpn"], "sku": sku, "moq": r["moq"],
            "order_qty": r["order_qty"], "unit": r["unit"],
            "extended": r["extended"],
            "reeling": "", "pack_size": "", "uom": "",
            "suffix_rl": "yes" if sku.upper().endswith("RL") else "",
            "verdict": "", "note": "",
        }
        if not sku or sku == "-" or r.get("supplier") != "element14":
            rec["verdict"] = "n/a"
            out.append(rec)
            continue

        ps = api.by_sku(sku)
        if not ps:
            rec["verdict"] = "SKU NOT FOUND"
            out.append(rec)
            continue
        p = ps[0]
        rec["reeling"] = str(p.get("reeling"))
        rec["pack_size"] = str(p.get("packSize"))
        rec["uom"] = p.get("unitOfMeasure") or ""

        problems = []
        if p.get("reeling") is True:
            problems.append("API says reeling=true (full reel)")
        if sku.upper().endswith("RL"):
            problems.append("SKU has RL suffix")
        try:
            if int(p.get("packSize") or 1) > 1:
                problems.append(f"packSize={p.get('packSize')} units per item")
        except (TypeError, ValueError):
            pass
        uom = (p.get("unitOfMeasure") or "").upper()
        if "REEL" in uom and "CUT TAPE" not in uom:
            problems.append(f"unitOfMeasure={p.get('unitOfMeasure')!r}")
        if moq_of(p) > MOQ_ALARM:
            problems.append(f"MOQ={moq_of(p)}")

        # Contradiction: RL-suffixed SKU that is NOT flagged as reeling.
        if sku.upper().endswith("RL") and p.get("reeling") is not True:
            rec["note"] = "RL suffix but reeling=false - suffix rule would misfire"

        if problems:
            rec["verdict"] = "REEL/MULTIPACK"
            rec["note"] = (rec["note"] + "; " if rec["note"] else "") + "; ".join(problems)
        else:
            rec["verdict"] = "individual"
        out.append(rec)

    cols = list(out[0].keys())
    with (BOM / "packaging-audit.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(out)

    bad = [r for r in out if r["verdict"] == "REEL/MULTIPACK"]
    missing = [r for r in out if r["verdict"] == "SKU NOT FOUND"]
    print(f"network={api.network_calls} cache={api.cache_hits} lines={len(out)}")
    print(f"individual parts : {sum(1 for r in out if r['verdict']=='individual')}")
    print(f"reel / multipack : {len(bad)}")
    print(f"sku not found    : {len(missing)}")
    print()
    if bad:
        print("=== MUST FIX ===")
        for r in bad:
            print(f"  {r['refs']:<22} qty={r['qty']:<3} *{r['moq']:<6} -> {r['order_qty']:<6} "
                  f"{r['mpn'][:22]:<22} sku={r['sku']:<12} {r['note'][:64]}")
    for r in out:
        if r["note"] and r["verdict"] == "individual":
            print(f"  note: {r['refs']} {r['sku']} - {r['note']}")
    print(f"\n-> {(BOM/'packaging-audit.csv')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
