# Umiko Rev 2 — TODO

Action items for the next board revision. Companion to the [Stretch / Future Ideas (Rev 2)](../README.md#stretch--future-ideas-rev-2) section in the README, which lists the full scope; this file captures the deeper design notes for the items that need concrete decisions before layout starts.

---

## 1. Bigger OLED — 1.09" 128×64 SSD1312

**Target part:** 1.09-inch 128×64 monochrome OLED breakout with SSD1312 driver, 4-pin I²C header (SDA / SCL / VCC / GND).

**Reference listing:** AliExpress item 3256809262936611 (~$32). Panel size 14 × 31.96 × 1.22 mm; active area 11.86 × 25.58 mm; 2.8-3.3V; welded to a breakout PCB that configures the SSD1312's BS0/BS1 pins for I²C mode and exposes the 4-pin header.

### Why this one
- Same 4-pin I²C interface as the current SSD1306 128×32 — **no PCB change required**, drops into the existing OLED footprint on both halves.
- 4× the pixel area (128×64 vs 128×32) — enough room for reef animation + WPM + layer name + RGB mode on one screen.
- SSD1312 command set is a superset of SSD1306 (same init bytes for display on/off, contrast, clock, VCOMH, addressing) — expected to run on QMK's SSD1306 driver with a minor init tweak.

### Firmware TODO
- [ ] In `keyboards/umiko/config.h`: set `#define OLED_IC OLED_IC_SSD1306` and `#define OLED_DISPLAY_128X64`. Flash and test.
- [ ] If contrast or rendering is off, override `oled_init_user()` with SSD1312-tuned values: contrast `81 CF`, VCOMH `DB 40` (from SSD1312 datasheet).
- [ ] Worst case (unlikely): copy `oled_driver.c` into `keyboards/umiko/` and add an `OLED_IC_SSD1312` branch mirroring SSD1306 with the two register tweaks above (~20 LOC).
- [ ] Rework `oled_task_user()` for 128×64 canvas: reef animation stays 128×32 in the top half, bottom half gets WPM / layer / RGB mode text.
- [ ] Consider redrawing reef animation frames at full 128×64 (aesthetic call).

### Case TODO
- [ ] Enlarge top-case OLED cutout from ~12 × 30 mm to **14 × 32 mm** (with ~0.2 mm tolerance).
- [ ] Test-print the enlarged cutout on a spare top-case iteration.

### Rev 2 board TODO (optional future-proofing)
- [ ] Add SPI pads (SCLK / MOSI / CS / DC / RES) alongside the 4-pin I²C header on the display footprint — leaves the door open for a 2.13" e-paper panel later without a third PCB revision.
- [ ] Relocate the display footprint closer to the top edge of the right half so the case can grow a proper bezel around it (see existing "Relocate the display closer to the top edge" bullet in README Rev 2 section).

### Validation
- [ ] Solder the SSD1312 module to a **Rev 1** board first (existing 4-pin OLED footprint) and confirm it lights up with the config change alone. If Rev 1 works, Rev 2 changes are firmware-only + case cutout.

### References
- [SSD1312 datasheet (buydisplay.com)](https://www.buydisplay.com/download/ic/SSD1312_Datasheet.pdf)
- [QMK OLED driver docs](https://docs.qmk.fm/features/oled_driver)
- [U8g2 library with SSD1312 support](https://github.com/olikraus/u8g2) — reference for init constants if QMK's SSD1306 defaults don't work

---

## 2. Side-emitting underglow — satellite PCB + pogo pins

**Goal:** Uniform, bright underglow that reads at the case edge, without moving LEDs closer to the main PCB perimeter (existing trace routing traffic prevents this).

### Approach: dedicated underglow subsystem
- Separate **satellite PCB** shaped as an outline ring hugging the main PCB perimeter.
- Populated with **SK6812 4020 side-view addressable LEDs** firing outward toward the case edge.
- Connects to the main PCB via **3 pogo pins per half**: VCC, GND, DIN.
- Same WS2812 protocol as current SK6812MINI-E — QMK firmware treats it as an extension of the existing chain (`LED_FLAG_UNDERGLOW`, updated `g_led_config` positions).

### Chain topology options
Two ways to wire the chain — both use 3 pogos, differ in firmware:

**Option A (recommended): satellite on its own driver channel.**
```
MCU GP25 → main-PCB per-key LEDs → dead-end
MCU GPxx → [pogo DIN] → satellite 4020 chain → dead-end
```
- Costs one extra MCU pin per half.
- Isolates the two subsystems — a bad per-key LED can't corrupt underglow (see [hardware_ws2812_chain_corruption.md](../../../.claude/projects/C--Users-neuro-dev-keyboard-umiko/memory/hardware_ws2812_chain_corruption.md)).
- Underglow can be disabled independently (satellite unplugged).
- RP2040 PIO supports multiple WS2812 channels — QMK exposes this via multiple driver instances.

**Option B: satellite terminates the main chain.**
```
MCU GP25 → main-PCB per-key LEDs → [pogo DIN] → satellite 4020 chain → dead-end
```
- Only 3 pogos, no extra MCU pin.
- Single chain; more susceptible to per-key LED failures corrupting downstream underglow.

### Main-PCB TODO (Rev 2 board)
- [ ] Add **three exposed pogo landing pads per half** (VCC, GND, DIN) on the bottom face where the satellite PCB overlaps.
- [ ] Add a **solder-jumper-selectable DIN out** — one pad to the pogo landing (satellite mode), one to the current onboard underglow chain (standalone mode). Lets Rev 2 work with or without the satellite fitted.
- [ ] For Option A: route a second WS2812 GPIO from each MCU to its own pogo pad.

### Satellite PCB TODO
- [ ] Ring / outline PCB matching main-PCB perimeter geometry.
- [ ] SK6812 4020 side-view footprints around perimeter, oriented outward.
- [ ] Pogo receptacle pads matching main-board landing pattern.
- [ ] Cutouts around mounting hardware so it shares the main PCB's case screws.
- [ ] Consider a thinner PCB (0.6-0.8 mm FR-4) to keep total assembly Z-height reasonable.

### Case TODO (critical — determines whether the light escapes)
The current case ring is 2 mm tall × 2 mm thick and the top shell overhangs it opaquely. Without a change, edge light gets blocked. Recommended combined solution:

- [ ] **Print the bottom case in translucent PLA** (or clear resin). The existing 2 mm × 2 mm structural ring becomes an acrylic light guide — LEDs fire into the inner face, ring emits outward through the outer face via total internal reflection.
- [ ] **Add a 1.5 mm horizontal case seam gap** between top and bottom shells around the perimeter. Modern industry-standard approach (Keychron Q, GMMK Pro) — dust ingress is acceptable with a magnet-attached bottom.
- [ ] Test both together before committing: print a bottom case in clear PLA + top case with a shortened skirt, mock up a WS2812 strip along the ring, verify uniformity.

### Firmware TODO
- [ ] Update `g_led_config` in `umiko.c` with the new satellite LED positions (x, y).
- [ ] Add satellite indices to `LED_FLAG_UNDERGLOW` so `rgb_matrix_indicators_advanced_user()` (existing underglow override) drives them automatically.
- [ ] For Option A: configure a second WS2812 driver instance in `keyboard.json` under `rgb_matrix.driver` — split-count adjustment for the satellite LEDs.
- [ ] Update `led_count` and `split_count` in `keyboard.json` `rgb_matrix` block.

### Prototype-first validation
- [ ] Before committing PCB space: hand-wire a small (~10 LED) SK6812 4020 test strip and mount it against a translucent-PLA test print of the case ring. Confirm the diffusion actually looks like uniform edge glow, not "10 discrete dots through a fog."
- [ ] If diffusion is uneven, iterate on ring cross-section (thicker? textured outer face?) before finalizing PCB.

### References
- [Dygma — ARGBW keyboard side-mounted LED design](https://dygma.com/blogs/product-development/the-only-rgbw-keyboard) — validates the perimeter side-firing approach
- [SK6812 4020 side-view LED strip (Super Lighting LED)](https://www.superlightingled.com/sk6812-4020-side-view-led-strip-c-5_486_120_711.html) — same protocol as current SK6812MINI-E
- Dygma Labs YouTube: separate outline PCB with pogo pin connection to main PCB — https://www.youtube.com/watch?v=HxwEuy5oHUo

---

## Cross-cutting: GPIO budget

Both features consume MCU pins. Sanity-check before layout:

- **Current RP2040 GPIO usage (per half):** 5 rows (GP4-8) + 8 cols (GP9-16) + WS2812 (GP25) + I²C (GP2, GP3) + serial split (GP0) = **17 pins**. RP2040 has 30 GPIOs — plenty of headroom.
- **Adding SPI OLED alternative (if pursued):** +4 pins (SCLK, MOSI, CS, DC), possibly +1 for RES = 5 more.
- **Adding second WS2812 channel (Option A satellite):** +1 pin.
- **Total worst-case for both:** 17 + 5 + 1 = **23 pins**. Still fits, but tight enough to lay out with pin assignments finalized before routing.
