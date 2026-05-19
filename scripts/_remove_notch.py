"""Remove the 1mm notch between plank inner side and PCB inner edge.

Strategy: keep the outer plank edges (X=165.30 left, X=182.89075 right) but extend
the inner side of each plank BACK to the PCB inner edge. Plank becomes 8mm wide.
The plank top line lengthens to span the full plank width; the plank inner vertical
and the 1mm gap-filler are deleted; the PCB inner edge line extends back up to the
plank top Y=34.09.
"""
import re

PCB = r'C:\Users\neuro\dev\keyboard\umiko\umiko.kicad_pcb'
with open(PCB, encoding='utf-8') as f:
    txt = f.read()

# Parse all Edge.Cuts segments
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
    segs.append({'kind': m.group(1), 'start_pos': p, 'end_pos': i, 'pts': pts, 'blk': blk})

def approx(a, b, tol=0.001):
    return abs(a - b) < tol

def pt_eq(p, x, y):
    return approx(p[0], x) and approx(p[1], y)

def line_endpoints_match(pts, x1, y1, x2, y2):
    """Match either start->end or end->start direction."""
    s, e = pts.get('start'), pts.get('end')
    if s is None or e is None: return False
    return ((pt_eq(s, x1, y1) and pt_eq(e, x2, y2)) or
            (pt_eq(s, x2, y2) and pt_eq(e, x1, y1)))

# ---- REMOVALS: 4 segments total (inner vertical + gap-filler, per half) ----
remove_targets = [
    # Left half
    (172.30, 34.09, 172.30, 36.09),  # plank inner vertical
    (172.30, 36.09, 173.30, 36.09),  # gap-filler
    # Right half
    (175.89075, 34.09, 175.89075, 36.09),  # plank inner vertical
    (174.89075, 36.09, 175.89075, 36.09),  # gap-filler
]

to_remove = []
for s in segs:
    if s['kind'] != 'line': continue
    for x1, y1, x2, y2 in remove_targets:
        if line_endpoints_match(s['pts'], x1, y1, x2, y2):
            to_remove.append(s)
            break

print(f'Remove: {len(to_remove)} (expected 4)')
for s in to_remove:
    print(f'  {s["pts"]}')
if len(to_remove) != 4:
    raise SystemExit('FAIL: removal targets not all matched')

# Apply removals bottom-up
to_remove.sort(key=lambda s: s['start_pos'], reverse=True)
out = txt
for s in to_remove:
    bp = s['start_pos']
    while bp > 0 and out[bp-1] in '\t ':
        bp -= 1
    if bp > 0 and out[bp-1] == '\n':
        bp -= 1
    out = out[:bp] + out[s['end_pos']:]

# ---- MODIFICATIONS ----
# 1. Left plank top: (165.80, 34.09) -> (172.30, 34.09)  becomes  (165.80, 34.09) -> (173.30, 34.09)
# 2. Right plank top: (175.89075, 34.09) -> (182.39075, 34.09)  becomes  (174.89075, 34.09) -> (182.39075, 34.09)
# 3. Left PCB inner edge: (173.30, 130.19) -> (173.30, 36.09)  becomes  (173.30, 130.19) -> (173.30, 34.09)
# 4. Right PCB inner edge: (174.89075, 36.09) -> (174.89075, 130.19)  becomes  (174.89075, 34.09) -> (174.89075, 130.19)

# Use simple string replace for each (KiCad's preserved formatting)
replacements = [
    ('(start 165.8 34.09)\n\t\t(end 172.3 34.09)',
     '(start 165.8 34.09)\n\t\t(end 173.3 34.09)'),
    ('(start 175.89075 34.09)\n\t\t(end 182.39075 34.09)',
     '(start 174.89075 34.09)\n\t\t(end 182.39075 34.09)'),
    ('(start 173.3 130.19)\n\t\t(end 173.3 36.09)',
     '(start 173.3 130.19)\n\t\t(end 173.3 34.09)'),
    ('(start 174.89075 36.09)\n\t\t(end 174.89075 130.19)',
     '(start 174.89075 34.09)\n\t\t(end 174.89075 130.19)'),
]
for old, new in replacements:
    n = out.count(old)
    print(f'  replace pattern: found {n} match(es) for {old[:50]}...')
    if n != 1:
        # Try reversed direction
        old_rev = re.sub(r'\(start ([\d.\-]+) ([\d.\-]+)\)\n\t\t\(end ([\d.\-]+) ([\d.\-]+)\)',
                         r'(start \3 \4)\n\t\t(end \1 \2)', old)
        new_rev = re.sub(r'\(start ([\d.\-]+) ([\d.\-]+)\)\n\t\t\(end ([\d.\-]+) ([\d.\-]+)\)',
                         r'(start \3 \4)\n\t\t(end \1 \2)', new)
        n2 = out.count(old_rev)
        print(f'    reversed pattern: {n2} match(es)')
        if n2 == 1:
            out = out.replace(old_rev, new_rev, 1)
            continue
        raise SystemExit(f'FAIL: pattern not uniquely found')
    out = out.replace(old, new, 1)

with open(PCB, 'w', encoding='utf-8') as f:
    f.write(out)
print(f'\nWrote {PCB}')
print(f'Removed {len(to_remove)} segments, modified 4 lines.')
