# LED chain order (task #42)

Traced from `umiko.kicad_pcb` by walking DIN -> DOUT nets between LED footprints. Chain starts identified by finding LEDs whose DIN net has no matching upstream DOUT. Result is deterministic from the shipped PCB — not a hypothesis.

## Summary

- **Left half** (42 LEDs): chain head = LED16 (an underglow LED). First 12 are underglow, remaining 30 are per-key.
- **Right half** (48 LEDs): chain head = LED89 (an underglow LED). First 15 are underglow, remaining 33 are per-key.
- Total: **90 LEDs** (27 underglow + 63 per-key), matches 63 switches.
- Underglow chain-first, per-key second, per side.

## QMK global indexing (with `MASTER_LEFT`, `split_count = [42, 48]`)

- `0..41` = left half chain (12 underglow at `0..11`, then 30 per-key at `12..41`)
- `42..89` = right half chain (15 underglow at `42..56`, then 33 per-key at `57..89`)

## Left chain (global indices `0..41`)

| Idx | LED | Type | Switch | Matrix | PCB (x, y) mm |
|---:|---|:---|:---|:---|---|
| 0 | LED16 | underglow | — | — | (38.8, 74.4) |
| 1 | LED18 | underglow | — | — | (38.8, 93.8) |
| 2 | LED25 | underglow | — | — | (46.7, 112.7) |
| 3 | LED31 | underglow | — | — | (83.4, 112.7) |
| 4 | LED37 | underglow | — | — | (122.0, 112.7) |
| 5 | LED36 | underglow | — | — | (149.3, 112.7) |
| 6 | LED30 | underglow | — | — | (149.2, 93.8) |
| 7 | LED24 | underglow | — | — | (141.7, 74.8) |
| 8 | LED17 | underglow | — | — | (135.1, 55.6) |
| 9 | LED15 | underglow | — | — | (106.3, 55.6) |
| 10 | LED6 | underglow | — | — | (77.9, 55.6) |
| 11 | LED5 | underglow | — | — | (44.5, 55.6) |
| 12 | LED1 | per-key | SW_1 | (0, 0) | (39.7, 40.5) |
| 13 | LED2 | per-key | SW_2 | (1, 0) | (44.5, 59.6) |
| 14 | LED3 | per-key | SW_3 | (2, 0) | (46.9, 78.6) |
| 15 | LED4 | per-key | SW_4 | (4, 0) | (42.1, 116.7) |
| 16 | LED9 | per-key | SW_7 | (4, 1) | (65.9, 116.7) |
| 17 | LED8 | per-key | SW_6 | (3, 1) | (51.6, 97.7) |
| 18 | LED7 | per-key | SW_5 | (0, 1) | (58.8, 40.5) |
| 19 | LED10 | per-key | SW_8 | (0, 2) | (77.8, 40.5) |
| 20 | LED11 | per-key | SW_9 | (1, 2) | (68.3, 59.6) |
| 21 | LED12 | per-key | SW_10 | (2, 2) | (73.1, 78.6) |
| 22 | LED13 | per-key | SW_11 | (3, 2) | (82.6, 97.7) |
| 23 | LED14 | per-key | SW_12 | (4, 2) | (89.8, 116.7) |
| 24 | LED23 | per-key | SW_17 | (4, 3) | (113.6, 116.7) |
| 25 | LED22 | per-key | SW_16 | (3, 3) | (101.6, 97.7) |
| 26 | LED21 | per-key | SW_15 | (2, 3) | (92.1, 78.6) |
| 27 | LED20 | per-key | SW_14 | (1, 3) | (87.3, 59.6) |
| 28 | LED19 | per-key | SW_13 | (0, 3) | (96.9, 40.5) |
| 29 | LED26 | per-key | SW_18 | (0, 4) | (115.9, 40.5) |
| 30 | LED27 | per-key | SW_19 | (1, 4) | (106.4, 59.6) |
| 31 | LED28 | per-key | SW_20 | (2, 4) | (111.2, 78.6) |
| 32 | LED29 | per-key | SW_21 | (3, 4) | (120.7, 97.7) |
| 33 | LED35 | per-key | SW_25 | (3, 5) | (139.7, 97.7) |
| 34 | LED34 | per-key | SW_24 | (2, 5) | (130.2, 78.6) |
| 35 | LED33 | per-key | SW_23 | (1, 5) | (125.4, 59.6) |
| 36 | LED32 | per-key | SW_22 | (0, 5) | (135.0, 40.5) |
| 37 | LED38 | per-key | SW_26 | (0, 6) | (154.0, 40.5) |
| 38 | LED39 | per-key | SW_27 | (1, 6) | (144.5, 59.6) |
| 39 | LED40 | per-key | SW_28 | (2, 6) | (149.3, 78.6) |
| 40 | LED41 | per-key | SW_29 | (3, 6) | (158.8, 97.7) |
| 41 | LED42 | per-key | SW_30 | (4, 6) | (146.9, 116.7) |

## Right chain (global indices `42..89`)

