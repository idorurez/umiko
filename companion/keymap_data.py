"""Static key legends for the umiko companion layer map.

Derived from keyboards/umiko/keymaps/default/keymap.c (LAYOUT_all order,
63 keys: 30 left + 33 right). ``None`` = transparent (falls through to
BASE); the panel renders those dimmed with the base legend.

Keep in sync with the firmware keymap by hand — there is no codegen.
"""

# Index must match `enum layers` in the firmware keymap.
LAYER_NAMES = ("BASE", "FN")

# Row geometry: LAYOUT_all order is left-to-right, top-to-bottom per half.
LEFT_ROWS = (
    tuple(range(0, 7)),
    tuple(range(7, 13)),
    tuple(range(13, 19)),
    tuple(range(19, 25)),
    tuple(range(25, 30)),
)
RIGHT_ROWS = (
    tuple(range(30, 37)),
    tuple(range(37, 45)),
    tuple(range(45, 52)),
    tuple(range(52, 58)),
    tuple(range(58, 63)),
)

BASE = (
    "`/Esc",
    "1", "2", "3", "4", "5", "6",
    "Tab", "Q", "W", "E", "R", "T",
    "FN", "A", "S", "D", "F", "G",
    "Shift", "Z", "X", "C", "V", "B",
    "Ctrl", "Win", "Alt", "FN", "Space",
    "7", "8", "9", "0", "-", "=", "Bksp",
    "Y", "U", "I", "O", "P", "[", "]", "\\",
    "H", "J", "K", "L", ";", "'", "Enter",
    "N", "M", ",", ".", "/", "Shift",
    "Space", "FN", "Alt", "Win", "Ctrl",
)

FN = (
    None,
    "F1", "F2", "F3", "F4", "F5", "F6",
    None, "Home", "Up", "End", "PgUp", None,
    None, "Left", "Down", "Right", "PgDn", None,
    None, None, None, None, None, None,
    None, None, None, None, None,
    "F7", "F8", "F9", "F10", "F11", "F12", None,
    "RGB+", "Hue+", "Sat+", "Val+", "Spd+", "◀Desk", "Desk▶", "Del",
    "RGB-", "Hue-", "Sat-", "Val-", "Spd-", None, None,
    "RGB", None, None, None, None, None,
    None, None, None, None, None,
)

LAYERS = (BASE, FN)

assert len(BASE) == 63 and len(FN) == 63
assert sum(len(r) for r in LEFT_ROWS) + sum(len(r) for r in RIGHT_ROWS) == 63
