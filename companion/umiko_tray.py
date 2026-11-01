#!/usr/bin/env python3
"""umiko companion tray app — live keyboard layer in the tray / menu bar.

Reads the layer-state reports the firmware pushes over QMK Raw HID
(see layer_state_set_kb in keyboards/umiko/umiko.c) and renders the
current layer as a tray icon.

Pure user-level HID reads: no driver, no admin, no installer, no binary.
Same file runs on Windows and macOS.

Usage:
    pip install -r requirements.txt
    python umiko_tray.py
"""

from __future__ import annotations

import argparse
import threading
import time

import hid
import pystray
from PIL import Image, ImageDraw, ImageFont

# Must match keyboard.json usb vid/pid.
VID = 0x4257
PID = 0x554D

# QMK Raw HID interface (shared with VIA / Console).
RAW_USAGE_PAGE = 0xFF60
RAW_USAGE = 0x61

# Must match the protocol in umiko.c (UMIKO_COMPANION_ID / UMIKO_MSG_LAYER).
PROTO_ID = 0x55
MSG_LAYER = 0x01

# Keep in sync with `enum layers` in keymaps/*/keymap.c.
LAYER_NAMES = {
    0: "BASE",
    1: "FN",
}

READ_LEN = 64  # RP2040 sends 32-byte reports; read up to 64 to be safe.
RECONNECT_DELAY = 2.0  # seconds between open attempts while disconnected.

GOLD = (200, 164, 77, 255)
CHARCOAL = (24, 24, 24, 255)
GRAY_FG = (150, 150, 150, 255)
GRAY_BG = (60, 60, 60, 255)


def layer_name(n: int) -> str:
    return LAYER_NAMES.get(n, f"L{n}")


def _load_font(px: int):
    for name in ("arial.ttf", "DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(name, px)
        except OSError:
            continue
    return ImageFont.load_default()


def make_icon(text: str, active: bool = True) -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        [2, 2, size - 3, size - 3],
        radius=12,
        fill=CHARCOAL if active else GRAY_BG,
    )
    font = _load_font(30 if len(text) < 3 else 22)
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(
        ((size - w) / 2 - bbox[0], (size - h) / 2 - bbox[1]),
        text,
        font=font,
        fill=GOLD if active else GRAY_FG,
    )
    return img


def open_device() -> hid.device:
    """Open the umiko Raw HID interface, preferring the usage-page match."""
    candidates = hid.enumerate(VID, PID)
    if not candidates:
        raise OSError("umiko not found")
    pick = candidates[0]
    for dev in candidates:
        if dev.get("usage_page") == RAW_USAGE_PAGE and dev.get("usage") == RAW_USAGE:
            pick = dev
            break
    dev = hid.device()
    dev.open_path(pick["path"])
    return dev


class Reader(threading.Thread):
    """Background HID read + reconnect loop. Calls back on state changes."""

    daemon = True

    def __init__(self, on_layer, on_connect):
        super().__init__(name="umiko-hid-reader")
        self._on_layer = on_layer
        self._on_connect = on_connect
        self._stop = threading.Event()
        self._connected = False

    def stop(self):
        self._stop.set()

    def _set_connected(self, value: bool):
        if value != self._connected:
            self._connected = value
            self._on_connect(value)

    def run(self):
        while not self._stop.is_set():
            try:
                dev = open_device()
            except OSError:
                self._set_connected(False)
                self._stop.wait(RECONNECT_DELAY)
                continue
            self._set_connected(True)
            try:
                while not self._stop.is_set():
                    try:
                        data = dev.read(READ_LEN, timeout_ms=500)
                    except OSError:
                        break  # device vanished; outer loop reconnects
                    if not data:
                        continue
                    if (
                        len(data) >= 3
                        and data[0] == PROTO_ID
                        and data[1] == MSG_LAYER
                    ):
                        self._on_layer(data[2])
            finally:
                dev.close()
            self._set_connected(False)


def _win_chrome(root) -> None:
    """Windows-only tweaks: dark titlebar + never steal focus on popup.

    WS_EX_NOACTIVATE keeps deiconify() from grabbing foreground
    activation, so keystrokes keep landing in the app behind the map.
    Silent no-op elsewhere.
    """
    try:
        import ctypes

        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        value = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 20, ctypes.byref(value), ctypes.sizeof(value)
        )
        ex = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, ex | 0x08000000)
        ctypes.windll.user32.SetWindowPos(
            hwnd, 0, 0, 0, 0, 0, 0x0020 | 0x0002 | 0x0001
        )
    except Exception:
        pass

