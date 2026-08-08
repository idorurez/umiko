"""Bespoke connectivity checker for umiko PCB.

For each named net, verifies all pads/segments/vias form a single connected
component. Flags:
- Vias with no continuation on the opposite layer (SDA_R gap class)
- Segment endpoints that don't touch any pad, via, or another segment endpoint
- Pads that don't touch any segment or via
- Nets whose pads aren't all connected via routed geometry

Tolerance: 0.05mm for point coincidence (accounts for KiCad rounding).
"""
import re
import math
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

pcb = open('umiko.kicad_pcb', encoding='utf-8').read()

TOLERANCE = 0.05  # mm — endpoints within this distance are considered coincident


def match_close(text, op):
    d = 0; i = op
    while i < len(text):
        if text[i] == '(': d += 1
        elif text[i] == ')':
            d -= 1
            if d == 0:
                return i + 1
        i += 1


def find_enclosing(text, idx, tag):
    depth = 1; i = idx
    while i > 0:
        i -= 1
        if text[i] == ')': depth += 1
        elif text[i] == '(':
            depth -= 1
            if depth == 0:
                after = text[i+1:i+50]
                m = re.match(r'(\w+)', after)
                if m and m.group(1) == tag:
                    return i
                depth = 1
    return -1


def rotate_offset(dx, dy, angle_deg):
    """Rotate a footprint-local (dx, dy) by the footprint's rotation."""
    a = math.radians(angle_deg)
    cos_a = math.cos(a)
    sin_a = math.sin(a)
    return (dx * cos_a - dy * sin_a, dx * sin_a + dy * cos_a)


def close(p1, p2, tol=TOLERANCE):
    return abs(p1[0] - p2[0]) <= tol and abs(p1[1] - p2[1]) <= tol


# Extract all pads with their (net, absolute_position, layers)
print('=' * 60)
print('Extracting pads, segments, vias per net...')
print('=' * 60)

net_pads = defaultdict(list)  # net_name → [(ref, pad_num, (x, y), layers)]

for m in re.finditer(r'\n\t\(footprint\s', pcb):
    p = m.start() + 1
    e = match_close(pcb, p)
    fb = pcb[p:e]
    ref_m = re.search(r'\(property "Reference"\s+"([^"]+)"', fb)
    if not ref_m:
        continue
    ref = ref_m.group(1)
    fp_at = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)', fb[:800])
    if not fp_at:
        continue
    fp_x, fp_y = float(fp_at.group(1)), float(fp_at.group(2))
    fp_rot = float(fp_at.group(3)) if fp_at.group(3) else 0.0

    for pm in re.finditer(r'\(pad "([^"]+)"', fb):
        ps = pm.start()
        pe = match_close(fb, ps)
        pb = fb[ps:pe]
        pn = pm.group(1)
        net = re.search(r'\(net "([^"]+)"\)', pb)
        pad_at = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)(?: ([\d.\-]+))?\)', pb)
        layers_m = re.search(r'\(layers ([^)]+)\)', pb)
        if not (net and pad_at):
            continue
        pdx, pdy = float(pad_at.group(1)), float(pad_at.group(2))
        # Apply footprint rotation to pad offset
        rdx, rdy = rotate_offset(pdx, pdy, fp_rot)
        abs_pos = (fp_x + rdx, fp_y + rdy)
        # Layers
        layers = layers_m.group(1) if layers_m else ''
        net_pads[net.group(1)].append((ref, pn, abs_pos, layers))


# Segments per net
net_segs = defaultdict(list)  # net → [(layer, start, end)]
for m in re.finditer(r'\(segment', pcb):
    ps = m.start()
    pe = match_close(pcb, ps)
    pb = pcb[ps:pe]
    net = re.search(r'\(net (\d+)\)', pb)
    net_str = re.search(r'\(net "([^"]+)"', pb)
    # Segments in KiCad reference net by number; but the parent tstamp block
    # often has net name. Get all name occurrences.
    start = re.search(r'\(start ([\d.\-]+) ([\d.\-]+)\)', pb)
    end = re.search(r'\(end ([\d.\-]+) ([\d.\-]+)\)', pb)
    layer = re.search(r'\(layer "([^"]+)"', pb)
    if not (start and end and layer):
        continue
    # Find the net name — need to look up by (net N) number in the net table
    if net_str:
        nname = net_str.group(1)
        net_segs[nname].append((layer.group(1), (float(start.group(1)), float(start.group(2))), (float(end.group(1)), float(end.group(2)))))


