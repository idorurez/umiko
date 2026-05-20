"""Remove old TRRS planks (Y=34-36 area) and add new inter-half USB-C planks
that extend from each half's inner edge INTO the gap to support J3/J4 bodies.

J3 body world bbox: X[170, 177.30], Y[40.45, 49.39] -- left half USB-C, faces right
J4 body world bbox: X[180.89, 188.19], Y[40.45, 49.39] -- right half USB-C, faces left
Left half inner edge X=173.30; right half inner edge X=184.89075.
Gap = 184.89075 - 173.30 = 11.591mm

New planks:
- Left: X 173.30 -> 177.30 (4mm protrusion), Y 39.45 -> 50.39 (body+1mm margin)
- Right: X 184.89075 -> 180.891 (4mm protrusion), Y 39.45 -> 50.39
- 0.5mm fillets on the 2 outer corners (the corners facing the gap)
- 90deg corners on inner side (continuation of inner edge)
- Gap between planks: 180.891 - 177.30 = 3.59mm (room for USB-C male-male coupler)
"""
import re
import uuid

PCB = r'C:\Users\neuro\dev\keyboard\umiko\umiko.kicad_pcb'
with open(PCB, encoding='utf-8') as f:
    txt = f.read()

# Parse Edge.Cuts segments
segs = []
for m in re.finditer(r'\(gr_(line|arc)\b', txt):
    p = m.start(); depth=1; i=m.end()
    while i < len(txt) and depth>0:
        c = txt[i]
        if c=='(': depth+=1
        elif c==')': depth-=1
        i+=1
    blk = txt[p:i]
    if 'Edge.Cuts' not in blk: continue
    pts_raw = re.findall(r'\((start|end|mid) ([\d.\-]+) ([\d.\-]+)\)', blk)
    pts = {key: (float(x), float(y)) for key, x, y in pts_raw}
    segs.append({'kind': m.group(1), 'start_pos': p, 'end_pos': i, 'pts': pts})

def approx(a, b, tol=0.01): return abs(a-b) < tol
def pt_eq(p, x, y): return approx(p[0], x) and approx(p[1], y)
def match(pts, expected):
    fwd = all(k in pts and pt_eq(pts[k], x, y) for k,x,y in expected)
    if fwd: return True
    swap = {'start':'end','end':'start','mid':'mid'}
    rev = [(swap[k], x, y) for k,x,y in expected]
    return all(k in pts and pt_eq(pts[k], x, y) for k,x,y in rev)

# Old TRRS planks to REMOVE (5 segments each side)
remove_specs = [
    # LEFT (Y=34-36 area, X 165.30-173.30)
    ('line', [('start', 165.800, 34.090), ('end', 172.800, 34.090)]),
    ('arc',  [('start', 165.300, 34.590), ('end', 165.800, 34.090)]),
    ('arc',  [('start', 172.800, 34.090), ('end', 173.300, 34.590)]),
    ('line', [('start', 165.300, 35.590), ('end', 165.300, 34.590)]),
    ('arc',  [('start', 165.300, 35.590), ('end', 164.800, 36.090)]),
    # RIGHT (Y=34-36, X 184.89075-192.891)
    ('line', [('start', 185.391, 34.090), ('end', 192.391, 34.090)]),
    ('arc',  [('start', 184.89075, 34.590), ('end', 185.391, 34.090)]),
    ('arc',  [('start', 192.391, 34.090), ('end', 192.891, 34.590)]),
    ('line', [('start', 192.891, 34.590), ('end', 192.891, 35.590)]),
    ('arc',  [('start', 193.391, 36.090), ('end', 192.891, 35.590)]),
]

to_remove = []
for s in segs:
    for kind, exp in remove_specs:
        if s['kind']==kind and match(s['pts'], exp):
            to_remove.append(s); break
print(f'Remove old TRRS plank segments: {len(to_remove)} (expected {len(remove_specs)})')
if len(to_remove) != len(remove_specs):
    for kind, exp in remove_specs:
        if not any(s['kind']==kind and match(s['pts'], exp) for s in segs):
            print(f'  MISSING: {kind} {exp}')
    raise SystemExit('FAIL')

to_remove.sort(key=lambda s: s['start_pos'], reverse=True)
out = txt
for s in to_remove:
    bp = s['start_pos']
    while bp > 0 and out[bp-1] in '\t ':
        bp -= 1
    if bp > 0 and out[bp-1] == '\n':
        bp -= 1
    out = out[:bp] + out[s['end_pos']:]

# ---- MODIFY main top edges (extend to meet inner edges) and inner edges (terminate at plank Y range) ----
def fmt_line_str(x1, y1, x2, y2):
    return f'(start {x1} {y1})\n\t\t(end {x2} {y2})'

