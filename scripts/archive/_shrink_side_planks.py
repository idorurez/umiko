"""Shrink side planks: move outer edges 1.5mm inward (toward board) so USB-C body overhangs."""
import re
import uuid

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
    if 'Edge.Cuts' not in blk: continue
    pts_raw = re.findall(r'\((start|end|mid) ([\d.\-]+) ([\d.\-]+)\)', blk)
    pts = {key: (float(x), float(y)) for key, x, y in pts_raw}
    segs.append({'kind': m.group(1), 'start_pos': p, 'end_pos': i, 'pts': pts})

def approx(a, b, tol=0.01):
    return abs(a - b) < tol
def pt_eq(p, x, y):
    return approx(p[0], x) and approx(p[1], y)
def match(pts, expected):
    fwd = all(k in pts and pt_eq(pts[k], x, y) for k, x, y in expected)
    if fwd: return True
    swap = {'start':'end','end':'start','mid':'mid'}
    rev = [(swap[k], x, y) for k,x,y in expected]
    return all(k in pts and pt_eq(pts[k], x, y) for k, x, y in rev)

# Identify the 10 current plank segments (5 per side) to remove
remove_specs = [
    # LEFT plank (current outer X = 30.68)
    ('line', [('start', 35.18, 37.89), ('end', 31.18, 37.89)]),
    ('arc',  [('start', 31.18, 37.89), ('end', 30.68, 38.39)]),
    ('line', [('start', 32.18, 38.39), ('end', 32.18, 47.33)]),
    ('arc',  [('start', 30.68, 47.33), ('end', 31.18, 47.83)]),
    ('line', [('start', 31.18, 47.83), ('end', 35.18, 47.83)]),
    # RIGHT plank (current outer X = 341.39)
    ('line', [('start', 336.89, 37.89), ('end', 340.89, 37.89)]),
    ('arc',  [('start', 340.89, 37.89), ('end', 341.39, 38.39)]),
    ('line', [('start', 341.39, 38.39), ('end', 341.39, 47.33)]),
    ('arc',  [('start', 341.39, 47.33), ('end', 340.89, 47.83)]),
    ('line', [('start', 340.89, 47.83), ('end', 336.89, 47.83)]),
]

to_remove = []
for s in segs:
    for kind, exp in remove_specs:
        if s['kind'] == kind and match(s['pts'], exp):
            to_remove.append(s); break

print(f'Remove: {len(to_remove)} (expected {len(remove_specs)})')
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

# Build new plank segments with outer X shifted 1.5mm inward
def new_uuid(): return str(uuid.uuid4())
def fmt_line(x1,y1,x2,y2):
    return (f'\t(gr_line\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n'
            f'\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(layer "Edge.Cuts")\n\t\t(uuid "{new_uuid()}")\n\t)')
def fmt_arc(x1,y1,mx,my,x2,y2):
    return (f'\t(gr_arc\n\t\t(start {x1} {y1})\n\t\t(mid {mx} {my})\n\t\t(end {x2} {y2})\n'
            f'\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(layer "Edge.Cuts")\n\t\t(uuid "{new_uuid()}")\n\t)')

# LEFT: inner X stays 35.18; outer X moves 30.68 -> 32.18 (3mm protrusion instead of 4.5)
LP_IN, LP_OUT = 35.18, 32.18
R = 0.5; M = 0.353553
P_TOP, P_BOT = 37.89, 47.83
left_plank = [
    fmt_line(LP_IN, P_TOP, LP_OUT + R, P_TOP),
    fmt_arc(LP_OUT + R, P_TOP, LP_OUT + R - M, P_TOP + R - M, LP_OUT, P_TOP + R),
    fmt_line(LP_OUT, P_TOP + R, LP_OUT, P_BOT - R),
    fmt_arc(LP_OUT, P_BOT - R, LP_OUT + R - M, P_BOT - R + M, LP_OUT + R, P_BOT),
    fmt_line(LP_OUT + R, P_BOT, LP_IN, P_BOT),
]
# RIGHT: inner X stays 336.89; outer X moves 341.39 -> 339.89
RP_IN, RP_OUT = 336.89, 339.89
right_plank = [
    fmt_line(RP_IN, P_TOP, RP_OUT - R, P_TOP),
    fmt_arc(RP_OUT - R, P_TOP, RP_OUT - R + M, P_TOP + R - M, RP_OUT, P_TOP + R),
    fmt_line(RP_OUT, P_TOP + R, RP_OUT, P_BOT - R),
    fmt_arc(RP_OUT, P_BOT - R, RP_OUT - R + M, P_BOT - R + M, RP_OUT - R, P_BOT),
    fmt_line(RP_OUT - R, P_BOT, RP_IN, P_BOT),
]

new_segments = left_plank + right_plank
inject = '\n' + '\n'.join(new_segments) + '\n'
out_stripped = out.rstrip()
assert out_stripped.endswith(')')
out = out_stripped[:-1] + inject + ')\n'

with open(PCB, 'w', encoding='utf-8') as f:
    f.write(out)
print(f'Removed {len(to_remove)}, added {len(new_segments)}.')
