"""Fillet the unfilleted board-outline corners around the USB-C planks and the two
top-inner main corners.

Targets (board-level Edge.Cuts gr_line junctions), radius:
  Main top-inner corners (convex):           1.25 mm
  USB-C plank base corners (reentrant):      0.50 mm
All are 90deg line-line junctions. For each, shorten the two lines to their
tangent points and insert a tangent gr_arc (uniform construction works for both
convex and reentrant corners).
"""
import re
import math
import uuid

PCB = r'C:\Users\neuro\dev\keyboard\umiko\umiko.kicad_pcb'
TOL = 0.02

targets = [
    # (x, y, radius)
    (173.30,   36.09, 1.25),   # left half top-inner main corner
    (184.89075, 36.09, 1.25),  # right half top-inner main corner
    (35.18,    54.24, 0.5),    # J1 left side plank base
    (35.18,    65.18, 0.5),
    (346.89,   54.24, 0.5),    # J2 right side plank base
    (346.89,   65.18, 0.5),
    (173.30,   39.45, 0.5),    # J3 inter-half left plank base
    (173.30,   50.39, 0.5),
    (184.89075, 39.45, 0.5),   # J4 inter-half right plank base
    (184.89075, 50.39, 0.5),
]

with open(PCB, encoding='utf-8') as f:
    txt = f.read()

def match_paren(s, o):
    d = 0; i = o
    while i < len(s):
        if s[i] == '(': d += 1
        elif s[i] == ')':
            d -= 1
            if d == 0: return i + 1
        i += 1
    raise ValueError

# parse board-level gr_line/gr_arc on Edge.Cuts
segs = []
for m in re.finditer(r'\(gr_(line|arc)\b', txt):
    e = match_paren(txt, m.start()); blk = txt[m.start():e]
    if 'Edge.Cuts' not in blk:
        continue
    pts = {k: (float(x), float(y)) for k, x, y in
           re.findall(r'\((start|mid|end) ([\d.\-]+) ([\d.\-]+)\)', blk)}
    wm = re.search(r'\(width ([\d.]+)\)', blk)
    segs.append({'kind': m.group(1), 's': m.start(), 'e': e, 'pts': pts,
                 'width': wm.group(1) if wm else '0.05'})

def near(a, b): return abs(a[0]-b[0]) < TOL and abs(a[1]-b[1]) < TOL

# accumulate per-segment endpoint replacements + collect new arcs
repl = {i: {} for i in range(len(segs))}
new_arcs = []
K = 1 - 1/math.sqrt(2)

for cx, cy, r in targets:
    C = (cx, cy)
    touch = []
    for i, seg in enumerate(segs):
        if seg['kind'] != 'line':
            continue
        for end in ('start', 'end'):
            if near(seg['pts'][end], C):
                touch.append((i, end))
    if len(touch) != 2:
        raise SystemExit(f'corner {C}: found {len(touch)} lines (expected 2)')
    Cref = segs[touch[0][0]]['pts'][touch[0][1]]
    ds = []
    Ts = []
    for i, end in touch:
        other = segs[i]['pts']['end' if end == 'start' else 'start']
        dx, dy = other[0]-Cref[0], other[1]-Cref[1]
        L = math.hypot(dx, dy); d = (dx/L, dy/L)
        T = (Cref[0]+r*d[0], Cref[1]+r*d[1])
        ds.append(d); Ts.append(T)
        repl[i][end] = T
    d1, d2 = ds
    mid = (Cref[0] + K*r*(d1[0]+d2[0]), Cref[1] + K*r*(d1[1]+d2[1]))
    width = segs[touch[0][0]]['width']
    new_arcs.append((Ts[0], mid, Ts[1], width))

def fmt(v): return f'{v:.6f}'

# apply endpoint replacements bottom-up so byte offsets stay valid
out = txt
for i in sorted(repl, reverse=True):
    if not repl[i]:
        continue
    seg = segs[i]
    blk = out[seg['s']:seg['e']]
    for end, T in repl[i].items():
        blk = re.sub(r'\(' + end + r' [\d.\-]+ [\d.\-]+\)',
                     f'({end} {fmt(T[0])} {fmt(T[1])})', blk, count=1)
    out = out[:seg['s']] + blk + out[seg['e']:]

# append new fillet arcs before the final closing paren
def arc_block(T1, mid, T2, width):
    return (f'\t(gr_arc\n\t\t(start {fmt(T1[0])} {fmt(T1[1])})\n'
            f'\t\t(mid {fmt(mid[0])} {fmt(mid[1])})\n'
            f'\t\t(end {fmt(T2[0])} {fmt(T2[1])})\n'
            f'\t\t(stroke\n\t\t\t(width {width})\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(layer "Edge.Cuts")\n\t\t(uuid "{uuid.uuid4()}")\n\t)')
inject = '\n' + '\n'.join(arc_block(*a) for a in new_arcs) + '\n'
out_stripped = out.rstrip()
assert out_stripped.endswith(')')
out = out_stripped[:-1] + inject + ')\n'

with open(PCB, 'w', encoding='utf-8') as f:
    f.write(out)
print(f'Filleted {len(targets)} corners; added {len(new_arcs)} arcs.')

# ---- verify loop closure: every board-level Edge.Cuts endpoint used exactly twice ----
from collections import Counter
segs2 = []
for m in re.finditer(r'\(gr_(line|arc)\b', out):
    e = match_paren(out, m.start()); blk = out[m.start():e]
    if 'Edge.Cuts' not in blk: continue
    pts = {k: (float(x), float(y)) for k, x, y in
           re.findall(r'\((start|mid|end) ([\d.\-]+) ([\d.\-]+)\)', blk)}
    segs2.append(pts)
endpoints = Counter()
for pts in segs2:
    for k in ('start', 'end'):
        endpoints[(round(pts[k][0], 3), round(pts[k][1], 3))] += 1
bad = {p: c for p, c in endpoints.items() if c != 2}
print(f'board Edge.Cuts segments now: {len(segs2)}')
print('loop closure OK' if not bad else f'OPEN ENDPOINTS: {bad}')
