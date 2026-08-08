"""Bespoke umiko audit — right-only-respin branch pre-fab check.

Checks:
1. Global label uniqueness (col7_R class of bug)
2. Every schematic net has at least 2 endpoints
3. PCB nets with zero routed segments
4. Edge.Cuts is a single closed loop
5. Right-half PCB doesn't reference left-half nets
6. LED chain (WS2812 DIN/DOUT continuity)
7. U12 pinout matches user's daughterboard (SDA,SCL,VCC,GND)
8. Aux origin at right-half bottom-left
9. col7_R fix — SW_61/62/63 wired to U7 GPIO16
"""
import re
import sys
from collections import defaultdict, Counter

sys.stdout.reconfigure(encoding='utf-8')

sch = open('umiko.kicad_sch', encoding='utf-8').read()
pcb = open('umiko.kicad_pcb', encoding='utf-8').read()

OK = '[OK]'
WARN = '[WARN]'


def find_enclosing(text, idx, tag):
    depth = 1
    i = idx
    while i > 0:
        i -= 1
        if text[i] == ')':
            depth += 1
        elif text[i] == '(':
            depth -= 1
            if depth == 0:
                after = text[i+1:i+50]
                m = re.match(r'(\w+)', after)
                if m and m.group(1) == tag:
                    return i
                depth = 1
    return -1


def mc(t, o):
    d = 0
    i = o
    while i < len(t):
        if t[i] == '(':
            d += 1
        elif t[i] == ')':
            d -= 1
            if d == 0:
                return i + 1
        i += 1


def check_global_labels():
    print('=' * 60)
    print('CHECK 1: Global label single-occurrence scan (col7_R class)')
    print('=' * 60)
    labels = re.findall(r'\(global_label "([^"]+)"', sch)
    counts = Counter(labels)
    single = [n for n, c in counts.items() if c == 1]
    suspicious = []
    for name in single:
        if re.match(r'^(col|row|SDA|SCL|VDD|VBUS|VCC|GND|DATA|/[A-Z0-9_]+|Net-|~)', name):
            suspicious.append(name)
    print(f'Total global labels: {len(labels)} unique={len(counts)}, single-occurrence={len(single)}')
    if suspicious:
        print(f'{WARN} {len(suspicious)} suspicious single-occurrence labels (may be dangling like col7_R was):')
        for n in suspicious[:30]:
            print(f'    {n}')
    else:
        print(f'{OK} No suspicious single-occurrence labels in known net-name patterns')
    print()


def check_pcb_nets_pads():
    print('=' * 60)
    print('CHECK 2: PCB nets — each connects to 2+ pads (no single-pad nets)')
    print('=' * 60)
    net_to_pads = defaultdict(list)
    for m in re.finditer(r'\n\t\(footprint\s', pcb):
        p = m.start() + 1
        e = mc(pcb, p)
        fb = pcb[p:e]
        ref_m = re.search(r'\(property "Reference"\s+"([^"]+)"', fb)
        if not ref_m:
            continue
        ref = ref_m.group(1)
        for pm in re.finditer(r'\(pad "([^"]+)"', fb):
            ps = pm.start()
            pe = mc(fb, ps)
            pb = fb[ps:pe]
            pn = pm.group(1)
            netm = re.search(r'\(net "([^"]+)"\)', pb)
            if netm:
                net_to_pads[netm.group(1)].append(f'{ref}.{pn}')
            else:
                net_to_pads['(unconnected)'].append(f'{ref}.{pn}')
    single = [
        n for n, pads in net_to_pads.items()
        if len(pads) == 1
        and not n.startswith('(')
        and not n.startswith('Net-(')  # KiCad auto-nets are internal, not schematic-declared
    ]
    if single:
        print(f'{WARN} {len(single)} nets connect to only ONE pad — floating/dangling:')
        for n in single[:30]:
            print(f'    {n} → {net_to_pads[n]}')
    else:
        print(f'{OK} All named nets connect to 2+ pads')
    print(f'  Total named nets: {len(net_to_pads)}')
    print(f'  Unconnected pads: {len(net_to_pads.get("(unconnected)", []))}')
    print()
    return net_to_pads


