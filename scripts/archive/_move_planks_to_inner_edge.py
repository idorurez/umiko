"""Replace the old inner USB-C planks (P2/P3) with small 2mm TRRS planks flush to each half's inner edge.

Left half inner edge at X=173.30; right half inner edge at X=174.89075.
New planks are 7mm wide, 2mm tall, 0.5mm fillet on outer corners only, flush on inner side.
"""
import re
import uuid

PCB = r'C:\Users\neuro\dev\keyboard\umiko\umiko.kicad_pcb'

with open(PCB, encoding='utf-8') as f:
    txt = f.read()

# ---- 1. Parse all Edge.Cuts gr_line / gr_arc segments with their byte spans ----
segs = []  # list of dicts: {kind, start_pos, end_pos, pts}
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

# ---- 2. Identify segments to REMOVE by coord match ----
def approx(a, b, tol=0.01):
    return abs(a - b) < tol

def match(pts, expected):
    """expected = list of (key, x, y) tuples that must all match within tol"""
    for key, x, y in expected:
        if key not in pts: return False
        if not approx(pts[key][0], x): return False
        if not approx(pts[key][1], y): return False
    return True

# P2 (left old plank) — 7 segments
P2_specs = [
    ('line', [('start', 151.04, 30.32), ('end', 151.04, 34.84)]),
    ('arc',  [('start', 151.04, 30.32), ('end', 152.29, 29.07)]),
    ('arc',  [('start', 151.04, 34.84), ('end', 149.79, 36.09)]),
    ('line', [('start', 162.05, 29.07), ('end', 152.29, 29.07)]),
    ('arc',  [('start', 162.05, 29.07), ('end', 163.3, 30.32)]),
    ('line', [('start', 163.3, 34.84), ('end', 163.3, 30.32)]),
    ('arc',  [('start', 164.55, 36.09), ('end', 163.3, 34.84)]),
]
# P3 (right old plank)
P3_specs = [
    ('line', [('start', 184.891, 30.32), ('end', 184.891, 34.84)]),
    ('arc',  [('start', 184.891, 30.32), ('end', 186.141, 29.07)]),
    ('arc',  [('start', 184.891, 34.84), ('end', 183.641, 36.09)]),
    ('line', [('start', 195.901, 29.07), ('end', 186.141, 29.07)]),
    ('arc',  [('start', 195.901, 29.07), ('end', 197.151, 30.32)]),
    ('line', [('start', 197.151, 34.84), ('end', 197.151, 30.32)]),
    ('arc',  [('start', 198.401, 36.09), ('end', 197.151, 34.84)]),
]
# Inner edge top fillets (will be replaced by extending inner edge straight up to plank top)
FILLET_SPECS = [
    ('arc',  [('start', 172.05, 36.09), ('end', 173.3, 37.34)]),    # left
    ('arc',  [('start', 174.89075, 37.34), ('end', 176.14075, 36.09)]),  # right
]
# Stale main board top edges between plank base and inner edge fillet (now orphaned)
STALE_SPECS = [
    ('line', [('start', 172.05, 36.09), ('end', 164.55, 36.09)]),   # left
    ('line', [('start', 183.641, 36.09), ('end', 176.14075, 36.09)]),  # right
]
# Inner edge VERTICAL lines (to be modified — endpoints change)
INNER_VERT_SPECS = [
    ('line', [('start', 173.3, 130.19), ('end', 173.3, 37.34)]),    # left half inner edge
    ('line', [('start', 174.89075, 37.34), ('end', 174.89075, 130.19)]),  # right half inner edge
]

remove_specs = P2_specs + P3_specs + FILLET_SPECS + STALE_SPECS
modify_specs = INNER_VERT_SPECS

to_remove = []
to_modify = []
for s in segs:
    for kind, exp in remove_specs:
        if s['kind'] == kind and match(s['pts'], exp):
            to_remove.append(s)
            break
    else:
        for kind, exp in modify_specs:
            if s['kind'] == kind and match(s['pts'], exp):
                to_modify.append(s)
                break

print(f'To remove: {len(to_remove)} (expected {len(remove_specs)})')
print(f'To modify: {len(to_modify)} (expected {len(modify_specs)})')
for s in to_remove:
    print(f'  REMOVE {s["kind"]} {s["pts"]}')
for s in to_modify:
    print(f'  MODIFY {s["kind"]} {s["pts"]}')

if len(to_remove) != len(remove_specs):
    print('ERROR: not all segments to remove were matched. Aborting.')
    raise SystemExit(1)
if len(to_modify) != len(modify_specs):
    print('ERROR: not all segments to modify were matched. Aborting.')
    raise SystemExit(1)

# ---- 3. Generate replacement segments ----
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

# --- LEFT HALF new plank (flush to inner edge X=173.30) ---
# Plank: X=166.30 (outer) to X=173.30 (inner, flush). Y=34.09 (top) to Y=36.09 (base).
# Fillets: 0.5mm on outer-top and outer-bottom corners. Inner-top corner: 90deg sharp.
L_OUTER_X = 166.30
L_INNER_X = 173.30
PLANK_TOP_Y = 34.09
PLANK_BASE_Y = 36.09
R = 0.5  # fillet radius
MID_OFFSET = R * (1 - 0.7071068)  # for 90° arc, mid is r*(1-cos45) from each tangent