def run_window(state, reader) -> None:
    """Minimal floating keymap: the active layer's bindings, live.

    Polls the shared state dict on a timer so all tk calls stay on the
    main thread; the reader thread only mutates the dict.
    """
    import tkinter as tk

    import keymap_data
    import key_geometry

    BG = "#181818"
    KEY = "#232323"
    GOLD = "#c8a44d"
    INK = "#e8e8e8"
    FAINT = "#5a5a5a"

    root = tk.Tk()
    root.title("umiko")
    root.attributes("-topmost", True)
    root.resizable(False, False)
    root.configure(bg=BG, padx=10, pady=10)

    S = 2.0  # px per mm
    TRIM = 20.0  # pull halves together by this many mm (display only)
    mapframe = tk.Frame(root, bg=BG,
                        width=int((key_geometry.BOARD_W_MM - TRIM) * S),
                        height=int(key_geometry.BOARD_H_MM * S))
    mapframe.pack()
    mapframe.pack_propagate(False)
    key_labels = {}
    for idx, (x, y, w, h) in enumerate(key_geometry.KEY_GEOMETRY):
        if idx >= 30:  # right half
            x -= TRIM
        lab = tk.Label(mapframe, text="", font=("Arial", 9),
                       fg=INK, bg=KEY,
                       highlightthickness=1, highlightbackground="#3a3a3a")
        lab.place(x=int(x * S) + 1, y=int(y * S) + 1,
                  width=int(w * S) - 2, height=int(h * S) - 2)
        key_labels[idx] = lab

    last_layer = [None]

    def render_map(n):
        legends = keymap_data.LAYERS[n] if n < len(keymap_data.LAYERS) else ()
        for idx, lab in key_labels.items():
            leg = legends[idx] if idx < len(legends) else None
            if leg is None:
                lab.config(text=keymap_data.BASE[idx], fg=FAINT)
            elif n == 0:
                lab.config(text=leg, fg=INK)
            else:
                lab.config(text=leg, fg=GOLD)

    shown = [False]

    def set_visible(v):
        if v != shown[0]:
            shown[0] = v
            if v:
                root.deiconify()
            else:
                root.withdraw()

    def refresh():
        if state["connected"] and state["layer"] is not None:
            n = state["layer"]
            root.title(f"umiko — {layer_name(n)}")
            if n != last_layer[0]:
                last_layer[0] = n
                render_map(n)
            set_visible(n != 0)
        elif state["connected"]:
            root.title("umiko — …")
            set_visible(False)
        else:
            root.title("umiko — offline")
            set_visible(False)
        root.after(100, refresh)

    def on_close():
        reader.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    render_map(0)
    _win_chrome(root)
    root.withdraw()
    refresh()
    root.mainloop()


def main() -> None:
    ap = argparse.ArgumentParser(description="umiko companion layer display")
    ap.add_argument("--window", action="store_true",
                    help="floating window instead of tray icon")
    args = ap.parse_args()

    state = {"layer": None, "connected": False}

    if args.window:
        reader = Reader(
            on_layer=lambda n: state.update(layer=n),
            on_connect=lambda c: state.update(connected=c),
        )
        reader.start()
        try:
            run_window(state, reader)
        except KeyboardInterrupt:
            pass
        finally:
            reader.stop()
        return
    icon = None  # bound below; callbacks run after icon exists

    def refresh():
        if state["connected"] and state["layer"] is not None:
            name = layer_name(state["layer"])
            icon.icon = make_icon(str(state["layer"]), active=True)
            icon.title = f"umiko — {name}"
        elif state["connected"]:
            icon.icon = make_icon("?", active=True)
            icon.title = "umiko — waiting for layer…"
        else:
            icon.icon = make_icon("–", active=False)
            icon.title = "umiko — disconnected"
        icon.update_menu()
        if state["connected"]:
            print(f"[umiko] connected, layer={state['layer']}", flush=True)
        else:
            print("[umiko] disconnected", flush=True)

    def title_text(item):
        if not state["connected"]:
            return "umiko — disconnected"
        if state["layer"] is None:
            return "umiko — connected"
        n = state["layer"]
        return f"umiko — {n}: {layer_name(n)}"

    reader = Reader(
        on_layer=lambda n: (state.update(layer=n), refresh()),
        on_connect=lambda c: (state.update(connected=c), refresh()),
    )

    def quit_app(icon, item):
        reader.stop()
        icon.stop()

    icon = pystray.Icon(
        "umiko",
        make_icon("–", active=False),
        "umiko — disconnected",
        menu=pystray.Menu(
            pystray.MenuItem(title_text, None, enabled=False),
            pystray.MenuItem("Quit", quit_app),
        ),
    )

    print("umiko companion starting… tray icon is in the taskbar (check ^ overflow).", flush=True)
    reader.start()
    try:
        icon.run()
    except KeyboardInterrupt:
        pass
    finally:
        reader.stop()


if __name__ == "__main__":
    main()