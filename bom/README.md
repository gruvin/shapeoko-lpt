# BOM tooling — `controller.kicad_pro`

Resolves every fitted BOM line in the KiCad project to a real **element14**
order code, verifies it against the schematic, and writes a purchasing sheet.

Current state: **63 fitted lines, 58 resolved with confidence, 5 need a human
decision** (see `REVIEW.md`). Prices are element14 NZ list prices (NZD) and are
a point-in-time snapshot — fine for budget guidance, not for a quote.

## Pipeline

```
controller.kicad_sch + 4 sheets
        │
        │  extract.py     parse s-expressions -> one record per symbol
        ▼
   symbols.json
        │
        │  build.py       group by (Value, Footprint); split out DNP / net-ties
        ▼
   groups.json
        │
        │  resolve.py     element14 API: pick one orderable part per line,
        │                 verify Value/Footprint, substitute where needed
        ▼
controller-bom.csv   issues.csv   not-fitted.csv
        │
        │  summarize.py
        ▼
   REVIEW.md
```

Run the whole thing:

```sh
./bom/run.sh              # analyse only - never touches the schematic
python3 bom/apply_fields.py --dry-run   # preview writing results back
python3 bom/apply_fields.py            # write results into the schematic
```

`run.sh` is safe to run any time. `apply_fields.py` modifies the `.kicad_sch`
files, so it is a separate, deliberate step.

## Files

| file | what it is |
|---|---|
| `extract.py` | parses the schematic hierarchy; one row per reference designator |
| `build.py` | groups symbols into BOM lines; handles `,` inside MPNs (`BC847C,215`) |
| `e14.py` | element14 Product Search API client: caching + rate limiting |
| `specs.py` | parses KiCad `Value` strings and element14 descriptions; has self-tests |
| `resolve.py` | the resolver and verifier |
| `audit_packaging.py` | verifies every line is an individual part, not a reel |
| `apply_fields.py` | writes the resolved part data back into the schematics |
| `fix_stale_instances.py` | strips stale per-project instance data from child sheets |
| `make_pcbway_bom.py` | writes `controller-PCBWay.xlsx` from the sample template |
| `summarize.py` | renders `REVIEW.md` |
| `overrides.json` | **human-reviewed decisions**; wins over everything else |
| `cache/` | every API response, so re-runs cost no quota (gitignored) |

Generated: `controller-bom.csv` (the BOM), `issues.csv` (needs a human),
`not-fitted.csv` (DNP/net-ties, excluded from totals), `REVIEW.md`.

## API

Official element14 Product Search API (`partner.element14.com`) — free,
self-service. Credentials live in `.env` at the repo root, which is gitignored:

```
E14_API_KEY=...
E14_STORE=nz.element14.com
E14_STORES=nz.element14.com,au.element14.com,uk.farnell.com
```

**The cache never expires** — good for re-runs, wrong weeks later. Stock and
prices silently go stale, and a re-run will happily "confirm" a part that is no
longer available. Before ordering, refresh it:

```sh
E14_REFRESH=1 ./bom/run.sh      # ignores the cache, re-fetches everything
```

That is ~275 calls for this design, comfortably inside the daily limit.

Limits: **2 calls/sec, 1000/day**. `e14.py` throttles to one call every 0.55 s
and caches aggressively; a full rebuild from a warm cache makes zero calls.

## How a part gets chosen

1. **Reviewed override** (`overrides.json`) — used as-is, then re-verified.
2. **Existing `E14MFR#` / `E14PART`** from the schematic.
3. **MPN embedded in the footprint name** (`..._43045-0412_...`) — strongest
   signal for connectors, since it says what the board was drawn for.
4. The schematic `Value`, when it is actually an MPN (`USBLC6-2SC6`).
5. **Generated MPN** for resistors: MULTICOMP PRO `MCSR__X<mmm><e>FTL`.
6. **Keyword search**, filtered hard on parsed spec + package.

Candidates are ranked by *agreement with the schematic first*, then stock, then
MOQ, then price. Stock never outranks correctness — that ordering is what
allowed the stale-MPN bugs to hide in the first place.

## Verification

Two independent sources are reconciled:

- **schematic** — `Value` (`5K6`, `100n/50V`, `330`) + `Footprint`
- **element14** — `displayName` (`"SMD Chip Resistor, 5.6 kohm, ± 1%, 0603"`)

The API's structured `attributes.Resistance` is deliberately **not** used: it is
unitless (`5.6` for 5.6 kΩ, `330` for 330 Ω) and therefore ambiguous.

Checks performed per line: value magnitude, kind, package family, voltage rating,
and (for connectors) whether the chosen MPN matches the footprint.

## Packaging — individual parts only

We want single parts, not full reels. element14 signals this three ways and they
do not always agree:

