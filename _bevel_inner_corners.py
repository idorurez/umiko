"""Add 0.5mm fillets to the inner-top corners where plank top meets PCB inner edge.

Left corner at (173.30, 34.09): plank top from outer + 0.5mm-fillet -> shortened to end at (172.80, 34.09);
add arc to (173.30, 34.59); inner edge starts at (173.30, 34.59) going down.
Right corner at (174.89075, 34.09): mirror.
"""
import re
import uuid

PCB = r'C:\Users\neuro\dev\keyboard\umiko\umiko.kicad_pcb'
with open(PCB, encoding='utf-8') as f:
    txt = f.read()

R = 0.5
M = 0.353553

def new_uuid():
    return str(uuid.uuid4())

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

# ---- LEFT corner at (173.30, 34.09) ----
# Plank top: was (165.80, 34.09) -> (173.30, 34.09); shorten to (165.80, 34.09) -> (172.80, 34.09)
# Inner edge: was (173.30, 130.19) -> (173.30, 34.09); shorten to (173.30, 130.19) -> (173.30, 34.59)
# Add arc: start (172.80, 34.09), mid (173.154, 34.236), end (173.30, 34.59) — convex fillet
L_arc = fmt_arc(173.30 - R, 34.09,
                173.30 - R + M, 34.09 + R - M,
                173.30, 34.09 + R)

# ---- RIGHT corner at (174.89075, 34.09) ----
# Plank top: was (174.89075, 34.09) -> (182.39075, 34.09); shorten to (175.39075, 34.09) -> (182.39075, 34.09)
# Inner edge: was (174.89075, 34.09) -> (174.89075, 130.19); shorten to (174.89075, 34.59) -> (174.89075, 130.19)
# Add arc: start (174.89075, 34.59), mid (175.037, 34.236), end (175.39075, 34.09)
R_arc = fmt_arc(174.89075, 34.09 + R,
                174.89075 + R - M, 34.09 + R - M,
                174.89075 + R, 34.09)

# Apply modifications via string replace
out = txt

# Left plank top: shorten end
old = '(start 165.8 34.09)\n\t\t(end 173.3 34.09)'
new = '(start 165.8 34.09)\n\t\t(end 172.8 34.09)'
assert out.count(old) == 1, f'L plank top: count={out.count(old)}'
out = out.replace(old, new, 1)

# Left inner edge: shorten end
old = '(start 173.3 130.19)\n\t\t(end 173.3 34.09)'
new = '(start 173.3 130.19)\n\t\t(end 173.3 34.59)'
assert out.count(old) == 1, f'L inner edge: count={out.count(old)}'
out = out.replace(old, new, 1)

# Right plank top: shorten start
old = '(start 174.89075 34.09)\n\t\t(end 182.39075 34.09)'
new = '(start 175.39075 34.09)\n\t\t(end 182.39075 34.09)'
assert out.count(old) == 1, f'R plank top: count={out.count(old)}'
out = out.replace(old, new, 1)

# Right inner edge: shorten start
old = '(start 174.89075 34.09)\n\t\t(end 174.89075 130.19)'
new = '(start 174.89075 34.59)\n\t\t(end 174.89075 130.19)'
assert out.count(old) == 1, f'R inner edge: count={out.count(old)}'
out = out.replace(old, new, 1)

# Inject 2 new arcs
inject = '\n' + L_arc + '\n' + R_arc + '\n'
out_stripped = out.rstrip()
assert out_stripped.endswith(')'), 'missing final paren'
out = out_stripped[:-1] + inject + ')\n'

with open(PCB, 'w', encoding='utf-8') as f:
    f.write(out)
print('Wrote PCB. Added 2 fillet arcs, shortened 4 segments.')
