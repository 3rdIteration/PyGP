# PyGP

PyGP is a open source python **globalplatform** client library. 
Using this library, you can use all features of GlobalPlatform project use Python programming language.

It supports Python 3.8 through 3.14 and relies only on Python dependencies
(`pyscard` and `cryptography`) — no Java runtime is required.

You can find more information in the [documentation](http://pygp.readthedocs.io/en/latest/index.html).

## Command line interface

### Using the installed `pygp` command

After installing the package with `pip install .`, a `pygp` command is registered
and can be used directly. Options follow the
[GlobalPlatformPro](https://github.com/martinpaljak/GlobalPlatformPro) `gp`
conventions:

```sh
# list the applets / packages installed on the card
pygp --list

# install every applet contained in a CAP file (multiple applets supported)
pygp --install MyApplet.cap

# install an applet and pass install parameters (tag C9), e.g. Seedkeeper memory size
pygp --install Seedkeeper.cap --params 020000

# delete an applet (and its package)
pygp --delete A0000008040001 --delete-deps

# lock the card by replacing the default keys with a new key
pygp --lock 0123456789ABCDEF0123456789ABCDEF

# unlock the card (restore the default GlobalPlatform test key)
pygp --unlock

# use individual keys instead of a single master key
pygp --list --key-enc <ENC> --key-mac <MAC> --key-dek <DEK>

# inspect a CAP file offline (no card needed)
pygp --cap-info MyApplet.cap
```

Run `pygp --help` for the full list of options.

### Running from source without installation

You can also run the CLI directly from the source repository without installing
the package, using Python's `-m` flag:

```sh
# Without installation, use python -m pygp.cli instead of pygp
python -m pygp.cli --help

# All commands work the same way
python -m pygp.cli --list
python -m pygp.cli --install MyApplet.cap
python -m pygp.cli --install Seedkeeper.cap --params 020000
python -m pygp.cli --cap-info MyApplet.cap
```

This is useful for development, testing, or when you prefer not to install the package.

