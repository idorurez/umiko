# Umiko Rev2 - SK6812 4020 Side-View Selection

**Date:** 2026-08-28  
**Branch:** `rev2` (workspace only, no GitHub commit yet)  
**Goal:** Main-PCB edge underglow, no satellite, no pogo, single GP25 chain per half

## Selected Primary PN

**MPN:** `SK6812SIDE-A` / `SK68XX SIDE` - 4.0 x 2.0 x 1.5 mm side-view
- Manufacturer: OPSCO Optoelectronics / Shenzhen Normand Electronic / Shenzhen Jercio Technology (same datasheet SPC/SK6812 SIDE Rev01 2017-03-14)
- Alternate MPNs: `SK6812SIDE-A-RVS`, `SK6812-EC3210 SIDE`, `SK6812-4020-SIDE`
- LCSC/JLC status 2026-08-28: **No direct LCSC listing found for 4020 SIDE** via search (JS-heavy site blocked simple fetch). SMBOM distributor listing shows `SK6812SIDE-A-RVS` package `SMD,4x2x1.6mm` as available via OPSCO. LCSC does stock SK6812 5050 (C5380881) but not the SIDE variant currently indexed. JLCPCB Basic/Extended library does not list SK6812 SIDE in public search results, so this will likely be a **Custom / Extended** part requiring LCSC `Cxxxx` or manual add. Treat as JLC extended, verify rotation on first order.
- Adafruit equivalent: Adafruit Product 4691 - Neopixel Side-Light RGB LED SK6812B 4020, described as 4.0x2.0x0.85mm thin version. Same electrical, same pad layout, different height/optical center.

### Why This PN

- Rev2 wants outward-facing 4020 at PCB edge. SIDE family is explicitly designed for this: emitting surface perpendicular to PCB, vs top-view 5050/3535.
- 5V, WS2812/SK6812 compatible protocol (800kHz, GRB, 24-bit), works with existing QMK `ws2812.driver=vendor` on GP25, no second driver.
- Stock availability via OPSCO is historically good for strip factories; thin 0.85mm variant is same footprint, lower profile for 2mm case support ring clearance.

## Alternatives Considered

1. **Adafruit 4691 4.0x2.0x0.85mm** - Same pad, 0.85mm thick vs 1.5mm. Better for low case, optical center 0.425mm vs 0.75mm above PCB. Tradeoff: less silicone lens, slightly lower mechanical robustness. Footprint identical, height only differs in 3D model and courtyard note.
2. **Generic SK6805 SIDE 5mA version** - Lower current (5mA vs 12mA per channel), same package. Saves power but dimmer. Could be used if polyfuse budget tight. Pin compatible.
3. **SK6812-B 5050 5.4x5.0x1.6mm (LCSC C5380881)** - Current Rev1 per-key and underglow. Not side-view, requires separate keepout, not suitable for edge outward emission. Rejected for edge use.
4. **SK6812 MINI-E reverse-mount (current per-key)** - Top emission, not side. Reusing footprint would place emitting face wrong direction and break optical path. Explicitly avoided.

## Datasheet Key Points

**Source:** Shenzhen Normand SK68XX SIDE Rev01 2017-08-15, slideshare mirror + mbed mirror `SK6812-4020_led_side.pdf` (mbed sunset page now, original PDF archived via forum attachment)

- Package: 4.0(L) x 2.0(W) x 1.5(H) mm, tolerance +-0.1mm. Thin variant 0.85mm H.
- Pinout (4 inline, 1.0mm pitch, viewed with emitting face +Y toward board edge):
  - Pin 1: DIN (data in)
  - Pin 2: VDD (5V)
  - Pin 3: DOUT (data out)
  - Pin 4: GND / VSS
- **Critical:** This is *different* from 5050 SK6812 (VSS/DIN/VDD/DOUT). Do not reuse 5050 symbol.
- Recommended land: ~0.6 x 0.9 mm pads, 1.0mm pitch, 4 pads inline centered under package. Solder mask expansion 0.05mm. (Prelim note from Adafruit and Normand welding plate size diagram)
- Absolute max: VDD 3.5-5.5V, logic VIN -0.5 to VDD+0.5, Topt -40 to +85C, ESD 4kV HBM.
- Electrical: VDD typ 5.2V (range 4.5-5.5 in spec), IDD static ~1mA, PWM 1.2kHz, data 800kHz, T0H 0.3us, T1H 0.6-0.9us variant, Trst 80us.
- Optical: 120 deg radiation, GRB order, R 620-630nm 700-1500mcd, G 515-530nm 2200-3300mcd, B 460-475nm 400-700mcd at 12mA version. 5mA version lower.
- Current: SK6812 = 12mA per channel nominal, total max ~36-39mA white + IC. Adafruit note says ~18mA constant drive - may be per channel limited. For power budget use **worst case 45mA per LED** (15mA x3) to be safe.

