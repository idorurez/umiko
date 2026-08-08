"""Top-mount outline rework: move J3/J4 inter-half USB-C planks from inner edges to top edges.

- Remove J3 inner plank (4 fillets + 2 horizontals + 1 outer vertical)
- Remove J4 inner plank (same)
- Merge each inner-edge upper+lower verticals into one continuous vertical (delete the lower one)
- Shrink top-edge horizontals L2 and R1 to end before the new top planks
- Add new top planks at X=154-165 (J3) and X=186.49-197.49 (J4), protrusion 2mm upward
- Each new plank: 4 0.5mm fillets + 2 verticals + 1 outer horizontal + 1 new "after-plank" horizontal

Mirror about gap center X=175.745. Outline goes from 50 segs -> 50 segs (16 removed, 16 added).
"""
import re
import math
import uuid

PCB = r'C:\Users\neuro\dev\keyboard\umiko\umiko.kicad_pcb'

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

# Parse all Edge.Cuts segments
segs = []
for m in re.finditer(r'\(gr_(line|arc)\b', t):
    e = mp(t, m.start()); blk = t[m.start():e]
    if 'Edge.Cuts' not in blk: continue
    pts = {k: (float(x), float(y)) for k, x, y in re.findall(r'\((start|mid|end) ([\d.\-]+) ([\d.\-]+)\)', blk)}
    r = cc(pts['start'], pts['mid'], pts['end']) if m.group(1) == 'arc' else 0
    segs.append({'k': m.group(1), 's': m.start(), 'e': e, 'p': pts, 'r': r, 'remove': False, 'replace': False})

print(f'Total segs: {len(segs)}')

# Current geometry
LEFT_INNER_X = 169.190
RIGHT_INNER_X = 182.301
LEFT_PLANK_OUTER_X = 172.190
RIGHT_PLANK_OUTER_X = 179.301
TOP_Y = 35.000

# New top plank positions (mirror about gap center 175.745)
J3_LEFT_X = 154.000
J3_RIGHT_X = 165.000
J4_LEFT_X = 186.490
J4_RIGHT_X = 197.490
PLANK_OUTER_Y = 33.000  # 2mm protrusion

# Identify old inner-plank segments to remove
for seg in segs:
    sx, sy = seg['p']['start']; ex, ey = seg['p']['end']
    in_j3 = 168.5 < sx < 173 and 168.5 < ex < 173 and 38 < sy < 51 and 38 < ey < 51
    in_j4 = 179 < sx < 183 and 179 < ex < 183 and 38 < sy < 51 and 38 < ey < 51
    if in_j3 or in_j4:
        if seg['k'] == 'arc' and abs(seg['r']-0.5) < 0.1:
            seg['remove'] = True
        elif seg['k'] == 'line' and abs(sy - ey) < 0.01:
            seg['remove'] = True
        elif seg['k'] == 'line' and abs(sx - ex) < 0.01:
            target_x = LEFT_PLANK_OUTER_X if in_j3 else RIGHT_PLANK_OUTER_X
            if abs(sx - target_x) < 0.5:
                seg['remove'] = True

n_removed_plank = sum(1 for s in segs if s['remove'])
print(f'plank segs to remove: {n_removed_plank} (expect 14: 7 per inner plank x 2)')
assert n_removed_plank == 14, f'expected 14, got {n_removed_plank}'

# Find inner-edge upper/lower verticals
def find_inner_verts(x_target):
    upper = lower = None
    for i, seg in enumerate(segs):
        if seg['k'] != 'line': continue
        sx, sy = seg['p']['start']; ex, ey = seg['p']['end']
        if abs(sx - ex) < 0.01 and abs(sx - x_target) < 0.5:
            ymin, ymax = min(sy, ey), max(sy, ey)
            if ymax < 40: upper = i
            elif ymin > 50: lower = i
    return upper, lower

li_u, li_l = find_inner_verts(LEFT_INNER_X)
ri_u, ri_l = find_inner_verts(RIGHT_INNER_X)
print(f'left inner upper/lower: {li_u}/{li_l}; right inner upper/lower: {ri_u}/{ri_l}')

