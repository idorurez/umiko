"""Change the radius of the 8 main board-corner fillets from R_FROM to R_TO,
leaving the 16 USB-C plank fillets (0.5mm) untouched.

For each Edge.Cuts gr_arc whose radius ~= R_FROM:
  recover the original sharp corner C from the arc, then re-tangent the two
  adjacent gr_lines and the arc to radius R_TO (uniform convex/reentrant fillet
  construction). A line shared by two main corners gets both ends updated.
"""
import re
import math

PCB = r'C:\Users\neuro\dev\keyboard\umiko\umiko.kicad_pcb'
R_FROM = 1.25
R_TO = 0.9
RTOL = 0.05
PTOL = 0.01
K = 1 - 1/math.sqrt(2)

with open(PCB, encoding='utf-8') as f:
    txt = f.read()

def mp(s, o):
    d = 0; i = o
    while i < len(s):
        if s[i] == '(': d += 1
        elif s[i] == ')':
            d -= 1
            if d == 0: return i + 1
        i += 1

def circumcenter(a, b, c):
    ax, ay = a; bx, by = b; cx, cy = c
    d = 2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
    ux = ((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/d
    uy = ((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/d
    return (ux, uy)

# parse board-level Edge.Cuts segments
segs = []
for m in re.finditer(r'\(gr_(line|arc)\b', txt):
    e = mp(txt, m.start()); blk = txt[m.start():e]
    if 'Edge.Cuts' not in blk: continue
    pts = {k: (float(x), float(y)) for k, x, y in
           re.findall(r'\((start|mid|end) ([\d.\-]+) ([\d.\-]+)\)', blk)}
    segs.append({'kind': m.group(1), 's': m.start(), 'e': e, 'pts': pts})

def near(a, b): return abs(a[0]-b[0]) < PTOL and abs(a[1]-b[1]) < PTOL
def fmt(v): return f'{v:.6f}'

line_repl = {}          # seg_idx -> {endkey: newpoint}
arc_repl = {}           # seg_idx -> (T1n, midn, T2n)
n = 0
for ai, seg in enumerate(segs):
    if seg['kind'] != 'arc':
        continue
    T1 = seg['pts']['start']; T2 = seg['pts']['end']; M = seg['pts']['mid']
    O = circumcenter(T1, M, T2)
    rcur = math.hypot(O[0]-T1[0], O[1]-T1[1])
    if abs(rcur - R_FROM) > RTOL:
        continue
    # recover sharp corner + edge directions
    C = (T1[0]+T2[0]-O[0], T1[1]+T2[1]-O[1])
    d1 = ((O[0]-T2[0])/rcur, (O[1]-T2[1])/rcur)   # unit dir C->T1
    d2 = ((O[0]-T1[0])/rcur, (O[1]-T1[1])/rcur)   # unit dir C->T2
    T1n = (C[0]+R_TO*d1[0], C[1]+R_TO*d1[1])
    T2n = (C[0]+R_TO*d2[0], C[1]+R_TO*d2[1])
    midn = (C[0]+R_TO*K*(d1[0]+d2[0]), C[1]+R_TO*K*(d1[1]+d2[1]))
    arc_repl[ai] = (T1n, midn, T2n)
    # update the lines that ended at T1/T2
    for Told, Tnew in ((T1, T1n), (T2, T2n)):
        for li, s2 in enumerate(segs):
            if s2['kind'] != 'line': continue
            for endk in ('start', 'end'):
                if near(s2['pts'][endk], Told):
                    line_repl.setdefault(li, {})[endk] = Tnew
    n += 1
print(f'main-corner arcs to re-radius ({R_FROM}->{R_TO}): {n}')
assert n == 8, f'expected 8, got {n}'

# build new text per modified segment, apply bottom-up
out = txt
mods = []
for ai, (T1n, midn, T2n) in arc_repl.items():
    blk = txt[segs[ai]['s']:segs[ai]['e']]
    blk = re.sub(r'\(start [\d.\-]+ [\d.\-]+\)', f'(start {fmt(T1n[0])} {fmt(T1n[1])})', blk, 1)
    blk = re.sub(r'\(mid [\d.\-]+ [\d.\-]+\)', f'(mid {fmt(midn[0])} {fmt(midn[1])})', blk, 1)
    blk = re.sub(r'\(end [\d.\-]+ [\d.\-]+\)', f'(end {fmt(T2n[0])} {fmt(T2n[1])})', blk, 1)
    mods.append((segs[ai]['s'], segs[ai]['e'], blk))
for li, repl in line_repl.items():
    blk = txt[segs[li]['s']:segs[li]['e']]
    for endk, T in repl.items():
        blk = re.sub(r'\(' + endk + r' [\d.\-]+ [\d.\-]+\)', f'({endk} {fmt(T[0])} {fmt(T[1])})', blk, 1)
    mods.append((segs[li]['s'], segs[li]['e'], blk))
for s, e, blk in sorted(mods, key=lambda x: x[0], reverse=True):
    out = out[:s] + blk + out[e:]

with open(PCB, 'w', encoding='utf-8') as f:
    f.write(out)
print(f'updated {len(arc_repl)} arcs + {len(line_repl)} lines')

# verify loop closure
from collections import Counter
ends = Counter()
for m in re.finditer(r'\(gr_(line|arc)\b', out):
    e = mp(out, m.start()); blk = out[m.start():e]
    if 'Edge.Cuts' not in blk: continue
    pts = {k: (float(x), float(y)) for k, x, y in
           re.findall(r'\((start|mid|end) ([\d.\-]+) ([\d.\-]+)\)', blk)}
    for k in ('start', 'end'):
        ends[(round(pts[k][0], 3), round(pts[k][1], 3))] += 1
bad = {p: c for p, c in ends.items() if c != 2}
print('loop closure OK' if not bad else f'OPEN: {bad}')
