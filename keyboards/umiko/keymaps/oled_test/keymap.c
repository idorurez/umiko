// SPDX-License-Identifier: GPL-2.0-or-later
#include QMK_KEYBOARD_H
#include <string.h>
#include <stdio.h>

// Layers
enum layers {
    _BASE = 0,
    _FN = 1,
};

// Tap dance: single tap = backtick (`), double tap = escape
enum tap_dance_actions {
    TD_GRV_ESC = 0,
};

tap_dance_action_t tap_dance_actions[] = {
    [TD_GRV_ESC] = ACTION_TAP_DANCE_DOUBLE(KC_GRV, KC_ESC),
};

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
    // _BASE: default QWERTY-ish TKL F-row-less
    [_BASE] = LAYOUT_all(
        TD(TD_GRV_ESC),
        KC_1,
        KC_2,
        KC_3,
        KC_4,
        KC_5,
        KC_6,
        KC_TAB,
        KC_Q,
        KC_W,
        KC_E,
        KC_R,
        KC_T,
        MO(_FN),
        KC_A,
        KC_S,
        KC_D,
        KC_F,
        KC_G,
        KC_LSFT,
        KC_Z,
        KC_X,
        KC_C,
        KC_V,
        KC_B,
        KC_LCTL,
        KC_LGUI,
        KC_LALT,
        MO(_FN),
        KC_SPC,
        KC_7,
        KC_8,
        KC_9,
        KC_0,
        KC_MINS,
        KC_EQL,
        KC_BSPC,
        KC_Y,
        KC_U,
        KC_I,
        KC_O,
        KC_P,
        KC_LBRC,
        KC_RBRC,
        KC_BSLS,
        KC_H,
        KC_J,
        KC_K,
        KC_L,
        KC_SCLN,
        KC_QUOT,
        KC_ENT,
        KC_N,
        KC_M,
        KC_COMM,
        KC_DOT,
        KC_SLSH,
        KC_RSFT,
        KC_SPC,
        MO(_FN),
        KC_RALT,
        KC_RGUI,
        KC_RCTL
    ),
    // _FN: momentary layer
    //   Left nav:  Q=HOME W=UP  E=END  R=PGUP    A=LEFT S=DOWN D=RIGHT F=PGDN
    //   Number row: 1-6 → F1-F6, 7-0 → F7-F10, - → F11, = → F12
    //   FN + [ = prev desktop, FN + ] = next desktop
    //   Right hand RGB Matrix controls:
    //     Y=NEXT U=HUE+ I=SAT+ O=VAL+ P=SPD+
    //     H=PREV J=HUE- K=SAT- L=VAL- ;=SPD-
    //     N=TOG
    //   Reset: no software reset. Use SW1/SW2 (PCB tacts) or hold the
    //   top-left key at plug-in (bootmagic, left half only).
    [_FN] = LAYOUT_all(
        KC_TRNS,    // 0  Esc/backtick — falls through to base tap dance
        KC_F1,      // 1
        KC_F2,      // 2
        KC_F3,      // 3
        KC_F4,      // 4
        KC_F5,      // 5
        KC_F6,      // 6
        KC_TRNS,    // 7  Tab
        KC_HOME,    // 8  Q
        KC_UP,      // 9  W
        KC_END,     // 10 E
        KC_PGUP,    // 11 R
        KC_TRNS,    // 12 T
        KC_TRNS,    // 13 Caps
        KC_LEFT,    // 14 A
        KC_DOWN,    // 15 S
        KC_RIGHT,   // 16 D
        KC_PGDN,    // 17 F
        KC_TRNS,    // 18 G
        KC_TRNS,    // 19 LSft
        KC_TRNS,    // 20 Z
        KC_TRNS,    // 21 X
        KC_TRNS,    // 22 C
        KC_TRNS,    // 23 V
        KC_TRNS,    // 24 B
        KC_TRNS,    // 25 LCtl
        KC_TRNS,    // 26 LGui
        KC_TRNS,    // 27 LAlt
        KC_TRNS,    // 28 MO(_FN)
        KC_TRNS,    // 29 Space
        KC_F7,      // 30 7
        KC_F8,      // 31 8
        KC_F9,      // 32 9
        KC_F10,     // 33 0
        KC_F11,     // 34 -
        KC_F12,     // 35 =
        KC_TRNS,    // 36 FN + Backspace → still Backspace
        RM_NEXT,    // 37 Y  - next RGB Matrix effect
        RM_HUEU,    // 38 U  - hue +
        RM_SATU,    // 39 I  - saturation +
        RM_VALU,    // 40 O  - value/brightness +
        RM_SPDU,    // 41 P  - speed +
        LCTL(LGUI(KC_LEFT)),   // 42 [  -> prev desktop
        LCTL(LGUI(KC_RIGHT)),  // 43 ]  -> next desktop
        KC_DEL,     // 44 FN + Backslash → Delete
        RM_PREV,    // 45 H  - previous RGB Matrix effect
        RM_HUED,    // 46 J  - hue -
        RM_SATD,    // 47 K  - saturation -
        RM_VALD,    // 48 L  - value/brightness -
        RM_SPDD,    // 49 ;  - speed -
        KC_TRNS,    // 50 '
        KC_TRNS,    // 51 Enter
        RM_TOGG,    // 52 N  - toggle RGB Matrix on/off
        KC_TRNS,    // 53 M
        KC_TRNS,    // 54 ,
        KC_TRNS,    // 55 .
        KC_TRNS,    // 56 /
        KC_TRNS,    // 57 RSft
        KC_TRNS,    // 58 Space
        KC_TRNS,    // 59 MO(_FN)
        KC_TRNS,    // 60 RAlt
        KC_TRNS,    // 61 RGui
        KC_TRNS     // 62 falls through to RCTL
    ),
};

