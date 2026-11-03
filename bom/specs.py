#!/usr/bin/env python3
"""
Spec parsing + comparison helpers.

Two independent sources of truth are reconciled:

  schematic  ->  Value field ("5K6", "100n/50V", "330") + Footprint
  element14  ->  displayName ("VISHAY - CRCW06035K60FKEA - SMD Chip Resistor,
                5.6 kohm, +- 1%, 125 mW, 0603 [1608 Metric], ...")
                + structured attributes (package, voltage rating)

The distributor's `attributes.Resistance` is deliberately NOT used: it is
unitless ("5.6" for 5.6 kohm, "330" for 330 ohm) and therefore ambiguous.
`displayName` carries units and is what a human would read, so we parse that.
"""

import re

# --- schematic Value parsing ------------------------------------------------

_KILO = {"K": 1e3, "M": 1e6, "R": 1.0, "k": 1e3, "m": 1e-3, "G": 1e9}

_CAP_UNITS = {
    "p": 1e-12, "P": 1e-12,
    "n": 1e-9, "N": 1e-9,
    "u": 1e-6, "U": 1e-6, "\u00b5": 1e-6, "\u03bc": 1e-6,
    "m": 1e-3, "M": 1e-3,
    "F": 1.0, "f": 1.0,
}


def parse_value(value: str, prefix: str = "") -> dict:
    """Parse a KiCad Value string into a normalised magnitude.

    Returns {kind, magnitude, voltage, raw} where kind is one of
    'resistance' | 'capacitance' | 'inductance' | 'unknown'.
    """
    raw = value.strip()
    out = {"raw": raw, "kind": "unknown", "magnitude": None, "voltage": None}
    if not raw:
        return out

    # Strip a "/50V" style voltage suffix, and any parenthesised notes
    s = re.sub(r"\([^)]*\)", " ", raw).strip()
    vm = re.search(r"/\s*(\d+(?:\.\d+)?)\s*V\b", s)
    if vm:
        out["voltage"] = float(vm.group(1))
        s = s[: vm.start()].strip()
    s = s.replace(" ", "")
    p = prefix.upper()

    def _try_resistance(t: str) -> dict | None:
        rm = re.fullmatch(r"(\d+(?:\.\d+)?)([RrKkMmGg])(\d+)?", t)
        if not rm:
            return None
        mult = _KILO[rm.group(2)]
        frac = rm.group(3)
        val = float(rm.group(1))
        if frac:
            # "5K6" -> 5.6k : digits after the multiplier form the mantissa
            val = float(f"{int(val)}.{frac}")
        return {"kind": "resistance", "magnitude": val * mult}

    def _try_capacitance(t: str) -> dict | None:
        cm = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([pPnNuU\u00b5\u03bcmMFf])(?:F)?", t)
        if not cm or "ohm" in t.lower():
            return None
        # 'M'/'m' are ambiguous with mega/milli; only trust them when the
        # reference prefix says this really is a capacitor.
        if cm.group(2) in ("M", "m", "F", "f") and not p.startswith("C"):
            return None
        mult = _CAP_UNITS.get(cm.group(2))
        if mult is None:
            return None
        return {"kind": "capacitance", "magnitude": float(cm.group(1)) * mult}

    def _try_inductance(t: str) -> dict | None:
        lm = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([nNuU\u00b5mM])(?:H)", t)
        if not lm:
            return None
        return {"kind": "inductance",
                "magnitude": float(lm.group(1)) * _CAP_UNITS[lm.group(2)]}

    # Try interpretations in an order hinted by the reference prefix, so that
    # e.g. "1M" on R14 is 1 megohm and not 1 millifarad.
    order = {
        "R": (_try_resistance, _try_capacitance, _try_inductance),
        "C": (_try_capacitance, _try_inductance, _try_resistance),
        "L": (_try_inductance, _try_capacitance, _try_resistance),
    }.get(p[:1], (_try_inductance, _try_capacitance, _try_resistance))

    for attempt in order:
        hit = attempt(s)
        if hit:
            out.update(hit)
            return out

    pm = re.fullmatch(r"(\d+(?:\.\d+)?)", s)
    if pm:
        val = float(pm.group(1))
        if prefix.upper().startswith("R"):
            out["kind"] = "resistance"
            out["magnitude"] = val
            out["ambiguous_unit"] = True
        elif prefix.upper().startswith("C"):
            out["kind"] = "capacitance"
            out["magnitude"] = None  # bare number is not a capacitance
            out["ambiguous_unit"] = True
        return out

    return out


