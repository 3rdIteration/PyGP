"""Helpers to build a minimal, synthetic CAP file for the test-suite.

A CAP file is a ZIP archive containing the Java Card converter components. For
the purpose of the tests we only need a valid ``Header`` component (carrying the
``DECAFFED`` magic and the package AID) and an ``Applet`` component listing one
or more applet AIDs. This is enough to exercise the :class:`pygp.loadfile.Loadfile`
parser and the multi-applet installation logic without depending on a real,
proprietary CAP file.
"""

import os
import tempfile
import zipfile


def _hex_to_bytes(hexstr):
    return bytes.fromhex(hexstr.replace(" ", ""))


def build_header_component(package_aid="A0000008040001"):
    """Build a Java Card Header.cap component (tag 0x01)."""
    aid = package_aid.replace(" ", "")
    aid_len = len(aid) // 2
    # data after the 2-byte size field:
    #   magic(4) + jc_minor(1) + jc_major(1) + flags(1)
    #   + pkg_minor(1) + pkg_major(1) + aid_len(1) + aid + name_len(1)
    body = "DECAFFED"          # magic number
    body += "00" + "03"        # Java Card version 3.0 (minor, major)
    body += "00"               # flags (no int support)
    body += "00" + "01"        # package version 1.0 (minor, major)
    body += "%02X" % aid_len   # AID length
    body += aid                # package AID
    body += "00"               # package name length (0)
    size = len(body) // 2
    return "01" + "%04X" % size + body


def build_applet_component(applet_aids):
    """Build a Java Card Applet.cap component (tag 0x03) listing several AIDs."""
    count = len(applet_aids)
    body = "%02X" % count
    for aid in applet_aids:
        aid = aid.replace(" ", "")
        aid_len = len(aid) // 2
        body += "%02X" % aid_len
        body += aid
        body += "0000"  # install_method offset (unused by the parser)
    size = len(body) // 2
    return "03" + "%04X" % size + body


def write_cap_file(path, package_aid="A0000008040001",
                   applet_aids=("A000000804000101", "A000000804000102")):
    """Create a synthetic CAP (ZIP) file at ``path``."""
    header = build_header_component(package_aid)
    applet = build_applet_component(list(applet_aids))
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("test/javacard/Header.cap", _hex_to_bytes(header))
        zf.writestr("test/javacard/Applet.cap", _hex_to_bytes(applet))
    return path


def make_temp_cap(**kwargs):
    """Create a synthetic CAP file in a temporary location and return its path."""
    fd, path = tempfile.mkstemp(suffix=".cap")
    os.close(fd)
    return write_cap_file(path, **kwargs)
