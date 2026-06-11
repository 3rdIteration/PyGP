# PyGP relies on the maintained, cross-platform ``pyscard`` package for PC/SC
# access instead of bundling a vendored SWIG wrapper. ``pyscard`` provides the
# native ``_scard`` extension built for the current platform / Python version,
# which keeps PyGP working on modern Python (3.12 - 3.14).
try:
    from smartcard.scard import *  # noqa: F401,F403
except ImportError as exc:  # pragma: no cover - environment dependent
    raise ImportError(
        "PyGP requires the 'pyscard' package for smart card communication. "
        "Install it with 'pip install pyscard'. On Linux you may also need the "
        "PC/SC development libraries (e.g. 'apt install libpcsclite-dev pcscd')."
    ) from exc
