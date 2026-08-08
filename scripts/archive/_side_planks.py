"""Remove old top planks (P1/P4) and add new side planks for J1/J2 (USB-Cs now on the side edges)."""
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
    if 'Edge.Cuts' not in blk:
        continue
    pts_raw = re.findall(r'\((start|end|mid) ([\d.\-]+) ([\d.\-]+)\)', blk)
    pts = {key: (float(x), float(y)) for key, x, y in pts_raw}
    segs.append({'kind': m.group(1), 'start_pos': p, 'end_pos': i, 'pts': pts})

def approx(a, b, tol=0.01):
    return abs(a - b) < tol

def pt_eq(p, x, y):
    return approx(p[0], x) and approx(p[1], y)

def match(pts, kind, expected):
    """expected = list of (key, x, y); try forward, then start<->end swapped."""
    fwd = all(k in pts and pt_eq(pts[k], x, y) for k, x, y in expected)
    if fwd: return True
    swap_map = {'start': 'end', 'end': 'start', 'mid': 'mid'}
    rev = [(swap_map[k], x, y) for k, x, y in expected]
    return all(k in pts and pt_eq(pts[k], x, y) for k, x, y in rev)

# ---- REMOVALS ----
P1_specs = [  # left old plank
    ('line', [('start', 59.240, 29.070), ('end', 49.480, 29.070)]),
    ('arc',  [('start', 48.230, 30.320), ('end', 49.480, 29.070)]),
    ('arc',  [('start', 59.240, 29.070), ('end', 60.490, 30.320)]),
    ('line', [('start', 48.230, 30.320), ('end', 48.230, 34.840)]),
    ('line', [('start', 60.490, 34.840), ('end', 60.490, 30.320)]),
    ('arc',  [('start', 48.230, 34.840), ('end', 46.980, 36.090)]),
    ('arc',  [('start', 61.740, 36.090), ('end', 60.490, 34.840)]),
]
P4_specs = [  # right old plank (mirror)
    ('line', [('start', 322.590, 29.070), ('end', 312.830, 29.070)]),
    ('arc',  [('start', 311.580, 30.320), ('end', 312.830, 29.070)]),
    ('arc',  [('start', 322.590, 29.070), ('end', 323.840, 30.320)]),
    ('line', [('start', 311.580, 30.320), ('end', 311.580, 34.840)]),
    ('line', [('start', 323.840, 34.840), ('end', 323.840, 30.320)]),
    ('arc',  [('start', 311.580, 34.840), ('end', 310.330, 36.090)]),
    ('arc',  [('start', 325.090, 36.090), ('end', 323.840, 34.840)]),
]
# Old main-board top edge stub between P1's left base and top-left corner fillet end
LEFT_STUB = [('line', [('start', 46.980, 36.090), ('end', 36.430, 36.090)])]
# Old main-board top edge stub between top-right corner fillet end and P4's right base
RIGHT_STUB = [('line', [('start', 335.640, 36.090), ('end', 325.090, 36.090)])]

remove_specs = P1_specs + P4_specs + LEFT_STUB + RIGHT_STUB

to_remove = []
for s in segs:
    for kind, exp in remove_specs:
        if s['kind'] == kind and match(s['pts'], kind, exp):
            to_remove.append(s)
            break

print(f'To remove: {len(to_remove)} (expected {len(remove_specs)})')
if len(to_remove) != len(remove_specs):
    matched_keys = set()
    for s in to_remove:
        matched_keys.add((s['kind'], tuple(sorted(s['pts'].items()))))
    print('Missing:')
    for kind, exp in remove_specs:
        found = any(s['kind']==kind and match(s['pts'], kind, exp) for s in segs)
        if not found:
            print(f'  {kind} {exp}')
    raise SystemExit('FAIL')

# Apply removals (bottom-up byte ordering)
to_remove.sort(key=lambda s: s['start_pos'], reverse=True)
out = txt
for s in to_remove:
    bp = s['start_pos']
    while bp > 0 and out[bp-1] in '\t ':
        bp -= 1
    if bp > 0 and out[bp-1] == '\n':
        bp -= 1
    out = out[:bp] + out[s['end_pos']:]

# ---- MODIFICATIONS (4 lines) ----
# 1. Extend left main top edge: was (61.740, 36.09) -> (149.79, 36.09), now (36.43, 36.09) -> (149.79, 36.09)
# 2. Extend right main top edge: was (198.401, 36.09) -> (310.330, 36.09), now (198.401, 36.09) -> (335.640, 36.09)
# 3. Split left edge: was (35.180, 37.340) -> (35.180, 130.190), now upper part (35.180, 37.340) -> (35.180, 37.890); add new lower part
# 4. Split right edge: was (336.890, 130.190) -> (336.890, 37.340), now lower part (336.890, 130.190) -> (336.890, 47.830); add new upper part

