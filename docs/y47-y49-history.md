# Y47 → Y49 order history — what actually happened

Retroactive record of the Y47 full-panel and Y49 right-only-respin fab orders. Written after the fact to correct earlier docs and memory files that captured contemporaneous misdiagnoses as if they were verified fact. Source-of-truth reconstruction from user recollection + git commit history.

## Y47 — full-panel order (2026-07-09, $489 total)

Both halves fabbed together. Discovered post-fab that the right side had **three separate PCB defects**:

1. **OLED pins reversed.** The OLED footprint had the wrong pin order — the 4-pin SSD1306 breakout wouldn't work as designed against the PCB pads. Only workarounds available were both unacceptable:
   - Rotate the OLED module 180° on install → display ends up upside-down / offset from the case cutout.
   - Install on the back side of the PCB → doesn't fit the case bottom mounting.
2. **Backspace 2U stabilizer cutout missing** (SW_61). During design we debated whether a 2U backspace really needed a stab. Decided yes, but the PCB cutout for the stab wire was never added.
3. **Hot-swap layer issue** near the backspace / stab area. Related to or adjacent to #2 — fixed together in the respin.

**Decision:** rather than field-rework three defects per board, respin the right half only.

The left half from Y47 was fully functional and remains the reference for "known-good" placements (see the D1 vs D5 polarity heuristic further down).

## Y49 — right-only respin (2026-07-12+, ~$300)

**Fixes that landed** (git commit `eee48aa` "Right-only-respin v3: rebuild from main with SW_61 stab + hot-swap layer fix"):

- OLED pin order corrected in the footprint.
- Backspace 2U stab cutout added (SW_61).
- Hot-swap layer issue resolved.
- CAD outputs regenerated (`88bb748`).

**New problem introduced by the respin:**

- **A short on B.Cu at approximately (322, 55).** All 3 boards from the Y49 batch shipped with it.
- **Root cause:** the GND_R pour on B.Cu needed refilling, but the refilled state was never saved to disk before Gerber export. GUI DRC looked clean because the fill was done in the GUI — but the on-disk `.kicad_pcb` didn't match, and Gerbers came from disk.

**Field rework on the short:**

- 2 boards: cut the B.Cu trace at ~(322, 55) with an X-Acto → fully functional.
- 3rd board: same cut, plus damage from our debug attempts (see below) → required bridging D5 and F2 to restore function, leaves the board without reverse-current protection.

## The D5 misdiagnosis (this is the part earlier docs got wrong)

While debugging why a Y49 board wouldn't power up via J2, we hypothesized D5 (PMEG2010BELD Schottky, SOD-882D) was reversed. **This hypothesis was wrong** — D5 had been placed correctly by JLCPCB on both Y47 and Y49.

Debug attempts based on the false hypothesis:
- Hot-air rework attempts on D5 damaged the part.
- Also burned F2 (the right-half 5V fuse) during the same session.
- The 3rd board's D5 + F2 collateral required bridging both to restore function.

**The actual issue on all 3 Y49 boards was the B.Cu short**, not D5. Once the short was cut, boards worked. The "D5 needs 180° rotation" narrative that ended up in commit messages and the original `hardware_d5_needs_180_rotation.md` memory file reflected the debug speculation, not a real fab defect.

The D5 guidance flip-flopped across three commits during that debug session:
- `9c2e336` "Remove D5=180° from JLC rotation correction list (my earlier bad guidance)"
- `6f00df3` "Revert D5 rotation guidance — 180° IS needed; JLC just missed applying it"
- `3abd36e` "D5 rotation guidance: 'compare to D1', not 'always 180°'"

Each flip was based on incomplete information. None of it was actually diagnosing the real problem (the pour-save short).

## Lessons and preventions

**Fixes that landed after Y49:**

1. **`scripts/prefab_check.sh`** (`d164d0c`) — the DRC-save-before-fab gate. Uses `kicad-cli` (not the GUI) to refill zones → save board → run DRC from disk state. Exit code non-zero blocks fab. This is the mandatory pre-fab gate now. See README §Pre-fab sanity gate.

2. **D5 polarity heuristic** — "compare to D1 on the left half, match its orientation, don't reason from B.Cu rotation math." Still a sound general polarity rule (SOD-882D is genuinely visually ambiguous), just — the "cost 3 boards" story attached to it was wrong.

**What would have prevented each Y47 issue:**

- **OLED pins reversed:** print the OLED footprint at 1:1, hold the physical module against it, confirm SDA/SCL/VCC/GND land in the correct physical positions. Do this for every polarized connector/module before fab. Especially critical when the module sits on B.Cu (mirror flip inverts the effective pin order).
- **Missing backspace stab cutout:** cross-check every stabilized switch position (Rev 1: SW_6, SW_30, SW_58, SW_61) has a stab wire cutout in `Edge.Cuts` before fab. Consider automating: enumerate all `*_stabilized` footprints, check for `Edge.Cuts` cutouts within radius, flag any without. Rev 2 policy: every key ≥ 2U on the layout gets a stab + cutout, no case-by-case debate.
- **Hot-swap layer issue:** verify all hot-swap sockets are on B.Cu, all 3D models are correctly attached (see the Aug 2026 fix for 4 stabilized footprints with broken relative paths for socket models).

**What would have prevented the Y49 short:**

- Running `scripts/prefab_check.sh` before uploading Gerbers. That's the entire purpose of the script now — assume the GUI lies, always assert from disk.

**What would have prevented the D5 misdiagnosis chase:**

- Diagnose from symptoms up, not from hypothesis down. Symptom was "5V present at F2 input+output but 25 mV at C118" — that's a downstream open or a downstream short pulling the rail to ground. Should have narrowed by continuity-testing +5V_R along its trace before ever touching D5 with hot air.
- Don't rework parts to test hypotheses. If you're not >90% sure a part is wrong, don't heat it. Rework damage is irreversible; hypothesis testing should be non-destructive first.

## Corrected attribution

Earlier phrasing in the README ("A bad 180° request on the right-only re-order killed 3 boards") and the original D5 memory file attributed the Y49 board damage to a D5 rotation error. Both were wrong. The actual attribution is:

- **All 3 Y49 boards damaged by:** the B.Cu short from unsaved pour refill.
- **1 of 3 boards additionally damaged by:** our own rework attempts based on the false D5 hypothesis.
- **D5 itself:** correctly placed by JLCPCB. Never rotated wrong from fab.

Docs and memory files updated 2026-08-23 to reflect this.
