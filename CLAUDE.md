# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Umiko is a split mechanical keyboard PCB designed in KiCad 9.0. It is a TKL F-row-less layout with per-key RGB (SK6812MINI-E), underglow, Proton-C microcontroller, OLED display support, Kailh hot-swap sockets, and TRRS split connectivity. Firmware runs on QMK.

## Key Files

- `umiko.kicad_sch` — Schematic (symbol-level design)
- `umiko.kicad_pcb` — PCB layout (physical routing and placement)
- `umiko.kicad_pro` — Project settings, design rules, net classes
- `umiko.kicad_dru` — Design rule definitions
- `sym-lib-table` / `fp-lib-table` — Symbol and footprint library paths
- `gbr/` — Gerber fabrication output files
- `drawings/` — Custom artwork footprints (logos in kicad_mod format)
- `lib/` — Git submodules for external component libraries

## External Libraries (Submodules)

Run `git submodule update --init --recursive` to pull library dependencies. Key submodules: `keebs.pretty`, `keyboard_parts.pretty`, `kicad_lib_tmk`, `SparkFun-KiCad-Libraries`, `nice-nano-kicad`, `qmk_hardware`.

## Design Rules

- Track widths: 0.2, 0.3, 0.4, 0.5mm
- Net classes defined: Default, GND, GNDA, VCC
- Teardrop connections enabled for vias

## Working with KiCad Files

KiCad files (.kicad_sch, .kicad_pcb) are S-expression text formats. They can be read and parsed but are primarily edited in KiCad's GUI. When reading these files, note they are very large (schematic ~69K lines, PCB ~144K lines). Lock files (`~*.lck`) and autosave files (`_autosave-*`) indicate KiCad has the project open.

## QMK Firmware

The keyboard uses QMK firmware compiled with dfu-util for split keyboard support. See README.md for firmware build instructions and the full bill of materials.
