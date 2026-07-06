# umiko

Split TKL F-row-less mechanical keyboard, RP2040-based, per-key RGB + underglow, low-profile Gateron KS-33 v2.0 switches.

* PCB / hardware: https://github.com/idorurez/umiko
* MCU: 2× RP2040 (one per half)
* Split transport: single-wire half-duplex PIO serial on GP0 (routed over D+ of inter-half USB-C)
* Matrix: 5 rows × 8 columns per half; scanned COL2ROW

## Build

```
qmk compile -kb umiko -km default -bl uf2-split-left
qmk compile -kb umiko -km default -bl uf2-split-right
```

## Flash

Each half is flashed independently. No reset circuit on the board; flashing uses BOOTSEL only:

1. Unplug USB.
2. Hold the BOOTSEL button on that half (SW1 left, SW2 right).
3. Plug USB back in while holding.
4. Release BOOTSEL — the half mounts as `RPI-RP2`.
5. Drag the `.uf2` for that half onto the drive.
