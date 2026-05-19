"""Align every per-key LED to its switch: dx=0, dy=-5.175 (KS-33 v2 window center)."""
import re

PCB = r'C:\Users\neuro\dev\keyboard\umiko\umiko.kicad_pcb'
TARGET_DY = -5.175  # KS-33 v2 datasheet: window center 5.175mm above switch
TARGET_DX = 0.0

with open(PCB, encoding='utf-8') as f:
    txt = f.read()

# Pass 1: scan footprints, record positions + the byte range of each footprint's own (at ...) line
fps = {}  # ref -> dict(x, y, rot, at_span (start, end), lib, is_underglow)
for m in re.finditer(r'\n\t\(footprint\s', txt):
    p = m.start() + 1
    depth = 0
    i = p
    while i < len(txt):
        c = txt[i]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                blk_end = i + 1
                blk = txt[p:blk_end]
                ref_m = re.search(r'\(property "Reference" "([^"]+)"', blk)
                lib_m = re.match(r'\(footprint "([^"]+)"', blk)
                # The FOOTPRINT's own (at ...) is the first one before (property ...)
                head_end = blk.find('(property')
                head = blk[:head_end] if head_end >= 0 else blk
                at_m = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)(?:\s+([\d.\-]+))?\)', head)
                if ref_m and at_m:
                    ref = ref_m.group(1)
                    fps[ref] = {
                        'x': float(at_m.group(1)),
                        'y': float(at_m.group(2)),
                        'rot': float(at_m.group(3)) if at_m.group(3) else None,
                        'at_abs_start': p + at_m.start(),
                        'at_abs_end': p + at_m.end(),
                        'lib': lib_m.group(1) if lib_m else '',
                    }
                break
        i += 1

# Determine each per-key LED's target switch
def per_key_led_for(sw_ref):
    sx, sy = fps[sw_ref]['x'], fps[sw_ref]['y']
    best = None
    for r, info in fps.items():
        if not r.startswith('LED'):
            continue
        if 'underglow' in info['lib']:
            continue
        d2 = (info['x'] - sx) ** 2 + (info['y'] - sy) ** 2
        if d2 > 50:
            continue
        if best is None or d2 < best[0]:
            best = (d2, r)
    return best[1] if best else None

# Build map: LED -> (new_x, new_y, current_x, current_y, switch_ref)
edits = []
for ref, info in fps.items():
    if not ref.startswith('SW_'):
        continue
    led = per_key_led_for(ref)
    if not led:
        continue
    sw_x, sw_y = info['x'], info['y']
    target_x = sw_x + TARGET_DX
    target_y = sw_y + TARGET_DY
    led_info = fps[led]
    if abs(led_info['x'] - target_x) > 1e-4 or abs(led_info['y'] - target_y) > 1e-4:
        edits.append((led, led_info, target_x, target_y, ref))

# Sort edits by start position DESCENDING so byte spans remain valid as we apply
edits.sort(key=lambda e: e[1]['at_abs_start'], reverse=True)
print(f'Applying {len(edits)} LED position fixes...')

out = txt
for led, info, new_x, new_y, sw in edits:
    rot = info['rot']
    rot_str = f' {rot}' if rot is not None else ''
    new_at = f'(at {new_x:.4f} {new_y:.4f}{rot_str})'
    out = out[:info['at_abs_start']] + new_at + out[info['at_abs_end']:]
    print(f'  {led}: ({info["x"]:.4f},{info["y"]:.4f}) -> ({new_x:.4f},{new_y:.4f})  [under {sw}]')

with open(PCB, 'w', encoding='utf-8') as f:
    f.write(out)
print(f'\nWrote {PCB}')
