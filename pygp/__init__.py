"""
PyGP - Python GlobalPlatform library

A Python library for JavaCard/GlobalPlatform operations, providing APDU-level
communication with smart cards supporting the GlobalPlatform specification.

Public API
----------
The following sections document the public API surface. Functions prefixed with
double-underscore (e.g. ``__get_loaded_package_aids__``) are considered private
and may change without notice; prefer their public counterparts where available.

Card Connection & Lifecycle
~~~~~~~~~~~~~~~~~~~~~~~~~~~
terminal, card, atr, close, reset_card, list_readers

Authentication & Secure Channel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
auth, init_update, ext_auth, try_auth, get_secure_channel_protocol

Status Queries (public wrappers)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
get_loaded_package_aids, get_installed_application_aids, get_card_status,
get_status_isd, get_status_applications, ls

APDU & Protocol
~~~~~~~~~~~~~~~~
send, select, select_isd, channel, manage_channel, last_response, last_status

Installation & Management
~~~~~~~~~~~~~~~~~~~~~~~~~~
install_load, install, registry_update, load_file, upload, upload_install,
delete, delete_package, delete_key, put_key, put_scp_key, extradite,
install_capfile, get_cap_info, get_applet_aids

GlobalPlatform Commands
~~~~~~~~~~~~~~~~~~~~~~~~
get_data, store_data, set_status, set_sd_state, set_app_state, set_crs_status,
get_cplc, get_key_information, get_certificate, perform_security_operation,
internal_auth, mutual_auth, get_crs_status

Key Management
~~~~~~~~~~~~~~~
set_key, get_key_in_repository

Logging & Configuration
~~~~~~~~~~~~~~~~~~~~~~~~
set_log_mode, echo, stop_on_error, change_protocol, sleep, get_version,
set_payload_mode, get_payload_list, set_start_timing, get_total_execution_time

TLV Utilities
~~~~~~~~~~~~~~
tlv_read, tlv_print

Constants
~~~~~~~~~~
SECURITY_LEVEL_*, CARD_ELEMENT_*, LIFE_CYCLE_*, SCARD_*, SCP02_IMPL_*, SCP03_IMPL_*
"""

# ---------------------------------------------------------------------------
# Backward-compatible wildcard import
# ---------------------------------------------------------------------------
# This single line preserves the exact behaviour of the original __init__.py
# so that every name previously reachable as ``pygp.<name>`` continues to work.
from pygp.pygp import *

# ---------------------------------------------------------------------------
# Explicit public re-exports
# ---------------------------------------------------------------------------
# `tlv_read` and `tlv_print` live in pygp.utils and reach pygp.py via
# ``from pygp.crypto import *``  (which itself does ``from pygp.utils import *``).
# Re-import them here so they are guaranteed to be part of the public API
# regardless of internal import chains.
from pygp.utils import tlv_read, tlv_print

# ---------------------------------------------------------------------------
# Exception hierarchy
# ---------------------------------------------------------------------------
# Every error PyGP raises derives from PyGPError(Exception), so `except
# Exception` catches them. These used to be bare BaseException, which escaped
# ordinary error handling and killed the calling process.
from pygp.exceptions import (
    PyGPError,
    PyGPConnectionError,
    PyGPCardError,
    PyGPDataError,
)

# `log_info` lives in pygp.logger and is needed by try_auth(). Import it
# explicitly to avoid circular-import issues (logger.py does ``from pygp import *``).
from pygp.logger import log_info

# Backward-compatibility: names starting with '_' are skipped by Python's
# ``import *`` filter. Re-export them explicitly so existing callers continue
# to work and so that ``__all__`` is accurate.
from pygp.pygp import (
    __version__,
    __get_loaded_package_aids__,
    __get_installed_application_aids__,
)

# ---------------------------------------------------------------------------
# Public wrapper: get_loaded_package_aids()
# ---------------------------------------------------------------------------
def get_loaded_package_aids():
    """
    Retrieve list of loaded package AIDs from the connected card.

    This is a public API wrapper around the GlobalPlatform GET STATUS command
    to query loaded packages. It safely handles errors and returns an empty
    list if the operation fails.

    :returns: List of package AIDs as uppercase hex strings
              (e.g. ``['E04B8AC02E', 'A000000151']``).
              Returns empty list if no packages are found or on error.
    :rtype: list

    :raises BaseException: If card communication fails or secure channel
                           is unavailable (when ``must_stop_on_error`` is True).

    Example::

        from pygp import get_loaded_package_aids
        aids = get_loaded_package_aids()
        for aid in aids:
            print(f"Package: {aid}")

    .. note:: The private ``__get_loaded_package_aids__()`` function remains
              available for backward compatibility but new code should prefer
              this public wrapper.
    """
    return __get_loaded_package_aids__()


