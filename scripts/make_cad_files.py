#!/usr/bin/env python
"""
make_cad_files.py — Generate CAD-friendly exports for case design (SolidWorks, Fusion, etc.).

KiCad's STEP export bundles every component into one flat multibody — SolidWorks
chokes on that, and there's no way to hide groups (e.g. "all switches"). So we
emit a *per-group* STEP for each logical component family. Import each STEP as
its own part in your SolidWorks Assembly; they all share the aux/drill origin,
so they mate at (0,0,0) and you can hide whichever group is in your way.

Outputs to ./cad/:
  Per-group STEP (for hide-friendly assembly in SolidWorks):
    - umiko-board.step         Bare PCB (no components)
    - umiko-switches.step      Key switches SW_1..SW_63
    - umiko-leds.step          Per-key + underglow LEDs (LED*)
    - umiko-connectors.step    USB-C receptacles (J1..J4)
    - umiko-ics.step           RP2040, flash, LDO, USB ESD, level shifters
    - umiko-passives.step      Everything else (caps, resistors, diodes, crystals,
                               BOOTSEL buttons, test points)

  Full reference (single multibody — same as before):
    - umiko-assembly.step      Everything at once
    - umiko-edge-cuts.dxf      2D board outline only — for sketch import
    - umiko-fab-front.dxf      Outline + F.Fab outlines (front-side footprint refs)
    - umiko-fab-back.dxf       Outline + B.Fab outlines (back-side footprint refs)

Notes:
  - All STEP exports use aux/drill origin so they line up with each other and
    with the gerbers.
  - DXFs are in mm.
"""

import os
import re
import subprocess
import sys

KICAD_CLI = os.environ.get(
    'KICAD_CLI',
    r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe',
)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(PROJECT_DIR, 'umiko.kicad_pcb')
CAD = os.path.join(PROJECT_DIR, 'cad')


def run(args, label):
    print(f'[{label}] running…')
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print(f'  STDERR: {r.stderr}')
        raise SystemExit(f'[{label}] FAILED (exit {r.returncode})')
    last = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ''
    print(f'  done — {last}')


def classify_halves(pcb_path):
    """Read PCB, classify each footprint as 'left' or 'right' by X position.
    Splits at the natural gap between the two halves (~5mm wide).
    Returns ([left_refs], [right_refs], midpoint_x)."""
    with open(pcb_path, encoding='utf-8') as f:
        txt = f.read()
    positions = {}
    for m in re.finditer(r'\n\t\(footprint\s', txt):
        p = m.start() + 1
        depth = 0
        i = p
        while i < len(txt):
            c = txt[i]
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    blk = txt[p:i + 1]
                    ref_m = re.search(r'\(property \"Reference\" \"([^\"]+)\"', blk)
                    head = blk[:blk.find('(property')] if '(property' in blk else blk
                    at_m = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)', head)
                    if ref_m and at_m and not ref_m.group(1).startswith('G***'):
                        positions[ref_m.group(1)] = float(at_m.group(1))
                    break
            i += 1
    xs = sorted(positions.values())
    gaps = sorted(((xs[i + 1] - xs[i], xs[i], xs[i + 1]) for i in range(len(xs) - 1)),
                  reverse=True)
    midpoint = (gaps[0][1] + gaps[0][2]) / 2
    left = sorted(r for r, x in positions.items() if x < midpoint)
    right = sorted(r for r, x in positions.items() if x >= midpoint)
    return left, right, midpoint


def step_group(label, filename, ref_filter):
    """Export a STEP file containing only the components matching ref_filter
    (KiCad --component-filter syntax: comma-separated refs, wildcards supported).

    Note: KiCad 10 rejects --no-board-body when --component-filter is set
    ("No valid PCB assembly"), so each group STEP also includes the board.
    On SolidWorks import, suppress or delete the duplicate board body in
    each group Part — keep one copy from umiko-board.step as the canonical
    board solid in the assembly."""
    run([
        KICAD_CLI, 'pcb', 'export', 'step',
        '--output', os.path.join(CAD, filename),
        '--subst-models',
        '--drill-origin',
        '--component-filter', ref_filter,
        PCB,
    ], f'step:{label}')


