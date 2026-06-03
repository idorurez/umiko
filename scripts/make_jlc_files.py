#!/usr/bin/env python
"""
make_jlc_files.py — Generate a JLCPCB-ready fab package from the umiko project.

Outputs to ./fab/:
  - umiko-jlc-gerbers.zip   (Gerbers + drill files, one zip for the JLC fab uploader)
  - umiko-cpl.csv           (Pick & Place / CPL file — JLC's exact column format)
  - umiko-bom-jlc.csv       (BOM — JLC's exact column format)

JLC's CSV requirements (matched from their official sample files):
  CPL columns:  Designator, Mid X, Mid Y, Layer, Rotation
                Mid X/Y values include "mm" suffix; Layer is Top/Bottom (capitalized).
  BOM columns:  Comment, Designator, Footprint, JLCPCB Part #（optional）
                Note: fullwidth Chinese parens around "optional" — copied from JLC's sample.

KiCad's default exports use different column names so direct upload fails;
this script converts them.

Usage (from the umiko project root):
  python make_jlc_files.py

Requires: KiCad 10 installed at the default Windows path, OR set KICAD_CLI env var.
"""

import csv
import os
import shutil
import subprocess
import sys
import zipfile

KICAD_CLI = os.environ.get(
    'KICAD_CLI',
    r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe',
)

# LCSC fallback for parts whose schematic symbol has no LCSC field.
# Keyed by footprint name; only applied when the BOM row has empty LCSC.
# Editing here means JLC auto-matches the part on upload and you don't
# get the "no part selected" prompt for each designator individually.
LCSC_OVERRIDES = {
    'onigaku:D3_SMD_v2': 'C81598',                   # 1N4148W matrix diode (SOD-123)
    'onigaku:YS-SK6812MINI-E': 'C5149201',           # SK6812MINI-E reverse-mount RGB
    'onigaku:YS-SK6812MINI-E_underglow': 'C5149201', # same chip, underglow orientation
}

# Components to exclude from JLC assembly (BOM + CPL). These are hand-soldered
# after the board comes back. Matched by schematic Value (groups all variants).
#   - YS-SK6812MINI-E (90 total: 63 per-key + 27 underglow)
#       Per-key are reverse-mount: body sits in a PCB cutout with lens facing
#       F.Cu — not a standard PnP placement. Underglow are standard SMD on B.Cu
#       but the OPSCO C5149201 chip layout is 180° from our footprint convention,
#       which would short +5V to GND on every LED. Hand-solder both to avoid
#       both issues.
#   - KEYSW (63 total: Gateron KS-33 hot-swap sockets)
#       Not in JLC's standard parts inventory; sourced separately from
#       Keebio/Gateron/AliExpress and hand-soldered with the switches.
DNP_VALUES = {
    'YS-SK6812MINI-E',
    'KEYSW',
}
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(PROJECT_DIR, 'umiko.kicad_pcb')
SCH = os.path.join(PROJECT_DIR, 'umiko.kicad_sch')
FAB = os.path.join(PROJECT_DIR, 'fab')


def run(args, label):
    print(f'[{label}] running…')
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  STDERR: {r.stderr}')
        raise SystemExit(f'[{label}] FAILED (exit {r.returncode})')
    last = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ''
    print(f'  done — {last}')


