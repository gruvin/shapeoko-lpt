# Hand-off: generate a PCBWay-format XLSX BOM

> **Status: DONE** — implemented in `bom/make_pcbway_bom.py`.
> Kept for the template analysis and the recorded decisions; the
> "Questions worth settling" at the end are still open.

## Recommendation: standalone script, not a KiCad plugin

KiCad's Python API only covers `pcbnew` — there is **no `eeschema` Python API**, so
a schematic-side BOM "plugin" cannot be written in Python. Anything resembling one
would be C++ or, more realistically, an external tool anyway.

There is also no need: the BOM data is already fully resolved and sitting in a CSV.
The right shape is a small script that reads `bom/controller-bom.csv` and writes the
spreadsheet. Keep KiCad as the source of truth and this as a formatter.

Second recommendation: **use PCBWay's sample as a template**, don't build a workbook
from scratch. It carries their logo, title, header styling, column widths and the
instruction footer. Replacing only the data rows guarantees the file still looks like
what their tooling expects.

## Project state (already done — do not redo)

`/Users/bryan/projects/shapeoko-lpt` is a KiCad project (Shapeoko CNC controller).
A BOM pipeline already exists in `bom/`:

| file | role |
|---|---|
| `extract.py` → `symbols.json` | per-symbol parse of the 5 schematic sheets |
| `build.py` → `groups.json` | groups symbols into 62 BOM lines, resolves ref ranges |
| `e14.py` | element14 API client (cached, rate-limited) |
| `specs.py` | parses KiCad values / element14 descriptions; has self-tests |
| `resolve.py` → `controller-bom.csv` | resolves + verifies one part per line |
| `apply_fields.py` | writes part data back into the schematics (idempotent) |
| `fix_stale_instances.py` | strips stale per-project instance data (idempotent) |
| `export_bom.sh` | regenerates `controller.csv` via `kicad-cli` |
| `run.sh` | runs the analysis chain |

Current result: **62 lines / 118 parts**, 60 element14 + 1 DigiKey (K1) + 1 LCSC (SW3).
47 SMD, 15 THT. Verified, reviewed, and written into the schematic.

Run `./bom/run.sh` to rebuild. It is read-only w.r.t. the schematics.

## The task

Produce `controller-PCBWay.xlsx` in PCBWay's BOM format from `bom/controller-bom.csv`.

## Template layout — decoded from `~/Desktop/a-sample-of-PCBWay-BOM.xlsx`

Three sheets; **Sheet2 and Sheet3 are empty**. All content is on Sheet1, which also
carries an embedded JPEG logo. Data extraction was done by unzipping the file
(`xl/worksheets/sheet1.xml`, `xl/sharedStrings.xml`).

| cell / row | content |
|---|---|
| `D2` | title, e.g. `xxxx xxxx xxxxx xxPCS BOM  (Sample Bill of Materials)` |
| row 6 | header row (styled) |
| row 7 onwards | data |
| rows 24–26 | boilerplate instruction text — keep as-is |

Header row (row 6):

| col | header | required |
|---|---|---|
| A | `Item #` | |
| B | `*Designator` | yes |
| C | `*Qty` | yes |
| D | `Manufacturer` | |
| E | `*Mfg Part #` | yes |
| F | `Description / Value` | |
| G | `*Package/Footprint` | yes |
| H | `Type` | |
| I | `Your Instructions / Notes` | |

Sample `Type` values observed: `SMD`, `thru-hole`, `DNS`.

Sample data rows (verbatim, for tone/format reference):

```
1  U1       1  Linear       LTC3780EG#PBF        IC BUCK-BOOST CONV 24-SSOP   24-SSOP  SMD
2  U2,U4    2  Fairchild    LM2904M              IC OPAMP DUAL -40-85 C 8-SOIC 8-SOIC   DNS
14 L3       1  TDK          ACM1211-102-2PL-TL   CHOKE COMM MODE 1000 OHM 6A SM SMD     SMD
15 CN3,CN4  2  Molex        53047-0510           CONN HEADER 5POS 1.25MM VERT  5POS     thru-hole
```