def merge_inner(upper_i, lower_i):
    u = segs[upper_i]; l = segs[lower_i]
    lo_ymax = max(l['p']['start'][1], l['p']['end'][1])
    if u['p']['end'][1] > u['p']['start'][1]:
        u['p']['end'] = (u['p']['end'][0], lo_ymax)
    else:
        u['p']['start'] = (u['p']['start'][0], lo_ymax)
    u['replace'] = True
    segs[lower_i]['remove'] = True

merge_inner(li_u, li_l)
merge_inner(ri_u, ri_l)

# Find L2 and R1 top-edge horizontals
L2 = R1 = None
for i, seg in enumerate(segs):
    if seg['k'] != 'line': continue
    sx, sy = seg['p']['start']; ex, ey = seg['p']['end']
    if abs(sy - ey) < 0.01 and sy < 37:
        xmin, xmax = min(sx, ex), max(sx, ex)
        if 144 < xmin < 146 and 168 < xmax < 169: L2 = i
        elif 183 < xmin < 184 and 208 < xmax < 209: R1 = i
print(f'L2: {L2}, R1: {R1}')
assert L2 is not None and R1 is not None

# Shrink L2: move whichever endpoint is at high X to (J3_LEFT_X - 0.5, TOP_Y) = (153.5, 35)
def shrink_horiz(idx, new_high_x):
    seg = segs[idx]
    sx, sy = seg['p']['start']; ex, ey = seg['p']['end']
    if sx > ex:
        seg['p']['start'] = (new_high_x, sy)
    else:
        seg['p']['end'] = (new_high_x, ey)
    seg['replace'] = True

shrink_horiz(L2, J3_LEFT_X - 0.5)
shrink_horiz(R1, J4_LEFT_X - 0.5)

# Build new segments
def fmt(v): return f'{v:.6f}'

def fillet_data(corner, dir_in, dir_out, r=0.5):
    cx = corner[0] + r * (dir_out[0] - dir_in[0])
    cy = corner[1] + r * (dir_out[1] - dir_in[1])
    t1 = (corner[0] - r * dir_in[0], corner[1] - r * dir_in[1])
    t2 = (corner[0] + r * dir_out[0], corner[1] + r * dir_out[1])
    dx = corner[0] - cx; dy = corner[1] - cy
    dist = math.hypot(dx, dy); ux, uy = dx / dist, dy / dist
    mid = (cx + r * ux, cy + r * uy)
    return t1, mid, t2

def make_line(x1, y1, x2, y2):
    return f'''\t(gr_line
\t\t(start {fmt(x1)} {fmt(y1)})
\t\t(end {fmt(x2)} {fmt(y2)})
\t\t(stroke
\t\t\t(width 0.05)
\t\t\t(type default)
\t\t)
\t\t(layer "Edge.Cuts")
\t\t(uuid "{uuid.uuid4()}")
\t)'''

def make_arc(s, m, ee):
    return f'''\t(gr_arc
\t\t(start {fmt(s[0])} {fmt(s[1])})
\t\t(mid {fmt(m[0])} {fmt(m[1])})
\t\t(end {fmt(ee[0])} {fmt(ee[1])})
\t\t(stroke
\t\t\t(width 0.05)
\t\t\t(type default)
\t\t)
\t\t(layer "Edge.Cuts")
\t\t(uuid "{uuid.uuid4()}")
\t)'''