# --- element14 displayName parsing -----------------------------------------

_UNIT_SCALE = {
    "p": 1e-12, "n": 1e-9, "\u00b5": 1e-6, "u": 1e-6, "m": 1e-3,
    "": 1.0, "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9,
}


def parse_e14_description(display: str) -> dict:
    """Extract magnitude, package and voltage from an element14 displayName.

    The kind is decided from the *words*, not from whichever unit regex
    happens to match first. This matters because an electrolytic capacitor
    description reads "... 100 uF, 35 V, 0.5 ohm, 2000 hours ..." -- the
    "0.5 ohm" is ESR, not a resistance.
    """
    out: dict = {"magnitude": None, "kind": "unknown", "package": None,
                 "voltage": None, "description": display}
    if not display:
        return out
    # Drop the "<BRAND> - <MPN> - " prefix
    body = display
    parts = display.split(" - ", 2)
    if len(parts) == 3:
        body = parts[2]

    low = body.lower()
    if "capacitor" in low or re.search(r"\bcap\b", low):
        out["kind"] = "capacitance"
    elif "resistor" in low or "potentiometer" in low:
        out["kind"] = "resistance"
    elif "inductor" in low or "choke" in low or "ferrite" in low:
        out["kind"] = "inductance"
    elif re.search(r"\b(ohm|ohms|kohm|Mohm)\b", body):
        out["kind"] = "resistance"

    def _first(pattern: str) -> float | None:
        m = re.search(pattern, body)
        if not m:
            return None
        return float(m.group(1)) * _UNIT_SCALE.get(m.group(2) or "", 1.0)

    if out["kind"] == "resistance":
        out["magnitude"] = _first(
            r"([\d.]+)\s*(k|K|M|G)?\s*(?:ohms?|ohm)\b"
        )
    elif out["kind"] == "capacitance":
        out["magnitude"] = _first(
            r"([\d.]+)\s*(\u00b5|\u03bc|u|n|p|m)?F\b(?!\w)"
        )
    elif out["kind"] == "inductance":
        out["magnitude"] = _first(
            r"([\d.]+)\s*(\u00b5|\u03bc|u|n|m)?H\b(?!\w)"
        )
    else:
        # Unknown kind: try each in turn, but never fall back to a bare
        # resistance match when the text also mentions a capacitor.
        for kind, pat in (
            ("capacitance", r"([\d.]+)\s*(\u00b5|\u03bc|u|n|p|m)?F\b(?!\w)"),
            ("inductance", r"([\d.]+)\s*(\u00b5|\u03bc|u|n|m)?H\b(?!\w)"),
            ("resistance", r"([\d.]+)\s*(k|K|M|G)?\s*(?:ohms?|ohm)\b"),
        ):
            v = _first(pat)
            if v is not None:
                out["kind"], out["magnitude"] = kind, v
                break

    # package: "0603 [1608 Metric]" / "SOT-23" / "TQFP-32"
    m = re.search(r"\b(\d{4})\s*\[\d{4}\s*Metric\]", body)
    if m:
        out["package"] = m.group(1)
    else:
        m = re.search(r"\b((?:SOT|SOIC|TQFP|VQFN|QFN|SOD|SMA|SMB|SMC|DO|TO|DIP|MSOP|TSSOP|SSOP|BGA|LQFP|DFN)[-\w]*)", body)
        if m:
            out["package"] = m.group(1).rstrip("-")

    # voltage: "10 V", "50 V" -- take the first standalone V figure
    m = re.search(r"\b(\d+(?:\.\d+)?)\s*V\b", body)
    if m:
        out["voltage"] = float(m.group(1))

    return out


# --- price formatting ------------------------------------------------------

def fmt_price(v, places: int = 4, min_places: int = 2) -> str:
    """Format a price the way element14 does: up to `places` decimals, with
    trailing zeros trimmed but never fewer than `min_places`.

        0.0275 -> '0.0275'      0.023 -> '0.023'
        2.7    -> '2.70'        5      -> '5.00'
    """
    if v is None or v == "":
        return ""
    try:
        x = float(v)
    except (TypeError, ValueError):
        return str(v)
    txt = f"{x:.{places}f}"
    if "." in txt:
        whole, frac = txt.split(".")
        frac = frac.rstrip("0").ljust(min_places, "0")
        return f"{whole}.{frac}"
    return txt


# --- comparison ------------------------------------------------------------

