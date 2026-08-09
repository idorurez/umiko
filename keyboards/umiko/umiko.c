// SPDX-License-Identifier: GPL-2.0-or-later
// umiko keyboard-level init file. Currently only holds g_led_config for
// RGB Matrix. Keep this small; keymap-level stuff belongs in keymaps/*/keymap.c.

#include "quantum.h"

#ifdef RGB_MATRIX_ENABLE

// ─── LED chain layout ─────────────────────────────────────────────────────
// Traced from umiko.kicad_pcb DIN->DOUT nets (see docs/led-chain.md).
// 90 total LEDs: left chain first (42), then right chain (48).
// Per side: underglow first, then per-key.
//   Left:  0..11 underglow, 12..41 per-key
//   Right: 42..56 underglow (right-local 0..14), 57..89 per-key (right-local 15..47)
// ──────────────────────────────────────────────────────────────────────────

led_config_t g_led_config = { {
    // Matrix -> LED chain index (10 rows × 8 cols)
    // Rows 0..4 = left half; rows 5..9 = right half.
    {     12,     18,     19,     28,     29,     36,     37, NO_LED },  // row 0
    {     13, NO_LED,     20,     27,     30,     35,     38, NO_LED },  // row 1
    {     14, NO_LED,     21,     26,     31,     34,     39, NO_LED },  // row 2
    { NO_LED,     17,     22,     25,     32,     33,     40, NO_LED },  // row 3
    {     15,     16,     23,     24, NO_LED, NO_LED,     41, NO_LED },  // row 4
    {     85,     84,     77,     76,     67,     66, NO_LED,     59 },  // row 5
    {     86,     83,     78,     75,     68,     65,     60,     58 },  // row 6
    {     87,     82,     79,     74,     69,     64,     61, NO_LED },  // row 7
    {     88,     81,     80,     73,     70, NO_LED,     62, NO_LED },  // row 8
    {     89, NO_LED, NO_LED,     72,     71, NO_LED,     63,     57 },  // row 9
}, {
    // LED physical positions (x, y) in RGB Matrix coordinate space (~0..224, ~0..64).
    // Order = chain order.  UG = underglow, PK = per-key.
    {  0, 28},  // idx  0  LED16  UG  —
    {  0, 45},  // idx  1  LED18  UG  —
    {  6, 61},  // idx  2  LED25  UG  —
    { 34, 61},  // idx  3  LED31  UG  —
    { 63, 61},  // idx  4  LED37  UG  —
    { 84, 61},  // idx  5  LED36  UG  —
    { 83, 45},  // idx  6  LED30  UG  —
    { 78, 29},  // idx  7  LED24  UG  —
    { 73, 13},  // idx  8  LED17  UG  —
    { 51, 13},  // idx  9  LED15  UG  —
    { 30, 13},  // idx 10  LED6   UG  —
    {  4, 13},  // idx 11  LED5   UG  —
    {  1,  0},  // idx 12  LED1   PK  SW_1
    {  4, 16},  // idx 13  LED2   PK  SW_2
    {  6, 32},  // idx 14  LED3   PK  SW_3
    {  2, 64},  // idx 15  LED4   PK  SW_4
    { 21, 64},  // idx 16  LED9   PK  SW_7
    { 10, 48},  // idx 17  LED8   PK  SW_6
    { 15,  0},  // idx 18  LED7   PK  SW_5
    { 30,  0},  // idx 19  LED10  PK  SW_8
    { 22, 16},  // idx 20  LED11  PK  SW_9
    { 26, 32},  // idx 21  LED12  PK  SW_10
    { 33, 48},  // idx 22  LED13  PK  SW_11
    { 39, 64},  // idx 23  LED14  PK  SW_12
    { 57, 64},  // idx 24  LED23  PK  SW_17
    { 48, 48},  // idx 25  LED22  PK  SW_16
    { 40, 32},  // idx 26  LED21  PK  SW_15
    { 37, 16},  // idx 27  LED20  PK  SW_14
    { 44,  0},  // idx 28  LED19  PK  SW_13
    { 58,  0},  // idx 29  LED26  PK  SW_18
    { 51, 16},  // idx 30  LED27  PK  SW_19
    { 55, 32},  // idx 31  LED28  PK  SW_20
    { 62, 48},  // idx 32  LED29  PK  SW_21
    { 76, 48},  // idx 33  LED35  PK  SW_25
    { 69, 32},  // idx 34  LED34  PK  SW_24
    { 66, 16},  // idx 35  LED33  PK  SW_23
    { 73,  0},  // idx 36  LED32  PK  SW_22
    { 87,  0},  // idx 37  LED38  PK  SW_26
    { 80, 16},  // idx 38  LED39  PK  SW_27
    { 84, 32},  // idx 39  LED40  PK  SW_28
    { 91, 48},  // idx 40  LED41  PK  SW_29
    { 82, 64},  // idx 41  LED42  PK  SW_30
    {219, 28},  // idx 42  LED89  UG  —
    {220, 45},  // idx 43  LED88  UG  —
    {215, 61},  // idx 44  LED84  UG  —
    {197, 61},  // idx 45  LED79  UG  —
    {179, 61},  // idx 46  LED75  UG  —
    {159, 61},  // idx 47  LED68  UG  —
    {141, 61},  // idx 48  LED61  UG  —
    {123, 61},  // idx 49  LED90  UG  —
    {125, 44},  // idx 50  LED55  UG  —
    {120, 29},  // idx 51  LED49  UG  —
    {125, 13},  // idx 52  LED48  UG  —
    {149, 13},  // idx 53  LED54  UG  —
    {170, 13},  // idx 54  LED60  UG  —
    {193, 13},  // idx 55  LED67  UG  —
    {211, 13},  // idx 56  LED74  UG  —
    {224, 64},  // idx 57  LED87  PK  SW_63
    {222, 16},  // idx 58  LED86  PK  SW_62
    {219,  0},  // idx 59  LED85  PK  SW_61
    {204, 16},  // idx 60  LED80  PK  SW_57
    {217, 32},  // idx 61  LED81  PK  SW_58
    {213, 48},  // idx 62  LED82  PK  SW_59
    {206, 64},  // idx 63  LED83  PK  SW_60
    {193, 32},  // idx 64  LED78  PK  SW_56
    {190, 16},  // idx 65  LED77  PK  SW_55
    {197,  0},  // idx 66  LED76  PK  SW_54
    {183,  0},  // idx 67  LED69  PK  SW_49
    {175, 16},  // idx 68  LED70  PK  SW_50
    {179, 32},  // idx 69  LED71  PK  SW_51
    {186, 48},  // idx 70  LED72  PK  SW_52
    {188, 64},  // idx 71  LED73  PK  SW_53
    {170, 64},  // idx 72  LED66  PK  SW_48
    {172, 48},  // idx 73  LED65  PK  SW_47
    {165, 32},  // idx 74  LED64  PK  SW_46
    {161, 16},  // idx 75  LED63  PK  SW_45
    {168,  0},  // idx 76  LED62  PK  SW_44
    {154,  0},  // idx 77  LED56  PK  SW_40
    {147, 16},  // idx 78  LED57  PK  SW_41
    {150, 32},  // idx 79  LED58  PK  SW_42
    {157, 48},  // idx 80  LED59  PK  SW_43
    {143, 48},  // idx 81  LED53  PK  SW_39
    {136, 32},  // idx 82  LED52  PK  SW_38
    {132, 16},  // idx 83  LED51  PK  SW_37
    {139,  0},  // idx 84  LED50  PK  SW_36
    {125,  0},  // idx 85  LED43  PK  SW_31
    {118, 16},  // idx 86  LED44  PK  SW_32
    {121, 32},  // idx 87  LED45  PK  SW_33
    {129, 48},  // idx 88  LED46  PK  SW_34
    {141, 64},  // idx 89  LED47  PK  SW_35
}, {
    // Per-LED flags. 1=LED_FLAG_KEYLIGHT (regular key), 2=LED_FLAG_UNDERGLOW,
    // 4=LED_FLAG_MODIFIER (thumb-cluster / mod keys).
    2,  // idx  0  LED16  LED_FLAG_UNDERGLOW
    2,  // idx  1  LED18  LED_FLAG_UNDERGLOW
    2,  // idx  2  LED25  LED_FLAG_UNDERGLOW
    2,  // idx  3  LED31  LED_FLAG_UNDERGLOW
    2,  // idx  4  LED37  LED_FLAG_UNDERGLOW
    2,  // idx  5  LED36  LED_FLAG_UNDERGLOW
    2,  // idx  6  LED30  LED_FLAG_UNDERGLOW
    2,  // idx  7  LED24  LED_FLAG_UNDERGLOW
    2,  // idx  8  LED17  LED_FLAG_UNDERGLOW
    2,  // idx  9  LED15  LED_FLAG_UNDERGLOW
    2,  // idx 10  LED6   LED_FLAG_UNDERGLOW
    2,  // idx 11  LED5   LED_FLAG_UNDERGLOW
    1,  // idx 12  LED1   LED_FLAG_KEYLIGHT
    1,  // idx 13  LED2   LED_FLAG_KEYLIGHT
    1,  // idx 14  LED3   LED_FLAG_KEYLIGHT
    4,  // idx 15  LED4   LED_FLAG_MODIFIER
    4,  // idx 16  LED9   LED_FLAG_MODIFIER
    1,  // idx 17  LED8   LED_FLAG_KEYLIGHT
    1,  // idx 18  LED7   LED_FLAG_KEYLIGHT
    1,  // idx 19  LED10  LED_FLAG_KEYLIGHT
    1,  // idx 20  LED11  LED_FLAG_KEYLIGHT
    1,  // idx 21  LED12  LED_FLAG_KEYLIGHT
    1,  // idx 22  LED13  LED_FLAG_KEYLIGHT
    4,  // idx 23  LED14  LED_FLAG_MODIFIER
    4,  // idx 24  LED23  LED_FLAG_MODIFIER
    1,  // idx 25  LED22  LED_FLAG_KEYLIGHT
    1,  // idx 26  LED21  LED_FLAG_KEYLIGHT
    1,  // idx 27  LED20  LED_FLAG_KEYLIGHT
    1,  // idx 28  LED19  LED_FLAG_KEYLIGHT
    1,  // idx 29  LED26  LED_FLAG_KEYLIGHT
    1,  // idx 30  LED27  LED_FLAG_KEYLIGHT
    1,  // idx 31  LED28  LED_FLAG_KEYLIGHT
    1,  // idx 32  LED29  LED_FLAG_KEYLIGHT
    1,  // idx 33  LED35  LED_FLAG_KEYLIGHT
    1,  // idx 34  LED34  LED_FLAG_KEYLIGHT
    1,  // idx 35  LED33  LED_FLAG_KEYLIGHT
    1,  // idx 36  LED32  LED_FLAG_KEYLIGHT
    1,  // idx 37  LED38  LED_FLAG_KEYLIGHT
    1,  // idx 38  LED39  LED_FLAG_KEYLIGHT
    1,  // idx 39  LED40  LED_FLAG_KEYLIGHT
    1,  // idx 40  LED41  LED_FLAG_KEYLIGHT
    4,  // idx 41  LED42  LED_FLAG_MODIFIER
    2,  // idx 42  LED89  LED_FLAG_UNDERGLOW
    2,  // idx 43  LED88  LED_FLAG_UNDERGLOW
    2,  // idx 44  LED84  LED_FLAG_UNDERGLOW
    2,  // idx 45  LED79  LED_FLAG_UNDERGLOW
    2,  // idx 46  LED75  LED_FLAG_UNDERGLOW
    2,  // idx 47  LED68  LED_FLAG_UNDERGLOW
    2,  // idx 48  LED61  LED_FLAG_UNDERGLOW
    2,  // idx 49  LED90  LED_FLAG_UNDERGLOW
    2,  // idx 50  LED55  LED_FLAG_UNDERGLOW
    2,  // idx 51  LED49  LED_FLAG_UNDERGLOW
    2,  // idx 52  LED48  LED_FLAG_UNDERGLOW
    2,  // idx 53  LED54  LED_FLAG_UNDERGLOW
    2,  // idx 54  LED60  LED_FLAG_UNDERGLOW
    2,  // idx 55  LED67  LED_FLAG_UNDERGLOW
    2,  // idx 56  LED74  LED_FLAG_UNDERGLOW
    4,  // idx 57  LED87  LED_FLAG_MODIFIER
    1,  // idx 58  LED86  LED_FLAG_KEYLIGHT
    1,  // idx 59  LED85  LED_FLAG_KEYLIGHT
    1,  // idx 60  LED80  LED_FLAG_KEYLIGHT
    1,  // idx 61  LED81  LED_FLAG_KEYLIGHT
    1,  // idx 62  LED82  LED_FLAG_KEYLIGHT
    4,  // idx 63  LED83  LED_FLAG_MODIFIER
    1,  // idx 64  LED78  LED_FLAG_KEYLIGHT
    1,  // idx 65  LED77  LED_FLAG_KEYLIGHT
    1,  // idx 66  LED76  LED_FLAG_KEYLIGHT
    1,  // idx 67  LED69  LED_FLAG_KEYLIGHT
    1,  // idx 68  LED70  LED_FLAG_KEYLIGHT
    1,  // idx 69  LED71  LED_FLAG_KEYLIGHT
    1,  // idx 70  LED72  LED_FLAG_KEYLIGHT
    4,  // idx 71  LED73  LED_FLAG_MODIFIER
    4,  // idx 72  LED66  LED_FLAG_MODIFIER
    1,  // idx 73  LED65  LED_FLAG_KEYLIGHT
    1,  // idx 74  LED64  LED_FLAG_KEYLIGHT
    1,  // idx 75  LED63  LED_FLAG_KEYLIGHT
    1,  // idx 76  LED62  LED_FLAG_KEYLIGHT
    1,  // idx 77  LED56  LED_FLAG_KEYLIGHT
    1,  // idx 78  LED57  LED_FLAG_KEYLIGHT
    1,  // idx 79  LED58  LED_FLAG_KEYLIGHT
    1,  // idx 80  LED59  LED_FLAG_KEYLIGHT
    1,  // idx 81  LED53  LED_FLAG_KEYLIGHT
    1,  // idx 82  LED52  LED_FLAG_KEYLIGHT
    1,  // idx 83  LED51  LED_FLAG_KEYLIGHT
    1,  // idx 84  LED50  LED_FLAG_KEYLIGHT
    1,  // idx 85  LED43  LED_FLAG_KEYLIGHT
    1,  // idx 86  LED44  LED_FLAG_KEYLIGHT
    1,  // idx 87  LED45  LED_FLAG_KEYLIGHT
    1,  // idx 88  LED46  LED_FLAG_KEYLIGHT
    4,  // idx 89  LED47  LED_FLAG_MODIFIER
} };

#endif
