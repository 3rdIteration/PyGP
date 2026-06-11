"""Command line interface for PyGP.

The command line options intentionally follow the conventions used by
`GlobalPlatformPro <https://github.com/martinpaljak/GlobalPlatformPro>`_ (the
``gp`` tool) so that existing scripts and habits keep working, while relying
only on Python dependencies (``pyscard``, ``cryptography``) instead of a Java
runtime.

Typical usage::

    # list installed applets / packages (authenticates with the default test key)
    pygp --list

    # install every applet contained in a CAP file
    pygp --install MyApplet.cap

    # install an applet and pass install parameters (tag C9), e.g. Seedkeeper
    pygp --install Seedkeeper.cap --params 020000

    # delete an applet (and its package)
    pygp --delete A0000008040001 --delete-deps

    # lock the card by replacing the default keys with a new key
    pygp --lock 0123456789ABCDEF0123456789ABCDEF

    # unlock the card (restore the default test key)
    pygp --unlock

    # use a non default key (single master key or individual keys)
    pygp --list --key 404142434445464748494A4B4C4D4E4F
    pygp --list --key-enc <ENC> --key-mac <MAC> --key-dek <DEK>
"""

import argparse
import sys

import pygp


# The GlobalPlatform "test" key used by the vast majority of development cards.
DEFAULT_GP_KEY = "404142434445464748494A4B4C4D4E4F"


