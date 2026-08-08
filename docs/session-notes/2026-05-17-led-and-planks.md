# Session notes — 2026-05-17

Resume point for case-design + plank/LED-cutout work.

## 1. LED alignment fix — DONE

All 63 per-key LEDs were realigned to the KS-33 v2 datasheet spec.

### Spec derivation (from page 1 of `SPEC-KS-33H10B050NN-Y24_Rev-2_KS-33_Red_Switch.pdf`)

PCB Layout view, dimensions read directly off the drawing:

- Top of RGB window → switch dead center: **6.30 mm**
- Bottom of RGB window → switch dead center: **4.05 mm**
- Therefore RGB window center (Y): **5.175 mm** above switch center
- RGB window dimensions: **5.00 mm wide × 2.25 mm tall**

In X: the window is centered ~+0.70 mm right of the switch stem (read as: window total width 5.00, right edge at 3.20 from stem → 3.20 − 2.50 = +0.70 mm offset). We chose **not** to compensate in X because the SK6812MINI-E package (3.5 mm wide) fits entirely inside the 5.0 mm window even centered on the stem — light spreads anyway.

### Target applied to every per-key LED

```
dx (LED.x − switch.x) = 0
dy (LED.y − switch.y) = −5.175
```

### Pre-fix state (what was wrong)

| Half  | Count | dy value     | Notes |
|-------|-------|--------------|-------|
| Left  | 28    | −5.199       | Drift, 0.024 mm too low                    |
| Left  | 1     | −5.218       | Outlier SW_26 / LED38                      |
| Left  | 1     | −5.326       | Outlier SW_12 / LED14                      |
| Right | 26    | −5.000       | Round number, 0.175 mm too high            |
| Right | 7     | −5.127       | Outliers SW_34, 39, 47, 52, 55, 57, 62     |

Plus 6 LEDs with non-zero X drift: LED8, LED13, LED22, LED29, LED35, LED47.

63 LEDs total were repositioned. Underglow LEDs were not touched.

### Files

- `_fix_led_alignment.py` — the patch script (can be deleted; saved for reference)
- `umiko.kicad_pcb.bak_led_align` — PCB snapshot **before** the fix
- `umiko.kicad_pcb` — fixed

### Verification

```
All per-key LEDs aligned: dx=0, dy=-5.175
```

---

## 2. Plank / USB-C / LED-cutout collision — OPEN

### Current connector positions

| Ref | Role             | X       | Y      |
|-----|------------------|---------|--------|
| J1  | Left external   | 54.360  | 34.105 |
| J3  | Left inner      | 157.170 | 34.110 |
| J4  | Right inner     | 191.021 | 34.110 |
| J2  | Right external  | 317.680 | 34.105 |

User just moved (manually in KiCad as a temp workaround):
- All J's: Y **+2.5 mm** (so the planks dip lower / shorter)
- J2 and J4 (the inner-leaning ones): X **−15–17 mm** (toward the inner edge of each half)

### Plank polygons (from current Edge.Cuts)

Each plank is a rectangular tab protruding ABOVE the main board top edge (Y=36.09) with 1.25 mm filleted corners. Top of each plank is at Y=29.07.

| Plank | Connector | X range (top, Y=29.07–30.32) | X range (base, Y=34.84–36.09) |
|-------|-----------|------------------------------|-------------------------------|
| P1    | J1        | 49.48–59.24                  | 46.98–61.74                   |
| P2    | J3        | 152.29–162.05                | 149.79–164.55                 |
| P3    | J4        | 186.14–195.90                | 183.64–198.40                 |
| P4    | J2        | 312.83–322.59                | 310.33–325.09                 |

Main board interior top edge: Y=36.09 between planks, fillet up to Y=37.34 at the side rails.

### LED cutouts under each plank

Every per-key LED has a 3.6 × 3.1 mm rectangular cutout in Edge.Cuts (for the SK6812MINI-E reverse-mount body to poke through the PCB). Top-row LEDs after the alignment fix:

