# umiko

![Image of schematic](images/umiko_schematic.svg)
![PCB front (with keycaps)](images/umiko_3dview_front.png)
![PCB perspective](images/umiko_3dview_persp.png)
![PCB front (no keys)](images/umiko_3dview_front_nokeys.png)
![PCB back (no keys)](images/umiko_3dview_back_nokeys.png)
![Case CAD in SolidWorks](images/umiko_case_solidworks.png)

A split, low-profile TKL F-row-less mechanical keyboard PCB. Two halves connect via a **top-mounted USB-C inter-half link** (single-wire QMK PIO serial over the D+ pin, with VBUS bridging 5 V across halves), each half is independently powered via its own side-mounted host USB-C and flashable, and each half has its own RP2040 microcontroller, per-key RGB, and underglow. Stabilizer cutouts are sized for Kailh Choc V2 stabilizers. Switches are Gateron KS-33 v2.0 low-profile (MX-compatible, hot-swap). 4-layer board with split L/R power rails and dedicated inner GND/3V3 planes.

## Features

* **Split layout** — two physically separate halves; each half has its own MCU and runs standalone
* **TKL, F-row-less** — full alpha + nav cluster on the right, no function row
* **Per-key RGB** (SK6812MINI-E reverse-mount, lights through PCB cutouts to underside of keycap)
* **Underglow** (SK6812MINI-E underglow variant, mounted on the back of the PCB)
* **Gateron KS-33 v2.0 low-profile hot-swap** switches (MX-compatible footprint, low-profile body)
* **Kailh Choc V2 stabilizers** (stabilizer cutouts on PCB sized for Choc V2, not MX stabs)
* **Side-mounted host USB-C** per half (on the outer edge of each board) for host connection and power
* **Top-mounted USB-C inter-half link** (HRO Type-C, on the top edge of each board near the inner-top corner) carrying single-wire PIO serial (over D+), GND, and 5 V bridge between halves
* **RP2040** — one per half, each with its own external QSPI flash (W25Q128) and 3V3 LDO (LP5907)
* **BOOTSEL-only flashing** — each half has a BOOTSEL button (SW1 left, SW2 right). No reset circuit by design; flashing is via "unplug USB → hold BOOTSEL → plug USB → release → drop .uf2"
* **SWD test points** — 8 pads per half organized as a pogo-clip pattern (CLK/IO/GND/3V3); pads mirrored across halves so a flipped 6-pin clip lands on matching signals
* **4-layer PCB** with split L/R rails — F.Cu signal/copper, In1.Cu split 3V3 planes (L/R), In2.Cu split GND planes (L/R), B.Cu signal/copper
* **QMK firmware**

## Hardware Specs

| | |
|--|--|
| **Dimensions** | 328.62 mm × 102.85 mm (end-to-end, both halves including the inter-half gap; left half 145.67 × 102.85, right half 169.84 × 102.85, inter-half gap 13.11 mm) |
| **MCU** | 2× Raspberry Pi RP2040 (QFN-56) |
| **Flash** | 2× Winbond W25Q128JVPIQ (16 MB QSPI) |
| **LDO** | 2× Texas Instruments LP5907 (3V3, X2SON-4) |
| **Crystal** | 2× 12 MHz (Crystal_SMD_2520-4Pin) |
| **USB ESD protection** | 2× USBLC6-2P6 |
| **Switches** | Gateron KS-33 v2.0 low-profile hot-swap (63 total) |
| **Stabilizers** | Kailh Choc V2 (2.25U and 2.75U key positions) |
| **Per-key RGB LEDs** | 63× SK6812MINI-E reverse-mount |
| **Underglow LEDs** | 27× SK6812MINI-E (B.Cu side) |
| **Host connector** | 2× HRO TYPE-C-31-M-12 (USB 2.0 16P), side-mounted on the outer edge of each half (4 mm plank protrusion, 1 mm USB-C overhang past plank face) |
| **Inter-half connector** | 2× HRO TYPE-C-31-M-12 (same part as host), top-edge mounted near the inner-top corner of each half (4 mm plank protrusion, 1 mm USB-C overhang). Carries A4/A9 VBUS = +5V bridge, A12/B12 = GND, A6/B6 = data (single-wire PIO serial); A7/B7 (D−) and A5/B5 (CC1/CC2) intentionally floating — see Design Notes |
| **Diodes** | 63× SK matrix diodes, 4× power-path Schottky (PMEG2010BELD), 4× LED indicators |
| **Polyfuse** | 2× 1.1 A (Fuse_0603) for USB power input |
| **Ferrite beads** | 2× 600 Ω (FB1/FB2) for VBUS filtering |
| **Case heat-set inserts** | **M2 × L4 × D3.5** brass knurled heat-set inserts (Ruthex-style or equivalent). Print 3.3 mm diameter holes in the case; insert with a soldering iron at ~200°C. Match with M2 screws (length depends on final case stack). |

