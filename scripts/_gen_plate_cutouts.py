"""Generate a complete plate cutout layer (switch openings + Choc V2 stab cutouts)
on Eco1.User INSIDE the real umiko.kicad_pcb, then export it (+ board outline)
to cad/umiko-plate-cutouts.dxf.

Putting the geometry on Eco1.User (a non-fab user layer) means:
  - you can SEE the plate in KiCad: enable "User.Eco1" in the Appearance panel
  - it does NOT affect PCB fabrication (Eco1.User is not a manufacturing layer)
  - it is bound to each footprint, so it moves/rotates with the switches
  - it is fully reversible (re-run strips+rebuilds; or delete the layer)

Switch opening: 14 x 14 mm (MX standard; KS-33 is MX-compatible), r=0.5.
Stab cutout (Choc V2 2u): verbatim from keebio/kb-plategen StabilizerCutout.ts
  (cutoutChocV2 + cutoutChocV2Wire), Y negated for KiCad's Y-down footprint frame.
  Body A 5.95x7.95 @ (+/-12, 0.3441); neck B 4.55x6.25 @ (+/-12, 6.7559);
  wire 24x1.4 @ (0, 8.2809); unioned into one outline; r=0.5.

Toggles below: SWITCH_W/H, and FLIP_STAB (negate Y if the wire/neck points the
wrong way relative to the keycaps when you eyeball it).
"""
import os
import re
import uuid
import shutil
import subprocess
from shapely.geometry import box
from shapely.ops import unary_union

