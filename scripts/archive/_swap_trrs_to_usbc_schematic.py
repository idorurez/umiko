"""Replace U4 and U12 TRRS symbols with USB-C symbols J3 and J4.

Path B: text-edit the schematic to delete the two TRRS symbol instances and
inject fresh USB-C symbol instances (modeled on J1) at the same positions
with Footprint preset. Wires that were on TRRS pins are left in place but
will dangle — user reconnects in KiCad GUI.

TRRS lib_symbol (keebio:TRRS) is intentionally left in the schematic's
embedded lib_symbols section in case the user wants to revert; safe to
keep since no instances reference it after this swap.
"""
import re
import uuid

SCH = r'C:\Users\neuro\dev\keyboard\umiko\umiko.kicad_sch'

with open(SCH, encoding='utf-8') as f:
    sch = f.read()

def find_symbol_block(text, ref):
    """Find the symbol instance with the given Reference. Returns (start, end, at_x, at_y, at_rot)."""
    for m in re.finditer(r'\n\t\(symbol\n', text):
        p = m.start() + 1
        depth = 1; i = m.end()
        while i < len(text) and depth > 0:
            c = text[i]
            if c == '(': depth += 1
            elif c == ')': depth -= 1
            i += 1
        blk = text[p:i]
        if f'(property "Reference" "{ref}"' in blk[:2000]:
            at_m = re.search(r'\(at ([\d.\-]+) ([\d.\-]+)(?:\s+([\d.\-]+))?\)', blk[:200])
            ax = float(at_m.group(1)); ay = float(at_m.group(2)); ar = at_m.group(3) or "0"
            return p, i, ax, ay, ar
    return None

# Find U4 and U12 (TRRS) and J1 (USB-C template)
u4 = find_symbol_block(sch, 'U4')
u12 = find_symbol_block(sch, 'U12')
j1 = find_symbol_block(sch, 'J1')
assert u4 and u12 and j1, 'Could not find U4, U12, or J1'
print(f'U4 at {sch[u4[0]:u4[0]+50]!r}... ({u4[2]}, {u4[3]}, {u4[4]})')
print(f'U12 at ({u12[2]}, {u12[3]}, {u12[4]})')
print(f'J1 template at ({j1[2]}, {j1[3]}, {j1[4]})')

j1_block = sch[j1[0]:j1[1]]

# Sheet path UUID for the instances block
sheet_path = '/4b4aa2f9-db35-4fc9-9772-4a4fa5dd4e1a'

def build_replacement(template, new_ref, new_x, new_y, new_rot):
    """Take the J1 template block, rewrite Reference, position, all UUIDs."""
    new = template

    # 1. Replace symbol-level UUID (the one after (in_bom yes)(on_board yes)(in_pos_files yes)(dnp no)(fields_autoplaced yes))
    # The first uuid in the block is the symbol UUID. Replace with new one.
    new_symbol_uuid = str(uuid.uuid4())
    new = re.sub(r'\(uuid "[^"]+"\)', f'(uuid "{new_symbol_uuid}")', new, count=1)

    # 2. Rewrite the symbol's (at X Y rot) header line — first (at ...) in block
    new = re.sub(r'\(at [\d.\-]+ [\d.\-]+(?:\s+[\d.\-]+)?\)',
                 f'(at {new_x} {new_y} {new_rot})', new, count=1)

    # 3. Reference property value: "J1" -> new_ref
    new = re.sub(r'\(property "Reference" "J1"', f'(property "Reference" "{new_ref}"', new, count=1)

    # 4. Rewrite each pin UUID (one per (pin "..." ... (uuid "...")) block)
    def replace_pin_uuid(m):
        return m.group(1) + str(uuid.uuid4()) + m.group(3)
    new = re.sub(r'(\(pin "[^"]+"\s*\(uuid ")([^"]+)(")', replace_pin_uuid, new)

    # 5. Update the (instances ... (reference "J1") ...) block to new_ref
    new = re.sub(r'\(reference "J1"\)', f'(reference "{new_ref}")', new)

    return new

# Build J3 (where U4 was) and J4 (where U12 was)
j3_block = build_replacement(j1_block, 'J3', u4[2], u4[3], u4[4])
j4_block = build_replacement(j1_block, 'J4', u12[2], u12[3], u12[4])

# Verify byte ordering: U12 < U4 in the file (1038375 < 1212614). Replace from the LATER one first
# so byte offsets stay valid for the earlier replacement.
if u4[0] < u12[0]:
    first, first_new = u12, j4_block
    second, second_new = u4, j3_block
else:
    first, first_new = u4, j3_block
    second, second_new = u12, j4_block

# Replace later block first
out = sch[:first[0]] + first_new + sch[first[1]:]
# Then replace earlier block (positions still valid since we modified the later region)
out = out[:second[0]] + second_new + out[second[1]:]

with open(SCH, 'w', encoding='utf-8') as f:
    f.write(out)

print(f'\nReplaced U4 -> J3 (USB-C, at {u4[2]}, {u4[3]})')
print(f'Replaced U12 -> J4 (USB-C, at {u12[2]}, {u12[3]})')
print('Wires on old TRRS pins are still in the schematic but will dangle. Reconnect in KiCad GUI.')