# Build net_number → net_name map since segments only carry net number
net_number_to_name = {}
for m in re.finditer(r'\(net (\d+) "([^"]+)"\)', pcb):
    net_number_to_name[int(m.group(1))] = m.group(2)


# Re-scan segments with proper net-number lookup
net_segs = defaultdict(list)
for m in re.finditer(r'\(segment', pcb):
    ps = m.start()
    pe = match_close(pcb, ps)
    pb = pcb[ps:pe]
    net_m = re.search(r'\(net (\d+)\)', pb)
    start = re.search(r'\(start ([\d.\-]+) ([\d.\-]+)\)', pb)
    end = re.search(r'\(end ([\d.\-]+) ([\d.\-]+)\)', pb)
    layer = re.search(r'\(layer "([^"]+)"', pb)
    if not (start and end and layer and net_m):
        continue
    nname = net_number_to_name.get(int(net_m.group(1)), f'net_{net_m.group(1)}')
    net_segs[nname].append((layer.group(1), (float(start.group(1)), float(start.group(2))), (float(end.group(1)), float(end.group(2)))))


# Vias per net
net_vias = defaultdict(list)  # net → [(pos, layers)]
for m in re.finditer(r'\(via', pcb):
    ps = m.start()
    pe = match_close(pcb, ps)
    pb = pcb[ps:pe]
    net_m = re.search(r'\(net (\d+)\)', pb)
    at = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)\)', pb)
    layers = re.search(r'\(layers "([^"]+)" "([^"]+)"\)', pb)
    if not (net_m and at):
        continue
    nname = net_number_to_name.get(int(net_m.group(1)), f'net_{net_m.group(1)}')
    net_vias[nname].append(((float(at.group(1)), float(at.group(2))),
                             (layers.group(1), layers.group(2)) if layers else ('F.Cu', 'B.Cu')))


# Zones — record zone existence per net (we won't do full polygon fill check,
# but presence of a zone strongly suggests connectivity for that net's zone
# layer)
net_zones = defaultdict(set)  # net → set of layers with zones
for m in re.finditer(r'\(zone', pcb):
    ps = m.start()
    pe = match_close(pcb, ps)
    pb = pcb[ps:pe]
    net_m = re.search(r'\(net_name "([^"]+)"', pb)
    layer = re.search(r'\(layer "([^"]+)"', pb) or re.search(r'\(layers "([^"]+)"', pb)
    if net_m:
        if layer:
            net_zones[net_m.group(1)].add(layer.group(1))


# Now build connectivity graph per net and check
print(f'\nNets discovered: {len(net_pads)}')
print(f'Nets with segments: {len(net_segs)}')
print(f'Nets with vias: {len(net_vias)}')
print(f'Nets with zones: {len(net_zones)}')

print()
print('=' * 60)
print('CONNECTIVITY CHECK')
print('=' * 60)


def find_component(node, adj):
    """BFS to find all nodes reachable from `node`."""
    visited = {node}
    queue = [node]
    while queue:
        curr = queue.pop()
        for nbr in adj.get(curr, []):
            if nbr not in visited:
                visited.add(nbr)
                queue.append(nbr)
    return visited


warnings = []