mods = [
    ('(start 61.74 36.09)\n\t\t(end 149.79 36.09)',
     '(start 36.43 36.09)\n\t\t(end 149.79 36.09)'),
    ('(start 198.401 36.09)\n\t\t(end 310.33 36.09)',
     '(start 198.401 36.09)\n\t\t(end 335.64 36.09)'),
    ('(start 35.18 37.34)\n\t\t(end 35.18 130.19)',
     '(start 35.18 37.34)\n\t\t(end 35.18 37.89)'),
    ('(start 336.89 130.19)\n\t\t(end 336.89 37.34)',
     '(start 336.89 130.19)\n\t\t(end 336.89 47.83)'),
]
for old, new in mods:
    rev = re.sub(r'\(start ([\d.\-]+) ([\d.\-]+)\)\n\t\t\(end ([\d.\-]+) ([\d.\-]+)\)',
                 r'(start \3 \4)\n\t\t(end \1 \2)', old)
    rev_new = re.sub(r'\(start ([\d.\-]+) ([\d.\-]+)\)\n\t\t\(end ([\d.\-]+) ([\d.\-]+)\)',
                     r'(start \3 \4)\n\t\t(end \1 \2)', new)
    if out.count(old) == 1:
        out = out.replace(old, new, 1); print(f'  mod fwd ok: {old[:40]}...')
    elif out.count(rev) == 1:
        out = out.replace(rev, rev_new, 1); print(f'  mod rev ok: {rev[:40]}...')
    else:
        print(f'  FAIL pattern: fwd_count={out.count(old)} rev_count={out.count(rev)}')
        print(f'    old: {old!r}')
        raise SystemExit('FAIL mod')

# ---- ADD NEW SEGMENTS ----
def new_uuid(): return str(uuid.uuid4())
def fmt_line(x1, y1, x2, y2):
    return (f'\t(gr_line\n\t\t(start {x1} {y1})\n\t\t(end {x2} {y2})\n'
            f'\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(layer "Edge.Cuts")\n\t\t(uuid "{new_uuid()}")\n\t)')
def fmt_arc(x1, y1, mx, my, x2, y2):
    return (f'\t(gr_arc\n\t\t(start {x1} {y1})\n\t\t(mid {mx} {my})\n\t\t(end {x2} {y2})\n'
            f'\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n\t\t)\n'
            f'\t\t(layer "Edge.Cuts")\n\t\t(uuid "{new_uuid()}")\n\t)')

# Left plank (J1 side): inner X=35.18 (board edge), outer X=30.68, Y range 37.89 - 47.83
LP_IN, LP_OUT = 35.18, 30.68
P_TOP, P_BOT = 37.89, 47.83
R = 0.5
M = 0.353553

left_plank = [
    # plank top: (35.18, 37.89) -> (31.18, 37.89)
    fmt_line(LP_IN, P_TOP, LP_OUT + R, P_TOP),
    # top-outer fillet at (30.68, 37.89): from (31.18, 37.89) to (30.68, 38.39)
    fmt_arc(LP_OUT + R, P_TOP, LP_OUT + R - M, P_TOP + R - M, LP_OUT, P_TOP + R),
    # outer vertical: (30.68, 38.39) -> (30.68, 47.33)
    fmt_line(LP_OUT, P_TOP + R, LP_OUT, P_BOT - R),
    # bottom-outer fillet at (30.68, 47.83): from (30.68, 47.33) to (31.18, 47.83)
    fmt_arc(LP_OUT, P_BOT - R, LP_OUT + R - M, P_BOT - R + M, LP_OUT + R, P_BOT),
    # plank bottom: (31.18, 47.83) -> (35.18, 47.83)
    fmt_line(LP_OUT + R, P_BOT, LP_IN, P_BOT),
    # left edge below plank: (35.18, 47.83) -> (35.18, 130.19)
    fmt_line(LP_IN, P_BOT, LP_IN, 130.19),
]

# Right plank (J2 side): inner X=336.89 (board edge), outer X=341.39, Y range 37.89 - 47.83
RP_IN, RP_OUT = 336.89, 341.39
right_plank = [
    # right edge above plank: (336.89, 37.34) -> (336.89, 37.89)
    fmt_line(RP_IN, 37.34, RP_IN, P_TOP),
    # plank top: (336.89, 37.89) -> (340.89, 37.89)
    fmt_line(RP_IN, P_TOP, RP_OUT - R, P_TOP),
    # top-outer fillet at (341.39, 37.89): from (340.89, 37.89) to (341.39, 38.39)
    fmt_arc(RP_OUT - R, P_TOP, RP_OUT - R + M, P_TOP + R - M, RP_OUT, P_TOP + R),
    # outer vertical: (341.39, 38.39) -> (341.39, 47.33)
    fmt_line(RP_OUT, P_TOP + R, RP_OUT, P_BOT - R),
    # bottom-outer fillet at (341.39, 47.83): from (341.39, 47.33) to (340.89, 47.83)
    fmt_arc(RP_OUT, P_BOT - R, RP_OUT - R + M, P_BOT - R + M, RP_OUT - R, P_BOT),
    # plank bottom: (340.89, 47.83) -> (336.89, 47.83)
    fmt_line(RP_OUT - R, P_BOT, RP_IN, P_BOT),
]

new_segments = left_plank + right_plank
inject = '\n' + '\n'.join(new_segments) + '\n'
out_stripped = out.rstrip()
assert out_stripped.endswith(')'), 'missing final paren'
out = out_stripped[:-1] + inject + ')\n'

with open(PCB, 'w', encoding='utf-8') as f:
    f.write(out)

print(f'\nWrote {PCB}')
print(f'Removed {len(to_remove)} old segments, modified 4 lines, added {len(new_segments)} new segments.')