| LED   | Under plank   | LED center (x, y)     | Cutout Y range       |
|-------|---------------|-----------------------|----------------------|
| LED1  | P1 (J1)      | (44.715, 40.538)      | 38.988 – 42.088      |
| LED7  | P1 (J1)      | (63.765, 40.538)      | 38.988 – 42.088      |
| LED38 | P2 (J3)      | (159.015, 40.538)     | 38.988 – 42.088      |
| LED43 | P3 (J4)      | (194.024, 40.545)     | 38.995 – 42.095      |
| LED85 | P4 (J2)      | (317.849, 40.545)     | 38.995 – 42.095      |

Gap from **plank base** (Y=36.09) to **LED cutout top** (Y≈38.99): **≈ 2.90 mm**.

So Edge.Cuts geometry doesn't actually intersect — there's ~2.9 mm of PCB material between each plank's foot and the nearest LED cutout. **But** that's the margin the user is concerned about: it's thin, and the case wall sits outside the board edge so it can effectively land over the LED cutout when wrapped around the plank.

### Why this is a problem for the case

When designing the case wall around the planks, the wall:
1. Has to wrap around the plank protrusion (so the USB-C is recessed flush)
2. Then return to the main board's top edge (Y=36.09)
3. Then run along the board edge until the next plank

The 2.9 mm strip of PCB material between the plank's foot and the LED cutout is where the case wall transition happens — it's tight for a 2–3 mm wall thickness.

### Options to discuss next session

**A. Move the LED cutouts away from the planks.**
The four top-row LEDs under planks (LED1, LED7, LED38, LED43, LED85 — actually 5 if you count both J1 LEDs) sit directly below their planks. Could relocate just those keys/LEDs to columns that aren't aligned with planks. Big disruption.

**B. Narrow the planks.**
The current planks are ~14.7 mm wide at the base. The USB-C receptacle (HRO TYPE-C-31-M-12) is ~9 mm wide. We could narrow the plank to ~11–12 mm and pull more clearance on each side. Easiest change.

**C. Move the planks horizontally to land between LEDs.**
Each LED column is 19.05 mm apart. If a plank is centered between two columns, it lands in a ~15 mm gap. P1 (J1, X=46.98–61.74) currently spans LED1 (X=44.71) and LED7 (X=63.77) — it sits roughly between them but the base widens at Y=36.09 and clips both. Tightening the plank base (option B) would solve this. Same logic applies to P2 / P3 / P4.

**D. Shorten the planks vertically (raise the top, so plank height is smaller).**
Doesn't help with LED conflict directly but reduces dead space at the top of the case. User already started this by moving J's down 2.5 mm.

**E. Accept the 2.9 mm strip and design the case wall thin in that region.**
A 1.5 mm wall in the plank-to-LED transition region (with a 2.9 mm clearance available) is doable. Less elegant but no PCB respin.

### Recommendation when resuming

Look at option **B** first (narrow plank base). The plank-base width is set by the fillet positions (Y=34.84 → 36.09 fillet). If we shrink the base by 3 mm total (1.5 mm per side), the plank-to-LED-cutout horizontal gap grows from ~0 to ~1.5 mm — more case wall to play with, no LED moves, no respin of routing.

---

## 3. Commits since session start

`70eb12b` — Add JLC/CAD export scripts, restore SW_17/D_17, refresh BOM (already pushed)

LED alignment fix is **uncommitted** — still local on `main` working tree. Decide before next push whether to commit alone or bundle with plank fix.

## 4. Working files left in tree

- `umiko.kicad_pcb.bak_led_align` — pre-LED-fix backup, safe to delete after verification
- `_fix_led_alignment.py` — one-shot patch script, safe to delete
- Plenty of older `*.bak_*` files — ignore unless rolling back

## 5. To resume

1. Reopen KiCad and visually confirm the LED alignment looks right (top row should sit at switch_y − 5.175 everywhere)
2. Pick one of the plank options above
3. If option B (narrow planks): the edits are mechanical — shrink each plank's base X range by ~3 mm symmetrically and shift the upper-side fillets to match. Can script it.