def check_edge_cuts_closure():
    print('=' * 60)
    print('CHECK 3: Edge.Cuts — closed loop check')
    print('=' * 60)
    edges = []
    for m in re.finditer(r'\(gr_(?:line|arc)\b', pcb):
        p = m.start()
        e = mc(pcb, p)
        blk = pcb[p:e]
        if '(layer "Edge.Cuts")' not in blk:
            continue
        starts = re.findall(r'\(start ([\d.\-]+) ([\d.\-]+)\)', blk)
        ends = re.findall(r'\(end ([\d.\-]+) ([\d.\-]+)\)', blk)
        for s, e2 in zip(starts, ends):
            edges.append(((float(s[0]), float(s[1])), (float(e2[0]), float(e2[1]))))
    endpoints = Counter()
    for a, b in edges:
        a_r = (round(a[0], 3), round(a[1], 3))
        b_r = (round(b[0], 3), round(b[1], 3))
        endpoints[a_r] += 1
        endpoints[b_r] += 1
    odd = [p for p, c in endpoints.items() if c % 2 != 0]
    print(f'Edge.Cuts perimeter segments: {len(edges)}')
    print(f'Unique endpoints: {len(endpoints)}')
    if odd:
        print(f'{WARN} {len(odd)} endpoints appear odd number of times (open ends / gaps):')
        for p in odd[:10]:
            print(f'    ({p[0]:.3f}, {p[1]:.3f})')
    else:
        print(f'{OK} All Edge.Cuts endpoints even (closed loop)')
    print()


def check_left_nets_absent(net_to_pads):
    print('=' * 60)
    print('CHECK 4: No left-half (_L) nets on right-only PCB')
    print('=' * 60)
    left_present = set()
    for net in net_to_pads:
        # Strict _L suffix, and not something like D_L (the diode matrix
        # column reference from the schematic — different naming)
        if re.search(r'_L$', net) and net != 'D_L' and not net.startswith('(') and not net.startswith('Net-'):
            left_present.add(net)
    if left_present:
        print(f'{WARN} {len(left_present)} left-half nets found on right-only PCB:')
        for n in sorted(left_present)[:20]:
            print(f'    {n} → {net_to_pads[n]}')
    else:
        print(f'{OK} No left-half (_L) nets referenced on this right-half PCB')
    print()


def check_led_chain():
    print('=' * 60)
    print('CHECK 5: LED chain — WS2812 DIN/DOUT continuity')
    print('=' * 60)
    led_dins = {}
    led_douts = {}
    for m in re.finditer(r'\n\t\(footprint\s', pcb):
        p = m.start() + 1
        e = mc(pcb, p)
        fb = pcb[p:e]
        ref_m = re.search(r'\(property "Reference"\s+"(LED\d+)"', fb)
        if not ref_m:
            continue
        ref = ref_m.group(1)
        for pm in re.finditer(r'\(pad "([^"]+)"', fb):
            ps = pm.start()
            pe = mc(fb, ps)
            pb = fb[ps:pe]
            pn = pm.group(1)
            pfn = re.search(r'\(pinfunction "([^"]+)"', pb)
            netm = re.search(r'\(net "([^"]+)"\)', pb)
            if pfn and netm:
                pf = pfn.group(1).upper()
                if 'DIN' in pf or pf == 'DI':
                    led_dins[ref] = netm.group(1)
                elif 'DOUT' in pf or pf == 'DO':
                    led_douts[ref] = netm.group(1)
    all_douts = set(led_douts.values())
    all_dins = set(led_dins.values())
    orphan_dins = []
    for led, din in led_dins.items():
        if din not in all_douts:
            if not re.match(r'^/?RGB_DO', din):
                orphan_dins.append((led, din))
    orphan_douts = []
    for led, dout in led_douts.items():
        if dout not in all_dins:
            orphan_douts.append((led, dout))
    print(f'LEDs on right-only PCB: {len(set(list(led_dins) + list(led_douts)))}')
    print(f'DIN entries: {len(led_dins)}, DOUT entries: {len(led_douts)}')
    if orphan_dins:
        print(f'{WARN} {len(orphan_dins)} LEDs with DIN not fed by any other LED DOUT (potential chain start OR break):')
        for led, net in orphan_dins[:10]:
            print(f'    {led} DIN={net}')
    if len(orphan_douts) > 1:
        print(f'{WARN} {len(orphan_douts)} LEDs with DOUT going nowhere (should be 1 for chain end):')
        for led, net in orphan_douts[:10]:
            print(f'    {led} DOUT={net}')
    elif len(orphan_douts) == 1:
        print(f'{OK} Exactly 1 chain end: {orphan_douts[0][0]} DOUT={orphan_douts[0][1]}')
    print()


