// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

// Split serial driver (vendor PIO) pin config is set via keyboard.json's
// split.serial.pin field. Half-duplex single-wire mode is inferred
// when RX and TX pins are the same (no full-duplex flag needed).

// OLED (0.91" SSD1306, 128x32)
// Portrait rotation is set via oled_init_user() in keymap.c
// (OLED_ROTATION_90/270 is an enum value, not a define, so it lives in code)
#define OLED_DISPLAY_128X32
#define OLED_TIMEOUT 0         // never sleep — reef keeps swimming

// Sync WPM across split so the OLED (on right) can react to typing
// that happens on the master (left) half.
#define SPLIT_WPM_ENABLE

// Fixed handedness: LEFT is always master. Right is always slave.
// Plug USB into LEFT's J2; right gets power + data via the split cable.
// This works out of the box (no per-half EEPROM setup required).
// To upgrade to dynamic handedness (either side can be master), swap
// this for `#define EE_HANDS` and follow the README's optional
// handedness-setup steps.
#define MASTER_LEFT

// Layer state sync across the split so both halves know the current layer
// (needed for the OLED layer indicator on the slave half).
#define SPLIT_LAYER_STATE_ENABLE

// ─── RGB Matrix ────────────────────────────────────────────────────────
// LED count + split_count + driver + animations set in keyboard.json.
// Underglow/per-key/modifier flags live in g_led_config in umiko.c.

// Framebuffer effects like TYPING_HEATMAP and DIGITAL_RAIN need this.
#define RGB_MATRIX_FRAMEBUFFER_EFFECTS

// Reactive effects (SOLID_REACTIVE_*, SPLASH, etc.) require key-press hooks.
#define RGB_MATRIX_KEYPRESSES

// Fine-grained step values for the FN + RGB tweak keys.
#define RGB_MATRIX_HUE_STEP  8
#define RGB_MATRIX_SAT_STEP  8
#define RGB_MATRIX_VAL_STEP  8
#define RGB_MATRIX_SPD_STEP  10

// Give underglow-only animations a way to leave per-key LEDs alone.
// (Effects check LED_FLAG_UNDERGLOW / LED_FLAG_KEYLIGHT internally.)