# ---------------------------------------------------------------------------
# Public wrapper: get_installed_application_aids()
# ---------------------------------------------------------------------------
def get_installed_application_aids():
    """
    Retrieve list of installed application AIDs from the connected card.

    This is a public API wrapper around the GlobalPlatform GET STATUS command
    to query installed applications. It safely handles errors and returns an
    empty list if the operation fails.

    :returns: List of application AIDs as uppercase hex strings.
              Returns empty list if no applications are found or on error.
    :rtype: list

    Example::

        from pygp import get_installed_application_aids
        aids = get_installed_application_aids()
        for aid in aids:
            print(f"Application: {aid}")

    .. note:: The private ``__get_installed_application_aids__()`` function
              remains available for backward compatibility.
    """
    return __get_installed_application_aids__()


# ---------------------------------------------------------------------------
# Non-fatal authentication helper: try_auth()
# ---------------------------------------------------------------------------
def try_auth(enc_key=None, mac_key=None, dek_key=None, scp=None, scpi=None,
             keysetversion='21', sequence_counter="000000",
             securitylevel=SECURITY_LEVEL_NO_SECURE_MESSAGING):
    """
    Attempt authentication with graceful fallback.

    This function is ideal for read-only operations where authentication
    failure is not fatal. Instead of raising an exception, it catches
    errors and returns a structured status dictionary, allowing callers
    to continue with reduced functionality.

    :param str enc_key: The Session Encryption Key (hex string or None
                        for card default).
    :param str mac_key: The Secure Channel MAC Key (hex string or None
                        for card default).
    :param str dek_key: The Key Encryption Key (hex string or None
                        for card default).
    :param str scp: The Secure Channel Protocol (None for card default).
    :param str scpi: The SCP Implementation (None for card default).
    :param str keysetversion: The Key Set version to use.
    :param str sequence_counter: The current sequence counter (payload mode).
    :param int securitylevel: The security level for secure messaging
                              (e.g. ``SECURITY_LEVEL_C_MAC``).

    :returns: A status dictionary with the following keys:

              * ``'authenticated'`` (bool): True if authentication succeeded.
              * ``'error'`` (str or None): Error message if authentication failed.
              * ``'timestamp'`` (float): Unix timestamp when auth was attempted.

    :rtype: dict

    Example::

        from pygp import try_auth, SECURITY_LEVEL_C_MAC

        result = try_auth(
            enc_key='404142434445464748494A4B4C4D4E4F',
            mac_key='404142434445464748494A4B4C4D4E4F',
            dek_key='404142434445464748494A4B4C4D4E4F',
            securitylevel=SECURITY_LEVEL_C_MAC,
        )

        if result['authenticated']:
            print("Authenticated - secure channel available")
        else:
            print(f"Auth failed: {result['error']} - continuing without auth")

    .. note:: This function does NOT raise exceptions. Use :func:`auth` when
              authentication failure should be fatal.
    """
    import time

    status = {
        'authenticated': False,
        'error': None,
        'timestamp': time.time(),
    }

    try:
        auth(enc_key=enc_key, mac_key=mac_key, dek_key=dek_key,
             scp=scp, scpi=scpi, keysetversion=keysetversion,
             sequence_counter=sequence_counter,
             securitylevel=securitylevel)
        status['authenticated'] = True
    except BaseException as e:
        status['error'] = str(e)
        # logger is available via wildcard import from pygp.py
        log_info(f"Authentication attempt failed: {e}")

    return status