def close(a: float | None, b: float | None, rel: float = 0.01) -> bool:
    if a is None or b is None:
        return False
    if a == b == 0:
        return True
    return abs(a - b) / max(abs(a), abs(b)) < rel


def fmt_mag(m: float | None, kind: str) -> str:
    if m is None:
        return "?"
    unit = {"resistance": "\u03a9", "capacitance": "F", "inductance": "H"}.get(kind, "")
    if kind == "resistance":
        if m >= 1e6:
            return f"{m/1e6:g}M{unit}"
        if m >= 1e3:
            return f"{m/1e3:g}k{unit}"
        return f"{m:g}{unit}"
    if kind == "capacitance":
        if m >= 1e-6:
            return f"{m/1e-6:g}\u00b5F"
        if m >= 1e-9:
            return f"{m/1e-9:g}nF"
        return f"{m/1e-12:g}pF"
    if kind == "inductance":
        if m >= 1e-3:
            return f"{m/1e-3:g}mH"
        if m >= 1e-6:
            return f"{m/1e-6:g}\u00b5H"
        return f"{m/1e-9:g}nH"
    return f"{m:g}{unit}"


if __name__ == "__main__":
    # Self-test: values that appear in this design, plus the element14 strings
    cases = [
        ("330", "R", 330.0, "resistance"),
        ("1M", "R", 1e6, "resistance"),
        ("5K6", "R", 5600.0, "resistance"),
        ("6K8", "R", 6800.0, "resistance"),
        ("130K", "R", 130e3, "resistance"),
        ("220K", "R", 220e3, "resistance"),
        ("10K", "R", 10e3, "resistance"),
        ("1K", "R", 1e3, "resistance"),
        ("680K", "R", 680e3, "resistance"),
        ("330K", "R", 330e3, "resistance"),
        ("100n/50V", "C", 100e-9, "capacitance"),
        ("1u/50V", "C", 1e-6, "capacitance"),
        ("22u/25V", "C", 22e-6, "capacitance"),
        ("100u/35V", "C", 100e-6, "capacitance"),
        ("68u/35V", "C", 68e-6, "capacitance"),
        ("22p", "C", 22e-12, "capacitance"),
        ("1u", "C", 1e-6, "capacitance"),
        ("100n", "C", 100e-9, "capacitance"),
        ("10uH", "L", 10e-6, "inductance"),
    ]
    bad = 0
    for val, pfx, want, kind in cases:
        got = parse_value(val, pfx)
        ok = got["kind"] == kind and close(got["magnitude"], want)
        if not ok:
            bad += 1
            print(f"  FAIL {val!r:<12} -> {got['kind']} {got['magnitude']} (want {kind} {want})")
    print(f"parse_value: {len(cases)-bad}/{len(cases)} pass")

    e14 = [
        ("VISHAY - CRCW06035K60FKEA - SMD Chip Resistor, 5.6 kohm, \u00b1 1%, 125 mW, 0603 [1608 Metric], Thick Film",
         5600.0, "resistance", "0603"),
        ("MULTICOMP PRO - MCSR06X3300FTL - SMD Chip Resistor, 330 ohm, \u00b1 1%, 100 mW, 0603 [1608 Metric]",
         330.0, "resistance", "0603"),
        ("YAGEO - CC0603KRX7R9BB104 - SMD Multilayer Ceramic Capacitor, 0.1 \u00b5F, 50 V, 0603 [1608 Metric]",
         100e-9, "capacitance", "0603"),
        ("MURATA - GRM31CR61E226KE15L - SMD Multilayer Ceramic Capacitor, 22 \u00b5F, 25 V, 1206 [3216 Metric]",
         22e-6, "capacitance", "1206"),
    ]
    bad = 0
    for s, want, kind, pkg in e14:
        g = parse_e14_description(s)
        ok = g["kind"] == kind and close(g["magnitude"], want) and g["package"] == pkg
        if not ok:
            bad += 1
            print(f"  FAIL {s[:60]!r} -> {g['kind']} {g['magnitude']} {g['package']}")
    print(f"parse_e14_description: {len(e14)-bad}/{len(e14)} pass")

    prices = [(0.0275, "0.0275"), (0.023, "0.023"), (2.7, "2.70"), (5, "5.00"),
              (0.0031, "0.0031"), (0.0049, "0.0049"), (13.5, "13.50"),
              (0.006, "0.006"), (0.4, "0.40")]
    bad = sum(1 for v, want in prices if fmt_price(v) != want)
    print(f"fmt_price: {len(prices)-bad}/{len(prices)} pass")
