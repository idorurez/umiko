# CLAUDE.md

This file provides guidance to AI coding assistants working in this repository.

## Project Overview

Umiko (海 + 子, "sea child") is a split, low-profile TKL F-row-less mechanical keyboard PCB designed in KiCad 10. Two physically separate halves; each half is standalone with its own MCU.

- **MCU:** 1× Raspberry Pi RP2040 (QFN-56) per half, each with W25Q128 QSPI flash, LP5907 3V3 LDO, 12 MHz crystal
- **Switches:** 63× Gateron KS-33 v2.0 low-profile, hot-swap sockets, 1N4148W diodes
- **Stabilizers:** Kailh Choc V2 (EOL — stock spares). NOT MX, NOT Gateron LP. PCB cutouts are Choc-V2 sized.
- **RGB:** 63× SK6812MINI-E reverse-mount per-key + SK6812 4020 side-view underglow (~20–33/half on GP25 chain, no satellite board)
- **USB:** side-mount host USB-C per half (outer edge) + top-mount inter-half USB-C carrying VBUS bridge, GND, and single-wire PIO serial on D+ (GP0, QMK vendor driver). J3/J4 are NOT real USB — never plug into a computer.
- **Flashing:** BOOTSEL-only (SW1 left, SW2 right). No reset circuit by design. SWD pogo pads mirrored across halves.
- **Stackup:** 4-layer, 1.6 mm — F.Cu signal, In1 split 3V3 (L/R), In2 split GND (L/R), B.Cu signal. 328.62 × 102.85 mm end-to-end.
- **Firmware:** QMK (RP2040, USB-detect master election, no handedness pin)

See README.md for the full BOM, assembly guide, JLC fab workflow, and design history.

## Key Files

- `umiko.kicad_sch` — Schematic (symbol-level design)
- `umiko.kicad_pcb` — PCB layout (physical routing and placement)
- `umiko.kicad_pro` — Project settings and design rules (source of truth for the Design Rules section below)
- `umiko.kicad_dru` — Custom design rule definitions
- `sym-lib-table` / `fp-lib-table` — Symbol and footprint library paths
- `footprints/` — Project-local `.pretty` libraries (`umiko-rev2`: SK6812-4020 side-view; `umiko-hybrid-switches`: MX + KS-33 hybrid)
- `symbols/` — Project-local symbols (`umiko-rev2.kicad_sym`)
- `keyboards/umiko/` — QMK keyboard definition authored here (`keyboard.json`, NOT `info.json`; `config.h`, `rules.mk`, keymaps). Copied into a fresh upstream QMK clone to build.
- `scripts/` — Build automation (see Scripts table)
- `docs/` — `toolchain-windows.md` (QMK/MSYS2 setup), `rev2-todo.md`, `rev2-4020-selection.md`, `led-chain.md`, `y47-y49-history.md`, `session-notes/`
- `fab/` — Script-generated JLC upload set (gerbers zip, BOM, CPL). Canonical fab output.
- `gbr/` — Older manual gerber/drill exports (superseded by `fab/`)
- `cad/` — Generated STEPs for case/plate CAD (SolidWorks)
- `drawings/` — Custom artwork footprints (logos in kicad_mod format)
- `reference/` — Reference models (e.g. Choc V2 stab holder STL)
- `lib/` — Git submodules for external component libraries (mostly legacy)
- `output/` — DRC gate output (`prefab_drc.json`)

## Libraries

Project-local libraries live in-repo under `footprints/` and `symbols/` (referenced via `${KIPRJMOD}`, portable).

The `onigaku` library (custom symbols, footprints, 3D models) is a **sibling repo** referenced by **absolute path** (`C:/Users/neuro/dev/keyboard/onigaku/...`). It must be cloned alongside this repo or library links break. Several other `*-lib-table` entries (MX_Alps_Hybrid, keebio, proton_c, MJ-4PP-9) are legacy absolute paths — `proton_c` and `bake-kujira` are disabled.

Git submodules (`git submodule update --init --recursive`): `lib/keebs.pretty`, `lib/kicad_lib_tmk`, `lib/keyboard_parts.pretty`, `lib/SparkFun-KiCad-Libraries`, `lib/nice-nano-kicad`, `lib/qmk_hardware`.

## Design Rules (from `umiko.kicad_pro`)

- 4-layer, JLCPCB standard tier: min clearance 0.1 mm, min hole 0.3 mm, min via 0.4/0.2 mm
- Track widths: 0.2 (signals), 0.3 (power/GND), 0.4, 0.5 mm
- No custom net classes — Default rules only
- Teardrops enabled (PTH pads, SMD pads, vias)
- Silkscreen defaults 1.0 mm / 0.15; only F.SilkS/B.SilkS print (Fab layers are editor-only)

## Scripts

| Script | What it does |
|---|---|
| `scripts/prefab_check.sh` | **Pre-fab gate — run before every gerber export.** Refills zones, saves, runs DRC via `kicad-cli` (no GUI cache). Exit 0 = safe to fab. Born from a real shipped short. |
| `scripts/make_jlc_files.py` | Reads sch + PCB (read-only), writes JLC-upload-ready gerbers zip, BOM, CPL to `fab/` in JLC's exact format |
| `scripts/make_cad_files.py` | 3D STEP exports (assembly, halves, component groups) to `cad/` for case CAD |
| `scripts/make_plate.py` | Plate STEP + DXF with switch + Choc V2 stab cutouts (canonical spec from `keebio/kb-plategen`) |
| `scripts/qmk_compile.sh [keymap]` | Runs `qmk compile` inside MSYS2 with required env vars. UF2 lands in the QMK clone. |

On Windows, `kicad-cli` lives at `C:/Program Files/KiCad/10.0/bin/kicad-cli.exe`.

## Working with KiCad Files

KiCad files (`.kicad_sch`, `.kicad_pcb`) are S-expression text. They are very large — read in windows, never whole. `~*.lck` files and `_autosave-*` files mean KiCad has the project open.

**Do not hand-edit `*.kicad_pcb` or `*.kicad_mod` files.** Make board/footprint changes through KiCad's GUI (or the Konnect MCP tools when configured — see `.mcp.json`). Scripted bulk edits go through pcbnew's scripting console, never raw text replacement.

## QMK Firmware

- Keyboard definition lives in-repo at `keyboards/umiko/`; it is built inside a **fresh upstream QMK clone** (`~/dev/keyboard/qmk_umiko`), not the stale `idorurez` fork. TODO: move to external-keyboard support so it lives with the PCB source.
- QMK CLI requires MSYS2 on Windows — one-time setup in `docs/toolchain-windows.md`, then compile with `scripts/qmk_compile.sh`.
- Config file must be named `keyboard.json` (old `info.json` name breaks `qmk compile`).
- Split transport: single-wire half-duplex PIO serial on GP0 (`split.serial.driver = "vendor"`). No handedness pin — master election is USB-detect based.
- Flash each half independently via BOOTSEL: unplug → hold BOOTSEL → plug → release → drop `.uf2` onto the RPI-RP2 drive.
