"""
Fix power net separation by switching from lib_name to lib_id approach.

For 10 core power variants: remove lib_name line, change lib_id to variant name.
For 3 unwanted variants: remove lib_name lines, remove lib_symbol definitions.
Preserve RP2040_1 lib_name references.
"""

import re

SCHEMATIC = r"C:\Users\neuro\dev\keyboard\umiko\umiko.kicad_sch"

# Core variants: lib_name -> new lib_id (remove lib_name, change lib_id)
CORE_VARIANTS = {
    "+1V1_L": "power:+1V1",
    "+1V1_R": "power:+1V1",
    "+3V3_L": "power:+3V3",
    "+3V3_R": "power:+3V3",
    "+5V_L": "power:+5V",
    "+5V_R": "power:+5V",
    "GND_L": "power:GND",
    "GND_R": "power:GND",
    "VBUS_L": "power:VBUS",
    "VBUS_R": "power:VBUS",
}

# Unwanted variants: just remove lib_name lines (keep original lib_id)
UNWANTED_VARIANTS = ["GNDA_GND_R", "VBUS_+5V_L", "VDD_+5V_R"]

# Unwanted lib_symbol definitions to remove (line ranges, 1-indexed)
# GNDA_GND_R: lines 965-1065, VBUS_+5V_L: lines 1066-1190, VDD_+5V_R: lines 1441-1565

with open(SCHEMATIC, "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Read {len(lines)} lines")

# Phase 1: Remove unwanted lib_symbol definitions
# Find and remove them by matching (symbol "NAME" at the lib_symbols level (2 tabs indent)
unwanted_sym_ranges = []
i = 0
while i < len(lines):
    for name in UNWANTED_VARIANTS:
        if lines[i].strip() == f'(symbol "{name}"' and lines[i].startswith('\t\t(symbol'):
            # Found start of unwanted lib_symbol definition
            start = i
            # Find the end - track parenthesis depth
            depth = 0
            for j in range(i, len(lines)):
                depth += lines[j].count('(') - lines[j].count(')')
                if depth == 0:
                    unwanted_sym_ranges.append((start, j + 1, name))
                    break
            break
    i += 1

# Remove in reverse order to maintain line numbers
for start, end, name in sorted(unwanted_sym_ranges, reverse=True):
    print(f"Removing lib_symbol '{name}': lines {start+1}-{end}")
    del lines[start:end]

print(f"After lib_symbol removal: {len(lines)} lines")

# Phase 2: Process instances - handle core and unwanted variants
core_count = {k: 0 for k in CORE_VARIANTS}
unwanted_count = {k: 0 for k in UNWANTED_VARIANTS}

i = 0
while i < len(lines):
    line = lines[i]

    # Check for lib_name lines
    m = re.match(r'^(\t+)\(lib_name "(.+)"\)\s*$', line)
    if m:
        indent = m.group(1)
        lib_name_val = m.group(2)

        if lib_name_val in CORE_VARIANTS:
            # Core variant: remove lib_name line, change next lib_id line
            old_lib_id = CORE_VARIANTS[lib_name_val]
            # Next line should be lib_id
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                m2 = re.match(r'^(\t+)\(lib_id "(.+)"\)\s*$', next_line)
                if m2 and m2.group(2) == old_lib_id:
                    # Replace lib_id with variant name
                    lines[i + 1] = f'{m2.group(1)}(lib_id "{lib_name_val}")\n'
                    # Remove lib_name line
                    del lines[i]
                    core_count[lib_name_val] += 1
                    continue  # Don't increment i since we deleted a line
                else:
                    print(f"WARNING: Expected lib_id '{old_lib_id}' after lib_name '{lib_name_val}' at line {i+1}, got: {next_line.strip()}")

        elif lib_name_val in UNWANTED_VARIANTS:
            # Unwanted variant: just remove lib_name line
            del lines[i]
            unwanted_count[lib_name_val] += 1
            continue  # Don't increment i

    i += 1

print("\nCore variant instance changes:")
total_core = 0
for name, count in sorted(core_count.items()):
    print(f"  {name}: {count}")
    total_core += count
print(f"  Total: {total_core}")

print("\nUnwanted variant lib_name removals:")
total_unwanted = 0
for name, count in sorted(unwanted_count.items()):
    print(f"  {name}: {count}")
    total_unwanted += count
print(f"  Total: {total_unwanted}")

# Validate: check remaining lib_name references (should only be RP2040)
remaining_lib_names = []
for i, line in enumerate(lines):
    m = re.match(r'^\t+\(lib_name "(.+)"\)', line)
    if m:
        remaining_lib_names.append((i+1, m.group(1)))

print(f"\nRemaining lib_name references: {len(remaining_lib_names)}")
for ln, name in remaining_lib_names:
    print(f"  Line {ln}: {name}")

# Validate parentheses balance
total_open = sum(line.count('(') for line in lines)
total_close = sum(line.count(')') for line in lines)
print(f"\nParentheses balance: {total_open} open, {total_close} close, diff={total_open - total_close}")

if total_open != total_close:
    print("ERROR: Parentheses are unbalanced! NOT saving.")
else:
    with open(SCHEMATIC, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"\nSaved {len(lines)} lines to {SCHEMATIC}")
