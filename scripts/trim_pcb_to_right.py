"""Trim umiko.kicad_pcb to only the right half.

Deletes every footprint, segment (trace), via, zone, and Edge.Cuts / other
gr_* graphic whose geometry is entirely west of X_TRIM (default 176.70 mm,
which is halfway between the max-L and min-R footprint centers).

Anything that crosses the boundary is preserved (there shouldn't be any —
we verified all Edge.Cuts entries are either entirely left or entirely
right, no L/R connections).

The resulting PCB is a right-half-only design ready for JLC fab:
- Left-half footprints, traces, vias, pours, and Edge.Cuts all gone
- Right-half geometry untouched (fillets, USB-C plank protrusions, etc.)

Nets in (net ...) declarations at the top of the file are left in place —
KiCad tolerates orphan net names.

This script is used on the `right-only-respin` branch as a one-shot.
Do not re-run on main. Do not merge the resulting PCB back to main.

Usage:
    python scripts/trim_pcb_to_right.py
"""
import os
import re
import shutil
import sys

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PCB = os.path.join(PROJECT, 'umiko.kicad_pcb')
X_TRIM = 176.70


def match_close(text, open_pos):
    d = 0
    i = open_pos
    while i < len(text):
        if text[i] == '(':
            d += 1
        elif text[i] == ')':
            d -= 1
            if d == 0:
                return i + 1
        i += 1
    return -1


def all_coords_in_left(block):
    """True iff every explicit coord in this block has X < X_TRIM.
    Returns None if the block has no coords (uninteresting)."""
    coords = re.findall(r'\((?:at|start|end|mid|center|xy) ([\d.\-]+) ([\d.\-]+)', block)
    if not coords:
        return None
    return all(float(x) < X_TRIM for x, _ in coords)


def main():
    if not os.path.exists(PCB):
        sys.exit(f'PCB not found: {PCB}')

    with open(PCB, encoding='utf-8') as f:
        pcb = f.read()

    print(f'Loaded {len(pcb):,} bytes')
    orig_len = len(pcb)

    # Find every top-level candidate block. Delete-set collects (start, end).
    delete_spans = []

    # Categories: footprint, segment, via, zone, gr_line, gr_arc, gr_rect,
    # gr_poly, gr_circle
    patterns = [
        (r'\n\t\(footprint\s', 'footprint'),
        (r'\n\t\(segment\s', 'segment'),
        (r'\n\t\(via\s', 'via'),
        (r'\n\t\(zone\s', 'zone'),
        (r'\n\t\(gr_line\s', 'gr_line'),
        (r'\n\t\(gr_arc\s', 'gr_arc'),
        (r'\n\t\(gr_rect\s', 'gr_rect'),
        (r'\n\t\(gr_poly\s', 'gr_poly'),
        (r'\n\t\(gr_circle\s', 'gr_circle'),
    ]

    counts = {k: [0, 0] for _, k in patterns}  # [total, deleted]

    for pattern, name in patterns:
        for m in re.finditer(pattern, pcb):
            block_start = m.start() + 1  # skip the leading newline
            block_end = match_close(pcb, block_start)
            block = pcb[block_start:block_end]
            counts[name][0] += 1
            in_left = all_coords_in_left(block)
            if in_left is True:
                # Include the preceding newline+tab in the delete span
                delete_spans.append((m.start(), block_end))
                counts[name][1] += 1

    # Print stats
    for name, (total, deleted) in counts.items():
        print(f'  {name:12} total={total:6}  deleting={deleted:6}')

    # Apply deletions from the end backward so offsets stay valid
    delete_spans.sort(key=lambda t: t[0], reverse=True)
    for s, e in delete_spans:
        pcb = pcb[:s] + pcb[e:]

    print(f'\nWrote {len(pcb):,} bytes (was {orig_len:,}, delta {orig_len - len(pcb):,})')

    with open(PCB, 'w', encoding='utf-8', newline='') as f:
        f.write(pcb)

    print(f'Saved {PCB}')


if __name__ == '__main__':
    main()
