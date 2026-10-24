#!/usr/bin/env python
"""Tests for toggle_switch_3d.py. Run: python scripts/test_toggle_switch_3d.py"""

import io
import os
import re
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import toggle_switch_3d as tgl


def mx_model(hidden):
    hide = '\n      (hide yes)' if hidden else ''
    return (
        '    (model "${KIPRJMOD}/footprints/hybrid_switches.pretty/CherryMX-Switch.step"%s\n'
        '      (at (xyz 0 0 0))\n'
        '      (scale (xyz 1 1 1))\n'
        '      (rotate (xyz 0 0 0))\n'
        '    )\n'
    ) % hide


def ks33_model(hidden):
    hide = '\n      (hide yes)' if hidden else ''
    return (
        '    (model "${KIPRJMOD}/footprints/hybrid_switches.pretty/Gateron-KS-33_v2.step"%s\n'
        '      (at (xyz 0 0 0))\n'
        '      (scale (xyz 1 1 1))\n'
        '      (rotate (xyz 0 0 0))\n'
        '    )\n'
    ) % hide


SOCKET_MODEL = (
    '    (model "./Gateron-KS33-Socket.step"\n'
    '      (at (xyz 0 0 0))\n'
    '      (scale (xyz 1 1 1))\n'
    '      (rotate (xyz 0 0 0))\n'
    '    )\n'
)

RESISTOR_MODEL = (
    '    (model "${KICAD10_3DMODEL_DIR}/Resistor_SMD.3dshapes/R_0603_1608Metric.step"\n'
    '      (at (xyz 0 0 0))\n'
    '      (scale (xyz 1 1 1))\n'
    '      (rotate (xyz 0 0 0))\n'
    '    )\n'
)


def fixture():
    return (
        '(kicad_pcb (version 20221018) (generator pcbnew)\n'
        '  (footprint "umiko-hybrid-switches:SW_MX_Gateron_LowProfile_Hybrid_THT_1U" (layer "F.Cu")\n'
        '    (at 10 20)\n'
        '    (property "Reference" "SW_1")\n'
        + mx_model(False) + ks33_model(True) +
        '  )\n'
        '  (footprint "umiko-hybrid-switches:SW_MX_Gateron_LowProfile_Hybrid_THT_1U" (layer "F.Cu")\n'
        '    (at 30 20)\n'
        '    (property "Reference" "SW_2")\n'
        + mx_model(True) + ks33_model(False) + SOCKET_MODEL +
        '  )\n'
        '  (footprint "Resistor_SMD:R_0603_1608Metric" (layer "F.Cu")\n'
        '    (at 50 20)\n'
        '    (property "Reference" "R_1")\n'
        + RESISTOR_MODEL +
        '  )\n'
        ')\n'
    )


def states(pcb_text):
    """Map (ref, variant-or-firstline) -> hidden? for every model block."""
    out = {}
    for p, q in tgl.find_footprints(pcb_text):
        blk = pcb_text[p:q]
        ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
        for mp, mq in tgl.find_model_blocks(blk):
            mblk = blk[mp:mq]
            variant = tgl.model_variant(mblk)
            key = (ref, variant or mblk.split('\n', 1)[0].strip())
            out[key] = '(hide yes)' in mblk
    return out


class ToggleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.pcb = os.path.join(self.tmp, 'test.kicad_pcb')
        with open(self.pcb, 'w', encoding='utf-8', newline='') as f:
            f.write(fixture())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_verb(self, verb):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = tgl.main([verb, '--pcb', self.pcb])
        with open(self.pcb, encoding='utf-8') as f:
            txt = f.read()
        return rc, buf.getvalue(), txt

    def test_default_pcb_is_repo_root(self):
        # Regression: the rev1 script looked inside scripts/ and crashed.
        self.assertEqual(os.path.basename(tgl.DEFAULT_PCB), 'umiko.kicad_pcb')
        self.assertEqual(os.path.dirname(tgl.DEFAULT_PCB),
                         os.path.dirname(tgl.SCRIPT_DIR))

    def test_model_variant(self):
        self.assertEqual(tgl.model_variant(mx_model(False)), 'mx')
        self.assertEqual(tgl.model_variant(ks33_model(True)), 'ks33')
        self.assertIsNone(tgl.model_variant(SOCKET_MODEL))
        self.assertIsNone(tgl.model_variant(RESISTOR_MODEL))

    def test_lowpro(self):
        rc, out, txt = self.run_verb('lowpro')
        self.assertEqual(rc, 0)
        st = states(txt)
        self.assertTrue(st[('SW_1', 'mx')])
        self.assertFalse(st[('SW_1', 'ks33')])
        self.assertTrue(st[('SW_2', 'mx')])
        self.assertFalse(st[('SW_2', 'ks33')])
        # Nothing else touched.
        self.assertIn('updated 2 ', out)
        self.assertTrue(os.path.exists(self.pcb + '.bak_toggle'))

    def test_mx_restores_default(self):
        self.run_verb('lowpro')
        rc, out, txt = self.run_verb('mx')
        self.assertEqual(rc, 0)
        st = states(txt)
        for ref in ('SW_1', 'SW_2'):
            self.assertFalse(st[(ref, 'mx')])
            self.assertTrue(st[(ref, 'ks33')])
        self.assertIn('updated 4 ', out)

    def test_show_matches_mx(self):
        self.run_verb('hide')
        _, _, txt = self.run_verb('show')
        st = states(txt)
        for ref in ('SW_1', 'SW_2'):
            self.assertFalse(st[(ref, 'mx')])
            self.assertTrue(st[(ref, 'ks33')])

    def test_hide(self):
        rc, _, txt = self.run_verb('hide')
        self.assertEqual(rc, 0)
        st = states(txt)
        for ref in ('SW_1', 'SW_2'):
            self.assertTrue(st[(ref, 'mx')])
            self.assertTrue(st[(ref, 'ks33')])

    def test_socket_and_resistor_untouched(self):
        before = fixture()
        for verb in ('mx', 'lowpro', 'hide', 'show'):
            self.run_verb(verb)
            with open(self.pcb, encoding='utf-8') as f:
                txt = f.read()
            self.assertIn(SOCKET_MODEL, txt, verb)
            self.assertIn(RESISTOR_MODEL, txt, verb)
        self.assertIn(SOCKET_MODEL, before)

    def test_idempotent(self):
        self.run_verb('lowpro')
        _, out, _ = self.run_verb('lowpro')
        self.assertIn('updated 0 ', out)

    def test_bad_verb(self):
        before = fixture()
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = tgl.main(['explode', '--pcb', self.pcb])
        self.assertEqual(rc, 1)
        with open(self.pcb, encoding='utf-8') as f:
            self.assertEqual(f.read(), before)


if __name__ == '__main__':
    unittest.main(verbosity=2)