| Idx (global) | LED | Type | Switch | Matrix | PCB (x, y) mm |
|---:|---|:---|:---|:---|---|
| 42 | LED89 | underglow | — | — | (327.8, 74.2) |
| 43 | LED88 | underglow | — | — | (329.9, 93.8) |
| 44 | LED84 | underglow | — | — | (323.4, 112.7) |
| 45 | LED79 | underglow | — | — | (299.9, 112.7) |
| 46 | LED75 | underglow | — | — | (275.4, 112.7) |
| 47 | LED68 | underglow | — | — | (248.5, 112.7) |
| 48 | LED61 | underglow | — | — | (224.9, 112.7) |
| 49 | LED90 | underglow | — | — | (201.3, 112.8) |
| 50 | LED55 | underglow | — | — | (203.8, 93.3) |
| 51 | LED49 | underglow | — | — | (197.6, 74.7) |
| 52 | LED48 | underglow | — | — | (204.1, 55.6) |
| 53 | LED54 | underglow | — | — | (235.9, 55.6) |
| 54 | LED60 | underglow | — | — | (264.1, 55.6) |
| 55 | LED67 | underglow | — | — | (294.0, 55.6) |
| 56 | LED74 | underglow | — | — | (318.3, 55.6) |
| 57 | LED87 | per-key | SW_63 | (9, 7) | (335.0, 116.7) |
| 58 | LED86 | per-key | SW_62 | (6, 7) | (332.6, 59.6) |
| 59 | LED85 | per-key | SW_61 | (5, 7) | (327.8, 40.5) |
| 60 | LED80 | per-key | SW_57 | (6, 6) | (308.8, 59.6) |
| 61 | LED81 | per-key | SW_58 | (7, 6) | (325.5, 78.6) |
| 62 | LED82 | per-key | SW_59 | (8, 6) | (320.7, 97.7) |
| 63 | LED83 | per-key | SW_60 | (9, 6) | (311.2, 116.7) |
| 64 | LED78 | per-key | SW_56 | (7, 5) | (294.5, 78.6) |
| 65 | LED77 | per-key | SW_55 | (6, 5) | (289.7, 59.6) |
| 66 | LED76 | per-key | SW_54 | (5, 5) | (299.3, 40.5) |
| 67 | LED69 | per-key | SW_49 | (5, 4) | (280.2, 40.5) |
| 68 | LED70 | per-key | SW_50 | (6, 4) | (270.7, 59.6) |
| 69 | LED71 | per-key | SW_51 | (7, 4) | (275.5, 78.6) |
| 70 | LED72 | per-key | SW_52 | (8, 4) | (285.0, 97.7) |
| 71 | LED73 | per-key | SW_53 | (9, 4) | (287.4, 116.7) |
| 72 | LED66 | per-key | SW_48 | (9, 3) | (263.6, 116.7) |
| 73 | LED65 | per-key | SW_47 | (8, 3) | (265.9, 97.7) |
| 74 | LED64 | per-key | SW_46 | (7, 3) | (256.4, 78.6) |
| 75 | LED63 | per-key | SW_45 | (6, 3) | (251.6, 59.6) |
| 76 | LED62 | per-key | SW_44 | (5, 3) | (261.2, 40.5) |
| 77 | LED56 | per-key | SW_40 | (5, 2) | (242.1, 40.5) |
| 78 | LED57 | per-key | SW_41 | (6, 2) | (232.6, 59.6) |
| 79 | LED58 | per-key | SW_42 | (7, 2) | (237.4, 78.6) |
| 80 | LED59 | per-key | SW_43 | (8, 2) | (246.9, 97.7) |
| 81 | LED53 | per-key | SW_39 | (8, 1) | (227.8, 97.7) |
| 82 | LED52 | per-key | SW_38 | (7, 1) | (218.3, 78.6) |
| 83 | LED51 | per-key | SW_37 | (6, 1) | (213.5, 59.6) |
| 84 | LED50 | per-key | SW_36 | (5, 1) | (223.1, 40.5) |
| 85 | LED43 | per-key | SW_31 | (5, 0) | (204.0, 40.5) |
| 86 | LED44 | per-key | SW_32 | (6, 0) | (194.5, 59.6) |
| 87 | LED45 | per-key | SW_33 | (7, 0) | (199.3, 78.6) |
| 88 | LED46 | per-key | SW_34 | (8, 0) | (208.8, 97.7) |
| 89 | LED47 | per-key | SW_35 | (9, 0) | (225.5, 116.7) |

## How this was derived

1. Parse every LED footprint's pad nets from `umiko.kicad_pcb`. Each LED has four pads: `VDD_1`, `DOUT_2`, `VSS_3`, `DIN_4`.
2. Build a map from each `Net-(LEDxx-DOUT)` net to the LED whose DIN pad receives it.
3. Identify chain heads: LEDs whose DIN net does not equal any other LED's DOUT.
4. Walk each chain from head, following DOUT -> next LED's DIN, until termination.
5. Cross-reference per-key LEDs with switches (nearest neighbour, always exactly 5.18 mm away — LEDs sit directly above their switch).
6. Cross-reference switches with matrix coordinates from `keyboard.json`'s `layouts.LAYOUT_all` (matched by scaled physical position — every switch resolved within 0.01 mm).

Regenerate any time with `scripts/_trace_led_chain.py` (a snapshot lives in `scripts/archive/` if renamed).