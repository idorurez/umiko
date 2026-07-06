#!/usr/bin/env bash
# Compile umiko QMK firmware.
#
# This script wraps the MSYS2 env setup we discovered during first-time
# QMK setup. Runs the compile via MSYS2's bash with all the right
# env vars, so you don't need to remember them or open a MINGW64 shell.
#
# Usage:
#   scripts/qmk_compile.sh              # default keymap
#   scripts/qmk_compile.sh mykeymap     # a different keymap
#
# Prereqs (one-time):
#   1. MSYS2 installed at C:/msys64 (see README "Toolchain (Windows)" section)
#   2. Deps installed via pacman: base-devel, mingw-w64-x86_64-python-pip,
#      mingw-w64-ucrt-x86_64-arm-none-eabi-gcc (+ binutils + newlib), rust,
#      mingw-w64-x86_64-python-pillow
#   3. QMK CLI installed: python -m pip install --user --break-system-packages
#      "jsonschema<4.18" qmk  (older jsonschema avoids the rpds-py rust build)
#   4. Junction: mklink /J C:\Users\neuro\qmk_firmware C:\Users\neuro\dev\keyboard\qmk_umiko
#      (QMK CLI looks at ~/qmk_firmware by default; this makes that path work)
#   5. Keymap file must exist at qmk_umiko/keyboards/umiko/keymaps/$KM/keymap.c

set -e
KM="${1:-default}"
MSYS_BASH="C:/msys64/usr/bin/bash.exe"

if [ ! -f "$MSYS_BASH" ]; then
    echo "ERROR: MSYS2 not installed at C:/msys64" >&2
    exit 1
fi

MSYSTEM=MINGW64 "$MSYS_BASH" -lc "
    export USERPROFILE='C:\\Users\\neuro'
    export HOME=/home/neuro
    export PATH=/c/Users/neuro/.local/bin:/ucrt64/bin:\$PATH
    qmk compile -kb umiko -km $KM
"

UF2=/c/Users/neuro/dev/keyboard/qmk_umiko/umiko_${KM}.uf2
if [ -f "$UF2" ]; then
    echo
    echo "UF2 ready: $UF2"
    echo "Flash by holding BOOTSEL (SW1 left, SW2 right), plugging USB,"
    echo "then dragging the UF2 onto the RPI-RP2 drive that appears."
else
    echo "ERROR: expected UF2 not found at $UF2" >&2
    exit 1
fi
