"""Widen side planks by 1mm total in Y direction (0.5mm at top + 0.5mm at bottom) for pad clearance."""
import re
import uuid

PCB = r'C:\Users\neuro\dev\keyboard\umiko\umiko.kicad_pcb'
with open(PCB, encoding='utf-8') as f:
    txt = f.read()

# Current plank Y range: 54.74 -> 64.68
# New plank Y range: 54.24 -> 65.18
OLD_TOP, OLD_BOT = 54.74, 64.68
NEW_TOP, NEW_BOT = 54.24, 65.18

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
    fwd = all(k in pts and pt_eq(pts[k], x, y) for k, x, y in expected)
    if fwd: return True
    swap = {'start':'end','end':'start','mid':'mid'}
    rev = [(swap[k], x, y) for k,x,y in expected]
    return all(k in pts and pt_eq(pts[k], x, y) for k, x, y in rev)

# Remove all 10 current plank segments
remove_specs = [
    # LEFT
    ('line', [('start', 35.18, OLD_TOP), ('end', 32.68, OLD_TOP)]),
    ('arc',  [('start', 32.68, OLD_TOP), ('end', 32.18, 55.24)]),
    ('line', [('start', 32.18, 55.24), ('end', 32.18, 64.18)]),
    ('arc',  [('start', 32.18, 64.18), ('end', 32.68, OLD_BOT)]),
    ('line', [('start', 32.68, OLD_BOT), ('end', 35.18, OLD_BOT)]),
    # RIGHT
    ('line', [('start', 336.89, OLD_TOP), ('end', 339.39, OLD_TOP)]),
    ('arc',  [('start', 339.39, OLD_TOP), ('end', 339.89, 55.24)]),
    ('line', [('start', 339.89, 55.24), ('end', 339.89, 64.18)]),
    ('arc',  [('start', 339.89, 64.18), ('end', 339.39, OLD_BOT)]),
    ('line', [('start', 339.39, OLD_BOT), ('end', 336.89, OLD_BOT)]),
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

# ---- Modify edge segments (above/below plank) ----
def fmt_line_str(x1,y1,x2,y2):
    return f'(start {x1} {y1})\n\t\t(end {x2} {y2})'

mods = [
    # Left edge above plank: end Y OLD_TOP -> NEW_TOP
    (fmt_line_str(35.18, 37.34, 35.18, OLD_TOP),
     fmt_line_str(35.18, 37.34, 35.18, NEW_TOP)),
    # Left edge below plank: start Y OLD_BOT -> NEW_BOT
    (fmt_line_str(35.18, OLD_BOT, 35.18, 130.19),
     fmt_line_str(35.18, NEW_BOT, 35.18, 130.19)),
    # Right edge above plank
    (fmt_line_str(336.89, 37.34, 336.89, OLD_TOP),
     fmt_line_str(336.89, 37.34, 336.89, NEW_TOP)),
    # Right edge below plank
    (fmt_line_str(336.89, 130.19, 336.89, OLD_BOT),
     fmt_line_str(336.89, 130.19, 336.89, NEW_BOT)),
]
for old, new in mods:
    rev_pat = re.sub(r'\(start ([\d.\-]+) ([\d.\-]+)\)\n\t\t\(end ([\d.\-]+) ([\d.\-]+)\)',
                     r'(start \3 \4)\n\t\t(end \1 \2)', old)
    rev_new = re.sub(r'\(start ([\d.\-]+) ([\d.\-]+)\)\n\t\t\(end ([\d.\-]+) ([\d.\-]+)\)',
                     r'(start \3 \4)\n\t\t(end \1 \2)', new)
    if out.count(old) == 1:
        out = out.replace(old, new, 1); print(f'  mod fwd ok')
    elif out.count(rev_pat) == 1:
        out = out.replace(rev_pat, rev_new, 1); print(f'  mod rev ok')
    else:
        print(f'  FAIL: fwd={out.count(old)} rev={out.count(rev_pat)}'); raise SystemExit()

# ---- ADD new plank segments at widened Y ----
def new_uuid(): return str(uuid.uuid4())
def fmt_line(x1,y1,x2,y2):
    return (f'\t(gr_line\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n'
            f'\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(layer "Edge.Cuts")\n\t\t(uuid "{new_uuid()}")\n\t)')
def fmt_arc(x1,y1,mx,my,x2,y2):
    return (f'\t(gr_arc\n\t\t(start {x1} {y1})\n\t\t(mid {mx} {my})\n\t\t(end {x2} {y2})\n'
            f'\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(layer "Edge.Cuts")\n\t\t(uuid "{new_uuid()}")\n\t)')

LP_IN, LP_OUT = 35.18, 32.18
RP_IN, RP_OUT = 336.89, 339.89
R = 0.5; M = 0.353553

left_plank = [
    fmt_line(LP_IN, NEW_TOP, LP_OUT + R, NEW_TOP),
    fmt_arc(LP_OUT + R, NEW_TOP, LP_OUT + R - M, NEW_TOP + R - M, LP_OUT, NEW_TOP + R),
    fmt_line(LP_OUT, NEW_TOP + R, LP_OUT, NEW_BOT - R),
    fmt_arc(LP_OUT, NEW_BOT - R, LP_OUT + R - M, NEW_BOT - R + M, LP_OUT + R, NEW_BOT),
    fmt_line(LP_OUT + R, NEW_BOT, LP_IN, NEW_BOT),
]
right_plank = [
    fmt_line(RP_IN, NEW_TOP, RP_OUT - R, NEW_TOP),
    fmt_arc(RP_OUT - R, NEW_TOP, RP_OUT - R + M, NEW_TOP + R - M, RP_OUT, NEW_TOP + R),
    fmt_line(RP_OUT, NEW_TOP + R, RP_OUT, NEW_BOT - R),
    fmt_arc(RP_OUT, NEW_BOT - R, RP_OUT - R + M, NEW_BOT - R + M, RP_OUT - R, NEW_BOT),
    fmt_line(RP_OUT - R, NEW_BOT, RP_IN, NEW_BOT),
]
new_segments = left_plank + right_plank
inject = '\n' + '\n'.join(new_segments) + '\n'
out_stripped = out.rstrip()
assert out_stripped.endswith(')')
out = out_stripped[:-1] + inject + ')\n'

with open(PCB, 'w', encoding='utf-8') as f:
    f.write(out)
print(f'Removed {len(to_remove)}, modified 4, added {len(new_segments)}. New plank Y: {NEW_TOP} - {NEW_BOT}')
