#!/usr/bin/env bash
# Pre-fab check for umiko PCB.
#
# Deterministic gate that catches the class of bug that shipped 3 dead boards
# in the Y49 batch: refilled zones in the KiCad GUI, DRC showed clean, but
# the fill state on disk was still the pre-refill overlap. Gerber export
# then produced a shorted board.
#
# This script runs kicad-cli directly on the FILE:
#   1. Refills all zones (--refill-zones)
#   2. Saves the refilled board (--save-board)
#   3. Runs DRC at error severity (--severity-error)
#   4. Exits nonzero on any violation (--exit-code-violations)
#
# There is no GUI session, no in-memory cache, no "did I save?" question.
# What passes this check is what will actually fab.
#
# Usage:
#   scripts/prefab_check.sh                     # check main PCB
#   scripts/prefab_check.sh path/to/other.kicad_pcb
#
# Exit code:
#   0 = clean, safe to export Gerbers
#   non-0 = DRC violation, DO NOT fab

PCB="${1:-umiko.kicad_pcb}"
KICAD_CLI="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"

if [ ! -f "$PCB" ]; then
    echo "ERROR: PCB file not found: $PCB" >&2
    exit 2
fi
if [ ! -f "$KICAD_CLI" ]; then
    echo "ERROR: kicad-cli not found at: $KICAD_CLI" >&2
    exit 2
fi

REPORT="output/prefab_drc.json"
mkdir -p output

echo "==> Refilling zones + saving + running DRC on $PCB"
echo "    (this modifies the file on disk — commit before/after as needed)"

# --refill-zones: force refill of every pour with current geometry
# --save-board: persist the refill to disk (this is what closes the "did I save?" gap)
# --severity-error: report only errors, not warnings (dangling traces = warning)
# --exit-code-violations: return nonzero if any violations remain
set +e
"$KICAD_CLI" pcb drc \
    --refill-zones \
    --save-board \
    --severity-error \
    --exit-code-violations \
    --format json \
    --output "$REPORT" \
    "$PCB"
RC=$?
set -e

if [ $RC -eq 0 ]; then
    echo
    echo "==> DRC CLEAN. Safe to export Gerbers."
    echo "    Report: $REPORT"
    exit 0
else
    echo
    echo "==> DRC FAILED (exit $RC). DO NOT fab this board."
    echo "    Report: $REPORT"
    echo
    echo "    Open the report and fix every error before proceeding."
    echo "    If a violation is a false positive, add it to the project's"
    echo "    DRC exclusions in KiCad (right-click → Exclude) — never bypass."
    exit $RC
fi
