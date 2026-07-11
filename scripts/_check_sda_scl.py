"""Focused check on SDA_R and SCL_R routing.

For each net, list all pads, segments, vias in order and find the specific
disconnection point.
"""
import re
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

pcb = open('umiko.kicad_pcb', encoding='utf-8').read()


def match_close(text, op):
    d = 0; i = op
    while i < len(text):
        if text[i] == '(': d += 1
        elif text[i] == ')':
            d -= 1
            if d == 0:
                return i + 1
        i += 1


# Build net_number → net_name
net_number_to_name = {}
for m in re.finditer(r'\(net (\d+) "([^"]+)"\)', pcb):
    net_number_to_name[int(m.group(1))] = m.group(2)


def check_net(target_net):
    print('=' * 60)
    print(f'Net: {target_net}')
    print('=' * 60)

    # Segments on this net (by number lookup)
    segs = []
    for m in re.finditer(r'\(segment', pcb):
        ps = m.start()
        pe = match_close(pcb, ps)
        pb = pcb[ps:pe]
        nm = re.search(r'\(net "([^"]+)"\)', pb)
        if not nm or nm.group(1) != target_net:
            continue
        start = re.search(r'\(start ([\d.\-]+) ([\d.\-]+)\)', pb)
        end = re.search(r'\(end ([\d.\-]+) ([\d.\-]+)\)', pb)
        layer = re.search(r'\(layer "([^"]+)"', pb)
        if start and end and layer:
            segs.append((layer.group(1), (float(start.group(1)), float(start.group(2))), (float(end.group(1)), float(end.group(2)))))

    # Vias on this net
    vias = []
    for m in re.finditer(r'\(via', pcb):
        ps = m.start()
        pe = match_close(pcb, ps)
        pb = pcb[ps:pe]
        nm = re.search(r'\(net "([^"]+)"\)', pb)
        if not nm or nm.group(1) != target_net:
            continue
        at = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)\)', pb)
        if at:
            vias.append((float(at.group(1)), float(at.group(2))))

    print(f'Segments: {len(segs)}, Vias: {len(vias)}')
    print()
    print('Segments (grouped by layer):')
    by_layer = defaultdict(list)
    for layer, s, e in segs:
        by_layer[layer].append((s, e))
    for layer in sorted(by_layer):
        print(f'  {layer}:')
        for s, e in by_layer[layer]:
            print(f'    ({s[0]:.4f}, {s[1]:.4f}) -> ({e[0]:.4f}, {e[1]:.4f})')

    print(f'\nVias (F.Cu ↔ B.Cu):')
    for v in vias:
        print(f'  ({v[0]:.4f}, {v[1]:.4f})')

    # Find dangling endpoints: endpoints that only appear in ONE place
    # (not touching another segment or via on the same layer, and not
    # coincident with a via on any layer)
    print(f'\n--- Dangling endpoint analysis ---')
    tol = 0.05
    all_endpoints = []  # (position, layer, id)
    for i, (layer, s, e) in enumerate(segs):
        all_endpoints.append((s, layer, f'seg{i}_start'))
        all_endpoints.append((e, layer, f'seg{i}_end'))
    via_positions = {(round(v[0], 4), round(v[1], 4)): True for v in vias}

    def close(p1, p2):
        return abs(p1[0] - p2[0]) <= tol and abs(p1[1] - p2[1]) <= tol

    dangling = []
    for i, (pos, layer, id_) in enumerate(all_endpoints):
        # Check if this endpoint touches another endpoint on the same layer, OR
        # touches a via (via connects all layers)
        touches = 0
        for j, (pos2, layer2, id2) in enumerate(all_endpoints):
            if i == j:
                continue
            if close(pos, pos2):
                if layer == layer2 or layer2 == 'via':
                    touches += 1
        # Check vias
        for v in vias:
            if close(pos, v):
                touches += 1
        if touches == 0:
            dangling.append((pos, layer, id_))

    if dangling:
        print(f'⚠️  {len(dangling)} dangling endpoints (touch nothing else):')
        for pos, layer, id_ in dangling:
            print(f'    {id_} on {layer} at ({pos[0]:.4f}, {pos[1]:.4f})')
    else:
        print('✓ No dangling endpoints found')
    print()


check_net('SDA_R')
check_net('SCL_R')