Designators are comma separated with no space. Qty is an integer.

## Source data

`bom/controller-bom.csv`, columns:

```
refs,qty,value,footprint,brand,mpn,supplier,sku,store,desc,status,stock,
lead_days,moq,order_qty,unit,extended,currency,assembly,substituted,
alternates,confidence,note
```

Note `refs` contains compressed ranges (`R25-R29,R31-R32`) — expand them. `build.py`
already has `compress_refs`; `groups.json` has the expanded `refs` list per line
keyed by `ref_range`, which is the easy way to get individual designators.

### Column mapping

| PCBWay column | source |
|---|---|
| `Item #` | sequential 1..N |
| `*Designator` | expanded `refs`, comma-joined |
| `*Qty` | `qty` (**board quantity**, not `order_qty` — PCBWay buys what the board needs) |
| `Manufacturer` | `brand` |
| `*Mfg Part #` | `mpn` |
| `Description / Value` | `desc` (fall back to `value` if empty) |
| `*Package/Footprint` | derived from `footprint` — see below |
| `Type` | `SMD` / `thru-hole` from `assembly`; see DNS below |
| `Notes` | sourcing info for external parts; blank otherwise |

### Deriving `Package/Footprint`

The sample uses short human labels (`0603`, `8-SOIC`, `24-SSOP`, `DPAK`, `5POS`), not
KiCad library names. `resolve.py` has `pkg_from_footprint()` which handles 4-digit
metric codes and a few families — **it is not sufficient**. Needs extending to cover
the actual set in this design:

```
C_0603_1608Metric        -> 0603
C_0402_1005Metric…       -> 0402
C_1206_3216Metric        -> 1206
CP_Elec_8x10.5_DOT       -> Elec 8x10.5      (project footprint)
CP_Elec_6.3x7.7_DOT      -> Elec 6.3x7.7
VQFN-32-1EP_4x4mm…       -> VQFN-32
TQFP-32_7x7mm_P0.8mm     -> TQFP-32
SOIC-16W_7.5x10.3mm…     -> SOIC-16W
SOIC-8_3.9x4.9mm…        -> SOIC-8
SO-16_3.9x9.9mm…         -> SO-16
SOT-23 / SOT-23-6        -> SOT-23 / SOT-23-6
SOD-523 / SOD-323        -> SOD-523 / SOD-323
D_SMA_DOT                -> SMA
TO-252-2                 -> TO-252
L_0603_1608Metric        -> 0603
L_12x12mm_H6mm           -> 12x12
R_Array_Convex_4x0603    -> 4x0603
PinHeader_1x03_P2.54mm…  -> 1x03 P2.54
PinSocket_1x23_P2.54mm…  -> 1x23 P2.54
TerminalBlock_Phoenix…   -> e.g. MPT 1x04 P2.54
Molex_Micro-Fit_3.0_43045-0812_2x04…  -> Micro-Fit 2x04
DSUB-25_Pins_Horizontal… -> DSUB-25
USB_Mini-B_Wuerth_…      -> USB Mini-B
KYCON_KPJX-4S-S          -> KPJX-4S
Relay_SPST_OJS_24V_10A   -> OJS relay
SW_Push_1P1T_NO_XUNPU_…  -> 3.9x3.0mm tact
ISP_SMD_100mil           -> 2x03 2.54 SMD
LED_0402_DOT             -> 0402
NetTie-2_SMD_Pad*        -> (excluded, see below)
```

Strip the library prefix (`Capacitor_SMD:`, `-Project:`, etc.). Sanity-check the
result against the sample's length/tone.

### Type / DNS

Bryan's standing decision (from an earlier JLCPCB order, being repeated for PCBWay):
**PCBWay places SMD only; THT is hand-soldered** to save cost.

