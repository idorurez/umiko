"""First-round case-buffer expansion of the board Edge.Cuts outline.

Per-edge outward offset (board grows; components stay put):
  top    +0.09   (move top edge up:   Y -= 0.09)
  bottom +1.398  (move bottom edge down: Y += 1.398)
  outer  +1.25   (left half: X -= 1.25 ; right half: X += 1.25)
  inner  +1.20   (toward the gap: left half X += 1.20 ; right half X -= 1.20)

USB-C planks ride rigidly with their edge (outer planks J1/J2, inner planks J3/J4).
Corner fillets (0.9 mm) shift by the COMBINATION of their two sides and the two
adjacent edges are reconnected to the shifted fillet tangents. Plank fillets
(0.5 mm) ride with their plank. All geometry is axis-aligned.
"""
import re
import math

PCB = r'C:\Users\neuro\dev\keyboard\umiko\umiko.kicad_pcb'
TOP, BOTTOM, OUTER, INNER = -0.09, 1.398, 1.25, 1.20

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

# parse board-level Edge.Cuts segments
segs = []
for m in re.finditer(r'\(gr_(line|arc)\b', t):
    e = mp(t, m.start()); blk = t[m.start():e]
    if 'Edge.Cuts' not in blk:
        continue
    pts = {k: (float(x), float(y)) for k, x, y in
           re.findall(r'\((start|mid|end) ([\d.\-]+) ([\d.\-]+)\)', blk)}
    r = cc(pts['start'], pts['mid'], pts['end']) if m.group(1) == 'arc' else 0.0
    segs.append({'kind': m.group(1), 's': m.start(), 'e': e, 'pts': pts, 'r': r})

def xband(x):
    if x < 50:  return (-OUTER, 0.0)   # outer-left
    if x < 179: return (+INNER, 0.0)   # inner-left
    if x < 215: return (-INNER, 0.0)   # inner-right
    return (+OUTER, 0.0)               # outer-right

def vec(seg):
    """Return (translation_vector, is_main_fillet)."""
    s, e = seg['pts']['start'], seg['pts']['end']
    mx, my = (s[0]+e[0])/2, (s[1]+e[1])/2
    if seg['kind'] == 'arc' and abs(seg['r']-0.9) < 0.1:           # main corner fillet
        xb = xband(mx)[0]
        yb = TOP if my < 50 else BOTTOM
        return (xb, yb), True
    if seg['kind'] == 'line' and abs(s[1]-e[1]) < 0.01:           # horizontal
        if my < 37:  return (0.0, TOP), False
        if my > 130: return (0.0, BOTTOM), False
        return xband(mx), False                                   # plank horizontal
    return xband(mx), False                                       # vertical line / plank fillet

def key(p): return (round(p[0], 3), round(p[1], 3))

# endpoint -> [(seg_idx, 'start'/'end')]
from collections import defaultdict
inc = defaultdict(list)
for i, seg in enumerate(segs):
    inc[key(seg['pts']['start'])].append((i, 'start'))
inc_e = defaultdict(list)
for i, seg in enumerate(segs):
    for k in ('start', 'end'):
        inc_e[key(seg['pts'][k])].append((i, k))

vectors = [vec(s) for s in segs]

# overrides: (seg_idx, key) -> new coord, from main fillets
overrides = {}
n_main = 0
for i, seg in enumerate(segs):
    v, ismain = vectors[i]
    if not ismain:
        continue
    n_main += 1
    for endk in ('start', 'end'):
        oc = seg['pts'][endk]
        nc = (oc[0]+v[0], oc[1]+v[1])               # fillet's translated tangent
        for (j, jk) in inc_e[key(oc)]:
            if j == i:
                continue
            overrides[(j, jk)] = nc                 # reconnect adjacent edge to it
print(f'main corner fillets: {n_main} (expect 8)')

def fmt(x): return f'{x:.6f}'

# rewrite each segment's coords (bottom-up by byte position)
out = t
for i in sorted(range(len(segs)), key=lambda k: segs[k]['s'], reverse=True):
    seg = segs[i]; v = vectors[i][0]
    blk = t[seg['s']:seg['e']]
    for k in ('start', 'mid', 'end'):
        if k not in seg['pts']:
            continue
        oc = seg['pts'][k]
        if (i, k) in overrides:
            nc = overrides[(i, k)]
        else:
            nc = (oc[0]+v[0], oc[1]+v[1])
        blk = re.sub(r'\(' + k + r' [\d.\-]+ [\d.\-]+\)',
                     f'({k} {fmt(nc[0])} {fmt(nc[1])})', blk, 1)
    out = out[:seg['s']] + blk + out[seg['e']:]

with open(PCB, 'w', encoding='utf-8') as f:
    f.write(out)

# verify loop closure + report new bbox
segs2 = []
for m in re.finditer(r'\(gr_(line|arc)\b', out):
    e = mp(out, m.start()); blk = out[m.start():e]
    if 'Edge.Cuts' not in blk: continue
    pts = {k: (float(x), float(y)) for k, x, y in
           re.findall(r'\((start|mid|end) ([\d.\-]+) ([\d.\-]+)\)', blk)}
    segs2.append(pts)
from collections import Counter
ends = Counter()
xs = []; ys = []
for pts in segs2:
    for k in ('start', 'end'):
        ends[(round(pts[k][0], 3), round(pts[k][1], 3))] += 1
    for k in pts:
        xs.append(pts[k][0]); ys.append(pts[k][1])
bad = {p: c for p, c in ends.items() if c != 2}
print('loop closure OK' if not bad else f'OPEN ENDPOINTS: {dict(list(bad.items())[:8])}')
print(f'new outline bbox: X[{min(xs):.2f},{max(xs):.2f}] Y[{min(ys):.2f},{max(ys):.2f}]')
