# umiko companion tray app

Shows the live keyboard layer in the system tray (Windows) or menu bar
(macOS). The firmware pushes a tiny Raw HID packet on every layer change;
this script listens and renders the current layer as an icon.

Packaged with the repo: firmware side in `keyboards/umiko/`, host side here.
No driver, no admin, no installer — plain Python doing user-level HID reads,
so it's about as work-machine-friendly as a listener can get.

## Run

```sh
cd companion
pip install -r requirements.txt
python umiko_tray.py            # tray / menu-bar icon
python umiko_tray.py --window   # floating always-on-top window
```

Then tap your FN key: the indicator should flip between `0` (BASE) and `1` (FN).

Requires firmware built with `"raw": true` (already enabled in
`keyboards/umiko/keyboard.json`) and flashed to the board.

## Protocol

32-byte Raw HID report, keyboard → host (see `layer_state_set_kb` in
`keyboards/umiko/umiko.c`):

| Byte | Value                                    |
| ---- | ---------------------------------------- |
| 0    | `0x55` (`U` — umiko companion)           |
| 1    | `0x01` (message: layer state)            |
| 2    | highest active layer number              |
| 3–6  | full `layer_state` bitmask, little-endian |
| rest | reserved (zero)                          |

Device: VID `0x4257` / PID `0x554D`, usage page `0xFF60` / usage `0x61`
(the standard QMK Raw HID interface, shared with VIA).

## Layer names

`LAYER_NAMES` at the top of `umiko_tray.py` maps layer numbers to names.
Keep it in sync with `enum layers` in `keymaps/*/keymap.c`. Unknown layers
show as `L<n>` rather than crashing.

## Notes

- Only the USB-connected (master) half sends reports; the slave has no USB.
- If VIA is also open, both tools share the Raw HID interface. The `0x55`
  report ID sits outside VIA's command range, so they coexist.
- Linux works too but needs a udev rule for user-level HID access
  (e.g. the standard QMK `50-qmk.rules`); Windows and macOS need nothing.
