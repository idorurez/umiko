"""Shift the new TRRS planks 1mm inward from each half's inner edge.

Before: plank inner side flush with PCB inner edge (X=173.30 left, X=174.89075 right).
After:  plank inner side 1mm inward (X=172.30 left, X=175.89075 right).
This adds:
  - A short main-board top-edge segment (1mm long) between the plank's inner bottom corner and the PCB inner edge
  - A plank inner-side vertical line (2mm long, between plank top and plank base)
And modifies the inner-edge vertical lines back to start at Y=36.09 (not Y=34.09).
"""
import re
import uuid

PCB = r'C:\Users\neuro\dev\keyboard\umiko\umiko.kicad_pcb'

with open(PCB, encoding='utf-8') as f:
    txt = f.read()

# ---- Parse all Edge.Cuts gr_line / gr_arc segments ----
segs = []
for m in re.finditer(r'\(gr_(line|arc)\b', txt):
    p = m.start(); depth=1; i=m.end()
    while i < len(txt) and depth>0:
        c = txt[i]
        if c=='(': depth+=1
        elif c==')': depth-=1
        i+=1
    blk = txt[p:i]
    if 'Edge.Cuts' not in blk:
        continue
    pts_raw = re.findall(r'\((start|end|mid) ([\d.\-]+) ([\d.\-]+)\)', blk)
    pts = {key: (float(x), float(y)) for key, x, y in pts_raw}
    segs.append({'kind': m.group(1), 'start_pos': p, 'end_pos': i, 'pts': pts})

print(f'Found {len(segs)} Edge.Cuts segments')

def approx(a, b, tol=0.001):
    return abs(a - b) < tol

def pt_eq(p1, p2):
    return approx(p1[0], p2[0]) and approx(p1[1], p2[1])

def match(pts, expected):
    """Try expected as-is; for arcs/lines also accept start/end swapped."""
    # Try forward
    if all(k in pts and pt_eq(pts[k], (x,y)) for k,x,y in expected):
        return True
    # Try start/end swapped (KiCad sometimes normalizes arc winding)
    swap_map = {'start': 'end', 'end': 'start', 'mid': 'mid'}
    swapped = [(swap_map[k], x, y) for k,x,y in expected]
    if all(k in pts and pt_eq(pts[k], (x,y)) for k,x,y in swapped):
        return True
    return False

# ---- Segments added by previous flush-plank script (to REMOVE) ----
# Left plank (5 segments)
L_OLD = [
    ('line', [('start', 149.79, 36.09), ('end', 165.80, 36.09)]),
    ('arc',  [('start', 165.80, 36.09), ('end', 166.30, 35.59)]),
    ('line', [('start', 166.30, 35.59), ('end', 166.30, 34.59)]),
    ('arc',  [('start', 166.30, 34.59), ('end', 166.80, 34.09)]),
    ('line', [('start', 166.80, 34.09), ('end', 173.30, 34.09)]),
]
# Right plank (5 segments)
R_OLD = [
    ('line', [('start', 174.89075, 34.09), ('end', 181.39075, 34.09)]),
    ('arc',  [('start', 181.39075, 34.09), ('end', 181.89075, 34.59)]),
    ('line', [('start', 181.89075, 34.59), ('end', 181.89075, 35.59)]),
    ('arc',  [('start', 181.89075, 35.59), ('end', 182.39075, 36.09)]),
    ('line', [('start', 182.39075, 36.09), ('end', 198.401, 36.09)]),
]
remove_specs = L_OLD + R_OLD

# ---- Find segments to remove ----
to_remove = []
for s in segs:
    for kind, exp in remove_specs:
        if s['kind'] == kind and match(s['pts'], exp):
            to_remove.append(s)
            break

print(f'To remove: {len(to_remove)} (expected {len(remove_specs)})')
if len(to_remove) != len(remove_specs):
    for s in segs:
        if s['kind'] in ('line','arc') and 30 < s['pts'].get('start',(99,99))[1] < 40:
            print(f'  candidate: {s["kind"]} {s["pts"]}')
    raise SystemExit('FAIL: not all removal targets found')

# ---- Apply removals (bottom-up to preserve byte offsets) ----
to_remove.sort(key=lambda s: s['start_pos'], reverse=True)
out = txt
for s in to_remove:
    bp = s['start_pos']
    while bp > 0 and out[bp-1] in '\t ':
        bp -= 1
    if bp > 0 and out[bp-1] == '\n':
        bp -= 1
    out = out[:bp] + out[s['end_pos']:]

# ---- Modify inner-edge vertical lines: change Y endpoint from 34.09 back to 36.09 ----
n1 = out.count('(start 173.3 130.19)\n\t\t(end 173.3 34.09)')
n2 = out.count('(start 174.89075 34.09)\n\t\t(end 174.89075 130.19)')
print(f'inner-edge line patterns found: L={n1} R={n2}')
out = out.replace('(start 173.3 130.19)\n\t\t(end 173.3 34.09)',
                  '(start 173.3 130.19)\n\t\t(end 173.3 36.09)', 1)
out = out.replace('(start 174.89075 34.09)\n\t\t(end 174.89075 130.19)',
                  '(start 174.89075 36.09)\n\t\t(end 174.89075 130.19)', 1)

