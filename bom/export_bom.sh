#!/bin/sh
# Regenerate controller.csv straight from the schematic, using the same field
# set and grouping as the project's saved BOM settings.
#
# Why this exists: the KiCad GUI BOM dialog has a "Current sheet only" scope
# option that is NOT persisted anywhere - it resets between sessions - and when
# it is set, the export silently contains only the root-sheet symbols. That is
# easy to miss because the preview can still show every part.
#
# Note: do NOT pass --sort-asc here. Despite its default being true, passing it
# explicitly makes the exporter throw bad_any_cast and write nothing (KiCad
# 10.0.7). Omitting it gives ascending order anyway.
set -e
cd "$(dirname "$0")/.."
KICAD_CLI="${KICAD_CLI:-/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli}"

ATTEMPTS=1
MIN_ROWS=20
while [ "$ATTEMPTS" -le 4 ]; do
    rm -f controller.csv
    "$KICAD_CLI" sch export bom controller.kicad_sch \
        --fields "Reference,Value,Footprint,QUANTITY,DNP,E14MFR#,E14MOQ,E14PART,Marking,Description" \
        --labels "Reference,Value,Footprint,Qty,DNP,E14MFR#,E14MOQ,E14PART,Marking,Description" \
        --group-by "Value,Footprint" \
        --sort-field "Reference" \
        -o controller.csv 2>/dev/null || true

    if [ -f controller.csv ]; then
        rows=$(( $(wc -l < controller.csv) - 1 ))
    else
        rows=0
    fi
    if [ "$rows" -ge "$MIN_ROWS" ]; then
        echo "controller.csv: $rows lines"
        exit 0
    fi
    echo "attempt $ATTEMPTS produced $rows lines - retrying" >&2
    ATTEMPTS=$((ATTEMPTS + 1))
done
echo "FAILED: exporter never produced a usable BOM" >&2
exit 1
