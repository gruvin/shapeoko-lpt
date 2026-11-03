#!/bin/sh
# Rebuild the controller BOM from the schematic. Safe to re-run: the element14
# responses are cached, so repeat runs cost no API quota.
set -e
cd "$(dirname "$0")"
python3 specs.py
python3 extract.py
python3 build.py
python3 resolve.py
python3 audit_packaging.py
python3 summarize.py
