"""
Fix power net separation using _L/_R suffixed variant lib_symbols
with explicit pin names matching the desired net names.
"""

import re
import sys
import shutil

SCHEMATIC = r"C:\Users\neuro\dev\keyboard\umiko\umiko.kicad_sch"

with open(SCHEMATIC, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"Original: {len(content)} chars, {content.count(chr(10))} lines")

def check_parens(text, label=""):
    depth = 0
    for i, ch in enumerate(text):
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        if depth < 0:
            line_num = text[:i].count('\n') + 1
            print(f"  {label} PAREN ERROR: negative at line {line_num}")
            return False
    if depth != 0:
        print(f"  {label} PAREN ERROR: final depth = {depth}")
        return False
    print(f"  {label} parens OK")
    return True

check_parens(content, "Original")

# ============================================================
# STEP 1: Clean up stale lib_symbols and lib_names
# ============================================================

REMOVE_LIBSYMS = [
    '+1V1_1', '+1V1_2',
    'onigaku:+3V3_R', 'onigaku:+3V3_L',
    'onigaku:GND_R', 'onigaku:GND_L',
    'onigaku:+1V1_R', 'onigaku:+1V1_L',
    'onigaku:+5V_R', 'onigaku:+5V_L',
    'PCM_0xcb:GND_A', 'PCM_0xcb:+3V3_B',
]

def remove_libsym(content, name):
    marker = f'\t\t(symbol "{name}"'
    idx = content.find(marker)
    if idx == -1:
        return content, False
    depth = 0
    i = idx
    while i < len(content):
        if content[i] == '(':
            depth += 1
        elif content[i] == ')':
            depth -= 1
            if depth == 0:
                end = i + 1
                if end < len(content) and content[end] == '\n':
                    end += 1
                content = content[:idx] + content[end:]
                return content, True
        i += 1
    return content, False

for name in REMOVE_LIBSYMS:
    content, removed = remove_libsym(content, name)
    if removed:
        print(f"  Removed lib_symbol: {name}")

# Remove ONLY power-related lib_name references (preserve RP2040_1 etc.)
POWER_LIB_NAMES_TO_REMOVE = ['+1V1_1', '+1V1_2']
removed_count = 0
for pln in POWER_LIB_NAMES_TO_REMOVE:
    pattern = f'\t\t(lib_name "{pln}")\n'
    count = content.count(pattern)
    if count > 0:
        content = content.replace(pattern, '')
        removed_count += count
        print(f"  Removed {count} lib_name refs for '{pln}'")
if removed_count:
    print(f"  Removed {removed_count} power lib_name references total")

# ============================================================
# STEP 2: Normalize power lib_ids to power: base forms
# ============================================================

LIBID_MAPPING = {
    'onigaku:+3V3_R': 'power:+3V3',
    'onigaku:+3V3_L': 'power:+3V3',
    'onigaku:+1V1_R': 'power:+1V1',
    'onigaku:+1V1_L': 'power:+1V1',
    'onigaku:+5V_R': 'power:+5V',
    'onigaku:+5V_L': 'power:+5V',
    'onigaku:GND_R': 'power:GND',
    'onigaku:GND_L': 'power:GND',
    'PCM_0xcb:GND_A': 'power:GND',
}

for old_id, new_id in LIBID_MAPPING.items():
    old_str = f'(lib_id "{old_id}")'
    new_str = f'(lib_id "{new_id}")'
    count = content.count(old_str)
    if count > 0:
        content = content.replace(old_str, new_str)
        print(f"  Changed {count}x lib_id: {old_id} -> {new_id}")

# Fix GND_A Value -> GND_R
if content.count('"Value" "GND_A"') > 0:
    content = content.replace('(property "Value" "GND_A"', '(property "Value" "GND_R"')
    print("  Changed GND_A Value -> GND_R")

check_parens(content, "After cleanup")

# ============================================================
# STEP 3: Scan instances and collect (lib_id, value) pairs
# ============================================================

POWER_VALUES = {'+3V3_L', '+3V3_R', '+1V1_L', '+1V1_R', '+5V_L', '+5V_R', 'GND_L', 'GND_R', 'VBUS_L', 'VBUS_R'}

