"""Shorten the inter-half (center) USB-C planks from 4mm to 3mm protrusion so the
USB-C connector body overhangs the plank edge (matching the side planks).

Left  plank outer X: 177.30 -> 176.30 (inner edge stays 173.30 -> 3mm protrusion)
Right plank outer X: 180.891 -> 181.891 (inner edge stays 184.89075 -> ~3mm protrusion)
Only the 5 outer plank segments per side change; inner vertical edges are untouched.
"""
import re
import uuid

PCB = r'C:\Users\neuro\dev\keyboard\umiko\umiko.kicad_pcb'
with open(PCB, encoding='utf-8') as f:
    txt = f.read()

# Parse Edge.Cuts segments
segs = []
for m in re.finditer(r'\(gr_(line|arc)\b', txt):
    p = m.start(); depth = 1; i = m.end()
    while i < len(txt) and depth > 0:
        c = txt[i]
        if c == '(': depth += 1
        elif c == ')': depth -= 1
        i += 1
    blk = txt[p:i]
    if 'Edge.Cuts' not in blk:
        continue
    pts_raw = re.findall(r'\((start|end|mid) ([\d.\-]+) ([\d.\-]+)\)', blk)
    pts = {key: (float(x), float(y)) for key, x, y in pts_raw}
    segs.append({'kind': m.group(1), 'start_pos': p, 'end_pos': i, 'pts': pts})

def approx(a, b, tol=0.01): return abs(a - b) < tol
def pt_eq(p, x, y): return approx(p[0], x) and approx(p[1], y)
def match(pts, expected):
    fwd = all(k in pts and pt_eq(pts[k], x, y) for k, x, y in expected)
    if fwd: return True
    swap = {'start': 'end', 'end': 'start', 'mid': 'mid'}
    rev = [(swap[k], x, y) for k, x, y in expected]
    return all(k in pts and pt_eq(pts[k], x, y) for k, x, y in rev)

# 5 current center plank segments per side to REMOVE
remove_specs = [
    # LEFT (outer X = 177.30)
    ('line', [('start', 173.3, 39.45), ('end', 176.8, 39.45)]),
    ('arc',  [('start', 176.8, 39.45), ('mid', 177.153553, 39.596447), ('end', 177.3, 39.95)]),
    ('line', [('start', 177.3, 39.95), ('end', 177.3, 49.89)]),
    ('arc',  [('start', 177.3, 49.89), ('mid', 177.153553, 50.243553), ('end', 176.8, 50.39)]),
    ('line', [('start', 176.8, 50.39), ('end', 173.3, 50.39)]),
    # RIGHT (outer X = 180.891)
    ('line', [('start', 184.89075, 39.45), ('end', 181.391, 39.45)]),
    ('arc',  [('start', 181.391, 39.45), ('mid', 181.037447, 39.596447), ('end', 180.891, 39.95)]),
    ('line', [('start', 180.891, 39.95), ('end', 180.891, 49.89)]),
    ('arc',  [('start', 180.891, 49.89), ('mid', 181.037447, 50.243553), ('end', 181.391, 50.39)]),
    ('line', [('start', 181.391, 50.39), ('end', 184.89075, 50.39)]),
]

to_remove = []
for s in segs:
    for kind, exp in remove_specs:
        if s['kind'] == kind and match(s['pts'], exp):
            to_remove.append(s); break
print(f'Remove center plank segments: {len(to_remove)} (expected {len(remove_specs)})')
if len(to_remove) != len(remove_specs):
    for kind, exp in remove_specs:
        if not any(s['kind'] == kind and match(s['pts'], exp) for s in segs):
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

# Build new shorter plank segments
def new_uuid(): return str(uuid.uuid4())
def fmt_line(x1, y1, x2, y2):
    return (f'\t(gr_line\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n'
            f'\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(layer "Edge.Cuts")\n\t\t(uuid "{new_uuid()}")\n\t)')
def fmt_arc(x1, y1, mx, my, x2, y2):
    return (f'\t(gr_arc\n\t\t(start {x1} {y1})\n\t\t(mid {mx} {my})\n\t\t(end {x2} {y2})\n'
            f'\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(layer "Edge.Cuts")\n\t\t(uuid "{new_uuid()}")\n\t)')

R = 0.5
M = 0.353553
P_TOP = 39.45
P_BOT = 50.39
LP_IN = 173.30
LP_OUT = 176.30   # was 177.30 (pulled back 1mm)
RP_IN = 184.89075
RP_OUT = 181.891  # was 180.891 (pulled back 1mm)

left = [
    fmt_line(LP_IN, P_TOP, LP_OUT - R, P_TOP),
    fmt_arc(LP_OUT - R, P_TOP, LP_OUT - R + M, P_TOP + R - M, LP_OUT, P_TOP + R),
    fmt_line(LP_OUT, P_TOP + R, LP_OUT, P_BOT - R),
    fmt_arc(LP_OUT, P_BOT - R, LP_OUT - R + M, P_BOT - R + M, LP_OUT - R, P_BOT),
    fmt_line(LP_OUT - R, P_BOT, LP_IN, P_BOT),
]
right = [
    fmt_line(RP_IN, P_TOP, RP_OUT + R, P_TOP),
    fmt_arc(RP_OUT + R, P_TOP, RP_OUT + R - M, P_TOP + R - M, RP_OUT, P_TOP + R),
    fmt_line(RP_OUT, P_TOP + R, RP_OUT, P_BOT - R),
    fmt_arc(RP_OUT, P_BOT - R, RP_OUT + R - M, P_BOT - R + M, RP_OUT + R, P_BOT),
    fmt_line(RP_OUT + R, P_BOT, RP_IN, P_BOT),
]

new_segments = left + right
inject = '\n' + '\n'.join(new_segments) + '\n'
out_stripped = out.rstrip()
assert out_stripped.endswith(')')
out = out_stripped[:-1] + inject + ')\n'

with open(PCB, 'w', encoding='utf-8') as f:
    f.write(out)
print(f'Removed {len(to_remove)} old, added {len(new_segments)} new center plank segments.')
print(f'LEFT  plank outer X: 177.30 -> {LP_OUT}  (protrusion {LP_IN - LP_OUT + 2*0:.3f} -> {LP_IN - LP_OUT:.3f}mm)')
print(f'RIGHT plank outer X: 180.891 -> {RP_OUT} (protrusion -> {RP_IN - RP_OUT:.3f}mm)')
print(f'Gap between center planks now: {RP_OUT - LP_OUT:.3f}mm')
