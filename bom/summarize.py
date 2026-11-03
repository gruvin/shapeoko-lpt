#!/usr/bin/env python3
"""Render bom/controller-bom.csv as a readable REVIEW.md for human checking."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOM = ROOT / "bom"


from specs import fmt_price


def money(v) -> str:
    """Line item: up to 4 decimals, matching element14's own precision."""
    if v in ("", None):
        return ""
    return "$" + fmt_price(v)


def money_total(v) -> str:
    """Aggregate: 2 decimals. Line detail keeps full precision above."""
    if v in ("", None):
        return ""
    return "$" + fmt_price(v, places=2)


def main() -> int:
    rows = list(csv.DictReader((BOM / "controller-bom.csv").open()))
    data = json.loads((BOM / "groups.json").read_text())
    nf = data["not_fitted"]

    tot = sum(float(r["extended"]) for r in rows if r["extended"] not in ("", None))
    subs = [r for r in rows if r["substituted"]]
    flagged = [r for r in rows if r["confidence"] in ("low", "none")]

    L: list[str] = []
    A = L.append

    A("# Controller BOM — review sheet\n")
    A(f"- source: `controller.kicad_pro` (4 sheets, {len(rows)} fitted BOM lines)")
    A(f"- prices: element14 NZ store, list price, NZD (AUD/GBP where NZ had no stock)")
    A(f"- **estimated total: {money_total(tot)}** (mixed currency, indicative only)\n")

    A("## Status\n")
    A(f"| | count |\n|---|---|")
    A(f"| lines resolved with confidence | {len(rows)-len(flagged)} |")
    A(f"| lines changed vs the schematic | {len(subs)} |")
    A(f"| lines needing your decision | {len(flagged)} |")
    A(f"| parts not fitted (DNP / net-tie) | {len(nf)} |\n")

    def tot_of(kind):
        return sum(float(r["extended"]) for r in rows
                   if r["assembly"] == kind and r["extended"] not in ("", None))
    A(f"Pick-and-place (SMD): {money_total(tot_of('SMD'))}  |  "
      f"hand solder (THT): {money_total(tot_of('THT'))}\n")

    A("## Needs your decision\n")
    for r in flagged:
        A(f"**{r['refs']}** — `{r['value']}` ({r['footprint'] or 'no footprint'})  ")
        if r["mpn"]:
            A(f"proposed: `{r['mpn']}` [{r['sku']}], stock {r['stock']}  ")
        A(f"> {r['note']}\n")

    A("## Changed vs the schematic\n")
    A("These lines are **not** what the schematic's `E14MFR#` field said.\n")
    A("| refs | value | footprint | part | why |")
    A("|---|---|---|---|---|")
    for r in subs:
        why = r["note"].replace("|", "/")[:150]
        A(f"| {r['refs']} | {r['value']} | {r['footprint'][:34]} "
          f"| `{r['mpn']}` | {why} |")
    A("")

    A("## Assumptions applied\n")
    A("- Passive substitution allowed (R/C/L/D): package + value + voltage matched.")
    A("- ICs/connectors only substituted within the same part family, else flagged.")
    A("- Where the schematic Value and its stored MPN disagreed, the **Value and")
    A("  footprint** were treated as authoritative and the MPN as stale.")
    A("- Quantity is rounded up to each part's MOQ/multiple to give a real order cost.\n")

    A("## Lines by part\n")
    A("`P/N` is the supplier catalogue number: element14 order code, DigiKey part")
    A("number, or LCSC number. Prices are element14 NZ list unless the supplier")
    A("column says otherwise.\n")
    A("| refs | qty | value | brand | manufacturer P/N | supplier | P/N | stock "
      "| MOQ | order | unit | ext | asm | conf |")
    A("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        A(f"| {r['refs']} | {r['qty']} | {r['value']} | {r['brand']} "
          f"| `{r['mpn']}` | {r['supplier']} | {r['sku']} "
          f"| {r['stock']} | {r['moq']} | {r['order_qty']} | {money(r['unit'])} "
          f"| {money(r['extended'])} | {r['assembly']} | {r['confidence']} |")
    A("")
    alts = [r for r in rows if r.get("alternates")]
    if alts:
        A("## Alternate sources\n")
        A("| refs | used | alternate |")
        A("|---|---|---|")
        for r in alts:
            A(f"| {r['refs']} | {r['supplier']} `{r['sku']}` | {r['alternates'].replace('|','/')} |")
        A("")

    A("## Descriptions\n")
    A("| refs | description |")
    A("|---|---|")
    for r in rows:
        A(f"| {r['refs']} | {r['desc'].replace('|','/')} |")
    A("")

    A("## Not fitted (excluded from totals)\n")
    A("| ref | value | footprint | reason |")
    A("|---|---|---|---|")
    for s in nf:
        A(f"| {s['Ref']} | {s['Value']} | {s['Footprint'] or '—'} | {s.get('reason','')} |")

    out = BOM / "REVIEW.md"
    out.write_text("\n".join(L) + "\n")
    print(f"wrote {out.relative_to(ROOT)} ({len(L)} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