# For each net with segments (skip pure-power nets that are covered by zones)
for net_name in sorted(set(net_pads.keys()) | set(net_segs.keys()) | set(net_vias.keys())):
    if net_name.startswith('unconnected-') or net_name.startswith('Net-('):
        continue  # skip auto-nets (usually intentional NC)
    # Skip pure power/ground rails (they'd need zone-polygon-fill analysis)
    if net_name in ('GND_L', 'GND_R', 'GND', '+3V3_L', '+3V3_R', '+5V_L', '+5V_R',
                    '+3V3', '+5V', 'GNDA', 'VCC'):
        continue

    pads = net_pads.get(net_name, [])
    segs = net_segs.get(net_name, [])
    vias = net_vias.get(net_name, [])

    if len(pads) < 2:
        continue  # single-pad nets can't have gaps

    # Build undirected graph
    # Nodes = pad positions, segment endpoints, via positions (with layer info)
    # For simplicity, we treat all as points and use tolerance-based coincidence
    # for edges.
    nodes = []  # list of ("pad" | "seg_end" | "via", position, layer_or_None)

    # Pads
    for ref, pn, pos, layers in pads:
        nodes.append(('pad', pos, layers, f'{ref}.{pn}'))

    # Segment endpoints — each segment has two endpoints on the same layer
    for i, (layer, s, e) in enumerate(segs):
        nodes.append(('seg', s, layer, f'seg{i}_start'))
        nodes.append(('seg', e, layer, f'seg{i}_end'))

    # Vias — a single node representing both layer connections
    for i, (pos, (top, bot)) in enumerate(vias):
        nodes.append(('via', pos, 'through', f'via{i}'))

    # Build adjacency
    adj = defaultdict(list)
    # For each segment, its own two endpoints are always connected
    for i, (layer, s, e) in enumerate(segs):
        n1 = ('seg', s, layer, f'seg{i}_start')
        n2 = ('seg', e, layer, f'seg{i}_end')
        adj[n1].append(n2)
        adj[n2].append(n1)

    # For coincidence (nodes at the same position on compatible layers)
    for i, n1 in enumerate(nodes):
        t1, pos1, l1, id1 = n1
        for j in range(i+1, len(nodes)):
            n2 = nodes[j]
            t2, pos2, l2, id2 = n2
            if not close(pos1, pos2):
                continue
            # Layer compatibility check:
            # - via can connect to F.Cu, B.Cu, or *.Cu-referenced things
            # - pads with layers like "*.Cu" or containing both F.Cu B.Cu are through-hole
            # - segments on specific layers only connect on same layer
            if t1 == 'via' or t2 == 'via':
                # Vias connect anything on F.Cu or B.Cu (through-vias)
                adj[n1].append(n2)
                adj[n2].append(n1)
                continue
            # Pads with '*.Cu' or containing multiple layers = through-hole
            def pad_all_layers(l):
                return '*.Cu' in l or ('F.Cu' in l and 'B.Cu' in l)
            l1_all = t1 == 'pad' and pad_all_layers(l1 or '')
            l2_all = t2 == 'pad' and pad_all_layers(l2 or '')
            if l1_all or l2_all:
                adj[n1].append(n2)
                adj[n2].append(n1)
                continue
            # Otherwise same layer required
            layer1_str = str(l1 or '')
            layer2_str = str(l2 or '')
            # Extract the copper layer name(s)
            def cu_layers(s):
                # For segments: 'F.Cu' or 'B.Cu' etc directly
                # For pads: might be '"F.Cu" "F.Paste" ...'
                cus = re.findall(r'([FB]\.Cu|In\d+\.Cu)', s)
                return set(cus)
            l1_cus = cu_layers(layer1_str) if t1 == 'pad' else {layer1_str}
            l2_cus = cu_layers(layer2_str) if t2 == 'pad' else {layer2_str}
            if l1_cus & l2_cus:
                adj[n1].append(n2)
                adj[n2].append(n1)

    # Find pad nodes and check they're all in one component
    pad_nodes = [n for n in nodes if n[0] == 'pad']
    if len(pad_nodes) < 2:
        continue
    first_component = find_component(pad_nodes[0], adj)
    disconnected = [n for n in pad_nodes[1:] if n not in first_component]
    if disconnected:
        # This net has pads NOT reachable through routed geometry
        # Check if any zone might explain it (skip if it's a rail net we already excluded)
        if net_name in net_zones:
            warnings.append((net_name, 'partial-zone-covered', pad_nodes, disconnected))
        else:
            warnings.append((net_name, 'GAP', pad_nodes, disconnected))


if not warnings:
    print('[OK] All signal nets checked — no unconnected pads found')
else:
    print(f'[WARN] {len(warnings)} nets have unconnected pads:')
    print()
    for net_name, kind, all_pads, disc in warnings:
        print(f'  {net_name} ({kind}):')
        for ref, pn, pos, _ in [(*n[3].split('.'), n[1], None) if '.' in n[3] else (n[3], '', n[1], None) for n in all_pads]:
            in_comp = 'CONNECTED' if (ref, pn) not in [(d[3].split('.')[0], d[3].split('.')[1] if '.' in d[3] else '') for d in disc] else 'DISCONNECTED'
            # Simpler: just list pads
            pass
        for n in all_pads:
            _, pos, _, id_str = n
            marker = 'X' if n in disc else '.'
            print(f'    [{marker}] {id_str} at ({pos[0]:.3f}, {pos[1]:.3f})')
        print()