* `reeling` — boolean in the API response. **This is the one to trust.**
* SKU suffix `RL` — 147 of 147 such SKUs in this dataset had `reeling: true`,
  so it is a reliable *hint*, but it is not the authoritative field.
* MOQ — **not reliable**. One reel SKU (`2393287RL`, an ACSL-6310 optocoupler)
  has MOQ 1, and three others have MOQ 10. Screening on MOQ would miss them,
  which is why `is_reel()` reads the flag.

`resolve.py` demotes any line whose chosen part is a reel, a multi-pack, or has
MOQ > 50, and `audit_packaging.py` re-checks the finished BOM against the API.

## Substitution policy

- **R / C / L / D** — automatic substitution by spec (package + value + voltage,
  and matching diode configuration: a dual-series part must not replace a single).
- **U / Q / Y / K / SW / RN** — only within the same MPN family, else flagged.
- **No footprint assigned** — never guessed; the line is flagged instead.

## Not fitted

`NT*` are net-ties (copper links, not parts). `C28` is a documentation symbol for
a deliberate groundplane gap. `JX1`, `J2B1`, `J9`, `SW1`, `SW2`, `R1` are
unpopulated. All are listed in `not-fitted.csv` and excluded from totals.

## Sourcing summary

64 fitted lines: **61 from element14**, 3 from elsewhere (J1/J2 and SW3 from
LCSC, J3 from Samtec — all THT, hand-soldered, so PCBWay's SMD-only policy does
not force a pricier distributor).

| ref | part | supplier P/N | note |
|---|---|---|---|
| `K1` | `OJ-SS-124HM,000` (TE/OEG OJ, **vented**, 24 VDC, SPST-NO 10 A) | element14 `1891694`, $4.11 | Sealing is not required. Coil is 1.28k = 450mW / 18.75mA vs the sealed part's 200mW / 8.3mA; the coil driver is Q5 (BC857, 100mA) so that is fine, and the contacts only switch the VFD digital input `VFD_FWD`. Superseded options are kept in the `alternates` field: DigiKey `OJS-SH-124HMF,00000` (sealed), element14 `3764773` (sealed 16 A, zero stock, 24-week lead), `OJ-SS-124LMHF,000` (vented, 200mW, Class F, 8 A). |
| `SW3` | TS-1088-AR02016 | LCSC `C720477` | Chinese part, local stock; also orderable by PCBWay |

`K1`'s board footprint was verified against the TE datasheet: pad spacings
7.62 / 12.70 / 2.54 mm match `.300` / `.500` / `.100 in`.

## Passive consolidation

All 24 capacitor and resistor lines are **MULTICOMP PRO** (element14's own
brand), on 21 distinct order codes. This was a deliberate choice: fewer brands,
better element14 stock, and much cheaper on the electrolytics.

Note that consolidation is not automatically cheaper — MULTICOMP's 0603
1µF/50V X7R costs more than the TDK X5R it replaced. The net saving came almost
entirely from `C8` (68µF 35V: $8.63 for the KEMET part vs $0.44 for MULTICOMP).

`C7` needed a schematic change: MULTICOMP has no 22µF/25V in 1206, so the Value
became `22u/16V` and the part is `1206X226K160CT`. Safe here — the rail is the
MAX5035 5V buck output.

Watch for duplicate listings: element14 often carries the same MPN under two
order codes with very different prices (e.g. `1206X226K160CT` is $0.273 on
249715401 and $0.625 on 2497154). `resolve.py` picks the cheaper.

## Resolved schematic issues

All previously-flagged items are now closed:

- `J7` is a **male** DB25 plug (`5504F1-25P-02A-03`), not a socket. Footprint
  corrected to `DSUB-25_Pins_Horizontal_..._EdgePinOffset7.70mm_...`.
- `D7`/`D8`/`D11` on the SOD-523 land pattern, using `BAT54KFILM`
  (`BAT54JFILM` is SOD-323 and does not fit).
- `L3` 0603 AVCC filter, `L2` 0805 USB-shield clamp, `SW3` named and drawn.
- `R1`, `SW1`, `J2B1` DNP; `JX1` DNP (external connector, reference only).
- `J1`/`J2`/`J3` are the inter-board 23-way connectors; see below.

## Inter-board connectors J1 / J2 / J3 (20.00 mm stack)

The two boards stack a **fixed 20.00 mm** apart on mechanical standoffs, and the
socket is a stock 8.5 mm strip, which fixes the pin geometry:

```
controller PCB top            0.00
socket body bottom           11.50     (20.00 - 8.50)
required pin tip             16.00 +/-0.25   (measured by Bryan)
=> J3 post must be 15.75 - 16.25 mm above the PCB
```

