"""Shift side planks + J1/J2 footprints down by 16.85mm to align with Q-row keycap top (Y=55.24)."""
import re
import uuid

DY = 16.85          # 55.24 (Q-row keycap top) - 38.39 (current body top)
NEW_TOP = 37.89 + DY    # 54.74
NEW_BOT = 47.83 + DY    # 64.68

PCB = r'C:\Users\neuro\dev\keyboard\umiko\umiko.kicad_pcb'
with open(PCB, encoding='utf-8') as f:
    txt = f.read()

# Parse all Edge.Cuts segments with byte spans
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

# Identify the 10 current plank segments to remove
remove_specs = [
    # LEFT plank
    ('line', [('start', 35.18, 37.89), ('end', 32.68, 37.89)]),
    ('arc',  [('start', 32.68, 37.89), ('end', 32.18, 38.39)]),
    ('line', [('start', 32.18, 38.39), ('end', 32.18, 47.33)]),
    ('arc',  [('start', 32.18, 47.33), ('end', 32.68, 47.83)]),
    ('line', [('start', 32.68, 47.83), ('end', 35.18, 47.83)]),
    # RIGHT plank
    ('line', [('start', 336.89, 37.89), ('end', 339.39, 37.89)]),
    ('arc',  [('start', 339.39, 37.89), ('end', 339.89, 38.39)]),
    ('line', [('start', 339.89, 38.39), ('end', 339.89, 47.33)]),
    ('arc',  [('start', 339.89, 47.33), ('end', 339.39, 47.83)]),
    ('line', [('start', 339.39, 47.83), ('end', 336.89, 47.83)]),
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

# ---- Modify the edge segments that bracketed the old plank position ----
# Left edge above plank: was (35.18, 37.34) -> (35.18, 37.89), update end Y to NEW_TOP
# Left edge below plank: was (35.18, 47.83) -> (35.18, 130.19), update start Y to NEW_BOT
# Right edge above plank: was (336.89, 37.34) -> (336.89, 37.89), update end Y to NEW_TOP
# Right edge below plank: was (336.89, 130.19) -> (336.89, 47.83), update end Y to NEW_BOT

def fmt_line_str(x1, y1, x2, y2):
    return f'(start {x1} {y1})\n\t\t(end {x2} {y2})'

mods = [
    # left edge above plank (37.34 -> NEW_TOP)
    (fmt_line_str(35.18, 37.34, 35.18, 37.89),
     fmt_line_str(35.18, 37.34, 35.18, NEW_TOP)),
    # left edge below plank (NEW_BOT -> 130.19)
    (fmt_line_str(35.18, 47.83, 35.18, 130.19),
     fmt_line_str(35.18, NEW_BOT, 35.18, 130.19)),
    # right edge above plank
    (fmt_line_str(336.89, 37.34, 336.89, 37.89),
     fmt_line_str(336.89, 37.34, 336.89, NEW_TOP)),
    # right edge below plank
    (fmt_line_str(336.89, 130.19, 336.89, 47.83),
     fmt_line_str(336.89, 130.19, 336.89, NEW_BOT)),
]
for old, new in mods:
    rev_pat = re.sub(r'\(start ([\d.\-]+) ([\d.\-]+)\)\n\t\t\(end ([\d.\-]+) ([\d.\-]+)\)',
                     r'(start \3 \4)\n\t\t(end \1 \2)', old)
    rev_new = re.sub(r'\(start ([\d.\-]+) ([\d.\-]+)\)\n\t\t\(end ([\d.\-]+) ([\d.\-]+)\)',
                     r'(start \3 \4)\n\t\t(end \1 \2)', new)
    if out.count(old) == 1:
        out = out.replace(old, new, 1); print(f'  mod fwd: {old[:30]!r}')
    elif out.count(rev_pat) == 1:
        out = out.replace(rev_pat, rev_new, 1); print(f'  mod rev: {rev_pat[:30]!r}')
    else:
        print(f'  FAIL pattern: fwd={out.count(old)} rev={out.count(rev_pat)}'); raise SystemExit()

# ---- ADD new plank segments at shifted Y ----
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
TOP, BOT = NEW_TOP, NEW_BOT  # 54.74, 64.68

left_plank = [
    fmt_line(LP_IN, TOP, LP_OUT + R, TOP),
    fmt_arc(LP_OUT + R, TOP, LP_OUT + R - M, TOP + R - M, LP_OUT, TOP + R),
    fmt_line(LP_OUT, TOP + R, LP_OUT, BOT - R),
    fmt_arc(LP_OUT, BOT - R, LP_OUT + R - M, BOT - R + M, LP_OUT + R, BOT),
    fmt_line(LP_OUT + R, BOT, LP_IN, BOT),
]
right_plank = [
    fmt_line(RP_IN, TOP, RP_OUT - R, TOP),
    fmt_arc(RP_OUT - R, TOP, RP_OUT - R + M, TOP + R - M, RP_OUT, TOP + R),
    fmt_line(RP_OUT, TOP + R, RP_OUT, BOT - R),
    fmt_arc(RP_OUT, BOT - R, RP_OUT - R + M, BOT - R + M, RP_OUT - R, BOT),
    fmt_line(RP_OUT - R, BOT, RP_IN, BOT),
]
new_segments = left_plank + right_plank
inject = '\n' + '\n'.join(new_segments) + '\n'
out_stripped = out.rstrip()
assert out_stripped.endswith(')')
out = out_stripped[:-1] + inject + ')\n'

# ---- Move J1 and J2 footprint origins ----
# J1 at (34.85, 42.86, 90) on B.Cu  ->  (34.85, 42.86 + DY, 90)
# J2 at (337.25, 42.86, -90) on B.Cu  ->  (337.25, 42.86 + DY, -90)
new_J_y = 42.86 + DY  # 59.71

# Find each J* footprint's (at ...) line by ref + replace Y in the FIRST (at) of the block
def move_footprint(text, jref, new_x, new_y):
    # find footprint with matching Reference
    matches = list(re.finditer(r'\(footprint "[^"]+"', text))
    for m in matches:
        p = m.start(); depth=1; i=m.end()
        while i<len(text) and depth>0:
            c=text[i]
            if c=='(': depth+=1
            elif c==')': depth-=1
            i+=1
        blk = text[p:i]
        if f'(property "Reference" "{jref}"' in blk:
            # Replace first (at ...) in block (the footprint origin)
            at_m = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)(?:\s+([\d.\-]+))?\)', blk[:blk.find('(property')])
            if at_m:
                old_at = at_m.group(0)
                rot_part = ' ' + at_m.group(3) if at_m.group(3) else ''
                new_at = f'(at {at_m.group(1)} {new_y}{rot_part})'
                new_blk = blk.replace(old_at, new_at, 1)
                return text[:p] + new_blk + text[i:]
    raise SystemExit(f'Could not find {jref}')

out = move_footprint(out, 'J1', 34.85, new_J_y)
out = move_footprint(out, 'J2', 337.25, new_J_y)

with open(PCB, 'w', encoding='utf-8') as f:
    f.write(out)
print(f'Removed {len(to_remove)} plank segments, modified 4 edge lines, added {len(new_segments)} new plank segments, moved J1+J2 to Y={new_J_y}.')
