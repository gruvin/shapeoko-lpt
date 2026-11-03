#!/usr/bin/env python3
"""
Resolve every fitted BOM line to exactly one orderable element14 part.

Policy (agreed with Bryan):
  * element14 NZ first, falling back to AU then UK when NZ has no stock.
  * One part per line. Where the schematic lists alternates, keep the best by
    (in stock, cut-tape, MOQ, price) and note the dropped ones.
  * Where the current part is out of stock or obsolete, substitute the nearest
    in-stock equivalent. Substitution is automatic only when Value+Footprint
    fully determine the part (passives, diodes, LEDs). For connectors and ICs a
    substitute must stay within the same MPN family, otherwise it is flagged.
  * Human-reviewed choices live in overrides.json and win outright.

Read-only with respect to the schematic. Writes:
  bom/controller-bom.csv   final purchasing BOM
  bom/issues.csv           lines needing a human decision
"""

import csv
import json
import re
from pathlib import Path

from e14 import (E14, moq_of, unit_price, is_reel, is_orderable,
                 pack_size)
from specs import (parse_value, parse_e14_description, close, fmt_mag,
                   fmt_price)

ROOT = Path(__file__).resolve().parent.parent
BOM = ROOT / "bom"

# Prefixes where spec-based substitution is safe.
SPEC_SUBSTITUTABLE = {"R", "C", "L", "D"}
# Prefixes where a substitute must share the base MPN / series.
SERIES_ONLY = {"U", "Q", "Y", "K", "SW", "RN"}


# ---------------------------------------------------------------- helpers

def pkg_from_footprint(fp: str) -> str | None:
    m = re.search(r"_(\d{4})_\d{4}Metric", fp)
    if m:
        return m.group(1)
    m = re.search(r"(\d{4})Metric", fp)
    return m.group(1) if m else None


# Package tokens that appear in BOTH KiCad footprint names and element14
# descriptions, so they can be compared meaningfully.
_PKG_PATTERNS = [
    # Chip sizes can appear inside an MPN without a word boundary (CD0603-B0340R
    # is an 0603 part), so bound on digits rather than on \b.
    (r"(?<!\d)(0402|0603|0805|1206|1210|1812|2010|2512)(?!\d)", None),
    (r"\b(SOD-\d{3})\b", None),
    (r"\b(SOT-\d{2,3}(?:-\d)?)\b", None),
    (r"\b(SMA|SMB|SMC)\b", {"SMA": "DO-214", "SMB": "DO-214", "SMC": "DO-214"}),
    (r"\b(DO-214[A-C]{1,2})\b", {"DO-214AC": "DO-214", "DO-214AA": "DO-214",
                                     "DO-214AB": "DO-214"}),
    (r"\b(MSOP|TSSOP|SSOP|SOIC|SOP)\b", None),
    (r"\b(V?QFN|DFN)\b", {"DFN": "QFN", "VQFN": "QFN"}),
    (r"\b([TL]?QFP)\b", {"LQFP": "QFP", "TQFP": "QFP"}),
    (r"\b(DPAK|D2PAK|TO-252|TO-263)\b", {"DPAK": "TO-252", "TO-263": "TO-252"}),
]


def pkg_tokens(s: str) -> set[str]:
    # Footprint names use '_' as a separator, which is a word character, so \b
    # does not fire (D_SOD-323_DOT). Normalise it to a space first.
    s = (s or "").replace("_", " ")
    out: set[str] = set()
    for pat, alias in _PKG_PATTERNS:
        for m in re.finditer(pat, s, re.IGNORECASE):
            tok = m.group(1).upper()
            out.add(alias.get(tok, tok) if alias else tok)
    return out


def mpn_from_footprint(fp: str) -> str | None:
    """Connector footprints that embed the exact MPN they were drawn for.

    Only unambiguous numeric manufacturer formats are used. KiCad's generic
    footprint names (e.g. TerminalBlock_Phoenix_MPT-0,5-4-2.54) look like part
    numbers but are not, and including them causes false mismatches.
    """
    for pat in (
        r"(\d{5}-\d{4})",   # Molex 43045-0412
        r"(\d{11})",         # Wurth 65100516121
    ):
        m = re.search(pat, fp)
        if m:
            return m.group(1)
    return None


