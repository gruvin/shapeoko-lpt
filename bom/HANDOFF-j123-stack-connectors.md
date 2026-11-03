# Hand-off: source parts (or a fabrication method) for J1/J2/J3 stack connectors

## The problem in one line

Three boards stack 20 mm apart using 23-way 2.54 mm connectors, and no standard
part reaches — the pins come up roughly **7 mm short**. Either find tall sockets,
find long-pin headers, or document a fabricated solution and leave J1/J2/J3 DNP.

## Physical reality (from Bryan — trust this, not the CAD)

```
        ┌────────────────────────────┐   ← interface board (bottom face)
        │  J1 / J2  pin headers       │      on B.Cu, pins pointing DOWN
        │  (standard, tin)            │
        └────────────────────────────┘
                    ↕  20.00 mm  (top of controller PCB → bottom of interface PCB)
             ↓ pins need 200 mil = 5.08 mm insertion
        ┌────────────────────────────┐
        │  J3  raised 23-way SOCKET   │      top of socket at 17.4 mm above PCB top
        │  + base alignment strip     │
        ├────────────────────────────┤   ← controller board (top face)
```

- **Stack height: 20.00 mm**, top of controller board to bottom of interface board.
- **J3** = 23-way **female socket**, raised. Top of the socket body measured at
  **17.4 mm above the controller PCB top surface**.
- **J1 / J2** = 23-way **male pin headers**, mounted on the **B.Cu (bottom)** side
  of the interface boards, pins pointing down into J3.
- Required pin insertion depth: **200 mil = 5.08 mm**.
- A **"base strip"** sits at the bottom of the pins to hold them aligned during
  PCB installation — i.e. a second socket strip (or spacer) used as a soldering jig.
- Shortfall with standard parts: **approximately 7 mm** too short.

## The CAD is NOT representative — do not trust it

Bryan has confirmed the STEP/3D models are **placeholders**. The current PCB says:

| ref | footprint in PCB | 3D model |
|---|---|---|
| J1, J2 | `Connector_PinSocket_2.54mm:PinSocket_1x23_P2.54mm_Vertical` | stock KiCad, 8.5 mm body |
| J3 | `Connector_PinHeader_2.54mm:PinHeader_1x23_P2.54mm_Vertical` | stock KiCad, 8.5 mm |

That is the **opposite** of the physical unit (J3 is the socket, J1/J2 are the
headers), and neither shows 17.4 mm or 20 mm. So whatever is chosen:

- the schematic `Value` for J1/J2/J3 is also wrong (`Conn_01x06_Female`,
  `Conn_01x022_Male`) — 23-way in all three cases;
- the PCB footprint must be changed to match the real part;
- and the 3D model should be replaced or dropped.

## The awkward bit: 23 ways

1x23 is non-standard. Bryan's method is to buy **1×36 or 1×40 strip and cut**.

- Single-row male header strip: trivially cuttable.
- Single-row female socket strip: usually cuttable.
- **"Elevated" / tall sockets are often moulded with closed end walls and cannot be
  cut** — this is the main constraint that may kill option A below.

If a part cannot be cut, it must exist in ≥23 ways in one row.

## Two candidate topologies

### Option A — tall socket at J3, standard headers at J1/J2

Keep J1/J2 as standard tin pin headers; replace J3 with a single-row 2.54 mm female
header whose body is ~17 mm tall (or an "elevated socket strip" that stacks to it).

- Pro: minimal change to J1/J2.
- Con: tall sockets are less common, usually more expensive, often not cuttable,
  and rarely stocked in quantity.

### Option B — standard socket at J3, long-pin headers at J1/J2

J3 becomes a standard 8.5 mm socket; J1/J2 use 2.54 mm headers with pins roughly
**7 mm longer** than standard so they reach down into it.

- Pro: both parts cheap, both cuttable from 1×40 strip, wide availability,
  LCSC/Chinese stock has many pin-length variants.
- Con: long pins will also protrude **above** the interface board (they are through
  hole) — check clearance into the enclosure. Also changes two line items instead of one.