instance_pattern = re.compile(
    r'\t\(symbol\n'
    r'\t\t\(lib_id "([^"]+)"\)\n'
    r'(?:(?!\t\(symbol\n)[\s\S])*?'
    r'\(property "Value" "([^"]+)"'
)

pairs = {}
for m in instance_pattern.finditer(content):
    lib_id, value = m.group(1), m.group(2)
    if value in POWER_VALUES:
        key = (lib_id, value)
        pairs[key] = pairs.get(key, 0) + 1

print(f"\nPower (lib_id, value) pairs:")
total_instances = 0
for (lib_id, value), count in sorted(pairs.items()):
    print(f"  {lib_id} + {value}: {count}")
    total_instances += count

# ============================================================
# STEP 4: Create _L/_R variant lib_symbols with explicit pin names
# ============================================================

UP_LIBIDS = {'power:+3V3', 'power:+1V1', 'power:+5V', 'power:VDD', 'power:VBUS'}
DOWN_LIBIDS = {'power:GND', 'power:GNDA'}

# Build variant map: (lib_id, value) -> variant_name
# Use the VALUE as the variant name (e.g., "+3V3_R", "GND_L")
# But multiple lib_ids may share the same value (e.g., power:GND and power:GNDA both with "GND_R")
# So we need unique variant names per (lib_id, value)

variant_map = {}
used_names = set()

for (lib_id, value), count in sorted(pairs.items()):
    base = lib_id.split(':')[1] if ':' in lib_id else lib_id
    # Try base_suffix first (e.g., "GND_R"), then add lib prefix if conflict
    var_name = value  # e.g., "+3V3_R", "GND_L"
    if var_name in used_names:
        # Conflict - add base prefix (e.g., "GNDA_GND_R" for power:GNDA with GND_R)
        var_name = f"{base}_{value}"
    if var_name in used_names:
        var_name = f"{base}_{value}_2"
    used_names.add(var_name)
    variant_map[(lib_id, value)] = var_name

print(f"\nVariant assignments:")
for (lib_id, value), var_name in sorted(variant_map.items()):
    print(f"  ({lib_id}, {value}) -> variant '{var_name}' [pin name = '{value}']")