def spec_match_score(product: dict, sv: dict) -> int:
    """0 = agrees with the schematic, 2 = contradicts it, 1 = cannot tell."""
    if sv.get("magnitude") is None:
        return 1
    d = parse_e14_description(product.get("displayName") or "")
    if d["magnitude"] is None:
        return 1
    if d["kind"] == sv["kind"] and close(d["magnitude"], sv["magnitude"]):
        return 0
    return 2


def resistor_mpn(ohms: float, size: str) -> str | None:
    """MULTICOMP PRO MCSR__X<mmm><e>FTL, where value = mmm x 10^e."""
    fam = {"0402": "MCSR04X", "0603": "MCSR06X",
           "0805": "MCSR08X", "1206": "MCSR12X"}.get(size or "")
    if not fam or not ohms or ohms <= 0:
        return None
    for e in range(0, 7):
        m3 = ohms / (10 ** e)
        if 100 <= m3 < 1000 and abs(m3 - round(m3)) < 1e-6:
            return f"{fam}{int(round(m3))}{e}FTL"
    return None


def looks_like_mpn(v: str) -> bool:
    v = v.strip()
    if not v or " " in v or "_" in v:
        return False
    if re.fullmatch(r"[\d.]+[pnu\u00b5mkKM]?H?", v):
        return False
    return bool(re.search(r"[A-Za-z]", v)) and len(v) >= 5


def clean_mpn(t: str) -> str:
    """Strip suffixes element14 does not index (SS24A+ -> SS24A)."""
    return t.strip().rstrip("+").strip()


def load_overrides() -> tuple[dict, dict]:
    p = BOM / "overrides.json"
    if not p.exists():
        return {}, {}
    raw = json.loads(p.read_text())
    needs = raw.pop("_needs_decision", {})
    raw.pop("_comment", None)
    return raw, needs


