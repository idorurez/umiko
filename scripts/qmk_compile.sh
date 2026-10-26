#!/usr/bin/env bash
# Compile umiko QMK firmware (twin binaries: left + right halves).
#
# This script wraps the MSYS2 env setup we discovered during first-time
# QMK setup. Runs the compile via MSYS2's bash with all the right
# env vars, so you don't need to remember them or open a MINGW64 shell.
#
# Twin-binary scheme: the `default` keymap builds LEFT, the `right` keymap
# builds RIGHT (see keyboards/umiko/umiko.c handedness block). Flash the
# matching file per half. Either half can take the USB cable; plug USB
# into exactly one half.
#
# Usage:
#   scripts/qmk_compile.sh              # build BOTH halves
#   scripts/qmk_compile.sh mykeymap     # build one keymap only
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
#      (sync keyboards/umiko/ from this repo into the clone before building)

set -e
MSYS_BASH="C:/msys64/usr/bin/bash.exe"
QMK=/c/Users/neuro/dev/keyboard/qmk_umiko

if [ ! -f "$MSYS_BASH" ]; then
    echo "ERROR: MSYS2 not installed at C:/msys64" >&2
    exit 1
fi

build_one() {
    MSYSTEM=MINGW64 "$MSYS_BASH" -lc "
        export USERPROFILE='C:\\Users\\neuro'
        export HOME=/home/neuro
        export PATH=/c/Users/neuro/.local/bin:/ucrt64/bin:\$PATH
        qmk compile -kb umiko -km $1
    "
    if [ ! -f "$QMK/umiko_$1.uf2" ]; then
        echo "ERROR: expected UF2 not found at $QMK/umiko_$1.uf2" >&2
        exit 1
    fi
}

if [ $# -eq 0 ]; then
    build_one default
    build_one right
    cp "$QMK/umiko_default.uf2" "$QMK/umiko_left.uf2"
    echo
    echo "UF2s ready:"
    echo "  $QMK/umiko_left.uf2   (flash LEFT half)"
    echo "  $QMK/umiko_right.uf2  (flash RIGHT half)"
else
    build_one "$1"
    echo
    echo "UF2 ready: $QMK/umiko_$1.uf2"
fi

echo "Flash by holding BOOTSEL (SW1 left, SW2 right), plugging USB,"
echo "then dragging the matching UF2 onto the RPI-RP2 drive that appears."
echo "Plug USB into exactly one half."
