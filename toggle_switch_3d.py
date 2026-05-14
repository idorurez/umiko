#!/usr/bin/env python
"""
toggle_switch_3d.py - Toggle 3D model visibility for Gateron switch footprints.

Usage:
    python toggle_switch_3d.py hide              # Hide just the KS-33 switch body
    python toggle_switch_3d.py show              # Show the KS-33 switch body
    python toggle_switch_3d.py hide all          # Hide all 3D models on switches (body + socket)
    python toggle_switch_3d.py show all          # Show all

This script edits umiko.kicad_pcb in place. A backup is created at
umiko.kicad_pcb.bak_toggle each run.

Make sure KiCad is CLOSED before running (or reload after).
"""

import re
import sys
import shutil
import os

PCB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'umiko.kicad_pcb')


def find_footprints(txt):
    out = []
    for m in re.finditer(r'\(footprint \"', txt):
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
    for m in re.finditer(r'\(model \"', blk):
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


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ('hide', 'show'):
        print(__doc__)
        sys.exit(1)

    action = sys.argv[1]  # 'hide' or 'show'
    scope = sys.argv[2] if len(sys.argv) > 2 else 'body'  # 'all' or 'body'

    if scope not in ('all', 'body'):
        print('Scope must be "all" or "body"')
        sys.exit(1)

    with open(PCB, 'r', encoding='utf-8', newline='') as f:
        txt = f.read()

    shutil.copyfile(PCB, PCB + '.bak_toggle')

    new_txt = txt
    count = 0

    fps = find_footprints(new_txt)
    # Process in reverse so offsets stay valid
    fps.sort(key=lambda x: x[0], reverse=True)

    for p, q in fps:
        blk = new_txt[p:q]
        libm = re.search(r'\(footprint \"([^\"]+)\"', blk)
        if not libm:
            continue
        lib = libm.group(1)
        if ('Gateron_KS33_Hotswap:' not in lib
                and 'onigaku:Gateron-KS33-2.0-Hotswap' not in lib):
            continue

        # Find and edit each (model ...) within this footprint
        models = find_model_blocks(blk)
        models.sort(key=lambda x: x[0], reverse=True)
        for mp, mq in models:
            mblk = blk[mp:mq]

            # If scope is 'body', only target the KS-33 switch body model
            if scope == 'body' and 'Gateron-KS-33_v2.step' not in mblk:
                continue

            new_mblk = mblk
            if action == 'hide':
                if not re.search(r'\(hide yes\)', mblk):
                    # Insert (hide yes) right after the (model "...") opening line
                    new_mblk = re.sub(
                        r'(\(model \"[^\"]+\")(\s*\r?\n)',
                        r'\1\2\t\t\t(hide yes)\n',
                        mblk, count=1,
                    )
            else:  # show
                # Remove (hide yes) if present
                new_mblk = re.sub(r'\s*\(hide yes\)\s*\r?\n?', '\n', mblk, count=1)

            if new_mblk != mblk:
                blk = blk[:mp] + new_mblk + blk[mq:]
                count += 1

        new_txt = new_txt[:p] + blk + new_txt[q:]

    depth = sum(1 for c in new_txt if c == '(') - sum(1 for c in new_txt if c == ')')
    if depth != 0:
        print(f'ABORTED: paren mismatch ({depth}). PCB unchanged.')
        sys.exit(1)

    with open(PCB, 'w', encoding='utf-8', newline='') as f:
        f.write(new_txt)

    print(f'{action.capitalize()}: updated {count} 3D model block(s) on Gateron switches (scope={scope})')
    print(f'Backup written to {PCB}.bak_toggle')


if __name__ == '__main__':
    main()
