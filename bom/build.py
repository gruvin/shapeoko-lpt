#!/usr/bin/env python3
"""
Group schematic symbols into BOM lines.

Grouping key is (Value, Footprint) -- same as KiCad's default -- but symbols
that are DNP / excluded-from-BOM / net-ties are pulled out into a separate
"not fitted" list so they never enter a total.

Outputs bom/groups.json
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOM = ROOT / "bom"

# Reference prefixes that are structural, not parts
NETTIE_PREFIXES = ("NT",)


def split_mpn_list(field: str) -> list[str]:
    """Split a comma-separated MPN field, but respect commas inside an MPN.

    Real-world examples from this design:
      'CC0603KRX7R9BB103,MC0603B104K500CT'  -> two parts  (list)
      'MCMR06X1004FTL,CRCW06035K60FKEA'     -> two parts  (list)
      'BC847C,215'                          -> ONE part   (NXP suffix)
      'MKDS 1,5/ 2-5,08'                    -> ONE part   (Phoenix)

    Heuristic: if any comma-separated token is short or purely numeric, the
    commas are part of a single MPN, not a list separator.
    """
    field = field.strip()
    if not field or field.upper() == "DNI":
        return []
    if "," not in field:
        return [field]

    toks = [t.strip() for t in field.split(",")]
    if any((len(t) < 3 or t.isdigit()) for t in toks):
        return [field]  # commas are internal
    return [t for t in toks if t]


def is_nettie(ref: str) -> bool:
    return ref.startswith(NETTIE_PREFIXES)


def ref_sort_key(ref: str) -> tuple:
    m = re.match(r"^([A-Za-z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def compress_refs(refs: list[str]) -> str:
    """R1,R2,R3,R7 -> R1-R3,R7  (KiCad-style range compression)."""
    by_prefix: dict[str, list[int]] = {}
    odd: list[str] = []
    for r in refs:
        m = re.match(r"^([A-Za-z]+)(\d+)$", r)
        if not m:
            odd.append(r)
            continue
        by_prefix.setdefault(m.group(1), []).append(int(m.group(2)))

    parts: list[str] = []
    for prefix in sorted(by_prefix):
        nums = sorted(set(by_prefix[prefix]))
        start = prev = nums[0]
        for n in nums[1:] + [None]:
            if n is not None and n == prev + 1:
                prev = n
                continue
            parts.append(
                f"{prefix}{start}" if start == prev else f"{prefix}{start}-{prefix}{prev}"
            )
            if n is not None:
                start = prev = n
    return ",".join(parts + sorted(odd))


def load_dnp_overrides() -> dict:
    """Refs a human has decided not to buy (e.g. cut from a stock strip)."""
    p = BOM / "overrides.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text()).get("_dnp", {})


def main() -> int:
    symbols = json.loads((BOM / "symbols.json").read_text())
    dnp_override = load_dnp_overrides()

    fitted: dict[tuple, list[dict]] = {}
    not_fitted: list[dict] = []

    for s in symbols:
        ref = s["Ref"]
        reason = None
        if ref in dnp_override:
            reason = f"not purchased - {dnp_override[ref]}"
        elif is_nettie(ref):
            reason = "net-tie (copper link, no part)"
        elif s["dnp"]:
            reason = "DNP flag set"
        elif s["exclude_from_bom"]:
            reason = "exclude_from_bom"
        elif s["Value"].strip().upper() in ("DNI", ""):
            reason = "value marked DNI"

        if reason:
            s = dict(s, reason=reason)
            not_fitted.append(s)
            continue

        fitted.setdefault((s["Value"], s["Footprint"]), []).append(s)

    groups = []
    for (value, fp), syms in fitted.items():
        refs = sorted((s["Ref"] for s in syms), key=ref_sort_key)
        mpns: list[str] = []
        skus: list[str] = []
        moqs: list[str] = []
        for s in syms:
            for t in split_mpn_list(s["E14MFR#"]):
                if t.upper() != "DNI" and t not in mpns:
                    mpns.append(t)
            for tok in s["E14PART"].split(","):
                t = tok.strip()
                if t and t.upper() != "DNI" and t not in skus:
                    skus.append(t)
            for tok in s["E14MOQ"].split(","):
                t = tok.strip()
                if t and t not in moqs:
                    moqs.append(t)
        groups.append(
            {
                "refs": refs,
                "ref_range": compress_refs(refs),
                "qty": len(refs),
                "value": value,
                "footprint": fp,
                "datasheet": sorted({s["Datasheet"] for s in syms if s["Datasheet"]}),
                "desc": sorted({s["Description"] for s in syms if s["Description"]}),
                "marking": sorted({s["Marking"] for s in syms if s["Marking"]}),
                "e14mpns": mpns,
                "e14skus": skus,
                "e14moq": moqs,
                "sheets": sorted({s["sheet"] for s in syms}),
            }
        )

    groups.sort(key=lambda g: ref_sort_key(g["refs"][0]))
    not_fitted.sort(key=lambda s: ref_sort_key(s["Ref"]))

    (BOM / "groups.json").write_text(
        json.dumps({"groups": groups, "not_fitted": not_fitted}, indent=2)
    )

    print(f"fitted BOM lines : {len(groups)}  ({sum(g['qty'] for g in groups)} parts)")
    print(f"not fitted       : {len(not_fitted)} lines/symbols")
    print()
    with_mpn = sum(1 for g in groups if g["e14mpns"])
    multi = [g for g in groups if len(g["e14mpns"]) > 1]
    print(f"lines with >=1 MPN : {with_mpn}")
    print(f"lines with NO MPN  : {len(groups) - with_mpn}")
    print(f"lines with MULTIPLE MPNs (need picking): {len(multi)}")
    for g in multi:
        print(f"   {g['ref_range']:<32} {g['value']:<20} {g['e14mpns']}")

    print()
    print("=== LINES WITH NO MPN ===")
    for g in groups:
        if not g["e14mpns"]:
            fp = g["footprint"].split(":")[-1]
            print(f"  {g['ref_range']:<30} q={g['qty']:<3} {g['value']:<22} {fp}")

    print()
    print("=== NOT FITTED ===")
    for s in not_fitted:
        print(f"  {s['Ref']:<7} {s['Value']:<34} {s['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
