import unittest
from unittest import mock

import pygp
from pygp import cli


class Test_Cli_Install(unittest.TestCase):
    """Verify ``pygp --install`` reports the applets install_capfile returns.

    The card access functions are stubbed so the test needs no reader or card.
    """

    def setUp(self):
        self.messages = []
        patches = [
            mock.patch.object(pygp, "set_log_mode"),
            mock.patch.object(pygp, "terminal"),
            mock.patch.object(pygp, "change_protocol"),
            mock.patch.object(pygp, "card"),
            mock.patch.object(pygp, "auth"),
            mock.patch.object(pygp, "close"),
            mock.patch.object(pygp, "echo", side_effect=self.messages.append),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def test_install_prints_each_applet(self):
        result = {
            "installed": [("A000000804000101", "A00000080400010101"),
                          ("A000000804000102", "D2760000850101")],
            "ndef_skipped": False,
        }
        with mock.patch.object(pygp, "install_capfile", return_value=result):
            self.assertEqual(cli.main(["--install", "Applet.cap"]), 0)
        self.assertEqual(self.messages,
                         ["Installed applet A000000804000101 as instance A00000080400010101",
                          "Installed applet A000000804000102 as instance D2760000850101"])


if __name__ == "__main__":
    unittest.main()
