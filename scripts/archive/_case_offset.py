"""Per-edge case-buffer offset of the board Edge.Cuts outline (asymmetric L/R).

Translation vectors applied per edge (board grows/retracts; components stay put).
USB-C planks ride rigidly with their edge; 0.9mm corner fillets shift by the
combination of their two sides and are reconnected; 0.5mm plank fillets ride
with their plank. All geometry is axis-aligned.

Round-3 deltas:
  LEFT  : top unchanged ; bottom down 0.06 ; outer(left) out 0.12 ; inner retract 0.01
  RIGHT : top unchanged ; bottom unchanged ; inner toward-gap 0.12 ; outer unchanged
"""
import re
import math

PCB = r'C:\Users\neuro\dev\keyboard\umiko\umiko.kicad_pcb'
SPLIT = 177.0  # x boundary between left and right halves (gap center ~176.6)

with open(PCB, encoding='utf-8') as f:
    t = f.read()

def mp(s, o):
    d = 0; i = o
    while i < len(s):
        if s[i] == '(': d += 1
        elif s[i] == ')':
            d -= 1
            if d == 0: return i + 1
        i += 1

def cc(a, b, c):
    ax, ay = a; bx, by = b; cx, cy = c
    d = 2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
    if abs(d) < 1e-9: return 0
    ux = ((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/d
    uy = ((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/d
    return math.hypot(ax-ux, ay-uy)

segs = []
for m in re.finditer(r'\(gr_(line|arc)\b', t):
    e = mp(t, m.start()); blk = t[m.start():e]
    if 'Edge.Cuts' not in blk:
        continue
    pts = {k: (float(x), float(y)) for k, x, y in
           re.findall(r'\((start|mid|end) ([\d.\-]+) ([\d.\-]+)\)', blk)}
    r = cc(pts['start'], pts['mid'], pts['end']) if m.group(1) == 'arc' else 0.0
    segs.append({'kind': m.group(1), 's': m.start(), 'e': e, 'pts': pts, 'r': r})

def xdelta(x):
    if x < 50:   return -0.12   # left outer  -> out (left)
    if x < SPLIT: return -0.01  # left inner  -> retract (left, away from gap)
    if x < 215:  return -0.12   # right inner -> toward gap (left)
    return 0.0                  # right outer -> unchanged

def ybottom(x):
    return 0.06 if x < SPLIT else 0.0    # left bottom +0.06 (down); right bottom unchanged

YTOP = 0.0    # both tops unchanged this round

def vec(seg):
    s, e = seg['pts']['start'], seg['pts']['end']
    mx, my = (s[0]+e[0])/2, (s[1]+e[1])/2
    if seg['kind'] == 'arc' and abs(seg['r']-0.9) < 0.1:          # main corner fillet
        yb = YTOP if my < 50 else ybottom(mx)
        return (xdelta(mx), yb), True
    if seg['kind'] == 'line' and abs(s[1]-e[1]) < 0.01:          # horizontal
        if my < 37:  return (0.0, YTOP), False
        if my > 130: return (0.0, ybottom(mx)), False
        return (xdelta(mx), 0.0), False                          # plank horizontal
    return (xdelta(mx), 0.0), False                              # vertical / plank fillet

def key(p): return (round(p[0], 3), round(p[1], 3))
from collections import defaultdict
inc_e = defaultdict(list)
for i, seg in enumerate(segs):
    for k in ('start', 'end'):
        inc_e[key(seg['pts'][k])].append((i, k))

vectors = [vec(s) for s in segs]

overrides = {}
n_main = 0
for i, seg in enumerate(segs):
    v, ismain = vectors[i]
    if not ismain:
        continue
    n_main += 1
    for endk in ('start', 'end'):
        oc = seg['pts'][endk]
        nc = (oc[0]+v[0], oc[1]+v[1])
        for (j, jk) in inc_e[key(oc)]:
            if j != i:
                overrides[(j, jk)] = nc
print(f'main corner fillets: {n_main} (expect 8)')

def fmt(x): return f'{x:.6f}'
out = t
for i in sorted(range(len(segs)), key=lambda k: segs[k]['s'], reverse=True):
    seg = segs[i]; v = vectors[i][0]
    blk = t[seg['s']:seg['e']]
    for k in ('start', 'mid', 'end'):
        if k not in seg['pts']:
            continue
        oc = seg['pts'][k]
        nc = overrides.get((i, k), (oc[0]+v[0], oc[1]+v[1]))
        blk = re.sub(r'\(' + k + r' [\d.\-]+ [\d.\-]+\)',
                     f'({k} {fmt(nc[0])} {fmt(nc[1])})', blk, 1)
    out = out[:seg['s']] + blk + out[seg['e']:]

with open(PCB, 'w', encoding='utf-8') as f:
    f.write(out)

# verify
from collections import Counter
ends = Counter(); xs = []; ys = []
for m in re.finditer(r'\(gr_(line|arc)\b', out):
    e = mp(out, m.start()); blk = out[m.start():e]
    if 'Edge.Cuts' not in blk: continue
    pts = {k: (float(x), float(y)) for k, x, y in
           re.findall(r'\((start|mid|end) ([\d.\-]+) ([\d.\-]+)\)', blk)}
    for k in ('start', 'end'): ends[(round(pts[k][0],3), round(pts[k][1],3))] += 1
    for k in pts: xs.append(pts[k][0]); ys.append(pts[k][1])
bad = {p: c for p, c in ends.items() if c != 2}
print('loop closure OK' if not bad else f'OPEN: {dict(list(bad.items())[:6])}')
print(f'new bbox: X[{min(xs):.2f},{max(xs):.2f}] Y[{min(ys):.2f},{max(ys):.2f}]')
