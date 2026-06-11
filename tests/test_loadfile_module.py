import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

import cap_fixture
import pygp

# ``import pygp`` re-exports the gp_functions module as ``pygp.gp`` and the error
# module as ``pygp.error`` (via ``from pygp.pygp import *``), so reuse those to
# avoid shadowing issues with the ``pygp.gp`` subpackage.
gp = pygp.gp
error = pygp.error


def _success(*args, **kwargs):
    status = error.create_no_error_status(0x00)
    return status


class Test_Loadfile(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cap_path = cap_fixture.make_temp_cap(
            package_aid="A0000008040001",
            applet_aids=("A000000804000101", "A000000804000102"),
        )

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.cap_path):
            os.remove(cls.cap_path)

    def test_package_aid(self):
        lf = pygp.get_cap_info(self.cap_path)
        self.assertEqual(lf.get_aid(), "A0000008040001")

    def test_is_cap_file(self):
        lf = pygp.get_cap_info(self.cap_path)
        self.assertTrue(lf.isCapfile())
        self.assertTrue(lf.isAppletPresent())

    def test_multiple_applets(self):
        """A single CAP file may carry several applets; all must be returned."""
        aids = pygp.get_applet_aids(self.cap_path)
        self.assertEqual(aids, ["A000000804000101", "A000000804000102"])

    def test_load_blocks_chunking(self):
        lf = pygp.get_cap_info(self.cap_path)
        blocks = lf.get_load_blocks(8)
        # every block but the last must be exactly block_size*2 hex chars long
        for block in blocks[:-1]:
            self.assertEqual(len(block), 8 * 2)
        # re-assembling the blocks must reproduce the header + code
        self.assertEqual("".join(blocks),
                         lf._Loadfile__createHeaderSize__() + lf.get_raw_code())


class Test_Install_Capfile(unittest.TestCase):
    """Verify the multi-applet / install-parameters orchestration of install_capfile.

    The actual card communication (gp.install_load / gp.load_blocks /
    gp.install_install) is stubbed so the logic can be tested without a card.
    """

    def setUp(self):
        self.cap_path = cap_fixture.make_temp_cap(
            package_aid="A0000008040001",
            applet_aids=("A000000804000101", "A000000804000102"),
        )
        self._orig = (gp.install_load, gp.load_blocks, gp.install_install)
        self.install_calls = []

        def fake_install_load(*args, **kwargs):
            return _success()

        def fake_load_blocks(*args, **kwargs):
            return _success()

        def fake_install_install(make_selectable, elf_aid, module_aid, instance_aid,
                                 privileges="00", specific=None, install_params=None, token=None):
            self.install_calls.append({
                "make_selectable": make_selectable,
                "elf_aid": elf_aid,
                "module_aid": module_aid,
                "instance_aid": instance_aid,
                "privileges": privileges,
                "specific": specific,
                "install_params": install_params,
                "token": token,
            })
            return _success()

        gp.install_load = fake_install_load
        gp.load_blocks = fake_load_blocks
        gp.install_install = fake_install_install

    def tearDown(self):
        gp.install_load, gp.load_blocks, gp.install_install = self._orig
        if os.path.exists(self.cap_path):
            os.remove(self.cap_path)

    def test_installs_every_applet(self):
        installed = pygp.install_capfile(self.cap_path)
        self.assertEqual(len(self.install_calls), 2)
        self.assertEqual([c["module_aid"] for c in self.install_calls],
                         ["A000000804000101", "A000000804000102"])
        # default instance AID equals the module AID
        self.assertEqual([c["instance_aid"] for c in self.install_calls],
                         ["A000000804000101", "A000000804000102"])
        self.assertEqual(installed,
                         [("A000000804000101", "A000000804000101"),
                          ("A000000804000102", "A000000804000102")])

    def test_install_parameters_shared(self):
        """A single params value is applied to every installed applet (tag C9)."""
        pygp.install_capfile(self.cap_path, application_specific_parameters="020000")
        for call in self.install_calls:
            self.assertEqual(call["specific"], "020000")

    def test_install_parameters_per_applet(self):
        pygp.install_capfile(self.cap_path,
                             application_specific_parameters=["AABB", "CCDD"])
        self.assertEqual(self.install_calls[0]["specific"], "AABB")
        self.assertEqual(self.install_calls[1]["specific"], "CCDD")

    def test_restrict_modules_and_instance_aids(self):
        pygp.install_capfile(self.cap_path,
                             module_aids=["A000000804000102"],
                             instance_aids=["A000000804000199"])
        self.assertEqual(len(self.install_calls), 1)
        self.assertEqual(self.install_calls[0]["module_aid"], "A000000804000102")
        self.assertEqual(self.install_calls[0]["instance_aid"], "A000000804000199")

    def test_privileges_shared_list(self):
        pygp.install_capfile(self.cap_path, application_privileges=["SD"])
        # privileges are converted to a hex byte string; SD must set a bit
        for call in self.install_calls:
            self.assertNotEqual(call["privileges"], "00")
            self.assertEqual(self.install_calls[0]["privileges"], call["privileges"])


if __name__ == "__main__":
    unittest.main()
