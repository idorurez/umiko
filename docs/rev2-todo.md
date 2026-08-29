# Rev2 TODO — narrow scope

## Underglow (edge-mounted side-view)
- [x] Decision: No pogo pads, no satellite PCB, no second LED driver
- [x] Architecture: Single GP25 chain per half, keep 63 per-key SK6812MINI-E reverse-mount unchanged
- [x] Part selected: SK6812SIDE-A 4.0×2.0×1.5mm side-view (thin 0.85mm Adafruit 4691 variant same pads, compatible)
- [x] Footprints created: `files/footprints/SK6812-4020-SideView.pretty/SK6812-4020-SideView.kicad_mod` and `_0p85mm` variant
- [x] Datasheet: DIN/VDD/DOUT/GND left→right toward edge, 4 pads 1.0mm pitch 0.6×0.9mm land, 5V 800kHz GRB
- [x] Decision: 16.7mm pitch (60/m) — 30 left / 33 right = 63 underglow total, 60 left total / 66 right total = 126 with per-key
- [ ] Measure actual Edge.Cuts perimeter in KiCad (left/right, not bounding box)
- [ ] Map keepouts: USB-C, inserts, screws, support ring 2×2mm hollow, OLED, TRRS
- [ ] Draw usable LED path offset 0.8-1mm from Edge.Cuts
- [x] Power budget analysis (2026-08-28): Rev 1 polyfuse (MF-PSMF110X-2, marked 500 mA in Value but likely 1.1 A hold in reality) is undersized for 126-LED Rev 2. Worst-case per half at brightness 150/255: left 60 LEDs × 45 mA × 59% = ~1.56 A, right 66 LEDs × ~1.72 A. Solid-white sustained peaks exceed 1 A hold. **Decision: upgrade polyfuse to 2 A hold / 4 A trip so we can keep `RGB_MATRIX_MAXIMUM_BRIGHTNESS` at 150 (brighter than expected). Bench-verify final cap after Rev 2 build.**

## Polyfuse upgrade (Rev 2)
- [ ] **Replace F1 + F2** with 2 A hold / 4 A trip polyfuse. Bourns candidate: `MF-FSMF200X-2` (2.00 A hold / 4.00 A trip). Package is likely **1206 (3.2 × 1.6 mm)** — larger than the current 0603.
- [ ] **Verify LCSC availability + exact package** at order time. If MF-FSMF200X-2 isn't stocked, plausible fallbacks in the same 1206 range: MF-FSMF250X-2 (2.5 A), MF-USMF200 (2 A, 1812). Any 2 A+ hold / 4 A+ trip polyfuse works — physical footprint dictates the pick.
- [ ] **Update PCB footprint** from `Fuse:Fuse_0603_1608Metric` → `Fuse:Fuse_1206_3216Metric` (or the matching pretty for the chosen part). Requires PCB redraw at F1/F2 positions on both halves.
- [ ] **Update BOM:** MPN + LCSC + value fields on F1/F2 after part is finalized. Current placeholders in schematic: Value=`2A`, MPN=`MF-FSMF200X-2`, LCSC=`TBD-verify` (from Aug 2026 update).
- [ ] **Verify USB-C host will actually supply 2 A.** Basic USB-C is 900 mA. Need at least USB-C 5V/1.5A (upgraded) or 5V/3A profile. Board doesn't negotiate PD, so relies on host default. Cheap hubs may cap current — document in README as "requires ≥1.5A USB-C source for full-brightness Rev 2 operation."
- [ ] Build 2-4 LED optical coupon with Proto-pasta iris material, test diffusion and seam
- [ ] New KiCad symbol for SIDE pinout, update schematic, maintain GP25 single chain, add 0-ohm bypass for optional DNP positions (empty breaks chain)

## LED ordering numbers (with spares) — decision 16.7mm
- Per-key: 63 total (30 left, 33 right) SK6812MINI-E — order 70+ (10% spare)
- Underglow side-view 16.7mm: 30 left + 33 right = 63 underglow → 63 + 15% = ~72-75 order
- Total to order for 16.7mm: 70 per-key + 75 underglow = ~145 LEDs
- Other densities for reference: 20mm sparse 42 underglow → ~50 order, 15mm dense 69 → ~80 order

## Switch support (keep narrow)
- Existing: Gateron KS-33 (and likely KS-27 compatible — verify official drawings before claiming)
- Candidate: MX + KS-33 combo (same MX stem, same 14mm plate cutout family, height difference lives in case standoffs/middle, not plate cutout — verify plate thickness/clip engagement from official drawings)
- Not candidate for Rev2: Choc V1 (different rectangular cutout, different stem, no cap overlap, requires 2 plate types)
- Mill-Max sockets: evaluate hole diameter / leg thickness for KS-33 vs MX, insertion force, board thickness, hand-assembly — do not assume JLC places them
- Required verification: obtain official KS-33 and MX mechanical drawings, compare PCB seating plane, underside of plate/retention-clip plane, specified plate thickness, locating posts, required top-plate opening

## Other Rev2 items retained
- Replace ambiguous D5 SOD-882D footprint (compare rotation directly with known-good D1, do not reason from math alone — B.Cu mirroring)
- Verify OLED pin order and F.Cu/B.Cu mirroring physically, move display closer to top edge, preferred 1.09" 128×64 SSD1312 or 1.3" SH1106, expose left-side I2C
- Deliberately map RGB positions
- Larger case-integrated BOOTSEL (QSPI_SS pin 57 to GND, RUN active-low reset)
- Optional sound hardware
- Replace EOL Kailh Choc V2 stabilizers (use 2U for 2.25U/2.75U/2U backspace positions)
- Add at least one GPIO status LED
- Consider SPLIT_USB_DETECT
- Case support ring ~2mm tall × 2mm thick hollow
- At-surface lettering (changed 2026-08-11)
- Prefab gate: `kicad-cli --refill-zones --save-board --severity-error --exit-code-violations`

## Power / firmware
- led_count currently 90 (split_count [42,48] left 12+30 right 15+33). Update to new counts after layout.
- Pins: GP0, GP2–GP16, GP25 (verify unused pins against schematic/PCB)
- Y49 short: +5V_R to GND_R around (322,55) on B.Cu — already fixed in latest