PROJECT = r'C:\Users\neuro\dev\keyboard\umiko'
PCB = os.path.join(PROJECT, 'umiko.kicad_pcb')
BAK = PCB + '.bak_platecuts'
CAD = os.path.join(PROJECT, 'cad')
OUT = os.path.join(CAD, 'umiko-plate-cutouts.dxf')
PLATE_STEP = os.path.join(CAD, 'umiko-plate.step')
TEMP_PCB = os.path.join(PROJECT, '_plate_step_temp.kicad_pcb')
GEN_STEP = True
PLATE_THICKNESS = 1.2   # mm — Choc V2 stab spec (Keebio); KS-33 clips tolerate it. Change to dial the sweet spot.
KICAD_CLI = os.environ.get('KICAD_CLI', r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe')

LAYER = 'Eco1.User'
R = 0.5
SWITCH_W, SWITCH_H = 14.0, 14.0   # 14.2 x 14.0 for Keebio "Choc V2" switch cutout
# Per-key stab orientation. Verified against KiCad: flip=False -> wire NORTH,
# flip=True -> wire SOUTH (after each footprint's rot=180 + B.Cu mirror).
# SW_30/SW_35 are the two bottom-edge keys -> NORTH (wire inward, off the edge);
# all other stab keys -> SOUTH.
NORTH_REFS = {'SW_30', 'SW_35'}

def rrect(cx, cy, w, h, r=R):
    inner = box(cx - w/2 + r, cy - h/2 + r, cx + w/2 - r, cy + h/2 - r)
    return inner.buffer(r, quad_segs=8, join_style=1)

def switch_cutout():
    # sharp 14x14, matching the KS-33 footprint's Dwgs.User cutout (corners at +/-7)
    return box(-SWITCH_W/2, -SWITCH_H/2, SWITCH_W/2, SWITCH_H/2)

def stab_cutout(flip=False):
    s = -1.0 if flip else 1.0
    parts = []
    for cx in (-12.0, 12.0):
        parts.append(rrect(cx, s*0.3441, 5.95, 7.95))   # body A
        parts.append(rrect(cx, s*6.7559, 4.55, 6.25))   # neck B
    parts.append(rrect(0.0, s*8.2809, 24.0, 1.4))       # wire slot
    return unary_union(parts).simplify(0.005, preserve_topology=True)

def fp_poly_blocks(geom):
    polys = list(geom.geoms) if geom.geom_type == 'MultiPolygon' else [geom]
    out = []
    for p in polys:
        pts = ' '.join(f'(xy {x:.4f} {y:.4f})' for x, y in p.exterior.coords[:-1])
        out.append(
            f'\t\t\t(fp_poly\n\t\t\t\t(pts {pts})\n'
            f'\t\t\t\t(stroke\n\t\t\t\t\t(width 0.1)\n\t\t\t\t\t(type solid)\n\t\t\t\t)\n'
            f'\t\t\t\t(fill no)\n\t\t\t\t(layer "{LAYER}")\n\t\t\t\t(uuid "{uuid.uuid4()}")\n\t\t\t)'
        )
    return '\n'.join(out)

def match_paren(text, open_pos):
    depth = 0
    i = open_pos
    while i < len(text):
        c = text[i]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError('unbalanced')

def strip_existing(text):
    """Remove any fp_poly blocks already on LAYER (idempotent re-runs)."""
    removed = 0
    while True:
        hit = None
        for m in re.finditer(r'\(fp_poly\b', text):
            end = match_paren(text, m.start())
            if f'(layer "{LAYER}")' in text[m.start():end]:
                hit = (m.start(), end); break
        if not hit:
            break
        s, e = hit
        # swallow leading whitespace + newline
        bp = s
        while bp > 0 and text[bp-1] in '\t ':
            bp -= 1
        if bp > 0 and text[bp-1] == '\n':
            bp -= 1
        text = text[:bp] + text[e:]
        removed += 1
    return text, removed

def main():
    if not os.path.exists(BAK):
        shutil.copy(PCB, BAK)
        print(f'backup -> {os.path.basename(BAK)}')
    with open(PCB, encoding='utf-8') as f:
        pcb = f.read()

    pcb, removed = strip_existing(pcb)
    if removed:
        print(f'stripped {removed} pre-existing {LAYER} polys')

    # Shapes computed once; fp_poly text (with fresh UUIDs) generated per footprint.
    sw_shape = switch_cutout()
    stab_shape = {False: stab_cutout(False), True: stab_cutout(True)}

    # find every footprint with Reference SW_<n>; note which are stabilized + ref
    spans = []  # (fp_open, fp_end, is_stab, ref)
    for m in re.finditer(r'\n\t\(footprint "([^"]+)"', pcb):
        fp_open = m.start() + 1
        fp_end = match_paren(pcb, fp_open)
        head = pcb[fp_open:fp_open + 1600]
        rm = re.search(r'\(property "Reference" "(SW_\d+)"', head)
        if rm:
            spans.append((fp_open, fp_end, '_stabilized' in m.group(1), rm.group(1)))
    n_stab = sum(1 for t in spans if t[2])
    print(f'switch footprints: {len(spans)} (stabilized: {n_stab})')
    print(f'north-facing stabs: {sorted(NORTH_REFS)}')
    assert len(spans) == 63 and n_stab == 5

    inj = 0
    for fp_open, fp_end, is_stab, ref in sorted(spans, key=lambda s: s[0], reverse=True):
        span = pcb[fp_open:fp_end]
        ef = span.rfind('(embedded_fonts')
        ins = (fp_open + ef + span[ef:].index(')') + 1) if ef != -1 else fp_end - 1
        block = fp_poly_blocks(sw_shape)               # fresh UUIDs per switch opening
        if is_stab:
            flip = ref not in NORTH_REFS               # north -> flip=False, south -> flip=True
            block += '\n' + fp_poly_blocks(stab_shape[flip])
        pcb = pcb[:ins] + '\n' + block + pcb[ins:]
        inj += 1
    print(f'injected plate cutouts into {inj} footprints')

    with open(PCB, 'w', encoding='utf-8') as f:
        f.write(pcb)

    os.makedirs(CAD, exist_ok=True)
    r = subprocess.run([
        KICAD_CLI, 'pcb', 'export', 'dxf',
        '--output', OUT,
        '--layers', f'Edge.Cuts,{LAYER}',
        '--output-units', 'mm',
        '--mode-single',
        '--use-drill-origin',
        PCB,
    ], capture_output=True, text=True)
    tail = (r.stdout + r.stderr).strip().splitlines()
    print('kicad-cli:', tail[-1] if tail else r.returncode)
    if r.returncode != 0:
        print(r.stderr)

    # Strip through-hole CIRCLE artifacts from the cut layer (KiCad plots holes on
    # every layer; the plate doesn't have switch post/leg holes).
    removed = clean_dxf(OUT, layers=(LAYER.replace('Eco1.User', 'User.Eco1'),))
    print(f'cleaned {removed} hole-circles off the cut layer')
    print(f'wrote {OUT} ({os.path.getsize(OUT)/1024:.1f} KB)' if os.path.exists(OUT) else 'NO OUTPUT')

    if GEN_STEP:
        gen_plate_step(pcb)

def gen_plate_step(pcb):
    """Build a temp board containing only the perimeter + plate cutouts (LED
    windows, pads, vias stripped) and export a clean 3D plate solid via KiCad's
    STEP exporter, in the same coordinate frame as the other STEP exports."""
    edits = []  # (start, end, replacement_or_None)
    for m in re.finditer(r'\(fp_(?:line|arc|rect|poly)\b', pcb):
        s = m.start(); e = match_paren(pcb, s); blk = pcb[s:e]
        if '(layer "Edge.Cuts")' in blk:
            edits.append((s, e, None))                              # strip LED windows / old PCB cutouts
        elif '(layer "Eco1.User")' in blk:
            edits.append((s, e, blk.replace('(layer "Eco1.User")', '(layer "Edge.Cuts")', 1)))  # promote my cutouts
    for m in re.finditer(r'\((?:pad|via)\b', pcb):
        s = m.start(); edits.append((s, match_paren(pcb, s), None))  # strip -> no drilled holes
    edits.sort(key=lambda x: x[0], reverse=True)
    t = pcb
    for s, e, rep in edits:
        if rep is None:
            bp = s
            while bp > 0 and t[bp-1] in '\t ':
                bp -= 1
            if bp > 0 and t[bp-1] == '\n':
                bp -= 1
            t = t[:bp] + t[e:]
        else:
            t = t[:s] + rep + t[e:]
    # A plate is a homogeneous 1.2mm sheet, not the PCB's 4-layer stackup:
    # drop the stackup and set the board thickness to 1.2mm for the export.
    # KiCad's STEP body renders ~0.09mm thinner than nominal, so bump the nominal
    # to land the solid at PLATE_THICKNESS.
    nominal = round(PLATE_THICKNESS + 0.09, 3)
    t = t.replace('(thickness 1.6)', f'(thickness {nominal})', 1)
    si = t.find('(stackup')
    if si != -1:
        se = match_paren(t, si)
        bp = si
        while bp > 0 and t[bp-1] in '\t ':
            bp -= 1
        if bp > 0 and t[bp-1] == '\n':
            bp -= 1
        t = t[:bp] + t[se:]
    with open(TEMP_PCB, 'w', encoding='utf-8') as f:
        f.write(t)
    r = subprocess.run([KICAD_CLI, 'pcb', 'export', 'step', '--output', PLATE_STEP,
                        '--board-only', '--drill-origin', TEMP_PCB],
                       capture_output=True, text=True)
    tail = (r.stdout + r.stderr).strip().splitlines()
    print('plate STEP:', tail[-1] if tail else r.returncode)
    if r.returncode != 0:
        print(r.stderr[:600])
    try:
        os.remove(TEMP_PCB)
    except OSError:
        pass
    if os.path.exists(PLATE_STEP):
        print(f'wrote {PLATE_STEP} ({os.path.getsize(PLATE_STEP)/1024:.1f} KB)')

def clean_dxf(path, layers=('User.Eco1',)):
    toks = open(path, encoding='utf-8', errors='ignore').read().split('\n')
    pairs = [(toks[i], toks[i+1]) for i in range(0, len(toks)-1, 2)]
    chunks, cur = [], []
    for c, v in pairs:
        if c.strip() == '0' and cur:
            chunks.append(cur); cur = []
        cur.append((c, v))
    if cur:
        chunks.append(cur)
    kept, removed = [], 0
    for ch in chunks:
        is_circle = ch and ch[0][0].strip() == '0' and ch[0][1].strip() == 'CIRCLE'
        if is_circle:
            lay = next((v.strip() for c, v in ch if c.strip() == '8'), None)
            if lay in layers:
                removed += 1
                continue
        kept.append(ch)
    out = []
    for ch in kept:
        for c, v in ch:
            out.append(c); out.append(v)
    open(path, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    return removed

if __name__ == '__main__':
    main()
