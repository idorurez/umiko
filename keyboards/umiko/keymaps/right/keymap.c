// SPDX-License-Identifier: GPL-2.0-or-later
// Right-half build: identical keymap to `default`, compiled with
// -DUMiko_RIGHT (see rules.mk) so is_keyboard_left_impl() returns false.
// Shared code is #included to avoid a forked copy that would drift; only
// this TU is compiled for `-km right`, so no duplicate symbols.
#include "../default/keymap.c"