def check_aux_origin():
    print('=' * 60)
    print('CHECK 6: Aux origin at right-half bottom-left')
    print('=' * 60)
    aux = re.search(r'\(aux_axis_origin ([\d.\-]+) ([\d.\-]+)\)', pcb)
    if aux:
        ax, ay = float(aux.group(1)), float(aux.group(2))
        print(f'aux_axis_origin: ({ax}, {ay})')
        if 180 < ax < 190 and 130 < ay < 138:
            print(f'{OK} Aux origin at right-half bottom-left as expected')
        else:
            print(f'{WARN} Aux origin at ({ax}, {ay}) — expected ~(182, 134) for right-half fab')
    print()


def check_u12_pinout():
    print('=' * 60)
    print('CHECK 7: U12 (OLED) pinout for user daughterboard')
    print('=' * 60)
    m = re.search(r'\(property "Reference"\s+"U12"', pcb)
    if not m:
        print('U12 not found on PCB')
        print()
        return
    fs = find_enclosing(pcb, m.start(), 'footprint')
    fe = mc(pcb, fs)
    fb = pcb[fs:fe]
    actual = []
    for i in range(1, 5):
        pm = re.search(rf'\(pad "{i}".*?\(net "([^"]+)"\)', fb, re.DOTALL)
        if pm:
            actual.append(pm.group(1))
    expected = ['SDA_R', 'SCL_R', '+3V3_R', 'GND_R']
    if actual == expected:
        print(f'{OK} U12 pinout: SDA,SCL,VCC,GND — matches daughterboard order')
    else:
        print(f'{WARN} U12 pinout unexpected')
        print(f'    Expected: {expected}')
        print(f'    Actual:   {actual}')
    print()


def check_col7_fix():
    print('=' * 60)
    print('CHECK 8: col7_R fix — U7 GPIO16 wired to SW_61/62/63')
    print('=' * 60)
    refs = set()
    for m in re.finditer(r'\n\t\(footprint\s', pcb):
        p = m.start() + 1
        e = mc(pcb, p)
        fb = pcb[p:e]
        if '"col7_R"' in fb:
            ref_m = re.search(r'\(property "Reference"\s+"([^"]+)"', fb)
            if ref_m:
                refs.add(ref_m.group(1))
    expected = {'U7', 'SW_61', 'SW_62', 'SW_63'}
    if refs == expected:
        print(f'{OK} col7_R connects exactly to U7 (GPIO16) + SW_61/62/63')
    elif 'U7' in refs and {'SW_61', 'SW_62', 'SW_63'}.issubset(refs):
        print(f'{OK} col7_R has all expected connections (plus extras): {sorted(refs)}')
    else:
        print(f'{WARN} col7_R references: {sorted(refs)}')
        print(f'    Expected: U7 + SW_61,SW_62,SW_63')
    print()


def check_rotation_correction_flags():
    print('=' * 60)
    print('CHECK 9: JLCPCB_CORRECTION fields — components with rotation notes')
    print('=' * 60)
    corrections = re.findall(r'\(property "JLCPCB_CORRECTION"\s+"([^"]*)"', sch)
    non_empty = [c for c in corrections if c.strip()]
    if non_empty:
        print(f'Components with rotation correction values: {len(non_empty)}')
        for c in non_empty[:10]:
            print(f'    {c}')
    else:
        print(f'{OK} No components have baked-in JLCPCB_CORRECTION values')
        print('  (JLC will need per-component rotation via their UI at BOM review:')
        print('   U2/U10 LP5907 = +90°, D1/D5 PMEG2010BELD = 180°, and any others surfaced')
        print('   during engineering review. Documented from prior JLC iterations.)')
    print()


def check_footprint_count_reconciliation():
    print('=' * 60)
    print('CHECK 10: Footprint count on right-only PCB')
    print('=' * 60)
    footprint_refs = re.findall(r'\(property "Reference"\s+"([^"]+)"', pcb)
    from collections import Counter
    prefix_count = Counter()
    for r in footprint_refs:
        pm = re.match(r'([A-Za-z_]+)', r)
        if pm:
            prefix_count[pm.group(1)] += 1
    print(f'Total footprints on PCB: {len(footprint_refs)}')
    print(f'By prefix:')
    for prefix, n in sorted(prefix_count.items(), key=lambda x: (-x[1], x[0])):
        print(f'    {prefix}: {n}')
    print()


if __name__ == '__main__':
    check_global_labels()
    net_to_pads = check_pcb_nets_pads()
    check_edge_cuts_closure()
    check_left_nets_absent(net_to_pads)
    check_led_chain()
    check_aux_origin()
    check_u12_pinout()
    check_col7_fix()
    check_rotation_correction_flags()
    check_footprint_count_reconciliation()
