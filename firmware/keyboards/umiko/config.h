// SPDX-License-Identifier: GPL-2.0-or-later
#pragma once

// Split serial driver (vendor PIO) pin config is set via info.json's
// split.serial.pin field. Half-duplex single-wire mode is inferred
// when RX and TX pins are the same (no full-duplex flag needed).
