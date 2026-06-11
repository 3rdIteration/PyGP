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

### Auto-detection and Duplicate Applet Prevention

PyGP includes smart auto-detection for known applet types (Keycard, Seedkeeper) and automatically prevents duplicate installations:

**Auto-detected applets:**
- **Keycard**: Automatically creates correct instance AIDs (A00000080400010101, D2760000850101, A00000080400010301) without needing manual parameters
- **Seedkeeper**: Automatically detects and applies the correct configuration for proper installation

**Duplicate prevention:**
When running `--install` on an applet that's already on the card, PyGP will:
1. Skip loading the package if it's already loaded
2. Skip creating application instances that already exist
3. Complete successfully without errors

This means you can safely re-run installation commands without worrying about "Sequence error" failures:

```sh
# These commands are safe to run multiple times
pygp --install keycard_v3.2.cap
pygp --install SeedKeeper-Ndef-v0.2.cap

# Output will show:
# Package X0000000000000000 is already loaded on the card, skipping load steps.
# Applet instance X00000000000000000 is already installed, skipping...
# Installed applet X000000000000000 as instance X00000000000000000
```

### Installing Multi-Applet CAP Files (Keycard, Seedkeeper)

Both Keycard and Seedkeeper CAP files contain multiple applets, including optional NDEF (NFC Data Exchange Format) applets. PyGP automatically handles all modules, but you can control which ones are instantiated using the `--module` flag.

**Important:** Both Keycard and Seedkeeper have NDEF applets that use the same NDEF instance AID (`D2760000850101`). You can only have one NDEF applet active at a time on the card.

#### Seedkeeper with NDEF (default)

```sh
# Install both main applet and NDEF applet
pygp --install SeedKeeper-Ndef-v0.2.cap

# Creates:
# - 536565644B656570657200 (main applet)
# - D2760000850101 (NDEF applet - NFC detectable)
```

#### Seedkeeper without NDEF

```sh
# Install only the main Seedkeeper applet (no NDEF)
pygp --install SeedKeeper-Ndef-v0.2.cap --module 536565644B656570657200

# Creates:
# - 536565644B656570657200 (main applet only)
```

#### Keycard with NDEF (default)

```sh
# Install all three Keycard applets including NDEF
pygp --install keycard_v3.2.cap

# Creates:
# - A00000080400010101 (main Keycard applet)
# - D2760000850101 (NDEF applet - NFC detectable)
# - A00000080400010301 (Cash applet)
```

#### Keycard without NDEF

```sh
# Install only the main Keycard and Cash applets (no NDEF)
pygp --install keycard_v3.2.cap --module A000000804000101 --module A000000804000103

# Creates:
# - A00000080400010101 (main Keycard applet)
# - A00000080400010301 (Cash applet)
# Note: No NDEF applet
```

#### Using both Seedkeeper and Keycard (choose one for NDEF)

```sh
# Install Seedkeeper with NDEF, Keycard without NDEF
pygp --install SeedKeeper-Ndef-v0.2.cap
pygp --install keycard_v3.2.cap --module A000000804000101 --module A000000804000103

# Or install Keycard with NDEF, Seedkeeper without NDEF
pygp --install keycard_v3.2.cap
pygp --install SeedKeeper-Ndef-v0.2.cap --module 536565644B656570657200
```

