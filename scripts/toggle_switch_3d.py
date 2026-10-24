#!/usr/bin/env python
"""
toggle_switch_3d.py - Switch 3D model variant for umiko hybrid switch footprints.

Usage:
    python toggle_switch_3d.py mx                 # Show regular MX bodies (repo default)
    python toggle_switch_3d.py lowpro             # Show Gateron KS-33 low-profile bodies
    python toggle_switch_3d.py hide               # Hide both switch bodies
    python toggle_switch_3d.py show               # Same as mx (restore default)
    python toggle_switch_3d.py <verb> --pcb PATH  # Operate on a different board file

Each hybrid footprint carries two 3D models; this script flips which one is
visible by adding/removing `(hide yes)` on the per-instance model blocks.
Models that are neither switch body (e.g. sockets) are never touched.

This script edits umiko.kicad_pcb in place. A backup is created at
umiko.kicad_pcb.bak_toggle each run.

Make sure KiCad is CLOSED before running (or reload after).

Model provenance (both verified seated by kicad-cli trial renders):
  CherryMX-Switch.step    <- onigaku packages3D "CherryMX Switch.step" (space renamed)
  Gateron-KS-33_v2.step   <- onigaku packages3D (same file, hash-verified copy)
  Both use identity transform (at 0 0 0, rot 0 0 0). Note: onigaku's own
  library pairs KS-33 with offset z -4.1 + rot 180/0/180, which renders
  below the board on umiko rev2 footprints - do not "restore" that transform.
"""

import re
import sys
import shutil
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Board lives at repo root, one level above scripts/.
DEFAULT_PCB = os.path.normpath(os.path.join(SCRIPT_DIR, '..', 'umiko.kicad_pcb'))

# Rev2 hybrid libs first; rev1 libs kept so old boards still toggle sanely.
SWITCH_LIBS = (
    'umiko-hybrid-switches:',
    'Gateron_KS33_Hotswap:',
    'onigaku:Gateron-KS33-2.0-Hotswap',
)

KS33_MARK = 'KS-33_v2'   # body only; 'KS33-Socket' files do NOT match this
MX_MARK = 'CherryMX'

# verb -> {variant: hidden?}
VERBS = {
    'mx': {'mx': False, 'ks33': True},
    'show': {'mx': False, 'ks33': True},
    'lowpro': {'mx': True, 'ks33': False},
    'hide': {'mx': True, 'ks33': True},
}


def find_footprints(txt):
    out = []
    for m in re.finditer(r'\(footprint "', txt):
        p = m.start()
        depth = 0
        i = p
        while i < len(txt):
            c = txt[i]
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    out.append((p, i + 1))
                    break
            i += 1
    return out


def find_model_blocks(blk):
    """Find all (model ...) blocks within a footprint block."""
    out = []
    for m in re.finditer(r'\(model "', blk):
        p = m.start()
        depth = 0
        i = p
        while i < len(blk):
            c = blk[i]
            if c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    out.append((p, i + 1))
                    break
            i += 1
    return out


def model_variant(mblk):
    """Classify a model block as 'mx', 'ks33', or None (leave alone)."""
    first = mblk.split('\n', 1)[0]
    if KS33_MARK in first:
        return 'ks33'
    if MX_MARK in first:
        return 'mx'
    return None


def set_hidden(mblk, hide):
    """Return (new_block, changed) with hide-flag set to `hide`."""
    has = re.search(r'\(hide yes\)', mblk) is not None
    if hide and not has:
        # Insert (hide yes) right after the (model "...") opening line
        return re.sub(
            r'(\(model "[^"]+")(\s*\r?\n)',
            r'\1\2\t\t(hide yes)\n',
            mblk, count=1,
        ), True
    if not hide and has:
        return re.sub(r'\s*\(hide yes\)\s*\r?\n?', '\n', mblk, count=1), True
    return mblk, False


def main(argv):
    args = [a for a in argv if a != '--help']
    if '--help' in argv or not args or args[0] not in VERBS:
        print(__doc__)
        return 1

    verb = args[0]
    want = VERBS[verb]
    pcb = DEFAULT_PCB
    if '--pcb' in args:
        i = args.index('--pcb')
        if i + 1 >= len(args):
            print('error: --pcb needs a path')
            return 1
        pcb = args[i + 1]

    with open(pcb, 'r', encoding='utf-8', newline='') as f:
        txt = f.read()

    shutil.copyfile(pcb, pcb + '.bak_toggle')

    new_txt = txt
    count = 0

    fps = find_footprints(new_txt)
    # Process in reverse so offsets stay valid
    fps.sort(key=lambda x: x[0], reverse=True)

    for p, q in fps:
        blk = new_txt[p:q]
        libm = re.search(r'\(footprint "([^"]+)"', blk)
        if not libm:
            continue
        lib = libm.group(1)
        if not any(key in lib for key in SWITCH_LIBS):
            continue

        # Find and edit each (model ...) within this footprint
        models = find_model_blocks(blk)
        models.sort(key=lambda x: x[0], reverse=True)
        for mp, mq in models:
            mblk = blk[mp:mq]
            variant = model_variant(mblk)
            if variant is None:
                continue
            new_mblk, changed = set_hidden(mblk, want[variant])
            if changed:
                blk = blk[:mp] + new_mblk + blk[mq:]
                count += 1

        new_txt = new_txt[:p] + blk + new_txt[q:]

    depth = sum(1 for c in new_txt if c == '(') - sum(1 for c in new_txt if c == ')')
    if depth != 0:
        print(f'ABORTED: paren mismatch ({depth}). PCB unchanged.')
        return 1

    with open(pcb, 'w', encoding='utf-8', newline='') as f:
        f.write(new_txt)

    print(f'{verb}: updated {count} 3D model block(s) on switch footprints')
    print(f'Backup written to {pcb}.bak_toggle')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