// ────────────────────────────────────────────────────────────────
// Shared 16-entry sine LUT (values 0..15).
// ────────────────────────────────────────────────────────────────
static const uint8_t sin_lut[16] = {
    8, 11, 13, 15, 14, 13, 11, 8, 8, 5, 3, 1, 2, 3, 5, 8
};

// ─── RGB Matrix ────────────────────────────────────────────────────────
// g_led_config (matrix map, per-LED positions and flags) lives in
// keyboards/umiko/umiko.c, derived from the trace in docs/led-chain.md.
//
// Per-key LEDs follow the base RGB Matrix effect (cycled via FN+Y/H).
// Underglow LEDs are OVERRIDDEN each frame with a slow blue↔white cycle,
// so their look is independent of whatever per-key effect is active.
// ──────────────────────────────────────────────────────────────────────

#ifdef RGB_MATRIX_ENABLE
#include "lib/lib8tion/lib8tion.h"

// Slow blue-to-white breathing loop for underglow LEDs.
// - Saturation oscillates 0..255 slowly (~20s period) — full sat = deep blue,
//   zero sat = pure white at the given value.
// - Hue gently wobbles inside the blue band (~154..186) so it feels alive.
// - Value stays modest (~80) so it never blinds you.
bool rgb_matrix_indicators_advanced_user(uint8_t led_min, uint8_t led_max) {
    uint32_t t       = timer_read32();
    uint8_t  sat_idx = (uint8_t)((t / 80) & 0xFF);          // ~20s per full cycle
    uint8_t  hue_idx = (uint8_t)((t / 40) & 0xFF);          // ~10s per hue wobble
    uint8_t  sat     = sin8(sat_idx);                        // 0..255
    int8_t   hue_off = (int8_t)((sin8(hue_idx) - 128) / 8);  // -16..+15
    hsv_t    hsv     = {(uint8_t)(170 + hue_off), sat, 80};
    rgb_t    rgb     = hsv_to_rgb(hsv);
    for (uint8_t i = led_min; i < led_max; i++) {
        if (g_led_config.flags[i] & LED_FLAG_UNDERGLOW) {
            rgb_matrix_set_color(i, rgb.r, rgb.g, rgb.b);
        }
    }
    return false;
}
#endif

// Force portrait orientation on init (flip other way)
oled_rotation_t oled_init_user(oled_rotation_t rotation) {
    return OLED_ROTATION_270;
}

// ────────────────────────────────────────────────────────────────
// OLED test — width/height check for SSD1312 128×64 module
//   Display is 128×64 native, rotated 270° -> 64 wide × 128 tall in oled fns
//   Renders a 1px border on all 4 edges (so you can see any lit-vs-dark
//   asymmetry), a mid-height crosshair, size labels, and a frame counter
//   that ticks so you know the display is actually refreshing.
// ────────────────────────────────────────────────────────────────
#ifdef OLED_ENABLE

#define TW  64   // rotated width (128×64 native, rotated 270°)
#define TH 128   // rotated height

static uint32_t last_tick = 0;
static uint16_t frame     = 0;

bool oled_task_user(void) {
    // Orientation fix (SEG_REMAP override) is at keyboard level in umiko.c.

    // ~10 Hz refresh
    uint32_t now = timer_read32();
    if (TIMER_DIFF_32(now, last_tick) < 100) return false;
    last_tick = now;
    frame++;

    oled_clear();

    // 1-pixel border around the full display
    for (uint8_t x = 0; x < TW; x++) {
        oled_write_pixel(x, 0,      true);
        oled_write_pixel(x, TH - 1, true);
    }
    for (uint8_t y = 0; y < TH; y++) {
        oled_write_pixel(0,      y, true);
        oled_write_pixel(TW - 1, y, true);
    }

    // Mid-height horizontal divider — proves middle of the buffer draws
    for (uint8_t x = 2; x < TW - 2; x++) {
        oled_write_pixel(x, TH / 2, true);
    }
    // Vertical center tick at top and bottom halves
    for (uint8_t y = 2; y < 8; y++) {
        oled_write_pixel(TW / 2, y, true);
        oled_write_pixel(TW / 2, TH - 1 - y, true);
    }

    // Header text — 6px font, 64px wide gives 10 chars per line.
    oled_set_cursor(0, 0);
    oled_write_P(PSTR(" SSD1312"), false);
    oled_set_cursor(0, 1);
    oled_write_P(PSTR(" 128x64"), false);
    oled_set_cursor(0, 2);
    oled_write_P(PSTR(" rot270"), false);

    // Frame counter below the mid divider
    oled_set_cursor(0, 9);
    oled_write_P(PSTR(" frame:"), false);
    oled_set_cursor(0, 10);
    char buf[10];
    snprintf(buf, sizeof(buf), " %6u", frame);
    oled_write(buf, false);

    // Which half is drawing
    oled_set_cursor(0, 12);
    oled_write_P(is_keyboard_master() ? PSTR(" MASTER") : PSTR(" SLAVE"), false);

    return false;
}

#endif