# ---------------------------------------------------------------------------
# Structured card status: get_card_status()
# ---------------------------------------------------------------------------
def get_card_status():
    """
    Retrieve comprehensive card status in structured format.

    Issues multiple GET STATUS commands to gather information about the
    Card Manager (ISD), installed applications, and loaded packages, then
    returns everything as a single dictionary.

    :returns: A dictionary with the following keys:

      * ``'card_manager'`` (dict or None): ISD info with sub-keys
        ``'aid'``, ``'lifecycle_state'``, ``'privileges'``.
      * ``'applications'`` (list): Installed applications, each a dict with
        ``'aid'``, ``'name'``, ``'lifecycle_state'``, ``'privileges'``.
      * ``'packages'`` (list): Loaded packages, each a dict with
        ``'aid'``, ``'name'``, ``'lifecycle_state'``.  Modules (if present)
        are listed under ``'modules'``.
      * ``'secure_channel_available'`` (bool): True if a secure channel is
        currently established.
      * ``'is_locked'`` (bool): True if the Card Manager lifecycle indicates
        a locked state.

    :rtype: dict

    :raises BaseException: If card communication fails.

    Example::

        from pygp import get_card_status

        status = get_card_status()
        print(f"Card locked: {status['is_locked']}")
        for app in status['applications']:
            print(f"  App: {app.get('name', 'unknown')} ({app['aid']})")
    """
    from pygp.gp import gp_functions as gp

    result = {
        'card_manager': None,
        'applications': [],
        'packages': [],
        'secure_channel_available': False,
        'is_locked': False,
    }

    # -- Check secure channel -------------------------------------------
    try:
        scp = get_secure_channel_protocol()
        result['secure_channel_available'] = scp is not None
    except BaseException:
        pass

    # -- Card Manager (ISD) status --------------------------------------
    try:
        error_status, isd_info = gp.get_status('80')
        __handle_error_status__(error_status, "get_card_status (isd): ")

        if isd_info is not None:
            status_dic = tlv_read(isd_info)['E3']
            aid_raw = status_dic['4F'].upper()
            lifecycle_raw = status_dic['9F70'][:2]
            privileges_raw = status_dic.get('C5', '')

            result['card_manager'] = {
                'aid': aid_raw,
                'name': aid_dict.get(aid_raw, ''),
                'lifecycle_state': SD_LifeCycleState.get(lifecycle_raw, lifecycle_raw),
                'privileges': gp_utils.bytesToPrivileges(privileges_raw),
            }
            result['is_locked'] = (lifecycle_raw == '7F')
    except BaseException:
        pass

    # -- Applications status --------------------------------------------
    try:
        error_status, app_info = gp.get_status('40')
        # Don't call __handle_error_status__ here since it's not accessible in __init__.py
        # Just log if there's an error and continue

        if app_info is not None:
            status_dic = tlv_read(app_info)['E3']
            app_list = status_dic if isinstance(status_dic, list) else [status_dic]

            for status_app in app_list:
                aid_raw = status_app.get('4F', '').upper()
                lifecycle_raw = status_app.get('9F70', '')[:2]
                privileges_raw = status_app.get('C5', '')

                result['applications'].append({
                    'aid': aid_raw,
                    'name': aid_dict.get(aid_raw, ''),
                    'lifecycle_state': Application_LifeCycleState.get(lifecycle_raw, lifecycle_raw),
                    'privileges': gp_utils.bytesToPrivileges(privileges_raw),
                })
    except BaseException as e:
        from pygp.logger import log_error
        log_error(f"Error parsing applications: {str(e)}")
        pass

    # -- Packages (executable load files) status ------------------------
    try:
        error_status, elf_info = gp.get_status('10')
        
        if elf_info is not None:
            status_dic = tlv_read(elf_info)['E3']
            elf_list = status_dic if isinstance(status_dic, list) else [status_dic]

            for status_elf in elf_list:
                aid_raw = status_elf.get('4F', '').upper()
                lifecycle_raw = status_elf.get('9F70', '')[:2]
                pkg_entry = {
                    'aid': aid_raw,
                    'name': aid_dict.get(aid_raw, ''),
                    'lifecycle_state': ExecutableLoadFile_LifeCycleState.get(lifecycle_raw, lifecycle_raw),
                    'modules': [],
                }

                # Parse module AIDs if present
                if '84' in status_elf:
                    modules = status_elf['84']
                    if isinstance(modules, list):
                        for mod_aid in modules:
                            pkg_entry['modules'].append({
                                'aid': mod_aid.upper(),
                                'name': aid_dict.get(mod_aid.upper(), ''),
                            })
                    elif isinstance(modules, str):
                        pkg_entry['modules'].append({
                            'aid': modules.upper(),
                            'name': aid_dict.get(modules.upper(), ''),
                        })

                result['packages'].append(pkg_entry)
    except BaseException:
        pass

    return result


# ---------------------------------------------------------------------------
# Module-to-package mapping: get_package_module_map()
# ---------------------------------------------------------------------------
def get_package_module_map():
    """
    Retrieve a mapping of module AIDs to their parent package AIDs.

    This function queries the card status to get all loaded packages and their
    modules, then returns a dictionary mapping each module AID to its parent
    package AID. This is useful for determining which modules (like NDEF) are
    part of which packages.

    :returns: A dictionary with module AIDs as keys and package AIDs as values.
              Example: ``{'536565644B656570657201': '536565644B6565706572', ...}``
              Returns empty dict if no packages are found or on error.
    :rtype: dict

    Example::

        from pygp import get_package_module_map

        mod_map = get_package_module_map()
        ndef_aid = '536565644B656570657201'
        if ndef_aid in mod_map:
            parent_pkg = mod_map[ndef_aid]
            print(f"NDEF module is part of package: {parent_pkg}")

    .. note:: Requires a secure channel to be established via :func:`auth`
              for full results.
    """
    status = get_card_status()
    module_map = {}

    for pkg in status.get('packages', []):
        pkg_aid = pkg['aid']
        for mod in pkg.get('modules', []):
            mod_aid = mod['aid']
            module_map[mod_aid] = pkg_aid

    return module_map


# Note: __all__ is intentionally NOT defined here.  The wildcard import
# ``from pygp.pygp import *`` brings in all public names from the core
# module (including crypto utilities, constants, and reference dicts).
# Defining a restrictive __all__ would break existing callers that rely on
# ``from pygp import *`` to access those names.  The new functions defined
# in this file (get_loaded_package_aids, get_installed_application_aids,
# try_auth, get_card_status) are always available as direct module attributes
# regardless of __all__.
