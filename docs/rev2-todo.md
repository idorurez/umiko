# Rev2 TODO — narrow scope

## Underglow (edge-mounted side-view)
- [x] Decision: No pogo pads, no satellite PCB, no second LED driver
- [x] Architecture: Single GP25 chain per half, keep 63 per-key SK6812MINI-E reverse-mount unchanged
- [x] Part selected: SK6812SIDE-A 4.0×2.0×1.5mm side-view (thin 0.85mm Adafruit 4691 variant same pads, compatible)
- [x] Footprints created: `files/footprints/SK6812-4020-SideView.pretty/SK6812-4020-SideView.kicad_mod` and `_0p85mm` variant
- [x] Datasheet: DIN/VDD/DOUT/GND left→right toward edge, 4 pads 1.0mm pitch 0.6×0.9mm land, 5V 800kHz GRB
- [ ] Measure actual Edge.Cuts perimeter in KiCad (left/right, not bounding box)
- [ ] Map keepouts: USB-C, inserts, screws, support ring 2×2mm hollow, OLED, TRRS
- [ ] Draw usable LED path offset 0.8-1mm from Edge.Cuts
- [ ] Choose density: 20mm pitch (~20 left / 22 right, total 42 underglow + 63 per-key = 105 total) vs 16.7mm pitch (~30/33 per half, total 126) vs 15mm pitch (~33/36)
- [ ] Recalc power: worst white 45mA/LED, typical mixed 15-20mA, RP2040 100mA, OLED 20-40mA, polyfuse 500mA hold / 1A trip per half — set `RGB_MATRIX_MAXIMUM_BRIGHTNESS` 100-120 after bench, not 150
- [ ] Build 2-4 LED optical coupon with Proto-pasta iris material, test diffusion and seam
- [ ] New KiCad symbol for SIDE pinout, update schematic, maintain GP25 single chain, add 0-ohm bypass for optional DNP positions (empty breaks chain)

## LED ordering numbers (with spares)
- Per-key: 63 total (30 left, 33 right) SK6812MINI-E — order 70+ (10% spare)
- Underglow side-view: provisional 20-33 per half depending on pitch:
  - Sparse 20mm: 20 left + 22 right = 42 underglow → 42 + 10% = ~46-50 order
  - Dense 16.7mm: 30 left + 33 right = 63 underglow → 63 + 15% = ~72-75 order
  - Dense 15mm: 33 left + 36 right = 69 underglow → ~80 order
- Total to order: 70 per-key + 50-80 underglow = 120-150 LEDs to cover either density with spares

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

