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


def run_window(state, reader) -> None:
    """Floating always-on-top layer indicator (tkinter, stdlib only).

    Polls the shared state dict on a timer so all tk calls stay on the
    main thread; the reader thread only mutates the dict.
    """
    import tkinter as tk

    root = tk.Tk()
    root.title("umiko")
    root.attributes("-topmost", True)
    root.resizable(False, False)
    root.configure(bg="#181818")

    number = tk.Label(
        root, text="–", font=("Arial", 72, "bold"),
        fg="#c8a44d", bg="#181818", width=3,
    )
    number.pack(padx=16, pady=(12, 0))
    name = tk.Label(
        root, text="connecting…", font=("Arial", 14),
        fg="#969696", bg="#181818",
    )
    name.pack(padx=16, pady=(0, 12))

    def refresh():
        if state["connected"] and state["layer"] is not None:
            number.config(text=str(state["layer"]))
            name.config(text=layer_name(state["layer"]))
        elif state["connected"]:
            number.config(text="?")
            name.config(text="waiting for layer…")
        else:
            number.config(text="–")
            name.config(text="disconnected")
        root.after(250, refresh)

    def on_close():
        reader.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    refresh()
    root.mainloop()


def main() -> None:
    ap = argparse.ArgumentParser(description="umiko companion layer display")
    ap.add_argument("--window", action="store_true",
                    help="floating window instead of tray icon")
    args = ap.parse_args()

    state = {"layer": None, "connected": False}

    if args.window:
        print("window mode: floating layer indicator", flush=True)
        reader = Reader(
            on_layer=lambda n: (
                state.update(layer=n),
                print(f"[umiko] connected, layer={n}", flush=True),
            ),
            on_connect=lambda c: (
                state.update(connected=c),
                print(f"[umiko] {'connected' if c else 'disconnected'}", flush=True),
            ),
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
