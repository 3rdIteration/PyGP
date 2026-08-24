"""
PyGP exception hierarchy.

Every error PyGP raises derives from :class:`PyGPError`, which derives from
``Exception``.

.. note::
   Prior to this module, PyGP raised bare ``BaseException``. That is not
   catchable by ``except Exception``, so a routine card error (no card seated,
   wrong key, flaky reader) would escape ordinary application error handling
   and terminate the calling process. Callers written against the old
   behaviour keep working: ``except BaseException`` still matches, because
   ``Exception`` is a subclass of ``BaseException``.

This module deliberately imports nothing from ``pygp``. ``pygp.utils`` sits at
the root of the internal import chain, so anything it depends on must be a
leaf module or the package will not import.
"""


class PyGPError(Exception):
    """Base class for every error raised by PyGP."""


class PyGPConnectionError(PyGPError):
    """Reader or card connection failure (no reader, no card, link lost)."""


class PyGPCardError(PyGPError):
    """The card rejected a command, or returned a failure status word."""


class PyGPDataError(PyGPError):
    """Invalid input: bad key, malformed CAP file, unsupported parameter."""


__all__ = [
    "PyGPError",
    "PyGPConnectionError",
    "PyGPCardError",
    "PyGPDataError",
]