## BOM

Quantities are rounded up to account for spares — order more than the minimum.

Part | Part number | Qty | Notes / Source
--- | --- | --- | ---
RP2040 MCU | RP2040 (QFN-56) | 2 | LCSC `C2040` / Mouser / DigiKey / direct from Raspberry Pi
QSPI Flash | Winbond W25Q128JVPIQ | 2 | LCSC `C190862` / Mouser / DigiKey
3.3V LDO | TI LP5907SNX-3.3 | 2 | LCSC `C133572` (XDFN-4, 1×1 mm) — 250 mA / 3.3 V. See [LDO history note](#ldo-history) below for why this instead of the Helios-spec'd TLV75533.
12 MHz crystal | 2520 4-pin SMD | 2 | LCSC `C2149204` / Mouser
USB-C receptacle (host + inter-half) | HRO TYPE-C-31-M-12 | 4 | LCSC `C165948` / JLC / AliExpress — same part used for all four positions (J1/J2 outer = host, J3/J4 top = inter-half)
USB ESD | USBLC6-2P6 | 2 | LCSC `C2827693` (SOT-666)
Polyfuse | Bourns MF-FSMF050X-2 (500 mA hold / 1 A trip, 0603) | 2 | LCSC `C210357` / DigiKey (per Helios reference design)
Ferrite bead | 600 Ω 0402 | 2 | LCSC `C160977`
Schottky diode | PMEG2010BELD (SOD-882) | 4 | LCSC `C552820` / DigiKey
Per-key LEDs | SK6812MINI-E (reverse mount) | 70+ | LCSC `C5149201` / AliExpress — order ~10% spare, fragile. Pin **numbers** between vendors differ but physical VDD/VSS/DIN/DOUT corners match
Underglow LEDs | SK6812MINI-E | 30+ | Same as above; same part (`C5149201`)
Switch diodes | 1N4148W (SOD-123) | 70+ | LCSC `C81598` / Mouser. Footprint `onigaku:D3_SMD_v2` is SOD-123, **not** SOD-323
Switches | Gateron KS-33 v2.0 low-profile | 63 | Keebio / Keychron / Gateron direct (hand-place; not from JLC stock)
Hot-swap sockets | Gateron KS33 hot-swap socket | 63 | Same source as switches
Stabilizers | Kailh Choc V2 (2u for 2.25U and 2.75U keys) | 2 sets | Choc V2 — **not** MX stabilizers
0603 100 nF ceramic caps | CC0603KRX7R9BB104 (or equiv 0.1µF X7R) | 90+ | LCSC auto-matches — confirm prompt is benign
0402 caps (LDO bypass) | varies (see schematic) | as schematic | LCSC `C1525` / `C15525` / `C52923` etc.
0402 resistors | varies | as schematic | LCSC `C25905` (5.1k) / `C11702` (1k) / `C25744` (10k) / `C25100` (27R)
BOOTSEL push button | 4×4×1.5 mm SMD | 2 | LCSC `C589221`
0402 status LEDs | red / blue / green (per spec) | 4 | LCSC `C130719` / `C130724`

## Software (QMK)

### Where the keyboard config lives

The umiko QMK keyboard definition lives in a **fresh clone of upstream QMK**, not in the older `idorurez/qmk_firmware` fork (which is on the `bakekujira` branch and carries stale history for an unrelated older board). Clean-slate approach:

```
git clone --depth 1 https://github.com/qmk/qmk_firmware.git ~/dev/keyboard/qmk_umiko
cd ~/dev/keyboard/qmk_umiko
git submodule update --init --recursive   # ~2 GB, ~10 min. Required for RP2040 (pico-sdk submodule)
```

The `keyboards/umiko/` folder is authored by-hand in this repo. Files: `info.json` (matrix pins, 5×8 scanning matrix, split serial vendor driver on GP0, LAYOUT_all with 63 keys extracted from the schematic), `rules.mk`, `config.h`, `keymaps/default/keymap.c`, `readme.md`. Copy these into `qmk_umiko/keyboards/umiko/` when setting up a fresh clone. (TODO: move keyboards/umiko/ into this repo and symlink or use QMK's external-keyboard support so it lives with the PCB source.)

### Toolchain (Windows) — verified working steps

QMK's CLI **requires** MSYS2 on Windows (its `MSYSTEM` environment check hard-fails in git-bash or a plain Windows shell). The steps below are the exact recipe that worked here — the QMK docs miss a few things (new pkg locations, Python home dir on MSYS2, `keyboard.json` vs `info.json`, jsonschema/rpds-py wheel build failure). Follow verbatim.

**1. Install MSYS2 to `C:/msys64`**

Download from https://www.msys2.org/. Default installer, install to `C:/msys64`. For silent install: `msys2-x86_64-latest.exe install --confirm-command --accept-messages --root C:/msys64`.

**2. Install packages via pacman (in the MSYS2 MINGW64 shell)**

```
pacman -Syu --noconfirm --disable-download-timeout
yes '' | pacman -S --noconfirm --needed --disable-download-timeout \
    base-devel git \
    mingw-w64-x86_64-python-pip mingw-w64-x86_64-python-cffi \
    mingw-w64-x86_64-python-pillow mingw-w64-x86_64-rust \
    mingw-w64-ucrt-x86_64-arm-none-eabi-gcc \
    mingw-w64-ucrt-x86_64-arm-none-eabi-binutils \
    mingw-w64-ucrt-x86_64-arm-none-eabi-newlib
```

Gotchas:
- The `arm-none-eabi-*` toolchain packages are only under the **UCRT64 repo**, not MINGW64 — that's why the package prefix is `mingw-w64-ucrt-x86_64-` for those three only.
- `yes ''` is required to answer pacman's group-membership prompts (which `--noconfirm` alone doesn't handle).
- `python-pillow` and `rust` are prerequisites for the QMK pip install — omitting them causes rpds-py / pillow to try building from source and fail.

**3. Install QMK CLI via pip (still in MSYS2 MINGW64 shell)**

```
python -m pip install --user --break-system-packages 'jsonschema<4.18'
python -m pip install --user --break-system-packages qmk
```

Notes:
- `--break-system-packages` is required because MSYS2's Python is PEP 668-managed. It just means "install into user site-packages" — safe.
- Pinning `jsonschema<4.18` avoids the modern `rpds-py` Rust build (which fails on MSYS2's Python ABI). Older jsonschema uses `pyrsistent` instead.
- Ensure `USERPROFILE` is set correctly before running pip, or the install path will contain a literal `~` and Python won't find its own packages. Set: `export USERPROFILE='C:\Users\<you>'`.

**4. Set up qmk_home + junction**

QMK CLI looks for qmk_firmware at `~/qmk_firmware` on the Windows side (`C:/Users/<you>/qmk_firmware`), regardless of the `user.qmk_home` config value. The cleanest fix is a directory junction:

```
cmd /c "mklink /J C:\Users\<you>\qmk_firmware C:\Users\<you>\dev\keyboard\qmk_umiko"
```

**5. Test compile**

Requires setting a few env vars every time you run qmk in MSYS2. The `scripts/qmk_compile.sh` wrapper in this repo handles it — just run:

```
scripts/qmk_compile.sh
```

or if you prefer to do it by hand from an MSYS2 MINGW64 shell:

```
export USERPROFILE='C:\Users\<you>'
export HOME=/home/<you>
export PATH=/c/Users/<you>/.local/bin:/ucrt64/bin:$PATH
qmk compile -kb umiko -km default
```

Output UF2 lands at `qmk_umiko/umiko_default.uf2` (~74 KB).

### QMK config: `keyboard.json` (NOT `info.json`)

Current QMK expects each keyboard folder to have `keyboard.json` at the top level (the old `info.json` name causes `qmk compile -kb umiko` to fail with `invalid keyboard_folder value`). Umiko's config is at `qmk_umiko/keyboards/umiko/keyboard.json`.

### Split handedness

Umiko has no dedicated handedness pin (`SPLIT_HAND_PIN`), so the default UF2 relies on QMK's USB-detect-based master election (whichever half enumerates as a USB HID device becomes master; the other becomes slave over the inter-half serial link). This may need tweaking if it doesn't behave — options include compile-time `MASTER_LEFT`/`MASTER_RIGHT` defines or `EE_HANDS` (per-half EEPROM handedness). TODO: revisit after first split test.

### Flash

Each half is flashed independently via BOOTSEL:

1. **Unplug USB** from the half you want to flash
2. **Hold the BOOTSEL button** on that half (SW1 left, SW2 right)
3. **Plug USB back in** while holding BOOTSEL
4. **Release BOOTSEL** — the half mounts as a USB mass-storage device (RPI-RP2)
5. **Drag-and-drop the `.uf2`** for that half onto the drive — it auto-reboots into the new firmware

Note: on this board the W25Q128 flash arrives blank from JLC, so first plug-in enters BOOTSEL automatically (RP2040 defaults to USB mass-storage mode when the QSPI flash contains no valid firmware). After first flash, subsequent re-flashes need the BOOTSEL button held.

No reset button on the board — power-cycle + BOOTSEL handles all flashing.

**Case-top BOOTSEL access:** the BOOTSEL buttons (SW1 left, SW2 right) are small SMD tactile switches on F.Cu that would be inaccessible with the plate + switches installed. The case top plate has a **~2 mm pinhole above each button** aligned to its PCB position — press with a paperclip, SIM ejector, or dedicated reset pin to activate BOOTSEL without disassembling. Pattern used by most low-profile keyboards (NuPhy / Keychron K-series). Coordinates in PCB frame:
* SW1 (left half BOOTSEL): (166.01, 57.53)
* SW2 (right half BOOTSEL): (188.17, 77.52)

### Split serial: what's happening on the wire

Umiko routes QMK's split-transport protocol over a **single-wire half-duplex PIO serial** running on **GP0** of each RP2040. GP0 connects to the D+ pin of each half's inter-half USB-C connector (J3 left, J4 right). A short USB-C-to-USB-C cable between J3 and J4 ties the two GP0 lines together and provides the 5V bridge (VBUS pins A4/A9) and GND (A12/B12).

QMK config:
- `info.json` → `split.serial.driver = "vendor"` (uses RP2040 PIO peripheral for the serial protocol)
- `config.h` → `SERIAL_USART_TX_PIN = GP0` (single pin used for both TX and RX in half-duplex)

The inter-half USB-C is **not** a real USB port — it's just a convenient 4-conductor connector shape (VBUS + GND + D+). Do not plug either J3 or J4 into a computer or USB device.

## Assembly Notes

### Soldering Order

1. **Smallest components first** — 0402 resistors/caps, then 0603, then SMD ICs
2. **MCUs (RP2040)** — these have an exposed thermal pad on the bottom that needs to be soldered (heat from below, use a hotplate or reflow station). Hand-soldering with a fine tip is doable but tricky.
3. **Flash chips, LDOs, ESD protection** — small SMD work
4. **Crystals** — fragile, place after the heavy soldering nearby is done
5. **USB-C receptacles** (HRO TYPE-C-31-M-12) — SMD signal pads + 4 THT shield legs + 2 NPTH alignment pegs; body sits on top of the PCB. Can be reflowed or hand-soldered.
6. **LEDs** — start with underglow (back side), then per-key (front side). Test as you solder.
7. **Switch sockets** (Kailh / Gateron KS33 hot-swap) — last to give all-around access during earlier soldering
8. **Stabilizers** — clip in before testing switches
9. **Switches** — plug in last, after firmware flash works

### Soldering Hints

* For 0402 / 0603 SMD pads, **flux liberally** and keep your tip tinned with a fine bead of solder
* For Kailh / KS-33 hot-swap sockets, **pre-tin both pads**, then place the socket and reheat one pad at a time while pressing down
* For RP2040's exposed thermal pad, **use the via stitching as a heat sink** — solder paste + hot air, or paste + skillet reflow

### LEDs

* The **underglow LEDs are reverse-mounted on B.Cu** (back of board) — their pads are on B.Cu but the body sits below the PCB. **Bend the terminals down to the soldering pads** before reflowing or hand-soldering.
* **Solder LEDs in the data chain order** and **test as you go** — if one is bad, all LEDs after it in the chain won't light up
* If an LED looks broken or melted after soldering, it's probably broken — desolder and replace

### Stabilizers

The stabilizer cutouts on this PCB are sized for **Kailh Choc V2 stabilizers**. Standard MX / Cherry-style stabilizers **will not fit** the cutout. Stabilizers are needed at the 2.25U and 2.75U thumb keys.

**Why not Gateron Low Profile (GLP) plate-mount stabilizers?** Because Gateron LP stabs mechanically limit switch travel — switches don't bottom out fully when installed with GLP stabs, requiring very specific keycaps to compensate. This is a stab-side mechanical constraint, not a cutout dimension issue, so redesigning the plate for GLP dimensions would not fix it. Per direct advice from bakingpy (author of `keebio/kb-plategen`, whose Choc V2 spec `make_plate.py` implements): "Don't use GLP stabs, go with Choc V2 ones." Kailh Choc V2 is the intended stab choice for Gateron KS-33 v2.0 switches and this design.

The stab cutouts follow the Choc V2 spec from `keebio/kb-plategen`, encoded in `scripts/make_plate.py`:
* Body A: 5.95 × 7.95 mm at (±12, ±0.3441)
* Neck B: 4.55 × 6.25 mm at (±12, ±6.7559)
* Wire slot: 24 × 1.4 mm at (0, ±8.2809)
* r=0.5 mm fillet, unioned into one outline per stab position
* Sign (±) depends on wire direction — north for SW_30 / SW_35 (bottom-edge keys), south for everything else

#### bakingpy's two-level plate design (adopted)

Rather than a single-layer 1.2 mm plate with all cutouts full-depth, this design uses a **2.2 mm plate with a two-level pocket at each stab position** — a novel approach shared by **bakingpy (Danny at Keebio)** as a printable STL sample (see `reference/choc_v2_stab_holder.stl`). The upper 1.2 mm level is shaped to the housing footprint (body A + neck B + wire slot), providing the exact clip-engagement depth for a Kailh Choc V2 stab. The lower 1.0 mm level uses a different, narrower shape to provide wire clearance below the housing.

**Why this is better than a naïve full-depth plate:**
* **Sturdier**: 2.2 mm of plate material is measurably more rigid than 1.2 mm, and the un-cut plate volume between the two levels (where their shapes differ) adds mechanical strength across each stab position.
* **Low-profile-friendly**: total keyboard Z-stack is unchanged — the extra thickness sits within the plate-to-PCB gap that the switch body needs anyway.
* **Choc V2 stab-friendly**: housing engagement depth is dimensioned to the actual Kailh spec, so clips grip and the wire has proper clearance.

This design was **incorporated directly and printed in PTFE with no additional expansion adjustments needed** — bakingpy's dimensions handle FDM tolerance for that print material out of the box. If you're printing in a different material (PLA / PETG / ABS / SLA resin), you may still need some outward relief per the tolerance-tuning section below.

#### FDM tolerance tuning (materials other than PTFE)

When printed as an integrated plate (Choc V2 stab cutouts + KS-33 v2.0 switch cutouts on the same plate face), the canonical `make_plate.py` dimensions come in **tight for FDM tolerance in most materials**. Switches (14 mm cutouts) fit press-fit and correctly, but stab housings bind on install and the wire drags in its slot. Iterate on the cutout dimensions in your CAD until the stabs seat and the wire moves freely — this is expected FDM work and every printer will need slightly different numbers.

**The principle: asymmetric relief, always outward from the switch cutout.**

The plate material between each stab cutout and the 14 mm switch cutout is thin (~2 mm) — thinning it further risks structural failure during install. So all tolerance relief goes on the **outward-facing edges** of each cutout:

* **Wire slot**: relieve on the **far-from-switch** long side (the outer wall of the wire trough). Never touch the switch-facing side.
* **Neck B**: relieve on the **far-from-switch** face (the outer wall of the neck pocket). Never touch the switch-facing side.
* **Body A**: relieve on the **outboard** face — the face that points away from the keyboard center (left face of the left stab, right face of the right stab). Never touch the switch-facing side.

Expect to need **more relief on the outboard edges of Body A** than the wire/neck features — the stab housing exerts the most lateral install force on the outer walls of the body pocket, and that's typically where binding is worst. Iterate: file, test-fit, transfer the successful delta back into CAD (or Move Face in SW), reprint.

Widening symmetrically, or inward toward the switch cutout, risks the plate breaking during install pressure. Always relieve outward.

**Why NOT back-port to `make_plate.py`:** the script's job is to produce cutouts true to the Kailh Choc V2 datasheet spec. Anyone using it (CNC-milling a metal plate, SLA-printing, injection-molding, or FDM on a differently-tuned printer) should start from the canonical spec and apply their own downstream tolerance. Baking a fudge factor into the script would bias future builders in the wrong direction. **The tolerance lives in your CAD/slicer downstream of the plate generator, not in the generator itself.**

**Where the edits live in this project's SW file:** individual `Move Face` operations are preserved as separate entries in the SolidWorks feature tree of the plate/case CAD — they aren't collapsed into the imported STEP body. Anyone iterating on the tolerance (tighter/looser, per-stab, or for a different manufacturing process) can find each Move Face feature in the tree, right-click → **Edit Feature**, adjust the distance, and rebuild. No need to redo the surgery from scratch or reimport the STEP.

### SWD Debug

If you need to flash via SWD (rare — BOOTSEL handles most needs):

* TP1-TP4 are SWD signals on the left half (CLK, IO) and right half (CLK, IO)
* TP5-TP8 are power references (GND_L, 3V3_L, GND_R, 3V3_R)
* All 8 pads are arranged in two mirrored 4-pad columns at 2.54 mm pitch (Adafruit pogo-clip 5433 compatible)
* Pad order on left is top-to-bottom: **CLK / IO / GND / 3V3**
* Pad order on right is mirrored: **3V3 / GND / IO / CLK** — so a flipped pogo clip lands on matching signals on both halves

## Manufacturing Notes (JLCPCB)

### Design rule clearances

This board is set up for **JLCPCB's standard 4-layer pricing tier**:

* **Minimum clearance**: 0.1 mm (4 mil) — JLC's standard min for 4-layer at no surcharge
* **Net class clearance**: 0.1 mm
* **Track widths**: 0.2 mm (signals), 0.3 mm (power/GND) — well above the 0.1 mm minimum
* **Min via**: 0.4 mm diameter / 0.2 mm drill
* **Min hole**: 0.3 mm (matches JLC standard)

If you want **tighter clearances** (down to 0.089 mm / 3.5 mil), JLC will accept the files but add a **+20% surcharge** on 4-8 layer boards.

### JLC fab options used for this design

* **Layers**: 4
* **Different Design in Panel**: 2 (left and right halves are separate outlines)
* **Min hole size**: 0.3 mm
* **Min track/spacing**: 5/5 mil (well within standard)
* **Outer copper**: 1 oz
* **Inner copper**: 0.5 oz (default for 4-layer)

### Fab file generation

Run `python scripts/make_jlc_files.py` from the project root. It produces three upload-ready files in `fab/`:

* `umiko-jlc-gerbers.zip` — gerbers + Excellon drill files (the fab upload)
* `umiko-bom-jlc.csv` — JLC-formatted BOM (header `Comment,Designator,Footprint,JLCPCB Part #（optional）`, comma-separated designators, ranges expanded)
* `umiko-cpl.csv` — JLC-formatted CPL (header `Designator,Mid X,Mid Y,Layer,Rotation`, mm-suffixed coords at 4-decimal precision, integer rotations 0–359, capitalized `Top`/`Bottom`)

The script bakes in LCSC overrides for parts whose schematic symbols don't carry an LCSC field (matrix diode `D3_SMD_v2` → `C81598`, per-key + underglow LED `YS-SK6812MINI-E` → `C5149201`). Add new mappings to the `LCSC_OVERRIDES` dict at the top of the script as needed.

It also maintains a `DNP_VALUES` set of schematic Values that are **excluded from both the BOM and CPL** so JLC won't try to assemble them — they're hand-soldered after the boards arrive. Current DNP list:

* **`YS-SK6812MINI-E`** (90 components: 63 per-key + 27 underglow) — the per-key LEDs are reverse-mount (body sits in a PCB cutout, lens facing F.Cu), not a standard PnP placement; the underglow variant is normal SMD but the OPSCO `C5149201` chip layout is 180° from our footprint's pin-corner convention. Hand-soldering side-steps both issues. Source: order ~10% spare from LCSC `C5149201` / AliExpress.
* **`KEYSW`** (63 components: Gateron KS-33 hot-swap sockets) — not in JLC's standard parts inventory. Source separately from Keebio / Gateron direct / AliExpress and solder with the switches.

### CAD exports (case / plate design)

Run `python scripts/make_cad_files.py` for SolidWorks-ready 3D, and `python scripts/make_plate.py` for the plate. Outputs land in `cad/` (per-group + assembly + per-half STEP, board-outline DXF, plus `umiko-plate.step` and `umiko-plate-cutouts.dxf`). Both scripts are **read-only on the source PCB** — all transforms happen in memory / on a self-deleting temp file; you can run them any time without affecting `umiko.kicad_pcb`.

* **Board thickness: 1.6 mm** — JLCPCB standard 4-layer; tolerance **±10% (≈ 1.44–1.76 mm)**, so give the case PCB pocket clearance up to ~1.76 mm.
* **Plate thickness: 1.2 mm** — Choc V2 stabilizer spec; the MX-stem KS-33 clips tolerate it.
* **Switches/keycaps are on `F.Cu`** (the front/typing surface); the **hot-swap sockets are on `B.Cu`** (the back). Note: the switch *footprints* are placed on the `B.Cu` layer — that's just where the socket pads live — but the switch *bodies* render on `F.Cu`. The plate sits on the `F.Cu` side; reference it from the `F.Cu` face and mate the plate underside to the switch plate-shelf.
* **STEP thickness compensation (important):** KiCad's STEP exporter models only the FR4 substrate — it omits the outer copper (~0.07 mm) and soldermask (~0.02 mm), so a 1.6 mm board would otherwise export as ~1.51 mm (and a 1.2 mm plate as ~1.11 mm). `make_cad_files.py` (board/assembly/halves) and `make_plate.py` (plate) **bump the nominal thickness +0.09 mm** so the exported solids measure a true **1.6 mm** and **1.2 mm**. Component X/Y placement is unaffected; only the Z thickness is corrected.
* **How components track the compensation:** correcting the board thickness moves the F.Cu face up, and **F.Cu-layer parts ride up with it automatically** (caps, resistors, RP2040/flash/LDO, crystals, ferrites, BOOTSEL) — they stay flush. The switch *bodies*, however, are anchored to their `B.Cu` socket footprints, so they do **not** ride the F.Cu compensation and would otherwise sit 0.09 mm below the raised F.Cu surface. `make_cad_files.py` therefore also nudges the switch 3D-model offset (`-4.1` → `-4.19`) in the temp export board so the switch bodies rise 0.09 mm and sit flush with the compensated F.Cu (typing) face. Net: on the compensated board every component sits at its true height — F.Cu electronics and switches flush on F.Cu, sockets/LEDs on B.Cu.
* **PLA case clearance (FDM print):** design the case inner cavity **0.3–0.5 mm larger per side** than the PCB outline. Print tolerance (typically ±0.1–0.2 mm per dimension, plus first-layer squish that grows internal cavities inward) dominates; PLA shrinkage (~0.3–0.5%) and the PLA vs. FR4 thermal differential (~63 ppm/°C, ≈ 0.3 mm over a 15 °C swing on a ~350 mm board) are smaller contributors. Use **0.5 mm per side** on the full-board long axis and **0.3 mm per side** on the short axis; **0.2 mm** in Z between the board and its ledge is plenty. Print a small corner test chunk first and tune your slicer's **XY size compensation** until the PCB slides in with light friction before committing to a full-case print.

### JLC upload gotcha

**Updates to BOM or CPL won't apply unless you restart the upload from the project menu.** Re-uploading just the BOM/CPL after a failed attempt will appear to succeed but JLC keeps the prior validation state, leading to errors like "Failed processing the CPL file" or "BOM doesn't match CPL" that don't actually correspond to the current file contents. The fix is to back up to the **PCB quote** step in JLC's flow and start the whole upload over (gerbers → BOM → CPL).

### CPL format quirks (learned the hard way)

JLC's CPL parser is unusually strict about:

* **Rotation must be a non-negative integer 0–359** — KiCad's default `-90.000000` will be rejected with "Failed processing the CPL file". `make_jlc_files.py` normalizes to integer mod 360.
* **Coordinates must be fixed at 4-decimal precision** — variable precision like `8.647045mm` also fails. The script formats with `.4f`.
* **Headers must match JLC's sample exactly**, including the fullwidth Chinese parens in the BOM's `JLCPCB Part #（optional）`.

## Design Notes

* **No reset circuit** — flashing is via BOOTSEL alone. RP2040's `~RUN` pin has an internal pull-up; leaving it floating is safe.
* **Inter-half connection** uses **USB-C (HRO TYPE-C-31-M-12, top-edge mounted)** carrying QMK PIO-serial split over a **single wire on D+** (A6/B6 are tied together, A7/B7 D− unused). VBUS (A4/A9) bridges 5 V across halves, GND (A12/B12) ties them. The 5 V bridge lets a single host USB-C power both halves through Schottky OR-ing. **CC1 and CC2 (A5/B5) on J3/J4 are currently floating** — design choice for the serial-bridge use case (the link doesn't speak USB protocol so no CC negotiation is needed). If a host USB-C cable is ever accidentally plugged into J3 or J4, a floating CC pin can pick up VCONN; the conservative add is 5.1 kΩ pull-downs to GND on each CC line at the connector. The host USB-C connectors (J1/J2) already have proper 5.1 kΩ CC pull-downs (R4/R5 and R21/R22).
* **Inter-half data is single-wire, not differential** — D+ carries half-duplex 12 MHz PIO serial; D− is intentionally floating. This is the same pattern as TRRS-based RING1 splits, just routed through USB-C-shaped pins. The connector is **not** an actual USB device port and should not be addressed as one in firmware.
* **Connector placement** — the two host USB-C jacks (J1/J2) are mounted on the outer-side edges of each half (aligned with the Q-row keycap top); the inter-half USB-C jacks (J3/J4) are on the **top edge** of each half, near the inner-top corner, so a short USB-C-to-USB-C cable bridges between them across the keyboard's top edge with minimal slack. All four USB-C connectors sit on Edge.Cuts plank protrusions of **4 mm** (with the connector's plug face overhanging the plank by **1 mm**, giving a clean 1 mm recess inside a planned 6 mm case wall).
* **Each half is fully independent** — you can power and flash each half on its own. Either half can be the master.
* **Edge cuts** have 1.25 mm fillets on all corners. Both halves form closed loops; no breakaway tabs (order as 2 separate boards, or as a customer panel).
* The `onigaku` repo (sibling library) contains the custom symbols, footprints, and 3D models referenced by this design. Must be cloned alongside this repo for KiCad to find the libraries.

### LDO history

The 3.3 V LDO for each half (U2 and U10) is `LP5907SNX-3.3` (TI, XDFN-4, LCSC `C133572`, 250 mA). This diverges from the 0xCB Helios reference design, which spec's a `TLV75533PDQNR` (TI, X2SON-4, LCSC `C2861882`, 500 mA). The history of why:

1. **Schematic originally matched Helios:** `TLV75533PDQNR` in the Value field, X2SON-4 footprint. Helios uses the same `PCM_0xcb:LP5907SNX-3.3-NOPB` schematic symbol for both parts since the 4-pin layout is identical (1=IN, 2=GND, 3=EN, 4=OUT).
2. **JLC ran out of TLV75533PDQNR in the X2SON-4 package** (TI X2SON parts have had recurring supply issues through 2025–2026; current LCSC and JLC stock for `C2861882` is zero, with no clear restock date). The pin-compatible LP5907 in the same XDFN-4 (1×1 mm) footprint was substituted to keep the existing PCB working without a layout change.
3. **The Value / MPN fields in the schematic weren't updated** during the substitution, so for a while the repo said `TLV75533PDQNR` while the placed chip was actually LP5907. This was confusing for anyone reading the BOM. **Fixed as of this commit:** Value, MPN, LCSC, Footprint, Datasheet for U2/U10 now all consistently describe the LP5907 that's actually placed.

**Why 250 mA is sufficient here:** Per-half 3.3 V load is ~150 mA peak — RP2040 (~50 mA active) + W25Q128 flash (~15 mA) + indicator LEDs (few mA) + OLED (~20 mA) + biases. **Per-key RGB LEDs are powered from VBUS 5 V, not from the 3.3 V rail**, so they don't load the LDO. The LP5907 has ~1.7× headroom over peak load.

**If a future revision needs the full 500 mA** (e.g. adding Bluetooth, a larger display, encoders on 3.3 V, or expansion headers that hand the rail out to user-added loads), the options are:

* **`TLV75533PDQNR` (X2SON-4, `C2861882`)** — drop-in for the current footprint *if* JLC has stock when you order. Check first.
* **`TLV75533PDBVR` (SOT-23-5, `C404027`)** — same chip in a larger, more reliably-stocked package. Requires a footprint swap on the PCB and a schematic-symbol replacement (5-pin: pad 5 = OUT, pad 4 = NR; the LP5907 4-pin symbol won't drive this correctly). Worth the rework only when the extra current is genuinely needed.

This note exists so future-you (or a contributor) doesn't re-investigate this from scratch.

## Stretch / Future Ideas (Rev 2)

* Build a matching case (likely integrated-plate style given the low-profile switches — see design notes)
* Build a plate (Kailh Choc V2 plate cutouts)
* OLED breakout board for SSD1306 / SH1106 (the inter-half I²C lines `SCL_*` / `SDA_*` are currently broken out but unwired)
* Sound and speakers (piezo or similar)
* Optional reset buttons per half (in case BOOTSEL alone proves too cumbersome)
* **Move BOOTSEL buttons away from U12 OLED area.** SW2 (right BOOTSEL) at (188.17, 77.52) sits close enough to U12 at (192.35, 130.19) that the OLED daughterboard PCB partially covers it once installed, complicating both case cutout design and BOOTSEL access. Relocate to an uncluttered PCB area — ideally along an outer edge or in the corner opposite the OLED.
* **Lower-profile OLED mounting.** Current design uses through-hole 4-pin header (2.54 mm pitch) → daughterboard sits ~10–12 mm above the main PCB, forcing the case OLED cutout to accommodate the entire daughterboard body (not just the display window). Options for v2:
  * **Low-height SMD pin headers** (e.g. 1.27 mm pitch short-body variants, ~3–5 mm mated height) → drops the stack considerably.
  * **Board-to-board connectors** (Hirose DF13 / DF23, JAE FI-X, or similar) with a matching mate on the daughterboard → ~2–4 mm mated height, but requires a daughterboard designed for it.
  * **Direct SMD OLED module** — solder the raw SSD1306 module (flex cable + display) directly onto main-PCB SMD pads. Eliminates the daughterboard entirely; case cutout only needs to clear the display window. Highest integration, lowest profile, but pads must match the specific module chosen.

## Inspiration

This design borrows ideas from:

* marvelous65 split — TKL split with separate inter-half data path
* [0xCB-Helios](https://github.com/0xCB-dev/0xCB-Helios) — schematic patterns for RP2040 + dual flash + LDO
* [0xCB-libs](https://github.com/0xCB-dev/0xCB-libs) — footprints for RP2040, W25Q128 flash (WSON8), LP5907 (X2SON-4), USB-C receptacle, SOD-882 Schottky and other small SMD parts used throughout this design

## Credits

* **bakingpy (Danny) at [Keebio](https://keeb.io)** — an enormous thank you. bakingpy authored [`keebio/kb-plategen`](https://github.com/keebio/kb-plategen) which is the source of the Kailh Choc V2 stab cutout spec that `scripts/make_plate.py` implements, personally recommended the Kailh Choc V2 stabilizer path over Gateron Low Profile after weighing switch-travel tradeoffs, and shared a printable [reference STL](reference/choc_v2_stab_holder.stl) demonstrating a novel two-level plate design that produces a sturdier, low-profile-friendly, Choc-V2-stab-friendly plate. That design was adopted directly for this build and produces working stabs in PTFE prints with no additional tolerance adjustments needed.
* The **QMK community** — for firmware help and their patience (without which this wouldn't exist).
* **Conor at [KeebSupply](https://keebsupply.com)** — manufacturing and build feasibility advice (KS-33 hot-swap pad clipping, stabilizer compatibility, fab tolerances).

## License

PCB files: CERN OHL v2 — Permissive (or your preferred license; verify before forking).
Firmware: GPL-2.0 (inherited from QMK).
