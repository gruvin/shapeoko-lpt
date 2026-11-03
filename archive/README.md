# Archive — superseded designs. Do not build from these.

## `v3.2/`

Everything here predates the current `controller.*` project and will never be
built again. It is kept for reference only.

| file | what it is |
|---|---|
| `controller-v3.2.kicad_pcb` | the v3.2 board, 100 footprints, one monolithic PCB |
| `controller-lower-cut.kicad_pcb` | the v3.2 board split into its **lower** cut, 72 footprints — carries `J3` plus J4–J23 |
| `controller-upper-cut.kicad_pcb` | the v3.2 board split into its **upper** cut, 21 footprints — carries `J2` and `J7` (DB25) |
| `schematics/` | intentionally empty; see `schematics/README.md` |

The v3.2-era **schematics were never archived** — only the boards survive. The
current `.kicad_sch` files are v3.3 and unrelated to these boards.

The two "cuts" exist only because JLCPCB needed the two halves ordered as
separate boards. They are not a per-board project structure and nothing current
depends on them. The current design is a single board (`controller.kicad_pcb`),
with lower/upper as a future decision rather than an existing split.

### If you ever open one of these

* The `.kicad_pcb` files are **self-contained** — open them standalone to look
  at copper, silkscreen, footprints. No schematic needed:

  ```sh
  kicad archive/v3.2/controller-lower-cut.kicad_pcb
  ```

* The `.kicad_pro` files are **deliberately unopenable**. Each one now points its
  root sheet at `schematics/<stem>.kicad_sch`, and every one of those files is
  absent (see `schematics/README.md`). Opening an archived project therefore
  fails with a plain *schematic file not found*, from inside this directory,
  with no route back up to the live v3.3 schematics at the repo root.

  This is stricter than it used to be, and it replaces a wrong note in an
  earlier draft of this file. The `.kicad_pro` never listed sub-sheet
  filenames — those live in the root `.kicad_sch` as sheet symbols. What the
  project stores is `schematic.top_level_sheets[0].filename`, i.e. the *root*
  sheet only:

  | project | root sheet pointer before | now |
  |---|---|---|
  | `controller-v3.2` | `controller-v3.2.kicad_sch` (never existed) | `schematics/controller-v3.2.kicad_sch` |
  | `controller-upper-cut` | none stored → KiCad infers `<stem>.kicad_sch` | `schematics/controller-upper-cut.kicad_sch` |
  | `controller-lower-cut` | none stored → same inference | `schematics/controller-lower-cut.kicad_sch` |

  The `sheets` array in the project file (five UUID/name pairs, matching the
  live hierarchy) is annotation bookkeeping — designator scope and ordering —
  not a file reference. That is why it looks like the live design: these
  projects were all saved from the same ancestry.

  Do not drop a stub `.kicad_sch` into `schematics/` to silence the error. An
  archived project that opens onto a board with no matching schematic is one
  *Update PCB from Schematic* away from destroying the archived board.

Gerbers for these versions live in `JLCPCB_V3.1_FROZEN/` and `JLCPCB_V3.2/` at
the repo root; they were deliberately left in place as the record of what was
actually ordered.