# Generate variant lib_symbols
variants_text = []
for (lib_id, value), var_name in sorted(variant_map.items()):
    base = lib_id.split(':')[1] if ':' in lib_id else lib_id
    is_down = lib_id in DOWN_LIBIDS
    pin_name = value  # The pin name IS the desired net name

    if is_down:
        ref_y, val_y, pin_angle = "-6.35", "-3.81", "270"
        gfx_lines = (
            f'\t\t\t(symbol "{var_name}_0_1"\n'
            f'\t\t\t\t(polyline\n'
            f'\t\t\t\t\t(pts\n'
            f'\t\t\t\t\t\t(xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27)\n'
            f'\t\t\t\t\t)\n'
            f'\t\t\t\t\t(stroke\n'
            f'\t\t\t\t\t\t(width 0)\n'
            f'\t\t\t\t\t\t(type default)\n'
            f'\t\t\t\t\t)\n'
            f'\t\t\t\t\t(fill\n'
            f'\t\t\t\t\t\t(type none)\n'
            f'\t\t\t\t\t)\n'
            f'\t\t\t\t)\n'
            f'\t\t\t)\n'
        )
    else:
        ref_y, val_y, pin_angle = "-3.81", "3.556", "90"
        gfx_lines = (
            f'\t\t\t(symbol "{var_name}_0_1"\n'
            f'\t\t\t\t(polyline\n'
            f'\t\t\t\t\t(pts\n'
            f'\t\t\t\t\t\t(xy -0.762 1.27) (xy 0 2.54)\n'
            f'\t\t\t\t\t)\n'
            f'\t\t\t\t\t(stroke\n'
            f'\t\t\t\t\t\t(width 0)\n'
            f'\t\t\t\t\t\t(type default)\n'
            f'\t\t\t\t\t)\n'
            f'\t\t\t\t\t(fill\n'
            f'\t\t\t\t\t\t(type none)\n'
            f'\t\t\t\t\t)\n'
            f'\t\t\t\t)\n'
            f'\t\t\t\t(polyline\n'
            f'\t\t\t\t\t(pts\n'
            f'\t\t\t\t\t\t(xy 0 2.54) (xy 0.762 1.27)\n'
            f'\t\t\t\t\t)\n'
            f'\t\t\t\t\t(stroke\n'
            f'\t\t\t\t\t\t(width 0)\n'
            f'\t\t\t\t\t\t(type default)\n'
            f'\t\t\t\t\t)\n'
            f'\t\t\t\t\t(fill\n'
            f'\t\t\t\t\t\t(type none)\n'
            f'\t\t\t\t\t)\n'
            f'\t\t\t\t)\n'
            f'\t\t\t\t(polyline\n'
            f'\t\t\t\t\t(pts\n'
            f'\t\t\t\t\t\t(xy 0 0) (xy 0 2.54)\n'
            f'\t\t\t\t\t)\n'
            f'\t\t\t\t\t(stroke\n'
            f'\t\t\t\t\t\t(width 0)\n'
            f'\t\t\t\t\t\t(type default)\n'
            f'\t\t\t\t\t)\n'
            f'\t\t\t\t\t(fill\n'
            f'\t\t\t\t\t\t(type none)\n'
            f'\t\t\t\t\t)\n'
            f'\t\t\t\t)\n'
            f'\t\t\t)\n'
        )

    sym = (
        f'\t\t(symbol "{var_name}"\n'
        f'\t\t\t(power)\n'
        f'\t\t\t(pin_numbers\n'
        f'\t\t\t\t(hide yes)\n'
        f'\t\t\t)\n'
        f'\t\t\t(pin_names\n'
        f'\t\t\t\t(offset 0)\n'
        f'\t\t\t\t(hide yes)\n'
        f'\t\t\t)\n'
        f'\t\t\t(exclude_from_sim no)\n'
        f'\t\t\t(in_bom yes)\n'
        f'\t\t\t(on_board yes)\n'
        f'\t\t\t(property "Reference" "#PWR"\n'
        f'\t\t\t\t(at 0 {ref_y} 0)\n'
        f'\t\t\t\t(effects\n'
        f'\t\t\t\t\t(font\n'
        f'\t\t\t\t\t\t(size 1.27 1.27)\n'
        f'\t\t\t\t\t)\n'
        f'\t\t\t\t\t(hide yes)\n'
        f'\t\t\t\t)\n'
        f'\t\t\t)\n'
        f'\t\t\t(property "Value" "{var_name}"\n'
        f'\t\t\t\t(at 0 {val_y} 0)\n'
        f'\t\t\t\t(effects\n'
        f'\t\t\t\t\t(font\n'
        f'\t\t\t\t\t\t(size 1.27 1.27)\n'
        f'\t\t\t\t\t)\n'
        f'\t\t\t\t)\n'
        f'\t\t\t)\n'
        f'\t\t\t(property "Footprint" ""\n'
        f'\t\t\t\t(at 0 0 0)\n'
        f'\t\t\t\t(effects\n'
        f'\t\t\t\t\t(font\n'
        f'\t\t\t\t\t\t(size 1.27 1.27)\n'
        f'\t\t\t\t\t)\n'
        f'\t\t\t\t\t(hide yes)\n'
        f'\t\t\t\t)\n'
        f'\t\t\t)\n'
        f'\t\t\t(property "Datasheet" ""\n'
        f'\t\t\t\t(at 0 0 0)\n'
        f'\t\t\t\t(effects\n'
        f'\t\t\t\t\t(font\n'
        f'\t\t\t\t\t\t(size 1.27 1.27)\n'
        f'\t\t\t\t\t)\n'
        f'\t\t\t\t\t(hide yes)\n'
        f'\t\t\t\t)\n'
        f'\t\t\t)\n'
        f'\t\t\t(property "Description" ""\n'
        f'\t\t\t\t(at 0 0 0)\n'
        f'\t\t\t\t(effects\n'
        f'\t\t\t\t\t(font\n'
        f'\t\t\t\t\t\t(size 1.27 1.27)\n'
        f'\t\t\t\t\t)\n'
        f'\t\t\t\t\t(hide yes)\n'
        f'\t\t\t\t)\n'
        f'\t\t\t)\n'
        f'\t\t\t(property "ki_keywords" "global power"\n'
        f'\t\t\t\t(at 0 0 0)\n'
        f'\t\t\t\t(effects\n'
        f'\t\t\t\t\t(font\n'
        f'\t\t\t\t\t\t(size 1.27 1.27)\n'
        f'\t\t\t\t\t)\n'
        f'\t\t\t\t\t(hide yes)\n'
        f'\t\t\t\t)\n'
        f'\t\t\t)\n'
        f'{gfx_lines}'
        f'\t\t\t(symbol "{var_name}_1_1"\n'
        f'\t\t\t\t(pin power_in line\n'
        f'\t\t\t\t\t(at 0 0 {pin_angle})\n'
        f'\t\t\t\t\t(length 0)\n'
        f'\t\t\t\t\t(name "{pin_name}"\n'
        f'\t\t\t\t\t\t(effects\n'
        f'\t\t\t\t\t\t\t(font\n'
        f'\t\t\t\t\t\t\t\t(size 1.27 1.27)\n'
        f'\t\t\t\t\t\t\t)\n'
        f'\t\t\t\t\t\t)\n'
        f'\t\t\t\t\t)\n'
        f'\t\t\t\t\t(number "1"\n'
        f'\t\t\t\t\t\t(effects\n'
        f'\t\t\t\t\t\t\t(font\n'
        f'\t\t\t\t\t\t\t\t(size 1.27 1.27)\n'
        f'\t\t\t\t\t\t\t)\n'
        f'\t\t\t\t\t\t)\n'
        f'\t\t\t\t\t)\n'
        f'\t\t\t\t)\n'
        f'\t\t\t)\n'
        f'\t\t\t(embedded_fonts no)\n'
        f'\t\t)\n'
    )

    if not check_parens(sym, f"Variant {var_name}"):
        print(f"FATAL: {var_name} has paren error")
        sys.exit(1)

    variants_text.append(sym)