mods = [
    # Left main top edge: was (149.79, 36.09)->(164.80, 36.09), extend to (173.30, 36.09)
    (fmt_line_str(149.79, 36.09, 164.8, 36.09),
     fmt_line_str(149.79, 36.09, 173.3, 36.09)),
    # Right main top edge: was (193.39075, 36.09)->(208.401, 36.09), extend left to (184.89075, 36.09)
    (fmt_line_str(193.39075, 36.09, 208.401, 36.09),
     fmt_line_str(184.89075, 36.09, 208.401, 36.09)),
    # Left inner edge: was (173.30, 130.19)->(173.30, 34.59), shorten top to Y=50.39 (below new plank)
    (fmt_line_str(173.3, 130.19, 173.3, 34.59),
     fmt_line_str(173.3, 130.19, 173.3, 50.39)),
    # Right inner edge: was (184.89075, 34.59)->(184.89075, 130.19), shorten top to Y=50.39
    (fmt_line_str(184.89075, 34.59, 184.89075, 130.19),
     fmt_line_str(184.89075, 50.39, 184.89075, 130.19)),
]
for old, new in mods:
    rev = re.sub(r'\(start ([\d.\-]+) ([\d.\-]+)\)\n\t\t\(end ([\d.\-]+) ([\d.\-]+)\)',
                 r'(start \3 \4)\n\t\t(end \1 \2)', old)
    rev_new = re.sub(r'\(start ([\d.\-]+) ([\d.\-]+)\)\n\t\t\(end ([\d.\-]+) ([\d.\-]+)\)',
                     r'(start \3 \4)\n\t\t(end \1 \2)', new)
    if out.count(old) == 1:
        out = out.replace(old, new, 1); print(f'  mod fwd ok')
    elif out.count(rev) == 1:
        out = out.replace(rev, rev_new, 1); print(f'  mod rev ok')
    else:
        print(f'  FAIL: fwd={out.count(old)} rev={out.count(rev)} | {old[:50]}'); raise SystemExit()

# ---- ADD: inner edges ABOVE new USB-C planks + new USB-C plank segments ----
def new_uuid(): return str(uuid.uuid4())
def fmt_line(x1,y1,x2,y2):
    return (f'\t(gr_line\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n'
            f'\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(layer "Edge.Cuts")\n\t\t(uuid "{new_uuid()}")\n\t)')
def fmt_arc(x1,y1,mx,my,x2,y2):
    return (f'\t(gr_arc\n\t\t(start {x1} {y1})\n\t\t(mid {mx} {my})\n\t\t(end {x2} {y2})\n'
            f'\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(layer "Edge.Cuts")\n\t\t(uuid "{new_uuid()}")\n\t)')

# Constants
R = 0.5
M = 0.353553
P_TOP = 39.45
P_BOT = 50.39
LP_IN = 173.30   # left half inner edge X
LP_OUT = 177.30  # left plank outer X (4mm protrusion)
RP_IN = 184.89075  # right half inner edge X
RP_OUT = 180.891 # right plank outer X (4mm protrusion leftward)

left = [
    # inner edge above plank: from (173.30, 36.09) [main top edge end] down to (173.30, 39.45)
    fmt_line(LP_IN, 36.09, LP_IN, P_TOP),
    # plank top: (173.30, 39.45) -> (176.80, 39.45)
    fmt_line(LP_IN, P_TOP, LP_OUT - R, P_TOP),
    # top-outer convex fillet at (177.30, 39.45)
    fmt_arc(LP_OUT - R, P_TOP, LP_OUT - R + M, P_TOP + R - M, LP_OUT, P_TOP + R),
    # outer vertical: (177.30, 39.95) -> (177.30, 49.89)
    fmt_line(LP_OUT, P_TOP + R, LP_OUT, P_BOT - R),
    # bottom-outer convex fillet at (177.30, 50.39)
    fmt_arc(LP_OUT, P_BOT - R, LP_OUT - R + M, P_BOT - R + M, LP_OUT - R, P_BOT),
    # plank bottom: (176.80, 50.39) -> (173.30, 50.39)
    fmt_line(LP_OUT - R, P_BOT, LP_IN, P_BOT),
]

right = [
    # inner edge above plank: (184.89075, 36.09) -> (184.89075, 39.45)
    fmt_line(RP_IN, 36.09, RP_IN, P_TOP),
    # plank top: (184.89075, 39.45) -> (181.391, 39.45) (going LEFT)
    fmt_line(RP_IN, P_TOP, RP_OUT + R, P_TOP),
    # top-outer convex fillet at (180.891, 39.45)
    fmt_arc(RP_OUT + R, P_TOP, RP_OUT + R - M, P_TOP + R - M, RP_OUT, P_TOP + R),
    # outer vertical: (180.891, 39.95) -> (180.891, 49.89)
    fmt_line(RP_OUT, P_TOP + R, RP_OUT, P_BOT - R),
    # bottom-outer convex fillet at (180.891, 50.39)
    fmt_arc(RP_OUT, P_BOT - R, RP_OUT + R - M, P_BOT - R + M, RP_OUT + R, P_BOT),
    # plank bottom: (181.391, 50.39) -> (184.89075, 50.39)
    fmt_line(RP_OUT + R, P_BOT, RP_IN, P_BOT),
]

new_segments = left + right
inject = '\n' + '\n'.join(new_segments) + '\n'
out_stripped = out.rstrip()
assert out_stripped.endswith(')')
out = out_stripped[:-1] + inject + ')\n'

with open(PCB, 'w', encoding='utf-8') as f:
    f.write(out)
print(f'Removed {len(to_remove)} old TRRS plank segments, modified 4 edge lines, added {len(new_segments)} new segments.')
print(f'New plank Y: {P_TOP} -> {P_BOT}')
print(f'LEFT plank X: {LP_IN} -> {LP_OUT} (4mm out into gap)')
print(f'RIGHT plank X: {RP_IN} -> {RP_OUT} (4mm out into gap)')
print(f'Gap between planks: {RP_OUT - LP_OUT:.3f}mm')
