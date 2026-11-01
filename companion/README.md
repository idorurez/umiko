# umiko companion

Live keyboard layer on your desktop. The firmware pushes a tiny Raw HID
packet on every layer change; this script listens and shows it.

No driver, no admin, no installer — plain Python doing user-level HID reads.

## Run

```sh
cd companion
pip install -r requirements.txt
python umiko_tray.py            # tray / menu-bar icon
python umiko_tray.py --window   # floating keymap window
```

Tap FN: the tray icon flips between `0` (BASE) and `1` (FN). The window
stays hidden until a non-base layer is active, then pops up with that
layer's full bindings — hold FN to study the map, release to dismiss it.
(Quit via the console with Ctrl+C, or close the window while FN is held.)

Requires firmware built with `"raw": true` (already enabled in
`keyboards/umiko/keyboard.json`) and flashed to the board.

## Keymap data

Legends live in `keymap_data.py`, derived by hand from
`keyboards/umiko/keymaps/default/keymap.c` — update both together when the
keymap changes. Keys that fall through to BASE render dimmed with the base
legend. Key positions/sizes live in `key_geometry.py`, generated from the
real switch footprints via `scripts/make_key_geometry.py` — rerun it if the
PCB layout changes.

## Layer names

`LAYER_NAMES` at the top of `umiko_tray.py` maps layer numbers to names.
Keep it in sync with `enum layers` in `keymaps/*/keymap.c`. Unknown layers
show as `L<n>` rather than crashing.

## Protocol

32-byte Raw HID report, keyboard → host (see `layer_state_set_kb` in
`keyboards/umiko/umiko.c`):

| Byte | Value                                     |
| ---- | ----------------------------------------- |
| 0    | `0x55` (`U` — umiko companion)            |
| 1    | `0x01` (message: layer state)             |
| 2    | highest active layer number               |
| 3–6  | full `layer_state` bitmask, little-endian |
| rest | reserved (zero)                           |

Device: VID `0x4257` / PID `0x554D`, usage page `0xFF60` / usage `0x61`
(the standard QMK Raw HID interface, shared with VIA).

## Notes

- Only the USB-connected (master) half sends reports; the slave has no USB.
- If VIA is also open, both tools share the Raw HID interface. The `0x55`
  report ID sits outside VIA's command range, so they coexist.
- Linux works too but needs a udev rule for user-level HID access
  (e.g. the standard QMK `50-qmk.rules`); Windows and macOS need nothing.
