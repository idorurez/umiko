"""Generate plate cutout artifacts from the current PCB switch positions
WITHOUT modifying the source PCB.

The source PCB (umiko.kicad_pcb) is opened read-only. All transforms
happen on an in-memory copy, which is written to a single temporary PCB
file that kicad-cli reads to produce the two artifacts:

  cad/umiko-plate-cutouts.dxf   board outline + per-key plate cutouts
  cad/umiko-plate.step          3D solid of the plate

The temp file is deleted at the end. The source PCB is never touched.

Cutout geometry:
  switch opening: 14 x 14 mm (MX standard; KS-33 is MX-compatible)
  stab cutout (Choc V2 2u): verbatim from keebio/kb-plategen
    Body A 5.95x7.95 @ (+/-12, 0.3441); neck B 4.55x6.25 @ (+/-12, 6.7559);
    wire 24x1.4 @ (0, 8.2809); unioned into one outline; r=0.5
  SW_30/SW_35 are the two bottom-edge keys -> wire points NORTH (off the edge);
  all other stab keys -> wire points SOUTH.
"""
import os
import re
import uuid
import subprocess
from shapely.geometry import box
from shapely.ops import unary_union as _unary_union


def unary_union(polys):
    """Wrapper around shapely.ops.unary_union that falls back to iterative
    union if shapely's numpy-based version hits a dtype error (shapely 2.0.4
    + newer numpy bug)."""
    try:
        return _unary_union(polys)
    except TypeError:
        polys = list(polys)
        result = polys[0]
        for p in polys[1:]:
            result = result.union(p)
        return result