all_variants = "".join(variants_text)

# Insert after (lib_symbols line
lib_sym_marker = '\t(lib_symbols\n'
idx = content.find(lib_sym_marker)
insert_pos = idx + len(lib_sym_marker)
content = content[:insert_pos] + all_variants + content[insert_pos:]
print(f"\nInserted {len(variant_map)} variant lib_symbols")

check_parens(content, "After insert")

# ============================================================
# STEP 5: Add lib_name to matching instances
# ============================================================

change_counter = [0]
for (lib_id, value), var_name in variant_map.items():
    escaped_lib_id = re.escape(lib_id)
    escaped_value = re.escape(value)

    pattern = re.compile(
        r'(\t\(symbol\n)'
        r'(\t\t\(lib_id "' + escaped_lib_id + r'"\)\n)'
        r'((?:(?!\t\(symbol\n)[\s\S])*?)'
        r'(\(property "Value" "' + escaped_value + r'")'
    )

    def make_replacer(vn):
        def repl(match):
            change_counter[0] += 1
            return (match.group(1) +
                    '\t\t(lib_name "' + vn + '")\n' +
                    match.group(2) + match.group(3) + match.group(4))
        return repl

    content = pattern.sub(make_replacer(var_name), content)

print(f"Added {change_counter[0]} lib_name references")

# ============================================================
# STEP 6: Final validation
# ============================================================

print(f"\n=== VALIDATION ===")
print(f"File: {len(content)} chars, {content.count(chr(10))} lines")

if not check_parens(content, "FINAL"):
    print("ABORTING")
    sys.exit(1)

# Check for duplicate lib_symbol names
libsym_names = re.findall(r'\t\t\(symbol "([^"]+)"', content)
seen = set()
for name in libsym_names:
    if name in seen:
        print(f"  DUPLICATE lib_symbol: {name}")
    seen.add(name)

for (lib_id, value), var_name in sorted(variant_map.items()):
    found = f'(symbol "{var_name}"' in content
    count = content.count(f'(lib_name "{var_name}")')
    print(f"  {var_name}: lib_sym={'OK' if found else 'MISSING'}, instances={count}")

for value in sorted(POWER_VALUES):
    total = len(re.findall(rf'\(property "Value" "{re.escape(value)}"', content))
    named = sum(content.count(f'(lib_name "{vn}")')
                for (_, v), vn in variant_map.items() if v == value)
    status = "OK" if total == named else f"WARNING: {named}/{total}"
    print(f"  {value}: {status} ({total})")

# ============================================================
# STEP 7: Write
# ============================================================

with open(SCHEMATIC, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nDone. Please test in KiCad.")