Bryan's own leaning was that B "might" work; it is probably the more buildable route.

## Search leads

Pin length on a 2.54 mm header is a *variant field* in most manufacturers' part
numbers, so search by series then pick the long-post variant:

- **Samtec** — `TSW` (headers; the middle field sets post length, e.g.
  `TSW-1xx-07-T-S` vs `TSW-1xx-24-T-S`), `ESQ` (elevated socket strip), `SSQ`/`SSW`
  (socket strips). Samtec publish a pin-length matrix.
- **Preci-Dip** — 2.54 mm headers with extended pins (series 350/351 etc.).
- **Würth** — WR-PHD range.
- **Harwin** — M20 series (`M20-999…`, `M20-997…`).
- **Multicomp PRO** — element14's own brand; check for extra-long-pin variants.
- **LCSC / PCBWay** — the likely best source for long-pin 2.54 mm strip and for
  elevated single-row sockets. Search in Chinese as well as English:
  `2.54mm 单排针 长针` (long-pin single-row header),
  `2.54mm 排母 加高` (elevated female header),
  `2.54 pin header long pin 20mm`.
  LCSC part pages expose **Pin Length** and **Height** attributes — filter on those.

Note these are **THT**, and Bryan's current PCBWay policy is SMD-only assembly, so
J1/J2/J3 get hand-soldered regardless. That removes any pressure to source them
from element14 — LCSC is fine and much cheaper.

`bom/e14.py` can query element14 directly; LCSC has no public API and needs browser
scraping (Camofox; LCSC's search is JS-heavy, so a snapshot of the product page is
more reliable than the results list).

## Acceptance criteria

1. Mates reliably across a fixed 20 mm stack with **≥ 5.08 mm** pin insertion.
2. Cuttable to 23 ways, or stocked in ≥23 ways single row.
3. 2.54 mm pitch, single row, THT.
4. **Tin** plating (J1/J2 are tin, not gold — keep cost down).
5. Sensible total cost for 3 connectors × 1 board.
6. If nothing matches: leave J1/J2/J3 DNP and write a fabrication note giving the
   exact long-pin header length + socket + base strip spec.

## Questions for Bryan before searching

1. Confirm the roles: **J3 = female socket (raised), J1/J2 = male headers on B.Cu.**
2. What is the **measured** pin protrusion on the current J1/J2 headers below the
   interface board? That fixes the exact extra length needed (the 7 mm is an estimate).
3. Is the "base strip" a second socket used as a spacer/jig, or a purpose-made part?
4. Do J1/J2's pins protrude **above** the interface board? Any enclosure clearance
   limit on that (relevant to option B)?
5. Preferred route if both are viable — A (one tall socket) or B (two long-pin headers)?
6. Once chosen, should the PCB footprints be corrected to match (they currently say
   the opposite roles)?

## Current BOM state for these three

`bom/overrides.json` → `_dnp` currently excludes them:

```json
"J1": "23-way socket strip - oddball length, order the next size up and cut",
"J2": "23-way socket strip - oddball length, order the next size up and cut",
"J3": "23-way pin header strip - oddball length, order the next size up and cut",
```

They appear in `bom/not-fitted.csv` and are absent from `bom/controller-bom.csv`
and the PCBWay sheet. Once a part is chosen, remove the `_dnp` entries and add
`overrides.json` entries with the MPN, then re-run:

```sh
./bom/run.sh && python3 bom/apply_fields.py && python3 bom/make_pcbway_bom.py
```

## Context you will need

- Project: `/Users/bryan/projects/shapeoko-lpt` (KiCad 10.0.7, `controller.kicad_pro`).
- Read `bom/README.md` first — it explains the pipeline, the `overrides.json`
  mechanism, and the traps already hit (KiCad GUI "Current sheet only", the
  `--sort-asc` CLI crash, merged-cell handling, property UUID rules).
- The BOM is otherwise complete: 62 lines, $206.70. Do not redo that work.
