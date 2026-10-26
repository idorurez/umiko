# Rev2 TODO — narrow scope

## Underglow (edge-mounted side-view)
- [x] Decision: No pogo pads, no satellite PCB, no second LED driver
- [x] Architecture: Single GP25 chain per half, keep 63 per-key SK6812MINI-E reverse-mount unchanged
- [x] Part selected: SK6812SIDE-A 4.0×2.0×1.5mm side-view (thin 0.85mm Adafruit 4691 variant same pads, compatible)
- [x] Footprints created: `footprints/SK6812-4020-SideView.pretty/SK6812-4020-SideView.kicad_mod` and `_0p85mm` variant
- [x] Datasheet: DIN/VDD/DOUT/GND left→right toward edge, 4 pads 1.0mm pitch 0.6×0.9mm land, 5V 800kHz GRB
- [x] Decision: 16.7mm pitch (60/m) — 30 left / 34 right = 64 underglow total, 60 left total / 67 right total = 127 with per-key
- [x] Edge.Cuts perimeter / keepouts / LED path — moot: placement done by hand, counts final (64), chains wired (closed 2026-10).
- [x] Power budget analysis (2026-08-28, counts refreshed 2026-10): current 750 mA SMD0805-075 is undersized for 127-LED Rev 2. Worst-case per half at brightness 150/255: left 60 LEDs × 45 mA × 59% = ~1.56 A, right 67 LEDs × 45 mA × 59% = ~1.78 A. Solid-white sustained peaks exceed the hold rating. **Decision: upgrade polyfuse to 2 A hold / 4 A trip so we can keep `RGB_MATRIX_MAXIMUM_BRIGHTNESS` at 150 (brighter than expected). Bench-verify final cap after Rev 2 build.**

## Polyfuse upgrade (Rev 2)
- [x] **Part selected: Bourns MF-NSMF200-2** (LCSC `C89656`). 2.0 A hold / 4.0 A trip / 6 V max / 1206 package. Correction 2026-10: the earlier `MF-MSMF200-2` pick is 1812, not 1206 (MSMF=1812, NSMF=1206 per distributor listings) — schematic now carries NSMF200-2/C89656.
- [x] **Update schematic F1/F2** to Value=`2A`, MPN=`MF-MSMF200-2`, LCSC=`C210837`, Footprint=`Fuse:Fuse_1206_3216Metric` (done 2026-10, direct edit, parens verified).
- [x] **Update PCB footprint** at F1/F2 from `Fuse:Fuse_0805_2012Metric` → `Fuse:Fuse_1206_3216Metric` (done 2026-10 via Update PCB from Schematic; nets verified: VBUS in, D1/D5 anode out).
- [ ] **Backup part options** if C89656 goes out of stock: Littelfuse 1206L200PR (1206, 2A hold / 3.5A trip — slightly lower trip; verify LCSC code at order time), or Bourns MF-MSMF200-2 (same 2A/4A but 1812 — needs footprint change). Dropped SF-1206F200-2 (one-time thin-film fuse, not resettable).
- [ ] **Verify USB-C host will actually supply the current.** Basic USB-C is 900 mA. Need at least USB-C 5V/1.5A (upgraded) or 5V/3A profile. Board doesn't negotiate PD, so relies on host default. Cheap hubs may cap current — document in README as "requires ≥1.5 A USB-C source for full-brightness Rev 2 operation."

### Power-draw research (2026-08-28)

Adafruit's rule-of-thumb for real-world SK6812 animation load: **~20 mA/LED average** (not 45 mA worst-case, not Dygma's 0.85 mA — those are the wireless-battery-capped outliers). For umiko Rev 2:
- Left: 60 LEDs × 20 mA + 100 mA MCU/OLED = ~1.3 A typical
- Right: 67 LEDs × 20 mA + 100 mA = ~1.44 A typical

Existing SMD0805-075 (750 mA hold) is **undersized for typical animation**, not just worst case. Aligns with r/olkb reports of random RGB dropouts on 100+ LED splits. 2 A / 1206 gives thermal-cool margin at 1.4 A sustained, handles solid-white transient peaks at brightness 150 without concern, and USB-C source current-limiting is the primary short-circuit protection anyway.