def build_parser():
    parser = argparse.ArgumentParser(
        prog="pygp",
        description="PyGP - a pure Python GlobalPlatform client (gp compatible CLI).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # --- reader / transport options ------------------------------------
    parser.add_argument("-r", "--reader", metavar="NAME", default=None,
                        help="Use the PC/SC reader whose name contains NAME (default: first reader with a card).")
    parser.add_argument("--protocol", choices=["T0", "T1", "Tx"], default="Tx",
                        help="Force the card transport protocol (default: Tx, i.e. T=0 or T=1).")
    parser.add_argument("--sdaid", metavar="AID", default=None,
                        help="Select this Security Domain AID instead of the default Issuer Security Domain.")

    # --- key / secure channel options ----------------------------------
    parser.add_argument("--key", metavar="HEX", default=None,
                        help="Single master key used for ENC, MAC and DEK (GlobalPlatform single key mode).")
    parser.add_argument("--key-enc", metavar="HEX", default=None, help="Secure Channel ENC key.")
    parser.add_argument("--key-mac", metavar="HEX", default=None, help="Secure Channel MAC key.")
    parser.add_argument("--key-dek", metavar="HEX", default=None, help="Secure Channel DEK key.")
    parser.add_argument("--key-ver", metavar="HEX", default="00",
                        help="Key set version used for INITIALIZE UPDATE (default: 00 = card default keyset).")
    parser.add_argument("--key-type", choices=["DES", "AES"], default=None,
                        help="Key type for PUT KEY operations (lock/unlock). Defaults to the negotiated SCP "
                             "(DES for SCP02, AES for SCP03).")
    parser.add_argument("--scp", choices=["02", "03"], default=None,
                        help="Force the Secure Channel Protocol (default: auto-detected from the card).")
    parser.add_argument("--secure", action="store_true",
                        help="Establish the secure channel with C-MAC (and C-DECRYPTION). Implied by most commands.")

    # --- informational commands ----------------------------------------
    parser.add_argument("-i", "--info", action="store_true", help="Print card ATR and Issuer Security Domain info.")
    parser.add_argument("-l", "--list", action="store_true", dest="do_list",
                        help="List the applets, packages and the card manager.")
    parser.add_argument("--readers", action="store_true", help="List the available PC/SC readers and exit.")
    parser.add_argument("--cap-info", metavar="CAP", default=None,
                        help="Print information about a CAP file (offline, no card needed) and exit.")

    # --- content management commands -----------------------------------
    parser.add_argument("--install", metavar="CAP", default=None,
                        help="Load a CAP file and install every applet it contains.")
    parser.add_argument("--load", metavar="CAP", default=None,
                        help="Load a CAP file (install for load + load blocks) without instantiating any applet.")
    parser.add_argument("--uninstall", metavar="CAP", default=None,
                        help="Delete the package (and its applets) corresponding to a CAP file.")
    parser.add_argument("--delete", metavar="AID", action="append", default=None,
                        help="Delete the applet or package with this AID (may be given several times).")
    parser.add_argument("--delete-deps", "--deletedeps", action="store_true", dest="delete_deps",
                        help="When deleting, also delete dependent/related packages and applets.")

    # --- install tuning -------------------------------------------------
    parser.add_argument("--create", metavar="AID", action="append", default=None,
                        help="Instance AID(s) to create when installing (default: the applet/module AID).")
    parser.add_argument("--module", metavar="AID", action="append", default=None,
                        help="Restrict installation to these module (applet) AID(s) from the CAP file.")
    parser.add_argument("--params", metavar="HEX", default=None,
                        help="Application specific install parameters (tag C9), e.g. Seedkeeper memory size.")
    parser.add_argument("--install-params", metavar="HEX", default=None,
                        help="System install parameters (tag EF).")
    parser.add_argument("--privs", metavar="PRIV", action="append", default=None,
                        help="Application privilege(s) to grant on install (e.g. --privs SD --privs TP).")
    parser.add_argument("--block-size", type=int, default=230, help="LOAD block size in bytes (default: 230).")

    # --- life cycle / lock-unlock --------------------------------------
    parser.add_argument("--lock", metavar="HEX", nargs="?", const=DEFAULT_GP_KEY, default=None,
                        help="Replace the card keys with a new key (lock the card). "
                             "Optionally give the new key value.")
    parser.add_argument("--unlock", action="store_true",
                        help="Restore the default GlobalPlatform test key (unlock the card).")
    parser.add_argument("--new-key", metavar="HEX", default=None,
                        help="New key value used by --lock (overrides the positional value).")
    parser.add_argument("--new-key-ver", metavar="HEX", default="01",
                        help="Key set version assigned to the new keys by --lock/--unlock (default: 01).")
    parser.add_argument("--lock-card", action="store_true", help="Set the card life cycle state to CARD_LOCKED.")
    parser.add_argument("--unlock-card", action="store_true", help="Set the card life cycle state back to SECURED.")
    parser.add_argument("--lock-applet", metavar="AID", default=None, help="Lock the applet with this AID.")
    parser.add_argument("--unlock-applet", metavar="AID", default=None, help="Unlock the applet with this AID.")

    # --- raw / misc -----------------------------------------------------
    parser.add_argument("--store-data", metavar="HEX", default=None, help="Send a STORE DATA command with this payload.")
    parser.add_argument("--apdu", metavar="HEX", action="append", default=None,
                        help="Send a raw APDU (may be given several times). Requires no secure channel by default.")

    # --- logging --------------------------------------------------------
    parser.add_argument("-d", "--debug", action="store_true", help="Show APDU exchanges.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose (debug level) logging.")
    parser.add_argument("--version", action="version", version="PyGP %s" % pygp.get_version())

    return parser


def _configure_logging(args):
    mode = pygp.CONSOLE_TRACE
    if args.verbose:
        mode |= pygp.DEBUG_LEVEL
    else:
        mode |= pygp.INFO_LEVEL
    if args.debug:
        mode |= pygp.APDU
    pygp.set_log_mode(mode)


def _resolve_keys(args):
    """Return (enc, mac, dek) key values from the CLI options.

    Mirrors GlobalPlatformPro: a single ``--key`` is used for all three keys,
    individual ``--key-enc/--key-mac/--key-dek`` override it, and the default GP
    test key is used when nothing is supplied.
    """
    base = args.key if args.key is not None else DEFAULT_GP_KEY
    enc = args.key_enc if args.key_enc is not None else base
    mac = args.key_mac if args.key_mac is not None else base
    dek = args.key_dek if args.key_dek is not None else base
    return enc, mac, dek


def _scp_arg(args):
    if args.scp is None:
        return None
    return int(args.scp, 16)


def _authenticate(args, security_level=None):
    """Open a secure channel using the supplied (or default) keys."""
    enc, mac, dek = _resolve_keys(args)
    if security_level is None:
        security_level = pygp.SECURITY_LEVEL_C_MAC
    pygp.auth(enc_key=enc, mac_key=mac, dek_key=dek, scp=_scp_arg(args),
              keysetversion=args.key_ver, securitylevel=security_level)


def _key_type_for_scp(args):
    if args.key_type is not None:
        return args.key_type
    scp = pygp.get_secure_channel_protocol()
    if scp == pygp.GP_SCP02:
        return "DES"
    # default to AES (SCP03 and modern cards)
    return "AES"


def _put_new_keys(args, new_key_value):
    """Replace the card keys (ENC/MAC/DEK) with ``new_key_value`` via PUT KEY."""
    key_type = _key_type_for_scp(args)
    new_ver = args.new_key_ver
    # store the three new keys in the off-card repository under the new version
    pygp.set_key("%s/1/%s/%s" % (new_ver, key_type, new_key_value))
    pygp.set_key("%s/2/%s/%s" % (new_ver, key_type, new_key_value))
    pygp.set_key("%s/3/%s/%s" % (new_ver, key_type, new_key_value))
    # PUT KEY replacing the current keyset
    pygp.put_scp_key(new_ver, replace=True)


def _run(args):
    # offline command: inspect a CAP file without a card
    if args.cap_info:
        print(pygp.get_cap_info(args.cap_info))
        return 0

    # list readers without requiring a card
    if args.readers:
        pygp.list_readers()
        return 0

    pygp.terminal(args.reader)

    try:
        pygp.change_protocol(args.protocol)
        pygp.card()

        if args.sdaid:
            pygp.select(args.sdaid)

        # commands that only need card access (no secure channel)
        if args.apdu:
            for apdu in args.apdu:
                pygp.send(apdu, raw_mode=True)

        if args.info:
            pygp.get_status_isd()

        # determine whether a secure channel is required
        needs_auth = any([
            args.do_list, args.install, args.load, args.uninstall, args.delete,
            args.lock is not None, args.unlock, args.lock_card, args.unlock_card,
            args.lock_applet, args.unlock_applet, args.store_data,
        ])

        if needs_auth:
            # locking/unlocking the keys needs DEK so use C-MAC + C-DECRYPTION
            level = pygp.SECURITY_LEVEL_C_DEC_C_MAC if (
                args.lock is not None or args.unlock) else pygp.SECURITY_LEVEL_C_MAC
            _authenticate(args, security_level=level)

        if args.do_list:
            pygp.ls()

        if args.load:
            pygp.load_file(args.load, block_size=args.block_size)

        if args.install:
            privileges = args.privs if args.privs else None
            installed = pygp.install_capfile(
                args.install,
                security_domain_aid=args.sdaid or '',
                module_aids=args.module,
                instance_aids=args.create,
                application_privileges=privileges,
                application_specific_parameters=args.params,
                install_parameters=args.install_params,
                block_size=args.block_size,
            )
            for module_aid, instance_aid in installed:
                pygp.echo("Installed applet %s as instance %s" % (module_aid, instance_aid))

        if args.uninstall:
            package_aid = pygp.get_cap_info(args.uninstall).get_aid()
            pygp.delete_package(package_aid)

        if args.delete:
            for aid in args.delete:
                if args.delete_deps:
                    pygp.delete_package(aid)
                else:
                    pygp.delete(aid)

        if args.store_data:
            pygp.store_data(args.store_data)

        if args.lock is not None:
            new_key = args.new_key if args.new_key is not None else args.lock
            _put_new_keys(args, new_key)

        if args.unlock:
            _put_new_keys(args, DEFAULT_GP_KEY)

        if args.lock_applet:
            pygp.set_app_state(pygp.LIFE_CYCLE_APPLICATION_LOCKED, args.lock_applet)

        if args.unlock_applet:
            pygp.set_app_state(pygp.LIFE_CYCLE_APPLICATION_SELECTABLE, args.unlock_applet)

        if args.lock_card:
            pygp.set_status(pygp.CARD_ELEMENT_ISD, pygp.LIFE_CYCLE_CARD_LOCKED, args.sdaid or pygp.ISD_APPLICATION_AID)

        if args.unlock_card:
            pygp.set_status(pygp.CARD_ELEMENT_ISD, pygp.LIFE_CYCLE_CARD_SECURED, args.sdaid or pygp.ISD_APPLICATION_AID)

        return 0
    finally:
        try:
            pygp.close()
        except BaseException:
            pass


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    # if no actionable option was given, print help
    actionable = any([
        args.info, args.do_list, args.readers, args.cap_info, args.install, args.load,
        args.uninstall, args.delete, args.lock is not None, args.unlock, args.lock_card,
        args.unlock_card, args.lock_applet, args.unlock_applet, args.store_data, args.apdu,
    ])
    if not actionable:
        parser.print_help()
        return 0

    _configure_logging(args)

    try:
        return _run(args)
    except BaseException as exc:  # surface a clean error message, full trace in debug mode
        if args.verbose:
            raise
        sys.stderr.write("Error: %s\n" % exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