class Resolver:
    def __init__(self) -> None:
        self.api = E14()

    @staticmethod
    def rank(pool: list[dict], qty: int) -> list[dict]:
        def key(p: dict) -> tuple:
            moq = moq_of(p) or 1
            return ((p.get("inv") or 0) <= 0, not is_orderable(p), is_reel(p),
                    moq, unit_price(p, max(qty, moq)) or 9e9)
        return sorted(pool, key=key)

    def best_across_stores(self, fetch, qty: int) -> tuple[dict | None, str]:
        best: tuple[dict | None, str] = (None, "")
        for store in self.api.stores:
            try:
                pool = fetch(store)
            except Exception:  # noqa: BLE001
                continue
            if not pool:
                continue
            cand = self.rank(pool, qty)[0]
            if (cand.get("inv") or 0) > 0 and is_orderable(cand):
                return cand, store
            if best[0] is None or (cand.get("inv") or 0) > (best[0].get("inv") or 0):
                best = (cand, store)
        return best

    def lookup_token(self, token: str, qty: int) -> tuple[dict | None, str]:
        def fetch(store: str) -> list[dict]:
            if token.isdigit():
                hits = self.api.by_sku(token, store=store)
                if hits:
                    return hits
            hits = self.api.by_mpn(token, store=store)
            return [p for p in hits
                    if (p.get("translatedManufacturerPartNumber") or "")
                    .strip().lower() == token.strip().lower()]
        return self.best_across_stores(fetch, qty)

    def search_spec(self, want: dict, pkg: str | None, qty: int
                    ) -> tuple[dict | None, str]:
        noun = {"capacitance": "ceramic capacitor", "resistance": "resistor",
                "inductance": "inductor"}.get(want["kind"], "")
        query = f"{noun} {fmt_mag(want['magnitude'], want['kind'])} {pkg or ''}".strip()

        def fetch(store: str) -> list[dict]:
            good = []
            for p in self.api.keyword(query, store=store, n=25, in_stock=True):
                d = parse_e14_description(p.get("displayName") or "")
                if d["kind"] != want["kind"]:
                    continue
                if not close(d["magnitude"], want["magnitude"]):
                    continue
                if pkg and d["package"] and d["package"] != pkg:
                    continue
                if want["kind"] == "capacitance":
                    need = want.get("voltage") or 50.0
                    if (d["voltage"] or 0) + 0.01 < need:
                        continue
                good.append(p)
            return good
        return self.best_across_stores(fetch, qty)

    def search_family(self, base_mpn: str, pkg: str | None, qty: int
                      ) -> tuple[dict | None, str]:
        stem = re.split(r"[-,]", base_mpn)[0]

        def fetch(store: str) -> list[dict]:
            good = []
            for p in self.api.keyword(f"{stem} {pkg or ''}", store=store,
                                      n=25, in_stock=True):
                mpn = (p.get("translatedManufacturerPartNumber") or "")
                if not mpn.lower().startswith(stem.lower()):
                    continue
                d = parse_e14_description(p.get("displayName") or "")
                if pkg and d["package"] and d["package"] != pkg:
                    continue
                good.append(p)
            return good
        return self.best_across_stores(fetch, qty)

    def search_diode(self, product: dict, qty: int) -> tuple[dict | None, str]:
        """Find an in-stock diode at least as highly rated as the original."""
        desc = product.get("displayName") or ""
        vr = re.search(r"(\d+(?:\.\d+)?)\s*V\b", desc)
        ia = re.search(r"(\d+(?:\.\d+)?)\s*mA\b", desc)
        kind = next((k for k in ("Schottky", "Zener", "Rectifier", "Switching",
                                 "Avalanche") if k.lower() in desc.lower()), "")
        # Diode configuration matters: a dual-series part in place of a single
        # drops two junctions instead of one and changes the circuit.
        conf = next((c for c in ("Dual Series", "Dual Common Cathode",
                                 "Dual Common Anode", "Dual", "Single")
                     if c.lower() in desc.lower()), "")
        if not (vr and ia):
            return None, ""
        v_need, i_need = float(vr.group(1)), float(ia.group(1))
        query = f"{kind} diode {v_need:g}V {i_need:g}mA".strip()

        def fetch(store: str) -> list[dict]:
            good = []
            for p in self.api.keyword(query, store=store, n=25, in_stock=True):
                d = p.get("displayName") or ""
                if kind and kind.lower() not in d.lower():
                    continue
                if conf and conf.lower() not in d.lower():
                    continue
                ev = re.search(r"(\d+(?:\.\d+)?)\s*V\b", d)
                ea = re.search(r"(\d+(?:\.\d+)?)\s*mA\b", d)
                if not (ev and ea):
                    continue
                if float(ev.group(1)) + 0.01 < v_need:
                    continue
                if float(ea.group(1)) + 0.01 < i_need * 0.8:
                    continue
                good.append(p)
            return good
        return self.best_across_stores(fetch, qty)


def assembly_type(desc: str, fp: str) -> str:
    """SMD vs THT for the pick-and-place decision.

    The distributor description is authoritative when it says "Through Hole" or
    "Surface Mount"/"SMD". Only fall back to footprint-name heuristics when it
    says neither (e.g. "Digital Isolator, WSOIC, 16 Pins").
    """
    d = (desc or "").lower()
    if "through hole" in d or "through-hole" in d:
        return "THT"
    if re.search(r"\bsmd\b", d) or "surface mount" in d:
        return "SMD"
    if "do-214" in d:          # SMA/SMB/SMC are all SMD
        return "SMD"

    f = fp.lower().replace("_", " ")
    for m in ("pinheader", "pinsocket", "terminalblock", "dsub", "relay",
              "kycon", "usb mini-b", "to-220", "dip ", "micro-fit"):
        if m in f:
            return "THT"
    for m in ("metric", "smd", "soic", "tqfp", "vqfn", "qfn", "sot-",
              "sod-", "to-252", "dpak", "cp elec", "handsolder",
              "do-214", "array", "so-", "sma", "smb", "smc"):
        if m in f:
            return "SMD"
    return "CHECK"


