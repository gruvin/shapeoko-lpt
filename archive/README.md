# Archive — superseded designs. Do not build from these.

## `v3.2/`

Everything here predates the current `controller.*` project and will never be
built again. It is kept for reference only.

| file | what it is |
|---|---|
| `controller-v3.2.kicad_pcb` | the v3.2 board, 100 footprints, one monolithic PCB |
| `controller-lower-cut.kicad_pcb` | the v3.2 board split into its **lower** cut, 72 footprints — carries `J3` plus J4–J23 |
| `controller-upper-cut.kicad_pcb` | the v3.2 board split into its **upper** cut, 21 footprints — carries `J2` and `J7` (DB25) |

The two "cuts" exist only because JLCPCB needed the two halves ordered as
separate boards. They are not a per-board project structure and nothing current
depends on them. The current design is a single board (`controller.kicad_pcb`),
with lower/upper as a future decision rather than an existing split.

### If you ever open one of these

* The `.kicad_pcb` files are **self-contained** — open them standalone to look
  at copper, silkscreen, footprints. No schematic needed.
* The `.kicad_pro` files are **not** safely openable as-is. They were saved when
  the project's root schematic was the repo-root `controller.kicad_sch`, which
  now belongs to the v3.3 design. Opening the archived project would pull the
  live schematics in and may re-annotate them into a divergent reference set —
  the same class of damage that `bom/fix_stale_instances.py` exists to repair.
  If you must, copy the whole repo to a scratch directory first.

Gerbers for these versions live in `JLCPCB_V3.1_FROZEN/` and `JLCPCB_V3.2/` at
the repo root; they were deliberately left in place as the record of what was
actually ordered.