Genders (confirmed by Bryan — the prototype had them reversed, the PCB is right):
**J3 = male pins on the mother/lower board, pins up** (interface boards live in
drawers, so they must not carry exposed pins); **J1/J2 = female sockets on the
underside of the interface boards**. J1 (GRBL) and J2 (LPT) are alternatives —
one interface board is connected at a time.

| ref | part | supplier | P/N | price |
|---|---|---|---|---|
| `J1`, `J2` | 23-way socket strip, 8.5 mm body, 3 mm tails | LCSC | `HC-PM254-8.5H-1x23PZ` = `C41376162` | $0.23 (MOQ 5) |
| `J3` | 23-way header, tin, .620in/15.75 mm post, .830in OAL | Samtec | `TSW-123-17-T-S` | $1.52 |

Backup if the 23-way socket goes out of stock: `HC-PM254-8.5H-1x24PZ` =
`C41376163` (15 714 in stock), cut one position.

Why 15.75 mm and not 16.00 mm: Samtec TSW lead styles step by .100in at that end
(`-15` = 13.21 mm, `-17` = 15.75 mm, `-18` = 18.29 mm, which would bottom out in
an 8.5 mm socket). 15.75 mm sits on the lower edge of the measured window. If
that proves marginal, `MTSW-123-10-T-S-630` gives exactly .630in = 16.00 mm but
is build-to-order with no stock.

Schematic symbols were corrected to match the PCB genders (`Conn_01x23_Female`
for J1/J2, `Conn_01x23_Male` for J3) and the `Value` fields from the placeholder
`Conn_01x06_Female` / `Conn_01x022_Male` to `CONN_23W_SOCKET` / `CONN_23W_PIN`.
The footprints were already right and were left alone.

## Legacy symbol names — do not "migrate" the transistors

KiCad 10 renamed the connector symbols, so 9 `lib_id`s in this design no longer
exist in the installed libraries. ERC reports them as `lib_symbol_issues`
(9 symbols, 15 messages) plus 21 `lib_symbol_mismatch` where the symbol *is*
found but the copy cached in the `.kicad_sch` differs from the library version.
Both are cosmetic: eeschema draws from the cached definition inside the
schematic, so the design works. They matter the day someone runs *Update Symbols
from Library* — a name that resolves to nothing becomes a mystery box.

Seven of the nine are **pin-identical** drop-ins (same pin numbers, names,
positions, lengths and electrical types — verified against the installed libs):

| legacy | KiCad 10 |
|---|---|
| `Connector:Conn_01x02_Female` | `Connector:Conn_01x02_Socket` |
| `Connector:Conn_01x03_Female` | `Connector:Conn_01x03_Socket` |
| `Connector:Conn_01x04_Female` | `Connector:Conn_01x04_Socket` |
| `Connector:Conn_01x06_Female` | `Connector:Conn_01x06_Socket` |
| `Connector:Conn_01x23_Female` (J1, J2) | `Connector:Conn_01x23_Socket` |
| `Connector:Conn_01x23_Male` (J3) | `Connector:Conn_01x23_Pin` |
| `Connector:Conn_01x02_Male` | `Connector:Conn_01x02_Pin` |

**The last two are the trap.** `Q_PMOS_GDS` (`power.kicad_sch`) and
`Q_PNP_BEC` (`conn.kicad_sch`) have identical pin *geometry* to the modern
`Q_PMOS` / `Q_PNP`, but the modern symbols number their pins with **letters**
(`G`/`D`/`S`, `B`/`C`/`E`) while the SOT-23 and TO-252 land patterns on this
board number their pads **1/2/3**. Renaming would silently unmap the
transistor from its footprint. Leave those two alone unless the footprints are
changed with them.

Note also that within the connector family the *genders are mirror drawings of
each other* — pin 1 of `Conn_01x23_Socket` sits on the opposite side to pin 1 of
`Conn_01x23_Pin`. Swapping `_Male`↔`_Female` (rather than `_Male`→`_Pin`) moves
every pin 10.16 mm sideways and leaves the wires hanging; the instances then need
mirroring to reconnect, which is why J1/J2/J3 carry `(mirror x)`.

### Renaming a cached symbol safely

A `lib_id` is stored in **two** places, and a rename must move both:

```
(lib_id "Connector:Conn_01x23_Male")          <- the placed instance
(lib_symbols
  (symbol "Connector:Conn_01x23_Male"          <- parent header, WITH nickname
    (symbol "Conn_01x23_Male_0_1"              <- child unit, WITHOUT nickname
    (symbol "Conn_01x23_Male_1_1"
```

Miss the child units and eeschema refuses the whole file with a bare
`Failed to load schematic` — no line number, no hint. `kicad-cli sch export
netlist` is the cheapest way to prove a file still loads.