def main():
    if not os.path.exists(KICAD_CLI):
        sys.exit(f'kicad-cli not found at {KICAD_CLI} — set KICAD_CLI env var')

    os.makedirs(CAD, exist_ok=True)

    # 1. Full assembly STEP (board + components in 3D)
    run([
        KICAD_CLI, 'pcb', 'export', 'step',
        '--output', os.path.join(CAD, 'umiko-assembly.step'),
        '--subst-models',
        '--drill-origin',
        PCB,
    ], 'step:assembly')

    # 2. Board-only STEP (no components) — base solid for the assembly
    run([
        KICAD_CLI, 'pcb', 'export', 'step',
        '--output', os.path.join(CAD, 'umiko-board.step'),
        '--board-only',
        '--drill-origin',
        PCB,
    ], 'step:board')

    # 3. Per-group STEPs (each import is just the listed parts; mate to board
    #    in your SolidWorks Assembly. All share aux/drill origin so they
    #    snap together at (0,0,0).)
    step_group('switches',   'umiko-switches.step',   'SW_*')                # SW_1..SW_63 key switches
    step_group('leds',       'umiko-leds.step',       'LED*')                # per-key + underglow RGB LEDs
    step_group('connectors', 'umiko-connectors.step', 'J*')                  # USB-C receptacles J1..J4
    step_group('ics',        'umiko-ics.step',        'U*')                  # RP2040, flash, LDO, USB ESD, level shifter
    step_group('passives',   'umiko-passives.step',
               'C*,R*,F*,FB*,D*,Y*,SW1,SW2,TP*')                              # everything else

    # 4. Per-half STEPs — for case design where you need to move the two
    #    halves apart to draw outlines/construction lines around each.
    #    Components are classified by X position relative to the natural
    #    inter-half gap in the panel.
    left, right, midpoint = classify_halves(PCB)
    print(f'[halves] split at X={midpoint:.2f}: left={len(left)} comps, right={len(right)} comps')
    step_group('half-left',  'umiko-half-left.step',  ','.join(left))
    step_group('half-right', 'umiko-half-right.step', ','.join(right))

    # 3. DXF: Edge.Cuts only
    run([
        KICAD_CLI, 'pcb', 'export', 'dxf',
        '--output', os.path.join(CAD, 'umiko-edge-cuts.dxf'),
        '--layers', 'Edge.Cuts',
        '--output-units', 'mm',
        '--mode-single',
        '--use-drill-origin',
        PCB,
    ], 'dxf:edge-cuts')

    # 4. DXF: front-side component reference (Edge.Cuts + F.Fab)
    run([
        KICAD_CLI, 'pcb', 'export', 'dxf',
        '--output', os.path.join(CAD, 'umiko-fab-front.dxf'),
        '--layers', 'Edge.Cuts,F.Fab',
        '--output-units', 'mm',
        '--mode-single',
        '--use-drill-origin',
        '--exclude-refdes', '--exclude-value',
        PCB,
    ], 'dxf:fab-front')

    # 5. DXF: back-side component reference (Edge.Cuts + B.Fab)
    run([
        KICAD_CLI, 'pcb', 'export', 'dxf',
        '--output', os.path.join(CAD, 'umiko-fab-back.dxf'),
        '--layers', 'Edge.Cuts,B.Fab',
        '--output-units', 'mm',
        '--mode-single',
        '--use-drill-origin',
        '--exclude-refdes', '--exclude-value',
        PCB,
    ], 'dxf:fab-back')

    print()
    print('=== Done. CAD assets in cad/ ===')
    for name in sorted(os.listdir(CAD)):
        size_kb = os.path.getsize(os.path.join(CAD, name)) / 1024
        print(f'  {name:30s}  {size_kb:>8.1f} KB')


if __name__ == '__main__':
    main()
