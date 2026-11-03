# Deliberately empty

The v3.2-era schematics were **never archived**. Only the boards were kept.
This directory exists so the three archived `.kicad_pro` files have somewhere
specific to look for their root sheet:

```
schematic.top_level_sheets[0].filename = "schematics/<stem>.kicad_sch"
```

Every one of those files is absent on purpose, with two consequences, both
wanted:

1. **They cannot reach the live v3.3 schematics.** The path is relative to the
   project file, so it resolves inside `archive/v3.2/` and stops there. There is
   no route back up to the repo root, and no chance of an archived project
   re-annotating the live design.
2. **Opening one fails loudly** — `Schematic file not found:
   …/archive/v3.2/schematics/controller-v3.2.kicad_sch` — instead of quietly
   creating a blank root sheet whose only purpose would be to tempt someone into
   running *Update PCB from Schematic* against a board that has no matching
   schematic.

Do **not** place a `.kicad_sch` here to silence that error. A stub sheet would
make the archived project look openable while its PCB and schematic agreed on
nothing, which is exactly the footgun this directory exists to prevent.

To inspect an archived board, open the `.kicad_pcb` directly — those files are
self-contained:

```sh
kicad archive/v3.2/controller-lower-cut.kicad_pcb
```