Verification that catches the dangerous mistakes: export the netlist before and
after and diff the `(nets` section only. A correct rename changes the `(part
"…")` names and **nothing else**; any change under `(nets` means a pin moved.

If ERC then reports `lib_symbol_mismatch` for those symbols, that is cosmetic:
the cache still holds the old `_Female`/`_Male` drawing, which differs from the
installed `_Socket`/`_Pin` in graphics only (pins are identical, verified).
*Tools → Update Symbols from Library* in the GUI clears it properly.

## Writing results back into the schematic

`apply_fields.py` pushes the resolved data into the symbol fields so the
schematic itself is the source of truth:

| field | content |
|---|---|
| `E14MFR#` | manufacturer part number (all parts) |
| `E14PART` / `E14MOQ` | element14 order code + MOQ |
| `DKPART` | DigiKey part number (DigiKey lines) |
| `LCSC` / `LCSCMFR#` | LCSC number + MPN (LCSC lines) |
| `MFR` | brand / manufacturer name |
| `Description` / `Datasheet` | part description + datasheet URL |
| `ALT` | alternate source, where one was recorded |

Every field written by `apply_fields.py` is forced to `(hide yes)`, so none of
this metadata appears on the drawing — `Description` in particular, which in
KiCad 10 is *visible* by default and would otherwise drop a long element14
description onto the schematic.

`Value` is deliberately **not** touched — it is the functional label driving
silkscreen and netlist meaning ("YELLOW", "RESET", "DB25_PINS_MountingHoles"),
not a part number.

Two things it deliberately will not clobber:

* a **non-empty `Datasheet`** — the real ST/Microchip/ADI/TE PDFs are better
  than the login-gated IHS links harvested from element14;
* a **non-empty `Description`** — hand-written ones (J7, SW3) are kept.

Fields that stop applying are **cleared**, not left behind. When `K1` moved from
DigiKey back to element14, its `DKPART` had to be emptied and its `ALT`
rewritten; without that, stale distributor data silently rides along. Two rules
make it safe:

* an empty value means *clear this field if it exists* — it is never used to
  create a blank property on every symbol (that mistake produced 236 spurious
  changes for a 2-field edit);
* the verifier treats "absent" as success for a field that is meant to be empty.

A dry run after a single-part change should report a handful of changes. Dozens
means something is wrong — look before writing.

### Two traps worth remembering

1. **KiCad 10 schematic properties carry no UUID.** Inserting one makes
   eeschema reject the entire file with a bare "Failed to load schematic".
2. **Collect replacements against the original string and apply them
   right-to-left.** Editing a block in place while iterating matches over the
   same string shifts every later offset and silently corrupts the file.

The script guards against both: it computes every sheet first, verifies that
every field reads back correctly and that parentheses balance, and only then
writes. Re-running it is a no-op.

## Stale instance data in child sheets

A `.kicad_sch` that was once saved as its own standalone project keeps a
`(project "<its own name>" …)` entry inside every symbol's `(instances …)`
block, next to the `(project "controller" …)` entry added when the sheet is
placed in this design.

`grbl-interface.kicad_sch` carried 62 such entries, and they claimed **different
designators** — `U1`, `C4`, `C7`, `C12` — which collide with the real `U1`,
`C4`, `C7`, `C12` in `power.kicad_sch`. With two competing references per
symbol, whichever entry KiCad resolves wins, so designators can appear
duplicated and the BOM dialog may drop or merge those symbols (inconsistently —
it is resolution-order dependent, which is why the symptom came and went).

`fix_stale_instances.py` removes any `(project …)` entry that is not
`controller`, then verifies that every symbol still has exactly one controller
entry and that parentheses balance. It is idempotent.

After running it, the design has **265 placed symbols and 265 unique
designators** — no duplicates.

## PCBWay BOM

```sh
python3 bom/make_pcbway_bom.py                   # 62 rows, title '1PCS' (one assembled board)
python3 bom/make_pcbway_bom.py --tht omit         # SMD only
```

Uses PCBWay's own sample workbook as a template, so their logo, title, header
styling, column widths and instruction footer are preserved — only the data rows
are replaced. Output: `bom/controller-PCBWay.xlsx`.

Two openpyxl traps are handled explicitly:

* **Merged ranges are not moved** by `delete_rows`/`insert_rows`. The footer's
  `A:I` merges stayed over the new data rows and silently swallowed every write
  to columns B–I. The script unmerges below the header and re-merges the footer
  at its new position.
* Cells carrying a **hyperlink** are stranded by row shifting, so the footer is
  snapshotted and re-emitted rather than moved.

Also note: PCBWay places **SMD only**; THT lines are included but marked
`thru-hole` so they see the full picture without quoting placement.

Requires `openpyxl` (installed under Homebrew python with
`pip install --break-system-packages openpyxl`).
