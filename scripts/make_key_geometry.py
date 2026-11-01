"""Map PCB switch positions to LAYOUT_all order; emit geometry + preview.

Usage (from repo root): python scripts/make_key_geometry.py umiko.kicad_pcb
Writes: companion/key_geometry.py, companion/_preview.png
"""

import re
import sys

PITCH = 19.05  # mm per 1u

text = open(sys.argv[1], encoding="utf-8").read()
starts = [m.start() for m in re.finditer(r"\(footprint ", text)]

sw = []
for i, s in enumerate(starts):
    e = starts[i + 1] if i + 1 < len(starts) else len(text)
    block = text[s:e]
    fp = re.search(r'\(footprint "([^"]+)"', block).group(1)
    mref = re.search(r'\(property "Reference" "([^"]+)"', block)
    mat = re.search(r"\(at ([-\d.]+) ([-\d.]+)", block)
    if not mref or not mat:
        continue
    ref = mref.group(1)
    if not re.fullmatch(r"SW_\d+", ref):
        continue  # skip SW1/SW2 BOOTSEL tacts
    mu = re.search(r"(\d+(?:\.\d+)?)U", fp)
    sw.append((ref, float(mu.group(1)), float(mat.group(1)), float(mat.group(2))))

assert len(sw) == 63, f"expected 63 key switches, got {len(sw)}"

# Split halves by the big X gap.
xs = sorted(x for _, _, x, _ in sw)
gap_i = max(range(len(xs) - 1), key=lambda i: xs[i + 1] - xs[i])
print(f"x gap: {xs[gap_i + 1] - xs[gap_i]:.1f}mm between halves")
left = sorted([s for s in sw if s[2] <= xs[gap_i]], key=lambda s: s[2])
right = sorted([s for s in sw if s[2] > xs[gap_i]], key=lambda s: s[2])
print(f"left: {len(left)}, right: {len(right)}")
assert (len(left), len(right)) == (30, 33)


def rows_of(half):
    by_y = sorted(half, key=lambda s: s[3])
    rows, cur = [], [by_y[0]]
    for s in by_y[1:]:
        if s[3] - cur[-1][3] > 10:
            rows.append(sorted(cur, key=lambda s: s[2]))
            cur = []
        cur.append(s)
    rows.append(sorted(cur, key=lambda s: s[2]))
    return rows


lrows, rrows = rows_of(left), rows_of(right)
print("left row counts:", [len(r) for r in lrows])
print("right row counts:", [len(r) for r in rrows])
assert [len(r) for r in lrows] == [7, 6, 6, 6, 5]
assert [len(r) for r in rrows] == [7, 8, 7, 6, 5]

# LAYOUT_all index order = row-major per half.
ordered = [s for r in lrows for s in r] + [s for r in rrows for s in r]
assert len(ordered) == 63

# Normalize: min center -> 0. Key rect = center +/- units/2 (top-left origin).
min_x = min(x - u * PITCH / 2 for _, u, x, _ in ordered)
min_y = min(y - PITCH / 2 for _, _, _, y in ordered)
geom = []
for ref, u, x, y in ordered:
    kx = x - u * PITCH / 2 - min_x
    ky = y - PITCH / 2 - min_y
    geom.append((round(kx, 2), round(ky, 2), round(u * PITCH, 2), round(PITCH, 2)))
board_w = round(max(x + w for x, _, w, _ in geom), 2)
board_h = round(max(y + h for _, y, _, h in geom), 2)
print(f"board: {board_w} x {board_h}mm")

# Sanity: spot-check wide keys land on wide legends.
sys.path.insert(0, "companion")
import keymap_data as k

for idx in (7, 13, 19, 25, 29, 36, 44, 51, 57, 58, 59):
    ref, u, x, y = ordered[idx]
    print(f"  idx {idx:2d} {k.BASE[idx]:>7s} <- {ref:>6s} {u}U")

with open("companion/key_geometry.py", "w", encoding="utf-8") as f:
    f.write('"""Key geometry in mm, LAYOUT_all order. GENERATED from umiko.kicad_pcb.\n')
    f.write('Do not hand-edit — rerun scripts/make_key_geometry.py\n')
    f.write('Tuple per key: (x, y, w, h), top-left origin.\n"""\n\n')
    f.write(f"BOARD_W_MM = {board_w}\nBOARD_H_MM = {board_h}\n\nKEY_GEOMETRY = (\n")
    for g in geom:
        f.write(f"    {g},\n")
    f.write(")\n")

# Preview render.
from PIL import Image, ImageDraw

S = 4  # px per mm
img = Image.new("RGB", (int(board_w * S) + 8, int(board_h * S) + 8), "#181818")
d = ImageDraw.Draw(img)
for i, (x, y, w, h) in enumerate(geom):
    x0, y0 = int(x * S) + 4, int(y * S) + 4
    x1, y1 = int((x + w) * S) + 4, int((y + h) * S) + 4
    d.rectangle([x0, y0, x1 - 1, y1 - 1], fill="#232323", outline="#3a3a3a")
    leg = k.BASE[i]
    bb = d.textbbox((0, 0), leg)
    d.text((x0 + (x1 - x0 - (bb[2] - bb[0])) / 2, y0 + 4), leg, fill="#e8e8e8")
img.save("companion/_preview.png")
print("wrote companion/key_geometry.py + companion/_preview.png")