def fill(row: dict, p: dict, store: str, qty: int) -> None:
    row["brand"] = p.get("brandName") or p.get("vendorName") or ""
    row["mpn"] = p.get("translatedManufacturerPartNumber") or ""
    row["sku"] = str(p.get("sku") or "")
    row["store"] = store
    row["supplier"] = ("element14" if ("element14" in store or "farnell" in store)
                       else store.split(".")[-2] if store else "")
    # displayName is "BRAND - MPN - Description", but brands can themselves
    # contain " - " (e.g. "TE CONNECTIVITY - OEG"), so strip by prefix.
    desc = p.get("displayName") or ""
    for prefix in (row["brand"], row["mpn"]):
        if prefix and desc.startswith(prefix + " - "):
            desc = desc[len(prefix) + 3:]
    row["desc"] = desc
    row["status"] = p.get("productStatus") or ""
    row["stock"] = p.get("inv")
    lt = (p.get("stock") or {}).get("leastLeadTime")
    row["lead_days"] = lt if lt is not None else ""
    row["moq"] = moq_of(p)
    mult = moq_of(p) or 1
    row["order_qty"] = -(-max(qty, mult) // mult) * mult
    # Keep element14's own precision: unit prices can carry 4 decimals and
    # rounding them early loses money across a line.
    u = unit_price(p, row["order_qty"])
    row["unit"] = fmt_price(u)
    if u is not None:
        row["extended"] = fmt_price(u * row["order_qty"])
    row["currency"] = ("NZD" if "nz." in store else
                       "AUD" if "au." in store else "GBP")
    row["assembly"] = assembly_type(row["desc"], row["footprint"])


def main() -> int:
    R = Resolver()
    api = R.api
    data = json.loads((BOM / "groups.json").read_text())
    overrides, needs_decision = load_overrides()
    rows: list[dict] = []

    for g in data["groups"]:
        qty = g["qty"]
        m = re.match(r"^([A-Za-z]+)", g["refs"][0])
        prefix = m.group(1).upper() if m else ""
        fp = g["footprint"].split(":")[-1]
        pkg = pkg_from_footprint(fp)
        sv = parse_value(g["value"], prefix)

        row = {k: "" for k in (
            "refs", "qty", "value", "footprint", "brand", "mpn", "supplier", "sku",
            "store", "desc",
            "status", "stock", "lead_days", "moq", "order_qty", "unit",
            "extended", "currency", "assembly", "substituted", "alternates", "confidence",
            "note")}
        row.update(refs=g["ref_range"], qty=qty, value=g["value"], footprint=fp)

        notes: list[str] = []
        ov = next((overrides[r] for r in g["refs"] if r in overrides), None)
        nd = next((needs_decision[r] for r in g["refs"] if r in needs_decision), None)

        # ---- 0a. override supplied from outside element14 (e.g. LCSC / local stock)
        if ov and ov.get("external"):
            row["brand"] = ov.get("brand", "")
            row["mpn"] = ov.get("mpn") or ov["external"]
            row["supplier"] = ov.get("external")
            row["sku"] = ov.get("supplier_pn", "-")
            row["alternates"] = ov.get("alternates", "")
            if ov.get("unit") is not None:
                row["unit"] = fmt_price(ov["unit"])
                row["currency"] = ov.get("currency", "")
                row["order_qty"] = qty
                row["extended"] = fmt_price(float(ov["unit"]) * qty)
            row["desc"] = ov.get("why", "")
            row["store"] = "external"
            row["substituted"] = "external"
            row["confidence"] = "external"
            row["assembly"] = assembly_type(ov.get("why", ""), fp)
            row["note"] = "not from element14: " + ov.get("why", "")
            if nd:
                row["note"] += " NEEDS DECISION: " + nd
            rows.append(row)
            continue

        # ---- 0b. reviewed override wins outright
        if ov:
            cand, st = R.lookup_token(ov["mpn"], qty)
            if cand:
                fill(row, cand, st, qty)
                row["alternates"] = ov.get("alternates", "")
                row["substituted"] = "reviewed"
                row["confidence"] = "high" if (cand.get("inv") or 0) > 0 else "low"
                row["note"] = "reviewed: " + ov.get("why", "")
                if (cand.get("inv") or 0) <= 0:
                    row["note"] += "; but zero stock"
                if nd:
                    row["note"] += " NEEDS DECISION: " + nd
                rows.append(row)
                continue
            notes.append(f"override {ov['mpn']} not resolvable")

        # A part with no footprint cannot be selected: the case size, height and
        # current rating are all unknown. Do not guess.
        if not fp:
            row["confidence"] = "none"
            row["note"] = "no footprint assigned in the schematic - cannot choose a part"
            if nd:
                row["note"] += " NEEDS DECISION: " + nd
            rows.append(row)
            continue

        # ---- 1. candidate tokens
        product, store, original_mpn = None, "", ""
        tokens: list[str] = []
        for t in list(g["e14mpns"]) + list(g["e14skus"]):
            t = clean_mpn(t)
            if t and t not in tokens:
                tokens.append(t)
        if looks_like_mpn(g["value"]):
            t = clean_mpn(g["value"])
            if t not in tokens:
                tokens.append(t)
        if (pkg_mpn := mpn_from_footprint(fp)) and pkg_mpn not in tokens:
            tokens.insert(0, pkg_mpn)   # footprint MPN is the strongest signal
        # If the schematic already carries an explicit element14 order code,
        # that is a human decision and must win over re-ranking by price.
        # Otherwise every run could pick a different (cheaper) listing for the
        # same MPN and the BOM would never settle.
        locked: dict | None = None
        for sku in g["e14skus"]:
            cand, st = R.lookup_token(clean_mpn(sku), qty)
            if cand and spec_match_score(cand, sv) != 2:
                locked = cand
                store = st
                original_mpn = sku
                break

        cands: list[tuple[str, dict, str]] = []

        for tok in tokens:
            cand, st = R.lookup_token(tok, qty)
            if cand:
                cands.append((tok, cand, st))

        # Choose the candidate that best agrees with the schematic. Stock only
        # breaks ties -- otherwise a high-stock but wrong-value part wins, which
        # is exactly the failure mode that produced the stale MPNs in the first
        # place (CRCW06035K60FKEA copied onto 1M and 330 ohm lines).
        if locked is not None:
            product = locked
        elif cands:
            cands.sort(key=lambda c: (spec_match_score(c[1], sv),
                                      (c[1].get("inv") or 0) <= 0))
            tok, cand, st = cands[0]
            product, store, original_mpn = cand, st, tok
            if len(cands) > 1:
                notes.append("alternates dropped: " +
                             ", ".join(c[0] for c in cands[1:]))

        # ---- 2. target spec for substitution
        want = dict(sv)
        if product:
            d0 = parse_e14_description(product.get("displayName") or "")
            if want["magnitude"] is None or want["kind"] == "unknown":
                want = {"kind": d0["kind"], "magnitude": d0["magnitude"],
                        "voltage": d0["voltage"]}
            if want.get("voltage") is None:
                want["voltage"] = d0["voltage"]

        usable = bool(product and is_orderable(product)
                      and (product.get("inv") or 0) > 0)

        # A part that contradicts the schematic Value is not usable either,
        # even if it is in stock: that is a stale field, not a sourcing problem.
        contradicts = bool(product and spec_match_score(product, sv) == 2)
        if contradicts:
            notes.append("stale MPN: does not match schematic Value")

        if not usable or contradicts:
            reason = ("obsolete"
                      if product and product.get("productStatus") == "NO_LONGER_MANUFACTURED"
                      else "no stock" if product else "not found")
            sub, sst, gen = None, "", None

            if prefix == "R" and want["kind"] == "resistance" and want["magnitude"] and pkg:
                gen = resistor_mpn(want["magnitude"], pkg)
            if gen:
                sub, sst = R.lookup_token(gen, qty)
                if sub:
                    notes.append(f"generated {gen}")
            if sub is None and prefix in SPEC_SUBSTITUTABLE and want["magnitude"] is not None:
                sub, sst = R.search_spec(want, pkg, qty)
            if sub is None and prefix in SERIES_ONLY and product:
                sub, sst = R.search_family(
                    product.get("translatedManufacturerPartNumber") or "", pkg, qty)
            if sub is None and prefix == "D" and product:
                # Diodes have no parseable magnitude, so look for a part with
                # at least the same voltage/current rating instead.
                sub, sst = R.search_diode(product, qty)
                if sub:
                    notes.append("equivalent rating, larger margin")
            if sub is None and contradicts and want["magnitude"] is not None \
                    and want["kind"] in ("resistance", "capacitance", "inductance"):
                sub, sst = R.search_spec(want, pkg, qty)
            if sub is None and product is None and want["kind"] in (
                    "resistance", "capacitance", "inductance"):
                sub, sst = R.search_spec(want, pkg, qty)

            if sub:
                if product:
                    notes.append(
                        f"{reason}: {original_mpn or product.get('translatedManufacturerPartNumber')}"
                        f" -> {sub.get('translatedManufacturerPartNumber')}")
                elif not gen:
                    notes.append(f"chosen by spec ({reason})")
                row["substituted"] = "yes"
                product, store = sub, sst
            elif product:
                notes.append(reason)
            else:
                notes.append("no equivalent found")

        # ---- 3. fill and verify
        if product:
            fill(row, product, store, qty)
            d = parse_e14_description(product.get("displayName") or "")
            # Package tokens are also present in the MPN itself (CD0603-x is an
            # 0603 part even though the description never says so).
            d["description"] = product.get("displayName") or ""
            conf = "high"
            if row["status"] == "NO_LONGER_MANUFACTURED":
                notes.append("OBSOLETE")
                conf = "none"
            elif (product.get("inv") or 0) <= 0:
                notes.append("zero stock")
                conf = "low"

            if sv["magnitude"] is not None and d["magnitude"] is not None:
                if sv["kind"] != d["kind"]:
                    notes.append(f"kind {sv['kind']}!={d['kind']}")
                    conf = "low"
                elif not close(sv["magnitude"], d["magnitude"]):
                    notes.append(f"VALUE {fmt_mag(sv['magnitude'], sv['kind'])}"
                                 f" != {fmt_mag(d['magnitude'], d['kind'])}")
                    conf = "low"
            elif row["substituted"] == "yes" and want["magnitude"] is not None:
                if not close(want["magnitude"], d["magnitude"]):
                    notes.append("substitute value differs")
                    conf = "low"

            # Compare package families using tokens that appear in both KiCad
            # footprint names and element14 descriptions. If each side names a
            # package but they share nothing, the substitute will not fit.
            fpk = pkg_tokens(fp)
            epk = pkg_tokens(d.get("description") or "")
            # Resistor/capacitor array footprints name the *element* size
            # (R_Array_Convex_4x0603) while the part is described by its body
            # size (1206), so they are not comparable.
            if "array" in fp.lower():
                fpk = set()            # A shared token, or one being a prefix of the other (SOT-23 vs
            # SOT-23-6), counts as compatible -- element14 descriptions are
            # often less specific than the KiCad footprint name.
            compatible = any(a == b or a.startswith(b) or b.startswith(a)
                             for a in fpk for b in epk)
            if fpk and epk and not compatible:
                notes.append(f"PACKAGE footprint={sorted(fpk)} part={sorted(epk)}")
                conf = "low"
            elif pkg and d["package"] and pkg != d["package"]:
                notes.append(f"PACKAGE footprint={pkg} part={d['package']}")
                conf = "low"

            if sv.get("voltage") and d["voltage"] and d["voltage"] + 0.01 < sv["voltage"]:
                notes.append(f"VOLTAGE need {sv['voltage']:g}V part {d['voltage']:g}V")
                conf = "low"

            fmpn = mpn_from_footprint(fp)
            if fmpn and row["mpn"] and fmpn.upper() not in row["mpn"].upper():
                notes.append(f"footprint drawn for {fmpn}")
                conf = "low"

            row["confidence"] = conf
        else:
            row["confidence"] = "none"

        # Packaging guard: this BOM must list individual parts. A full reel or
        # a multi-pack is acceptable only if nothing else is available.
        if product:
            pk = []
            if is_reel(product):
                pk.append("FULL REEL")
            if pack_size(product) > 1:
                pk.append(f"packSize={pack_size(product)}")
            if moq_of(product) > 50:
                pk.append(f"MOQ={moq_of(product)}")
            if pk:
                notes.append("packaging: " + ", ".join(pk))
                if row["confidence"] == "high":
                    row["confidence"] = "low"

        row["note"] = "; ".join(notes)
        if nd:
            row["note"] = (row["note"] + "; " if row["note"] else "") + "NEEDS DECISION: " + nd
            row["confidence"] = "none"
        rows.append(row)

    # ---- post-verification pass
    # Reviewed overrides skip the inline checks, so re-verify every row from its
    # own description before writing. Catches a wrong override as well as a
    # wrong automatic pick.
    for r in rows:
        if not r["mpn"] or r["supplier"] not in ("element14",):
            continue
        m = re.match(r"^([A-Za-z]+)", r["refs"])
        sv = parse_value(r["value"], m.group(1).upper() if m else "")
        d = parse_e14_description(r["desc"])
        if sv["magnitude"] is None or d["magnitude"] is None:
            continue
        bad = []
        if sv["kind"] != d["kind"]:
            bad.append(f"kind {sv['kind']}!={d['kind']}")
        elif not close(sv["magnitude"], d["magnitude"]):
            bad.append(f"value {fmt_mag(sv['magnitude'], sv['kind'])}"
                       f" != {fmt_mag(d['magnitude'], d['kind'])}")
        if sv.get("voltage") and d["voltage"] and d["voltage"] + 0.01 < sv["voltage"]:
            bad.append(f"voltage need {sv['voltage']:g}V part {d['voltage']:g}V")
        pk = pkg_tokens(r["footprint"])
        ep = pkg_tokens(r["desc"])
        if pk and ep and not any(a == b or a.startswith(b) or b.startswith(a)
                                 for a in pk for b in ep):
            bad.append(f"package {sorted(pk)} vs {sorted(ep)}")
        if bad:
            r["note"] = (r["note"] + "; " if r["note"] else "") + "VERIFY: " + "; ".join(bad)
            if r["confidence"] == "high":
                r["confidence"] = "low"

    # ---- write
    cols = list(rows[0].keys())
    with (BOM / "controller-bom.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    issues = [r for r in rows if r["confidence"] in ("low", "none")]
    external = [r for r in rows if r["confidence"] == "external"]
    with (BOM / "issues.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(issues)

    # Not-fitted parts, documented but excluded from any total.
    nf = data["not_fitted"]
    with (BOM / "not-fitted.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ref", "value", "footprint", "reason", "sheet"])
        for s in nf:
            w.writerow([s["Ref"], s["Value"], s["Footprint"],
                        s.get("reason", ""), s["sheet"]])

    from collections import Counter
    print(f"network={api.network_calls}  cache={api.cache_hits}  lines={len(rows)}\n")
    print("confidence:", dict(Counter(r["confidence"] for r in rows)))
    print("substituted:", sum(1 for r in rows if r["substituted"]))
    priced = [r for r in rows if r["extended"] not in ("", None)]
    if external:
        print(f"\nnot from element14: {len(external)} -> "
              + ", ".join(f"{r['refs']}={r['mpn']}" for r in external))
    print(f"priced: {len(priced)}/{len(rows)}")
    print(f"total: {sum(float(r['extended']) for r in priced):,.2f} (mixed currency)")
    smd = [r for r in rows if r["assembly"] == "SMD"]
    tht = [r for r in rows if r["assembly"] == "THT"]
    chk = [r for r in rows if r["assembly"] == "CHECK"]
    def sub(rs):
        return sum(float(r["extended"]) for r in rs if r["extended"] not in ("", None))
    print(f"\nPCBWay assembly (SMD): {len(smd)} lines, {sub(smd):,.2f}")
    print(f"hand solder (THT)   : {len(tht)} lines, {sub(tht):,.2f}")
    if chk:
        print(f"unclassified        : {len(chk)} lines -> "
              + ", ".join(r["refs"] for r in chk))
    print()
    print("=== NEEDS ATTENTION ===")
    for r in issues:
        print(f"  {r['refs']:<24} {str(r['value'])[:18]:<18} {r['confidence']:<5} {r['note'][:96]}")
    print(f"\n-> {BOM/'controller-bom.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
