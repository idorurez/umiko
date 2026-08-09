// SPDX-License-Identifier: GPL-2.0-or-later
#include QMK_KEYBOARD_H
#include <string.h>

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
    //   Esc → QK_BOOT
    //   Left nav:  Q=HOME W=UP  E=END  R=PGUP    A=LEFT S=DOWN D=RIGHT F=PGDN
    //   Number row: 1-6 → F1-F6, 7-0 → F7-F10, - → F11, = → F12
    //   FN + [ = prev desktop, FN + ] = next desktop
    //   Right hand RGB Matrix controls:
    //     Y=NEXT U=HUE+ I=SAT+ O=VAL+ P=SPD+
    //     H=PREV J=HUE- K=SAT- L=VAL- ;=SPD-
    //     N=TOG
    [_FN] = LAYOUT_all(
        QK_BOOT,    // 0  Esc
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
// No custom rgb_matrix logic needed here — QMK handles animations
// natively via LED_FLAG_UNDERGLOW / LED_FLAG_KEYLIGHT / LED_FLAG_MODIFIER,
// and cycles through the effect list enabled in keyboard.json via FN+Y/H.
// ──────────────────────────────────────────────────────────────────────

// Force portrait orientation on init (flip other way)
oled_rotation_t oled_init_user(oled_rotation_t rotation) {
    return OLED_ROTATION_270;
}

// ────────────────────────────────────────────────────────────────
// OLED: portrait 32×128 reef scene.
//   Backdrop: pre-baked bitmap of a reef silhouette (from a PNG source
//     thresholded at 145). Static, drawn every frame from PROGMEM.
//   Text overlay (top 16 px): "umiko" + master/slave + layer.
//   Fish overlay: small sprite swims horizontally in the empty water
//     region between the text and the top of the reef.
//   Bubble overlay: 1-pixel bubbles rise from just above the reef through
//     the water column toward the waterline.
// ────────────────────────────────────────────────────────────────
#ifdef OLED_ENABLE
#    include <string.h>

#define OLED_W  32
#define OLED_H  128

// Reef bitmap — 32×128 portrait, threshold=145
// Row-major: 4 bytes per row, LSB = leftmost column of each byte.
static const uint8_t reef_bitmap[128 * 4] PROGMEM = {
    0xE1, 0xF8, 0xFF, 0xFF,  // y=0
    0x9E, 0x81, 0xF0, 0x3F,  // y=1
    0x38, 0x06, 0xEF, 0xF0,  // y=2
    0x00, 0x30, 0x80, 0xC3,  // y=3
    0x00, 0x30, 0x02, 0x18,  // y=4
    0x00, 0x30, 0x00, 0x18,  // y=5
    0x00, 0x00, 0x00, 0x00,  // y=6
    0x00, 0x00, 0x00, 0x00,  // y=7
    0x00, 0x00, 0x00, 0x00,  // y=8
    0x00, 0x00, 0x00, 0x00,  // y=9
    0x00, 0x00, 0x00, 0x00,  // y=10
    0x00, 0x00, 0x00, 0x00,  // y=11
    0x00, 0x00, 0x00, 0x00,  // y=12
    0x00, 0x00, 0x00, 0x80,  // y=13
    0x00, 0x00, 0x18, 0x20,  // y=14
    0x00, 0x00, 0x10, 0x20,  // y=15
    0x00, 0x00, 0xC0, 0x01,  // y=16
    0x00, 0x00, 0x00, 0x00,  // y=17
    0x00, 0x00, 0x12, 0x00,  // y=18
    0x00, 0x60, 0x10, 0x00,  // y=19
    0x08, 0x00, 0x00, 0x30,  // y=20
    0x00, 0x00, 0x03, 0x30,  // y=21
    0x00, 0x00, 0x00, 0x00,  // y=22
    0x00, 0x00, 0x00, 0x00,  // y=23
    0x00, 0x00, 0x00, 0x00,  // y=24
    0x00, 0x00, 0x00, 0x00,  // y=25
    0x00, 0x00, 0x00, 0x00,  // y=26
    0x00, 0x00, 0x00, 0xC8,  // y=27
    0x00, 0x00, 0x00, 0x98,  // y=28
    0x00, 0x00, 0x00, 0x90,  // y=29
    0x00, 0x00, 0x10, 0x10,  // y=30
    0x00, 0x00, 0xA0, 0x38,  // y=31
    0x00, 0x00, 0x60, 0x60,  // y=32
    0x00, 0x40, 0x30, 0xE1,  // y=33
    0x00, 0x80, 0x21, 0x85,  // y=34
    0x00, 0x00, 0xC9, 0x0C,  // y=35
    0x00, 0x40, 0x73, 0xC4,  // y=36
    0x00, 0x80, 0xC7, 0x92,  // y=37
    0xC0, 0x10, 0xCC, 0x93,  // y=38
    0xF0, 0x61, 0x59, 0xCE,  // y=39
    0xE0, 0xE1, 0x5F, 0x62,  // y=40
    0x00, 0x00, 0xFE, 0x39,  // y=41
    0x00, 0x00, 0xF0, 0x9F,  // y=42
    0x00, 0x00, 0xC0, 0xC9,  // y=43
    0x00, 0xE0, 0x82, 0xC9,  // y=44
    0x00, 0xF8, 0xCF, 0xE7,  // y=45
    0x00, 0xE8, 0x9F, 0xE7,  // y=46
    0x80, 0xE0, 0x3F, 0xEE,  // y=47
    0x80, 0x81, 0x7E, 0xCC,  // y=48
    0x00, 0x1A, 0xF8, 0x9C,  // y=49
    0x20, 0x0C, 0xE0, 0x79,  // y=50
    0x40, 0x4D, 0x84, 0xFB,  // y=51
    0x70, 0x4B, 0xA6, 0xFE,  // y=52
    0xC0, 0x31, 0x94, 0xFE,  // y=53
    0x80, 0x31, 0xCC, 0x7F,  // y=54
    0x4B, 0x33, 0xE7, 0x3F,  // y=55
    0x4E, 0xB6, 0xC7, 0x9F,  // y=56
    0x98, 0x28, 0xFE, 0xDF,  // y=57
    0xBC, 0x79, 0xF3, 0x97,  // y=58
    0xE3, 0xFF, 0xF3, 0xA3,  // y=59
    0x00, 0xEE, 0xF7, 0x2C,  // y=60
    0xC8, 0xE1, 0xB7, 0x81,  // y=61
    0xF8, 0x18, 0x0B, 0xF2,  // y=62
    0x20, 0x1E, 0xFC, 0xF6,  // y=63
    0x00, 0x32, 0xDF, 0xCB,  // y=64
    0xC0, 0x89, 0x17, 0x9C,  // y=65
    0xA0, 0x81, 0x3F, 0xF9,  // y=66
    0x00, 0x80, 0xD9, 0xFE,  // y=67
    0x00, 0x80, 0xE1, 0xBF,  // y=68
    0x00, 0x00, 0x00, 0xCF,  // y=69
    0x00, 0x00, 0x08, 0xFC,  // y=70
    0x00, 0x00, 0x00, 0x30,  // y=71
    0x00, 0x00, 0x00, 0x00,  // y=72
    0x03, 0x00, 0x00, 0x00,  // y=73  (fish sprite lifted out)
    0x07, 0x00, 0x00, 0x04,  // y=74  (fish sprite lifted out, including tail)
    0x00, 0x00, 0x00, 0x00,  // y=75  (fish sprite lifted out, including tail)
    0x00, 0x00, 0x00, 0x00,  // y=76  (fish sprite lifted out, including tail)
    0x00, 0x00, 0x00, 0x40,  // y=77  (fish sprite lifted out)
    0x00, 0x00, 0xF0, 0x03,  // y=78  (fish sprite lifted out)
    0x00, 0x08, 0xF8, 0x60,  // y=79
    0x00, 0x00, 0x30, 0x80,  // y=80
    0x00, 0x00, 0x00, 0xC8,  // y=81
    0x00, 0x00, 0x00, 0xF0,  // y=82
    0x00, 0x00, 0x00, 0xC0,  // y=83
    0xC0, 0x00, 0x04, 0xE0,  // y=84
    0xF8, 0x00, 0x40, 0x00,  // y=85
    0x1E, 0x00, 0x00, 0x00,  // y=86
    0x02, 0x00, 0x02, 0x1C,  // y=87
    0x00, 0x00, 0x04, 0x80,  // y=88
    0x24, 0x4C, 0xE0, 0x93,  // y=89
    0x14, 0x47, 0xF0, 0x9F,  // y=90
    0x0A, 0x07, 0xB8, 0x07,  // y=91
    0x26, 0x8F, 0x7C, 0x83,  // y=92
    0xD2, 0x21, 0x7C, 0xF0,  // y=93
    0xFA, 0x04, 0x41, 0xF8,  // y=94
    0x7C, 0x03, 0x00, 0xFC,  // y=95
    0x17, 0x10, 0x14, 0xFC,  // y=96
    0xF7, 0x1E, 0x90, 0xFC,  // y=97
    0x3F, 0x2D, 0xD0, 0x3D,  // y=98
    0x8F, 0x1A, 0xF4, 0xC2,  // y=99
    0x6F, 0xC9, 0x6C, 0xF6,  // y=100
    0x86, 0xE7, 0xF6, 0x3D,  // y=101
    0xDC, 0xD1, 0xF9, 0x1C,  // y=102
    0x3D, 0xCC, 0xF3, 0xCE,  // y=103
    0x7F, 0xFF, 0x93, 0xFB,  // y=104
    0xFF, 0xBE, 0x5F, 0xFF,  // y=105
    0xEF, 0xFC, 0xFF, 0xFE,  // y=106
    0xEC, 0xAD, 0xFD, 0xF0,  // y=107
    0x5B, 0xFB, 0x7F, 0x40,  // y=108
    0x52, 0xF2, 0xEF, 0x00,  // y=109
    0x1B, 0x87, 0x2D, 0x00,  // y=110
    0xAC, 0xDD, 0x1B, 0x00,  // y=111
    0xD0, 0x30, 0xCF, 0x01,  // y=112
    0x34, 0xF8, 0xCD, 0x04,  // y=113
    0xD3, 0xF2, 0xC6, 0x05,  // y=114
    0x90, 0x91, 0xC3, 0x0B,  // y=115
    0x9D, 0x30, 0x83, 0x0F,  // y=116
    0x64, 0x08, 0x07, 0xCF,  // y=117
    0x00, 0xE6, 0x00, 0xDE,  // y=118
    0x4E, 0x88, 0xF0, 0xFC,  // y=119
    0x00, 0x80, 0xF9, 0xDD,  // y=120
    0xD0, 0xC7, 0x19, 0xDF,  // y=121
    0x40, 0x00, 0x28, 0xBF,  // y=122
    0x0F, 0x3C, 0x14, 0xFE,  // y=123
    0x39, 0x26, 0x0C, 0xFF,  // y=124
    0xF0, 0x03, 0x0C, 0xFE,  // y=125
    0x04, 0x98, 0x00, 0xFE,  // y=126
    0x04, 0x48, 0x01, 0xFC,  // y=127
};

// Blit the reef bitmap onto the OLED buffer, only touching ON pixels.
// (Called after oled_clear() so OFF pixels are already 0.)
static void draw_reef(void) {
    for (uint8_t y = 0; y < OLED_H; y++) {
        for (uint8_t bi = 0; bi < 4; bi++) {
            uint8_t byte = pgm_read_byte(&reef_bitmap[y * 4 + bi]);
            if (byte == 0) continue;
            uint8_t x_base = bi * 8;
            for (uint8_t bit = 0; bit < 8; bit++) {
                if (byte & (1u << bit)) {
                    oled_write_pixel(x_base + bit, y, true);
                }
            }
        }
    }
}

// ─── Overlay: fish ───
// Sprite: 5-wide × 3-tall body + 2-pixel tail (wiggles). Right-facing only.
static void draw_fish(int16_t x, int16_t y, uint16_t phase) {
    for (int16_t dx = -3; dx <= -1; dx++) {
        if (x + dx >= 0 && x + dx < OLED_W) {
            oled_write_pixel((uint8_t)(x + dx), y - 1, true);
            oled_write_pixel((uint8_t)(x + dx), y + 1, true);
        }
    }
    for (int16_t dx = -4; dx <= 0; dx++) {
        if (x + dx >= 0 && x + dx < OLED_W) {
            oled_write_pixel((uint8_t)(x + dx), y, true);
        }
    }
    // Tail wiggle
    int16_t tx = x - 5;
    if (tx >= 0 && tx < OLED_W) {
        oled_write_pixel((uint8_t)tx, y, true);
        if ((phase >> 1) & 1) {
            oled_write_pixel((uint8_t)tx, y - 1, true);
        } else {
            oled_write_pixel((uint8_t)tx, y + 1, true);
        }
    }
    int16_t ttx = x - 6;
    if (ttx >= 0 && ttx < OLED_W) {
        if ((phase >> 1) & 1) {
            oled_write_pixel((uint8_t)ttx, y - 2, true);
        } else {
            oled_write_pixel((uint8_t)ttx, y + 2, true);
        }
    }
}

// ─── Overlay: bubbles ───
#define MAX_BUBBLES 4
#define BUBBLE_TOP_Y   18   // bubbles pop when rising past this
#define BUBBLE_BOTTOM_Y 40  // bubbles spawn here (just above the reef top)

typedef struct {
    int8_t  x;
    int16_t y_q2;    // fixed-point y * 4 (quarter-pixels)
    uint8_t rise;    // quarter-pixels per tick
    bool    alive;
} bubble_t;

static bubble_t bubbles[MAX_BUBBLES] = {0};

// xorshift PRNG (deterministic, no Date/rand deps)
static uint32_t rng_state = 0xC0FFEE01;
static inline uint32_t xorshift32(void) {
    uint32_t x = rng_state;
    x ^= x << 13; x ^= x >> 17; x ^= x << 5;
    rng_state = x;
    return x;
}

static void spawn_bubble(bubble_t *b) {
    uint32_t r = xorshift32();
    b->x     = (int8_t)(r & 0x1F);          // 0..31
    b->y_q2  = BUBBLE_BOTTOM_Y * 4;
    b->rise  = 1 + (uint8_t)((r >> 8) & 1); // 1 or 2 quarter-pixels/tick
    b->alive = true;
}

static void draw_bubble(int8_t bx, int8_t by) {
    if (bx >= 0 && bx < OLED_W && by >= 0 && by < OLED_H) {
        oled_write_pixel((uint8_t)bx, (uint8_t)by, true);
    }
}

static uint32_t oled_last_frame     = 0;
static uint16_t oled_phase          = 0;
static int16_t  fish_x              = -8;
static uint8_t  bubble_spawn_countdown = 0;

bool oled_task_user(void) {
    // Frame rate scales with WPM: idle ~7 fps, fast typing ~25 fps.
    uint32_t now = timer_read32();
    uint8_t  wpm = get_current_wpm();
    uint32_t interval = (wpm >= 20) ? (150 - (wpm - 20)) : 150;
    if (interval < 40)  interval = 40;
    if (interval > 150) interval = 150;
    if (TIMER_DIFF_32(now, oled_last_frame) < interval) return false;
    oled_last_frame = now;
    oled_phase++;

    oled_clear();

    // Backdrop (silhouette fish at y=73-78 already removed from the bitmap
    // — we redraw it as an animated overlay below)
    draw_reef();

    // Text (single top row: master/slave + layer, e.g. "M L0")
    oled_set_cursor(0, 0);
    oled_write_P(is_keyboard_master() ? PSTR("M L") : PSTR("S L"), false);
    oled_write_char('0' + get_highest_layer(layer_state), false);

    // Overlay 1: the silhouette fish, now bobbing.
    // The sprite is the EXACT pixels lifted from the bitmap at (7, 73)..(17, 78).
    // 11 pixels wide × 6 tall — includes the small tail fin at cols 9,10.
    // Vertical bob via sin_lut (~±2 px), slow phase for a natural drift.
    static const uint16_t sil_fish[6] = {
        0x0178,  // .  .  .  #  #  #  #  .  #  .  .   (row 0 was y=73)
        0x04FC,  // .  .  #  #  #  #  #  #  .  .  #   (row 1 was y=74) — tail
        0x07FE,  // .  #  #  #  #  #  #  #  #  #  #   (row 2 was y=75) — tail
        0x05EF,  // #  #  #  #  .  #  #  #  #  .  #   (row 3 was y=76) eye + tail
        0x01EF,  // #  #  #  #  .  #  #  #  #  .  .   (row 4 was y=77)
        0x013E,  // .  #  #  #  #  #  .  .  #  .  .   (row 5 was y=78)
    };
    int8_t big_bob = ((int8_t)sin_lut[(oled_phase >> 2) & 0x0F] - 8) / 3;
    int16_t sprite_x = 7;
    int16_t sprite_y = 73 + big_bob;
    for (uint8_t row = 0; row < 6; row++) {
        uint16_t bits = sil_fish[row];
        for (uint8_t col = 0; col < 11; col++) {
            if (bits & (1u << col)) {
                int16_t px = sprite_x + col;
                int16_t py = sprite_y + row;
                if (px >= 0 && px < OLED_W && py >= 0 && py < OLED_H) {
                    oled_write_pixel((uint8_t)px, (uint8_t)py, true);
                }
            }
        }
    }

    // Overlay 2: small fish swimming left→right in the empty water at y=22
    fish_x++;
    if (fish_x >= OLED_W + 8) fish_x = -8;
    draw_fish(fish_x, 22, oled_phase);

    // Bubble spawner
    if (bubble_spawn_countdown == 0) {
        for (uint8_t i = 0; i < MAX_BUBBLES; i++) {
            if (!bubbles[i].alive) {
                spawn_bubble(&bubbles[i]);
                bubble_spawn_countdown = 12 + (uint8_t)(xorshift32() & 0x0F);
                break;
            }
        }
    } else {
        bubble_spawn_countdown--;
    }

    // Bubble tick — rise, pop at the top
    for (uint8_t i = 0; i < MAX_BUBBLES; i++) {
        if (!bubbles[i].alive) continue;
        bubbles[i].y_q2 -= (int16_t)bubbles[i].rise;
        int8_t by = (int8_t)(bubbles[i].y_q2 >> 2);
        if (by <= BUBBLE_TOP_Y) {
            bubbles[i].alive = false;
            continue;
        }
        draw_bubble(bubbles[i].x, by);
    }

    return false;
}

#endif