PROJECT = r'C:\Users\neuro\dev\keyboard\umiko'
PCB = os.path.join(PROJECT, 'umiko.kicad_pcb')
CAD = os.path.join(PROJECT, 'cad')
OUT_DXF = os.path.join(CAD, 'umiko-plate-cutouts.dxf')
OUT_STEP = os.path.join(CAD, 'umiko-plate.step')
OUT_DXF_SW = os.path.join(CAD, 'umiko-switches-only.dxf')
OUT_STEP_SW = os.path.join(CAD, 'umiko-switches-only.step')
TEMP_PCB = os.path.join(PROJECT, '_plate_temp.kicad_pcb')
GEN_STEP = True
PLATE_THICKNESS = 1.2   # mm — Choc V2 stab spec
KICAD_CLI = os.environ.get('KICAD_CLI', r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe')

LAYER = 'Eco1.User'
R = 0.5
SWITCH_W, SWITCH_H = 14.0, 14.0
# Switches-only alt output: wider east-west for Kailh clip clearance, tight N/S.
# Overridable via CLI arg: python scripts/make_plate.py 14.6 14.0
SWITCH_W_ALT, SWITCH_H_ALT = 14.2, 14.0
NORTH_REFS = {'SW_30', 'SW_35'}


def rrect(cx, cy, w, h, r=R):
    inner = box(cx - w/2 + r, cy - h/2 + r, cx + w/2 - r, cy + h/2 - r)
    return inner.buffer(r, quad_segs=8, join_style=1)


def switch_cutout():
    return box(-SWITCH_W/2, -SWITCH_H/2, SWITCH_W/2, SWITCH_H/2)


def switch_cutout_alt(w=None, h=None):
    """Switch cutout for the switches-only alt output. Defaults to
    SWITCH_W_ALT x SWITCH_H_ALT (14.2 x 14 for Kailh clip clearance).
    Override w and h to generate any size."""
    if w is None:
        w = SWITCH_W_ALT
    if h is None:
        h = SWITCH_H_ALT
    return box(-w/2, -h/2, w/2, h/2)


def stab_cutout(flip=False):
    s = -1.0 if flip else 1.0
    parts = []
    for cx in (-12.0, 12.0):
        parts.append(rrect(cx, s*0.3441, 5.95, 7.95))
        parts.append(rrect(cx, s*6.7559, 4.55, 6.25))
    parts.append(rrect(0.0, s*8.2809, 24.0, 1.4))
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
    """Remove any fp_poly blocks already on LAYER (so we don't end up with
    duplicates from a previously-injected PCB)."""
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
        bp = s
        while bp > 0 and text[bp-1] in '\t ':
            bp -= 1
        if bp > 0 and text[bp-1] == '\n':
            bp -= 1
        text = text[:bp] + text[e:]
        removed += 1
    return text, removed


def inject_cutouts(pcb, switches_only=False, alt_w=None, alt_h=None):
    """In-memory: strip any existing Eco1.User polys, then inject fresh
    cutouts into every switch footprint at its current position.

    When switches_only=True: inject ONLY the switch opening (default
    14.2 x 14 mm, the Kailh-clip-clearance variant), no stab cutouts.
    Override alt_w/alt_h to generate a different cutout size.
    """
    pcb, removed = strip_existing(pcb)
    if removed:
        print(f'(in-memory) stripped {removed} pre-existing {LAYER} polys')
    if switches_only:
        sw_shape = switch_cutout_alt(alt_w, alt_h)
        stab_shape = None
    else:
        sw_shape = switch_cutout()
        stab_shape = {False: stab_cutout(False), True: stab_cutout(True)}
    spans = []
    for m in re.finditer(r'\n\t\(footprint "([^"]+)"', pcb):
        fp_open = m.start() + 1
        fp_end = match_paren(pcb, fp_open)
        head = pcb[fp_open:fp_open + 1600]
        rm = re.search(r'\(property "Reference" "(SW_\d+)"', head)
        if rm:
            spans.append((fp_open, fp_end, '_stabilized' in m.group(1), rm.group(1)))
    n_stab = sum(1 for t in spans if t[2])
    if switches_only:
        print(f'switch footprints: {len(spans)} (switches-only mode — no stab cutouts)')
    else:
        print(f'switch footprints: {len(spans)} (stabilized: {n_stab})')
        print(f'north-facing stabs: {sorted(NORTH_REFS)}')
    assert len(spans) == 63 and n_stab == 6
    inj = 0
    for fp_open, fp_end, is_stab, ref in sorted(spans, key=lambda s: s[0], reverse=True):
        span = pcb[fp_open:fp_end]
        ef = span.rfind('(embedded_fonts')
        ins = (fp_open + ef + span[ef:].index(')') + 1) if ef != -1 else fp_end - 1
        block = fp_poly_blocks(sw_shape)
        if is_stab and not switches_only:
            flip = ref not in NORTH_REFS
            block += '\n' + fp_poly_blocks(stab_shape[flip])
        pcb = pcb[:ins] + '\n' + block + pcb[ins:]
        inj += 1
    print(f'(in-memory) injected plate cutouts into {inj} footprints')
    return pcb


def transform_for_step(pcb):
    """In-memory: take a PCB with Eco1.User cutouts and reduce it to a
    plate-shaped temp board for the STEP exporter. Strip Edge.Cuts fp_*
    polys (LED windows), promote Eco1.User -> Edge.Cuts so the cutouts
    become holes in the solid, strip pads/vias (no drilled holes in the
    plate), drop the 4-layer stackup, and set thickness to PLATE_THICKNESS
    (+ KiCad's known ~0.09 mm STEP undershoot)."""
    edits = []
    for m in re.finditer(r'\(fp_(?:line|arc|rect|poly)\b', pcb):
        s = m.start(); e = match_paren(pcb, s); blk = pcb[s:e]
        if '(layer "Edge.Cuts")' in blk:
            edits.append((s, e, None))
        elif '(layer "Eco1.User")' in blk:
            edits.append((s, e, blk.replace('(layer "Eco1.User")', '(layer "Edge.Cuts")', 1)))
    for m in re.finditer(r'\((?:pad|via)\b', pcb):
        s = m.start(); edits.append((s, match_paren(pcb, s), None))
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
    return t


def clean_dxf(path, layers=('User.Eco1',)):
    """Strip through-hole CIRCLE artifacts from the cut layer (KiCad plots
    drill holes on every layer; the plate doesn't have them)."""
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


def run_cli(args, label):
    r = subprocess.run(args, capture_output=True, text=True)
    tail = (r.stdout + r.stderr).strip().splitlines()
    print(f'{label}: {tail[-1] if tail else r.returncode}')
    if r.returncode != 0:
        print(r.stderr[:600])


def main():
    # CLI: optional [alt_width alt_height] positional args override the
    # switches-only cutout size. Default is 14.2 x 14. Example:
    #   python scripts/make_plate.py            → alt is 14.2 x 14
    #   python scripts/make_plate.py 14.6 14.0  → alt is 14.6 x 14, filename
    #                                             becomes umiko-switches-only-14.6x14.step
    import sys
    alt_w, alt_h = SWITCH_W_ALT, SWITCH_H_ALT
    if len(sys.argv) >= 3:
        alt_w, alt_h = float(sys.argv[1]), float(sys.argv[2])
    # Alt output filenames encode the size if overridden from default
    if (alt_w, alt_h) == (SWITCH_W_ALT, SWITCH_H_ALT):
        out_dxf_sw, out_step_sw = OUT_DXF_SW, OUT_STEP_SW
    else:
        base = f'umiko-switches-only-{alt_w:g}x{alt_h:g}'
        out_dxf_sw = os.path.join(CAD, base + '.dxf')
        out_step_sw = os.path.join(CAD, base + '.step')

    print('Reading source PCB (read-only; the source will not be modified)...')
    with open(PCB, encoding='utf-8') as f:
        source_pcb = f.read()

    # In-memory: inject plate cutouts at current footprint positions.
    cutouts_pcb = inject_cutouts(source_pcb)

    os.makedirs(CAD, exist_ok=True)

    # Write to temp; run DXF export against the temp.
    with open(TEMP_PCB, 'w', encoding='utf-8') as f:
        f.write(cutouts_pcb)
    run_cli([
        KICAD_CLI, 'pcb', 'export', 'dxf',
        '--output', OUT_DXF,
        '--layers', f'Edge.Cuts,{LAYER}',
        '--output-units', 'mm',
        '--mode-single',
        '--use-drill-origin',
        TEMP_PCB,
    ], 'DXF')
    removed = clean_dxf(OUT_DXF, layers=(LAYER.replace('Eco1.User', 'User.Eco1'),))
    print(f'cleaned {removed} hole-circles off the cut layer')
    if os.path.exists(OUT_DXF):
        print(f'wrote {OUT_DXF} ({os.path.getsize(OUT_DXF)/1024:.1f} KB)')

    if GEN_STEP:
        # In-memory: transform for STEP; overwrite temp with the plate-only form.
        step_pcb = transform_for_step(cutouts_pcb)
        with open(TEMP_PCB, 'w', encoding='utf-8') as f:
            f.write(step_pcb)
        run_cli([
            KICAD_CLI, 'pcb', 'export', 'step',
            '--output', OUT_STEP,
            '--board-only',
            '--drill-origin',
            TEMP_PCB,
        ], 'STEP')
        if os.path.exists(OUT_STEP):
            print(f'wrote {OUT_STEP} ({os.path.getsize(OUT_STEP)/1024:.1f} KB)')

    # ---- ALT output: switches-only plate at alt_w x alt_h, no stabs ----
    print()
    print(f'=== Switches-only alt output ({alt_w} x {alt_h} mm) ===')
    switches_pcb = inject_cutouts(source_pcb, switches_only=True, alt_w=alt_w, alt_h=alt_h)
    with open(TEMP_PCB, 'w', encoding='utf-8') as f:
        f.write(switches_pcb)
    run_cli([
        KICAD_CLI, 'pcb', 'export', 'dxf',
        '--output', out_dxf_sw,
        '--layers', f'Edge.Cuts,{LAYER}',
        '--output-units', 'mm',
        '--mode-single',
        '--use-drill-origin',
        TEMP_PCB,
    ], 'DXF (switches-only)')
    clean_dxf(out_dxf_sw, layers=(LAYER.replace('Eco1.User', 'User.Eco1'),))
    if os.path.exists(out_dxf_sw):
        print(f'wrote {out_dxf_sw} ({os.path.getsize(out_dxf_sw)/1024:.1f} KB)')

    if GEN_STEP:
        step_sw_pcb = transform_for_step(switches_pcb)
        with open(TEMP_PCB, 'w', encoding='utf-8') as f:
            f.write(step_sw_pcb)
        run_cli([
            KICAD_CLI, 'pcb', 'export', 'step',
            '--output', out_step_sw,
            '--board-only',
            '--drill-origin',
            TEMP_PCB,
        ], 'STEP (switches-only)')
        if os.path.exists(out_step_sw):
            print(f'wrote {out_step_sw} ({os.path.getsize(out_step_sw)/1024:.1f} KB)')

    # Clean up temp file.
    try:
        os.remove(TEMP_PCB)
    except OSError:
        pass
    print('done. source PCB untouched.')


if __name__ == '__main__':
    main()