# ---- Generate new segments (shifted 1mm inward; 7 segments per side) ----
def new_uuid():
    return str(uuid.uuid4())

def fmt_line(x1, y1, x2, y2):
    return (f'\t(gr_line\n'
            f'\t\t(start {x1} {y1})\n'
            f'\t\t(end {x2} {y2})\n'
            f'\t\t(stroke\n'
            f'\t\t\t(width 0.05)\n'
            f'\t\t\t(type default)\n'
            f'\t\t)\n'
            f'\t\t(layer "Edge.Cuts")\n'
            f'\t\t(uuid "{new_uuid()}")\n'
            f'\t)')

def fmt_arc(x1, y1, mx, my, x2, y2):
    return (f'\t(gr_arc\n'
            f'\t\t(start {x1} {y1})\n'
            f'\t\t(mid {mx} {my})\n'
            f'\t\t(end {x2} {y2})\n'
            f'\t\t(stroke\n'
            f'\t\t\t(width 0.05)\n'
            f'\t\t\t(type default)\n'
            f'\t\t)\n'
            f'\t\t(layer "Edge.Cuts")\n'
            f'\t\t(uuid "{new_uuid()}")\n'
            f'\t)')

# Constants
TOP_Y = 34.09
BASE_Y = 36.09
R = 0.5
M = 0.353553  # r * (1 - cos45) = r * (1 - 0.707) ≈ 0.146; ALSO r*sin45 = 0.354
# For arc midpoint we want 45° point ON the arc, which is r * sin45 = 0.354 from the tangent line

# --- LEFT half new plank (X shifted -1mm) ---
L_INNER = 172.30   # was 173.30
L_OUTER = 165.30   # was 166.30
PCB_L_INNER = 173.30

left = [
    # 1. Main board top edge: ends at (L_OUTER - R, BASE_Y) where bottom-outer fillet begins
    fmt_line(149.79, BASE_Y, L_OUTER - R, BASE_Y),
    # 2. Bottom-outer CONCAVE fillet at (L_OUTER, BASE_Y)
    fmt_arc(L_OUTER - R, BASE_Y,
            L_OUTER - R + M, BASE_Y - R + M,
            L_OUTER, BASE_Y - R),
    # 3. Plank outer vertical
    fmt_line(L_OUTER, BASE_Y - R, L_OUTER, TOP_Y + R),
    # 4. Top-outer CONVEX fillet at (L_OUTER, TOP_Y)
    fmt_arc(L_OUTER, TOP_Y + R,
            L_OUTER + R - M, TOP_Y + R - M,
            L_OUTER + R, TOP_Y),
    # 5. Plank top
    fmt_line(L_OUTER + R, TOP_Y, L_INNER, TOP_Y),
    # 6. Plank inner vertical (NEW — wasn't needed in flush version)
    fmt_line(L_INNER, TOP_Y, L_INNER, BASE_Y),
    # 7. Main board top edge gap-filler (1mm) between plank inner side and PCB inner edge
    fmt_line(L_INNER, BASE_Y, PCB_L_INNER, BASE_Y),
]

# --- RIGHT half new plank (X shifted +1mm) ---
R_INNER = 175.89075  # was 174.89075
R_OUTER = 182.89075  # was 181.89075
PCB_R_INNER = 174.89075

right = [
    # 1. Main board top edge gap-filler (1mm) between PCB inner edge and plank inner side
    fmt_line(PCB_R_INNER, BASE_Y, R_INNER, BASE_Y),
    # 2. Plank inner vertical (NEW)
    fmt_line(R_INNER, BASE_Y, R_INNER, TOP_Y),
    # 3. Plank top
    fmt_line(R_INNER, TOP_Y, R_OUTER - R, TOP_Y),
    # 4. Top-outer CONVEX fillet at (R_OUTER, TOP_Y)
    fmt_arc(R_OUTER - R, TOP_Y,
            R_OUTER - R + M, TOP_Y + R - M,
            R_OUTER, TOP_Y + R),
    # 5. Plank outer vertical
    fmt_line(R_OUTER, TOP_Y + R, R_OUTER, BASE_Y - R),
    # 6. Bottom-outer CONCAVE fillet at (R_OUTER, BASE_Y)
    fmt_arc(R_OUTER, BASE_Y - R,
            R_OUTER + R - M, BASE_Y - R + M,
            R_OUTER + R, BASE_Y),
    # 7. Main board top edge: from (R_OUTER + R, BASE_Y) outward
    fmt_line(R_OUTER + R, BASE_Y, 198.401, BASE_Y),
]

new_segments = left + right

# ---- Inject before final closing paren ----
inject = '\n' + '\n'.join(new_segments) + '\n'
out_stripped = out.rstrip()
if out_stripped.endswith(')'):
    out = out_stripped[:-1] + inject + ')\n'
else:
    raise SystemExit('ERROR: missing final closing paren')

with open(PCB, 'w', encoding='utf-8') as f:
    f.write(out)

print(f'\nWrote {PCB}')
print(f'Removed {len(to_remove)}, modified 2 inner-edge lines, added {len(new_segments)} new segments.')