# Concave fillet at (166.30, 36.09) — board outline turns from horizontal main board edge UP onto plank
# Tangent on horizontal at (166.30 - 0.5, 36.09); tangent on vertical at (166.30, 36.09 - 0.5)
# Mid: (166.30 - 0.354 ? ... ) — for concave, center is OUTSIDE board at (165.80, 35.59)
# Mid from center direction toward midway between tangents
left_plank_segs = [
    # New main board top edge (149.79, 36.09) -> (165.80, 36.09)
    # — fills gap from old P2 BL fillet end to new plank outer fillet start
    fmt_line(149.79, 36.09, L_OUTER_X - R, PLANK_BASE_Y),
    # Bottom-outer CONCAVE fillet: arc from (165.80, 36.09) -> mid -> (166.30, 35.59)
    fmt_arc(L_OUTER_X - R, PLANK_BASE_Y,
            L_OUTER_X - R + 0.353553, PLANK_BASE_Y - R + 0.353553,
            L_OUTER_X, PLANK_BASE_Y - R),
    # Outer vertical: (166.30, 35.59) -> (166.30, 34.59)
    fmt_line(L_OUTER_X, PLANK_BASE_Y - R, L_OUTER_X, PLANK_TOP_Y + R),
    # Top-outer CONVEX fillet: arc from (166.30, 34.59) -> mid -> (166.80, 34.09)
    fmt_arc(L_OUTER_X, PLANK_TOP_Y + R,
            L_OUTER_X + R - 0.353553, PLANK_TOP_Y + R - 0.353553,
            L_OUTER_X + R, PLANK_TOP_Y),
    # Plank top: (166.80, 34.09) -> (173.30, 34.09)
    fmt_line(L_OUTER_X + R, PLANK_TOP_Y, L_INNER_X, PLANK_TOP_Y),
]

# --- RIGHT HALF new plank (flush to inner edge X=174.89075) ---
R_INNER_X = 174.89075
R_OUTER_X = R_INNER_X + 7.0  # 181.89075
right_plank_segs = [
    # Plank top: (174.89075, 34.09) -> (181.39075, 34.09)
    fmt_line(R_INNER_X, PLANK_TOP_Y, R_OUTER_X - R, PLANK_TOP_Y),
    # Top-outer CONVEX fillet at (181.89075, 34.09)
    # Tangent points: (181.39075, 34.09) on top; (181.89075, 34.59) on outer vertical
    # Center inside board (lower-LEFT of corner): (181.39075, 34.59)
    fmt_arc(R_OUTER_X - R, PLANK_TOP_Y,
            R_OUTER_X - R + 0.353553, PLANK_TOP_Y + R - 0.353553,
            R_OUTER_X, PLANK_TOP_Y + R),
    # Outer vertical (going down): (181.89075, 34.59) -> (181.89075, 35.59)
    fmt_line(R_OUTER_X, PLANK_TOP_Y + R, R_OUTER_X, PLANK_BASE_Y - R),
    # Bottom-outer CONCAVE fillet at (181.89075, 36.09)
    # Tangent: (181.89075, 35.59), (182.39075, 36.09); center outside at (182.39075, 35.59)
    fmt_arc(R_OUTER_X, PLANK_BASE_Y - R,
            R_OUTER_X + R - 0.353553, PLANK_BASE_Y - R + 0.353553,
            R_OUTER_X + R, PLANK_BASE_Y),
    # New main board top edge (182.39075, 36.09) -> (198.401, 36.09)
    fmt_line(R_OUTER_X + R, PLANK_BASE_Y, 198.401, PLANK_BASE_Y),
]

new_segments = left_plank_segs + right_plank_segs

# ---- 4. Apply changes: remove + modify + add (work from bottom of file upward to preserve offsets) ----
# Removals
to_remove.sort(key=lambda s: s['start_pos'], reverse=True)
out = txt
for s in to_remove:
    # Find the leading \n\t (or whitespace) before start_pos so we also strip surrounding indent
    p = s['start_pos']
    # Walk back to include preceding tab(s) and newline
    bp = p
    while bp > 0 and out[bp-1] in '\t ':
        bp -= 1
    if bp > 0 and out[bp-1] == '\n':
        bp -= 1
    out = out[:bp] + out[s['end_pos']:]

# Modify: shorten inner edge vertical lines to extend up to plank top Y=34.09
# Left: was (173.3, 130.19) -> (173.3, 37.34); modify endpoint (173.3, 37.34) -> (173.3, 34.09)
out = out.replace('(start 173.3 130.19)\n\t\t(end 173.3 37.34)',
                  '(start 173.3 130.19)\n\t\t(end 173.3 34.09)', 1)
# Right: was (174.89075, 37.34) -> (174.89075, 130.19); modify start to (174.89075, 34.09)
out = out.replace('(start 174.89075 37.34)\n\t\t(end 174.89075 130.19)',
                  '(start 174.89075 34.09)\n\t\t(end 174.89075 130.19)', 1)

# Add new segments: inject right before the closing ) of the kicad_pcb file
# Find a good injection point — just before the final closing paren of the file
# Easier: append before the last ')\n' at end of file
inject = '\n' + '\n'.join(new_segments) + '\n'
# Strip trailing whitespace/newlines from out
out_stripped = out.rstrip()
if out_stripped.endswith(')'):
    out = out_stripped[:-1] + inject + ')\n'
else:
    print('ERROR: could not find final closing paren')
    raise SystemExit(1)

with open(PCB, 'w', encoding='utf-8') as f:
    f.write(out)

print(f'\nWrote {PCB}')
print(f'Removed {len(to_remove)} segments, modified 2 inner-edge lines, added {len(new_segments)} new segments.')