- `assembly == SMD` → `SMD`
- `assembly == THT` → `thru-hole`
- DNP parts → `DNS`

Include THT rows so PCBWay sees the full picture but doesn't quote placement.

### Rows to exclude entirely

`bom/not-fitted.csv` holds 26 entries; almost none are real purchasable parts:

- `NT*` net-ties — copper links, not components
- `H1`–`H8` mounting holes — plated pads
- `C28` — a documentation symbol for a deliberate groundplane gap
- `JX1` — external connector reference only (`in_bom no`)
- `R1`, `SW1`, `SW2`, `J2B1`, `J9` — DNP / DNI, external memos
- `J1`/`J2`/`J3` — 23-way strip connectors, **cut from stock strip**, deliberately
  marked "not purchased"

Do **not** emit these as rows. They are documented in `not-fitted.csv` if needed.

### Notes column for external parts

Two lines are not element14, so PCBWay may struggle:

- `K1` — `OJS-SH-124HMF,00000`, DigiKey `41-OJS-SH-124HMF,00000-ND`. TE/OEG sealed
  relay. Not stocked by element14 or LCSC; likely **consigned**.
- `SW3` — `TS-1088-AR02016`, **LCSC C720477**. Chinese part, PCBWay can source it;
  put the LCSC code in Notes so their tooling matches it.

## Environment

Uses Bryan's **Homebrew Python 3.14** (`/usr/local/bin/python3`). Homebrew is
PEP 668 externally-managed, so a plain `pip install` is refused; the accepted route
is the escape hatch:

```sh
/usr/local/bin/python3 -m pip install --break-system-packages openpyxl
```

`openpyxl` 3.1.5 is **already installed** this way. A venv also works if you prefer
isolation, but is not required.

## Traps already hit in this session (avoid repeating)

- **`kicad-cli --sort-asc true` crashes** with `bad_any_cast` and writes nothing.
  Its default is already `true`; never pass it. `--sort-field Reference` alone is fine.
- **The GUI BOM dialog defaults to the Export tab**, which hides the "Current sheet
  only / Entire project" scope selector — leaving it on current-sheet silently
  exports only root-sheet symbols. Use `bom/export_bom.sh` or set it in the Edit tab.
- **Grouping by `Value` without `Footprint`** merges different parts onto one line
  with two MPNs. The project preset was fixed to group by `Value` + `Footprint`.
- The schematic's `Description` field is deliberately `(hide yes)`; do not "fix" that.
- `bom/apply_fields.py` must not add `(uuid …)` to schematic properties — KiCad 10
  properties have none, and one makes eeschema reject the whole file.

## Acceptance criteria

1. `bom/controller-PCBWay.xlsx` opens in Excel/Numbers without repair prompts.
2. Header row matches the sample exactly, including the `*` prefixes.
3. Rows for all 62 BOM lines (SMD + THT), no net-ties/mounting holes/DNP memos.
4. Every `*Designator`, `*Qty`, `*Mfg Part #`, `*Package/Footprint` populated.
5. Qty uses board quantity (sum = 118).
6. `Type` correctly SMD/thru-hole; `DNS` only where genuinely not fitted.
7. Logo, title and footer text preserved from the template.
8. A short summary printed: row count, SMD/THT/DNS counts, any rows with a blank
   required field.

## Questions worth settling with Bryan first

1. **Title text in D2** — the sample reads `xxxx xxxx xxxxx xxPCS BOM`. Should it say
   `Shapeoko LPT Controller 3.3 — Npcs BOM`? What quantity?
2. **Should THT rows be included at all**, or omit them so PCBWay only sees what it
   places? (Earlier decision was include-but-mark, matching the sample which contains
   `thru-hole` rows.)
3. **Consigned part handling for K1** — leave a Notes line, or omit and handle by email?
4. **Board quantity** to quote for (affects nothing in the BOM itself, but the title
   and PCBWay's quote need it).