## KiCad Footprint Created

**Location:** `~/workspace/goals/umiko-split-keyboard/files/footprints/SK6812-4020-SideView.pretty/`

- `SK6812-4020-SideView.kicad_mod` - primary 1.5mm height version
- Properties embedded: MPN, LCSC_PN placeholder, datasheet link, JLC rotation note.

Design rules in footprint:
- Pads: 0.6x0.9mm rect SMD on F.Cu, F.Paste, F.Mask, at X=-1.5,-0.5,+0.5,+1.5 Y=0, 1.0mm pitch.
- Fab outline: 4.0x2.0 centered at 0,0 on F.Fab.
- Silkscreen: arrow +Y indicating emit direction, label "EMIT -> +Y", pin names.
- Courtyard: 2.6 x 1.8 rect (0.5mm + 0.1mm extra on emit side for lens), F.CrtYd 0.05mm.
- Cmts.User: keep 0.8mm clearance to Edge.Cuts, emitting face toward edge, JLC rotation 0 deg = DIN left.
- No thermal pad, single copper layer.

**Needed follow-ups before PCB layout:**
- Add second variant `SK6812-4020-SideView_0.85mm` with same pads but 3D model height 0.85mm and adjusted courtyard if case ring is 2mm tall x 2mm thick.
- Verify with real part on hand: measure pad to lens offset, optical center height 0.75mm (1.5mm part) vs 0.425mm (0.85mm part). Critical for support ring diffusion.
- Confirm JLC Extended rotation: typical JLC feed for 4020 SIDE has Pin1 at left when tape feeds. Our Pin1 DIN left matches 0 deg. **Must confirm on first JLC order with centroid file and photo.**
- Add to JLC BOM as custom: Manufacturer OPSCO, MPN SK6812SIDE-A, Package SMD4020SIDE.

## Power Implications

- Current Rev1: 27 underglow + 63 per-key = 90 total. Polyfuse 500mA hold / 1A trip per half.
- Proposed: keep 63 per-key unchanged. Increase underglow from 12/15 to maybe 20-33 per half (see perimeter math).
- Example 20 per half + 63 per-key = 83 per half? Wait split_count is per-half, but per half total includes per-key. Left half currently 12 underglow + 30 per-key? Actually split_count [42,48] means left 42 total (12 underglow +30 per-key) and right 48 total (15 underglow +33 per-key) = 63 per-key. If we go to 20 underglow left: 20+30=50 left. Right 22+33=55. Total 105. 50*45mA=2.25A worst white! Far exceeds polyfuse.
- Realistic QMK brightness limiting required: `RGB_MATRIX_MAXIMUM_BRIGHTNESS 150` (~59% ) still 1.33A worst. Need to design for **average** 10-15mA per LED at typical colors, not full white, and set firmware limit ~100-120 and test with bench supply.
- Must include: RP2040 ~100mA, OLED ~20-40mA, USB Schottky 0.3V drop, trace resistance, split power bridging via TRRS.
- Recommendation: Do not claim 150 is safe. Measure actual Edge.Cuts perimeter, decide density (20mm vs 16.7mm pitch), then recalc with 60mA per LED worst and 20mA typical, then set `RGB_MATRIX_MAXIMUM_BRIGHTNESS` and `RGB_MATRIX_SPLIT_TRANSPORT` safety.

## Next Steps for PCB Layout

1. **Measure actual Edge.Cuts** in KiCad for left/right halves (not bounding box). Current provisional 497/545mm is bounding only.
2. Map keepouts: USB-C, mounting holes, inserts, screw heads, component heights, case support ring (2mm x 2mm hollow), OLED FPC, TRRS jack.
3. Draw usable LED path offset 0.8-1.0mm from Edge.Cuts, on both straight edges and corners.
4. Compare 20mm pitch (25 left /27 right) vs 16.7mm (60/m) (30/33) vs 15mm (33/36). Denser corners may need tighter pitch.
5. Recalc per-half power and safe QMK brightness with real counts.
6. Build 2-4 LED optical coupon using real case material (Proto-pasta metallic iris, ~2mm thick, hollow center), test diffusion, seam, color at intended brightness.
7. Add footprint to KiCad library, update schematic symbol (new symbol for SIDE pinout, not reuse 5050), assign to edge positions, maintain single serial chain per half (GP25).
8. Verify empty-position chain break: if any underglow position is DNP, add 0-ohm bypass or solder jumper footprint in series, or make underglow contiguous from end of per-key chain.

## Files Prepared

- `~/workspace/goals/umiko-split-keyboard/files/footprints/SK6812-4020-SideView.pretty/SK6812-4020-SideView.kicad_mod`
- This report: `~/workspace/goals/umiko-split-keyboard/files/rev2-4020-selection.md`

No GitHub commit made. Ready for user review and manual copy into `~/workspace/.../umiko/.../footprints/` or repo `rev2` branch when approved.