Sources: [Adafruit NeoPixel Überguide](https://learn.adafruit.com/adafruit-neopixel-uberguide/powering-neopixels), [SK6812 measurements (dest-unreach.be)](https://blog.dest-unreach.be/2023/08/31/sk6812/), [Digital LED power (quinled.info)](https://quinled.info/2020/03/12/digital-led-power-usage/).
- [ ] Build 2-4 LED optical coupon with Proto-pasta iris material, test diffusion and seam
- [x] SIDE symbol/schematic/chain — symbol + schematic + single chain per half all in place; 0-ohm bypass moot (zero DNP instances in schematic, verified 2026-10).

## LED ordering numbers (with spares) — decision 16.7mm
- Per-key: 63 total (30 left, 33 right) SK6812MINI-E — order 70+ (10% spare)
- Underglow side-view 16.7mm: 30 left + 34 right = 64 underglow → 64 + 15% = ~74 order
- Total to order for 16.7mm: 70 per-key + 74 underglow = ~144 LEDs
- Other densities for reference: 20mm sparse 42 underglow → ~50 order, 15mm dense 69 → ~80 order

## Switch support (keep narrow)
- Existing: Gateron KS-33 (and likely KS-27 compatible — verify official drawings before claiming)
- Candidate: MX + KS-33 combo (same MX stem, same 14mm plate cutout family, height difference lives in case standoffs/middle, not plate cutout — verify plate thickness/clip engagement from official drawings)
- Not candidate for Rev2: Choc V1 (different rectangular cutout, different stem, no cap overlap, requires 2 plate types)
- Mill-Max sockets: evaluate hole diameter / leg thickness for KS-33 vs MX, insertion force, board thickness, hand-assembly — do not assume JLC places them
- Required verification: obtain official KS-33 and MX mechanical drawings, compare PCB seating plane, underside of plate/retention-clip plane, specified plate thickness, locating posts, required top-plate opening

## Other Rev2 items retained
- [x] D5 SOD-882D orientation — verified identical to known-good D1 (same footprint, B.Cu, rot -90, verified 2026-10). Replacement moot.
- [x] OLED verify/move — moot for rev2: no OLED connector on the board (SCL/SDA nets are MCU-only, verified 2026-10). Revive if adding the breakout (see Stretch).
- Deliberately map RGB positions
- [x] Larger case-integrated BOOTSEL — deferred by user 2026-10 (keeping the small tact).
- Optional sound hardware
- Replace EOL Kailh Choc V2 stabilizers (Durock V3 evaluated + rejected 2026-10; else stock spares and accept the risk)
- [x] GPIO status LED — done: D4 on `/USER_LED_R` wired to U7 (verified 2026-10).
- Consider SPLIT_USB_DETECT
- Case support ring ~2mm tall × 2mm thick hollow
- At-surface lettering (changed 2026-08-11)
- Prefab gate: `kicad-cli --refill-zones --save-board --severity-error --exit-code-violations`

## Underglow decoupling cap placement (blocked on socket decision, 2026-09-06)
- [x] **Mill-Max vs Kailh hotswap decision** — decided: Mill-Max (user 2026-10). No footprint swap needed: 0305 receptacles fit the 1.5mm holes. Buy + fit test tracked below.
- [ ] Mill-Max buy + fit test: buy 0305-2-15-80-47-80-10-0 loose (keeb-vendor standard; 126 + spares ≈ 150); solder ONE socket and test-fit a KS-33 (retention + continuity) before full assembly; caliper KS-33 pins (~1.0x0.45mm inferred vs 0.64 barrel).
- [x] **Cap placement pattern**: 147× 100nF placed in schematic, C10↔LED16 reference pair intact on PCB (3.6mm, verified 2026-10). (Mapping doc `scratchpad/led_cap_pairs.json` is lost; regenerable if ever needed.)
- [x] C10 placed as example (3.6mm above LED16 along right-edge perimeter, rot 180) — user tuned by hand. Pattern rule TBD once socket footprint is finalized.

## Underglow chain wiring (2026-09-04)
- [x] **LED49 was mis-wired into the RIGHT chain** — fixed: now LED91 → LED49 → LED100, all left half (x=29.5 column, monotonic edge walk, verified 2026-10).
- [x] **Chain re-order + right-half LED pass** — both chains walk monotonic runs; 34/34 right underglow emit outward (same check passes hand-verified left 30/30; verified 2026-10).

## Power / firmware
- led_count in `keyboard.json` still rev1 (90, split_count [42,48]). Rev2 needs 127 with split [60,67] plus rev2 LED positions.
- Pins: GP0, GP2–GP16, GP25 (verify unused pins against schematic/PCB)
- Y49 short: +5V_R to GND_R around (322,55) on B.Cu — already fixed in latest

## DRC cleanup (pre-fab gate, verified 2026-10)
- [x] `(attr smd)` added to `onigaku:D3_SMD_v2` + `YS-SK6812MINI-E` (126 instances; onigaku repo, uncommitted — commit there separately). Update Footprints from Library done in GUI 2026-10 — all 126 instances verified carrying `(attr smd)`. `PCM_0xcb:X2SON-4` deliberately untouched (Plugin-Manager lib; exclude instead).
- [x] Exclude 6 `footprint_type_mismatch` in the DRC dialog (done 2026-10; turned out moot — the footprint update cleared all 132 anyway).
- [x] SW1/SW2 clearance cluster + unconnected stub — 10 errors cleared by the footprint updates; +3V3_R stub turned out to be U8 pad 1↔5 hop, routed 2026-10. DRC reads 0/0.
- [x] Refill zones + rerun `scripts/prefab_check.sh` to green before gerber export. (Green 2026-10: 0 violations, 0 unconnected, exit 0. Report: `output/prefab_drc.json`.)

## Handedness revisit (open)
- [x] Handedness — twin-binary scheme (user 2026-10): `default` builds LEFT, `right` (+UMiko_RIGHT) builds RIGHT; master elected by GP19 VBUS detect (local-only sensing verified on schematic). Both UF2s compile; right object verified different from left. Flash matching file per half; USB into exactly one half.