def main():
    if not os.path.exists(KICAD_CLI):
        sys.exit(f'kicad-cli not found at {KICAD_CLI} — set KICAD_CLI env var')

    # Clean and recreate fab/
    if os.path.exists(FAB):
        shutil.rmtree(FAB)
    os.makedirs(os.path.join(FAB, 'gerber'))
    os.makedirs(os.path.join(FAB, 'drill'))

    # All three outputs must share the same coordinate frame or JLC's preview
    # overlays placements offset from the board outline. JLC's standard KiCad
    # convention is "aux/drill origin at lower-left of the board, plot all
    # outputs relative to that origin". The aux origin is set inside the PCB
    # file (see (aux_axis_origin …)) and we apply --use-drill-file-origin /
    # --drill-origin plot to every export.

    # 1. Gerbers (aligned to aux origin)
    run([
        KICAD_CLI, 'pcb', 'export', 'gerbers',
        '--output', os.path.join(FAB, 'gerber') + os.sep,
        '--no-x2', '--no-netlist', '--subtract-soldermask',
        '--use-drill-file-origin',
        '--layers', 'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts',
        PCB,
    ], 'gerbers')

    # 2. Drill files (aligned to aux origin: --drill-origin plot)
    run([
        KICAD_CLI, 'pcb', 'export', 'drill',
        '--output', os.path.join(FAB, 'drill') + os.sep,
        '--format', 'excellon', '--excellon-units', 'mm',
        '--drill-origin', 'plot',
        '--excellon-separate-th', '--generate-map', '--map-format', 'pdf',
        PCB,
    ], 'drill')

    # 3. Pick and place (aligned to aux origin)
    raw_pos = os.path.join(FAB, '_pos-raw.csv')
    run([
        KICAD_CLI, 'pcb', 'export', 'pos',
        '--output', raw_pos,
        '--units', 'mm', '--format', 'csv',
        '--use-drill-file-origin',
        PCB,
    ], 'pos')

    # 4. BOM (raw — KiCad's headers)
    raw_bom = os.path.join(FAB, '_bom-raw.csv')
    run([
        KICAD_CLI, 'sch', 'export', 'bom',
        '--output', raw_bom,
        '--fields', 'Reference,Value,Footprint,LCSC,MPN,Manufacturer,Description,JLCPCB_CORRECTION',
        '--group-by', 'Value,Footprint,LCSC,MPN',
        SCH,
    ], 'bom')

    # 5. Convert pos → CPL in JLC format (filtered against BOM — see step 6)
    #    We build the CPL after the BOM so we can filter.
    cpl_path = os.path.join(FAB, 'umiko-cpl.csv')

    # 6. Convert BOM to JLC format (expanding ref ranges — JLC's parser
    #    doesn't understand 'C1-C42' style ranges, only comma-separated lists)
    def expand_refs(s):
        """Expand 'C1-C5,C7' -> 'C1,C2,C3,C4,C5,C7'."""
        import re as _re
        out = []
        for tok in s.split(','):
            tok = tok.strip()
            if not tok:
                continue
            m = _re.match(r'^([A-Za-z_]+)(\d+)-([A-Za-z_]+)?(\d+)$', tok)
            if m and (m.group(3) is None or m.group(1) == m.group(3)):
                prefix = m.group(1)
                a = int(m.group(2))
                b = int(m.group(4))
                if a <= b:
                    for i in range(a, b + 1):
                        out.append(f'{prefix}{i}')
                else:
                    out.append(tok)
            else:
                out.append(tok)
        return ','.join(out)

    jlc_bom = os.path.join(FAB, 'umiko-bom-jlc.csv')
    with open(raw_bom, 'r', encoding='utf-8', newline='') as f:
        bom_rows = list(csv.DictReader(f))

    # Keep BOM grouped (one row per unique part type, comma-separated
    # designators). JLC's parts-selection UI groups by part type anyway —
    # this lets a single LCSC pick apply to all matching designators.
    # Ranges (e.g. 'C1-C42') must be expanded to comma-separated lists;
    # JLC's parser handles commas but not dashes.
    bom_refs_set = set()
    dnp_count = 0
    with open(jlc_bom, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Comment', 'Designator', 'Footprint', 'JLCPCB Part #（optional）'])
        for r in bom_rows:
            if r['Value'] in DNP_VALUES:
                # Skip DNP rows entirely — they won't be in BOM, and the CPL
                # filter below will drop their refs too since they're not in
                # bom_refs_set.
                dnp_count += len(expand_refs(r['Reference']).split(','))
                continue
            expanded = expand_refs(r['Reference'])
            bom_refs_set.update(x.strip() for x in expanded.split(',') if x.strip())
            lcsc = r.get('LCSC', '') or LCSC_OVERRIDES.get(r['Footprint'], '')
            w.writerow([
                r['Value'],
                expanded,
                r['Footprint'],
                lcsc,
            ])
    print(f'[BOM] wrote {jlc_bom} ({len(bom_rows)} grouped rows; designator ranges expanded)')
    if dnp_count:
        print(f'       DNP (excluded from JLC assembly): {dnp_count} components matching {sorted(DNP_VALUES)}')

    # 7b. Now write CPL, filtering out any refs not present in the BOM.
    #    This excludes test points (exclude_from_bom), orphan footprints with
    #    no schematic counterpart, and any other CPL-only entries that would
    #    cause JLC's parser to complain about missing BOM entries.
    with open(raw_pos, 'r', encoding='utf-8', newline='') as f:
        pos_rows = list(csv.DictReader(f))
    kept, dropped = 0, []
    with open(cpl_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
        for r in pos_rows:
            ref = r['Ref']
            if ref not in bom_refs_set:
                dropped.append(ref)
                continue
            # JLC's CPL parser is strict:
            #   - Rotation must be non-negative integer (0..359). KiCad emits
            #     signed floats like '-90.000000' which JLC rejects.
            #   - Coordinates must be 4-decimal fixed precision. KiCad emits
            #     variable precision (2..6 decimals) which also rejects with
            #     "Failed processing the CPL file" — match the sample's '95.0518mm'.
            rot = int(round(float(r['Rot']))) % 360
            w.writerow([
                ref,
                f"{float(r['PosX']):.4f}mm",
                f"{float(r['PosY']):.4f}mm",
                r['Side'].capitalize(),
                rot,
            ])
            kept += 1
    print(f'[CPL] wrote {cpl_path} ({kept} rows; {len(dropped)} dropped: not in BOM)')
    if dropped:
        print(f'       dropped refs: {", ".join(dropped[:20])}{"..." if len(dropped) > 20 else ""}')

    # 7. Clean up raw KiCad-format intermediates
    os.remove(raw_pos)
    os.remove(raw_bom)

    # 8. Zip gerbers + drill
    zip_path = os.path.join(FAB, 'umiko-jlc-gerbers.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for d in (os.path.join(FAB, 'gerber'), os.path.join(FAB, 'drill')):
            for f in os.listdir(d):
                z.write(os.path.join(d, f), arcname=f)
    size_kb = os.path.getsize(zip_path) / 1024
    print(f'[ZIP] wrote {zip_path} ({size_kb:.1f} KB)')

    print()
    print('=== Done. Upload to JLC ===')
    print(f'  Gerbers:  {zip_path}')
    print(f'  CPL:      {cpl_path}')
    print(f'  BOM:      {jlc_bom}')


if __name__ == '__main__':
    main()