def top_plank_segments(L, R, top_y=TOP_Y, outer_y=PLANK_OUTER_Y, after_end_x=None):
    """Generate the 7 plank segments + 1 'after-plank' horizontal."""
    out = []
    # base-left fillet (concave): corner=(L, top), dir_in=(1,0), dir_out=(0,-1)
    t1, m, t2 = fillet_data((L, top_y), (1, 0), (0, -1))
    out.append(make_arc(t1, m, t2))
    # plank left vertical: (L, top-0.5) -> (L, outer+0.5)
    out.append(make_line(L, top_y - 0.5, L, outer_y + 0.5))
    # outer-left fillet (convex): corner=(L, outer), dir_in=(0,-1), dir_out=(1,0)
    t1, m, t2 = fillet_data((L, outer_y), (0, -1), (1, 0))
    out.append(make_arc(t1, m, t2))
    # plank outer horizontal: (L+0.5, outer) -> (R-0.5, outer)
    out.append(make_line(L + 0.5, outer_y, R - 0.5, outer_y))
    # outer-right fillet (convex): corner=(R, outer), dir_in=(1,0), dir_out=(0,1)
    t1, m, t2 = fillet_data((R, outer_y), (1, 0), (0, 1))
    out.append(make_arc(t1, m, t2))
    # plank right vertical: (R, outer+0.5) -> (R, top-0.5)
    out.append(make_line(R, outer_y + 0.5, R, top_y - 0.5))
    # base-right fillet (concave): corner=(R, top), dir_in=(0,1), dir_out=(1,0)
    t1, m, t2 = fillet_data((R, top_y), (0, 1), (1, 0))
    out.append(make_arc(t1, m, t2))
    # new "after-plank" horizontal: (R+0.5, top) -> (after_end_x, top)
    if after_end_x is not None:
        out.append(make_line(R + 0.5, top_y, after_end_x, top_y))
    return out

new_segs = []
new_segs += top_plank_segments(J3_LEFT_X, J3_RIGHT_X, after_end_x=168.290)  # L2's original end
new_segs += top_plank_segments(J4_LEFT_X, J4_RIGHT_X, after_end_x=208.401)  # R1's original end
print(f'new segs to add: {len(new_segs)} (expect 16: 8 per side x 2)')
assert len(new_segs) == 16

# Apply changes: bottom-up by byte position
out_text = t
for seg in sorted(segs, key=lambda s: s['s'], reverse=True):
    if seg['remove']:
        start = seg['s']
        while start > 0 and out_text[start-1] in '\t ': start -= 1
        end = seg['e']
        if end < len(out_text) and out_text[end] == '\n': end += 1
        out_text = out_text[:start] + out_text[end:]
    elif seg['replace']:
        block = out_text[seg['s']:seg['e']]
        p = seg['p']
        block = re.sub(r'\(start ([\d.\-]+) ([\d.\-]+)\)',
                       f'(start {fmt(p["start"][0])} {fmt(p["start"][1])})', block, 1)
        if 'mid' in p:
            block = re.sub(r'\(mid ([\d.\-]+) ([\d.\-]+)\)',
                           f'(mid {fmt(p["mid"][0])} {fmt(p["mid"][1])})', block, 1)
        block = re.sub(r'\(end ([\d.\-]+) ([\d.\-]+)\)',
                       f'(end {fmt(p["end"][0])} {fmt(p["end"][1])})', block, 1)
        out_text = out_text[:seg['s']] + block + out_text[seg['e']:]

# Insert new segments just before the final `)` of the kicad_pcb file
last_paren = out_text.rfind(')')
insertion = '\n'.join(new_segs) + '\n'
out_text = out_text[:last_paren] + insertion + out_text[last_paren:]

with open(PCB, 'w', encoding='utf-8') as f:
    f.write(out_text)

# Verify loop closure
from collections import Counter
ends = Counter(); xs = []; ys = []
for m in re.finditer(r'\(gr_(line|arc)\b', out_text):
    e = mp(out_text, m.start()); blk = out_text[m.start():e]
    if 'Edge.Cuts' not in blk: continue
    pts = {k: (float(x), float(y)) for k, x, y in re.findall(r'\((start|mid|end) ([\d.\-]+) ([\d.\-]+)\)', blk)}
    for k in ('start', 'end'): ends[(round(pts[k][0], 3), round(pts[k][1], 3))] += 1
    for k in pts: xs.append(pts[k][0]); ys.append(pts[k][1])
bad = {p: c for p, c in ends.items() if c != 2}
print('loop closure OK' if not bad else f'OPEN: {dict(list(bad.items())[:8])}')
print(f'new bbox: X[{min(xs):.3f},{max(xs):.3f}] Y[{min(ys):.3f},{max(ys):.3f}]')
# count segments
n_segs = sum(1 for _ in re.finditer(r'\(gr_(line|arc)\b', out_text)
             if 'Edge.Cuts' in out_text[_.start():mp(out_text, _.start())])
print(f'total Edge.Cuts segs after rework: should be 50')
