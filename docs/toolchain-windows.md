# QMK toolchain setup (Windows) — verified working steps

QMK's CLI **requires** MSYS2 on Windows (its `MSYSTEM` environment check hard-fails in git-bash or a plain Windows shell). The steps below are the exact recipe that worked for umiko — the QMK docs miss a few things (new pkg locations, Python home dir on MSYS2, `keyboard.json` vs `info.json`, jsonschema/rpds-py wheel build failure). Follow verbatim.

## 1. Install MSYS2 to `C:/msys64`

Download from https://www.msys2.org/. Default installer, install to `C:/msys64`. For silent install: `msys2-x86_64-latest.exe install --confirm-command --accept-messages --root C:/msys64`.

## 2. Install packages via pacman (in the MSYS2 MINGW64 shell)

```
pacman -Syu --noconfirm --disable-download-timeout
yes '' | pacman -S --noconfirm --needed --disable-download-timeout \
    base-devel git \
    mingw-w64-x86_64-python-pip mingw-w64-x86_64-python-cffi \
    mingw-w64-x86_64-python-pillow mingw-w64-x86_64-rust \
    mingw-w64-ucrt-x86_64-arm-none-eabi-gcc \
    mingw-w64-ucrt-x86_64-arm-none-eabi-binutils \
    mingw-w64-ucrt-x86_64-arm-none-eabi-newlib
```

Gotchas:
- The `arm-none-eabi-*` toolchain packages are only under the **UCRT64 repo**, not MINGW64 — that's why the package prefix is `mingw-w64-ucrt-x86_64-` for those three only.
- `yes ''` is required to answer pacman's group-membership prompts (which `--noconfirm` alone doesn't handle).
- `python-pillow` and `rust` are prerequisites for the QMK pip install — omitting them causes rpds-py / pillow to try building from source and fail.

## 3. Install QMK CLI via pip (still in MSYS2 MINGW64 shell)

```
python -m pip install --user --break-system-packages 'jsonschema<4.18'
python -m pip install --user --break-system-packages qmk
```

Notes:
- `--break-system-packages` is required because MSYS2's Python is PEP 668-managed. It just means "install into user site-packages" — safe.
- Pinning `jsonschema<4.18` avoids the modern `rpds-py` Rust build (which fails on MSYS2's Python ABI). Older jsonschema uses `pyrsistent` instead.
- Ensure `USERPROFILE` is set correctly before running pip, or the install path will contain a literal `~` and Python won't find its own packages. Set: `export USERPROFILE='C:\Users\<you>'`.

## 4. Set up qmk_home + junction

QMK CLI looks for qmk_firmware at `~/qmk_firmware` on the Windows side (`C:/Users/<you>/qmk_firmware`), regardless of the `user.qmk_home` config value. The cleanest fix is a directory junction:

```
cmd /c "mklink /J C:\Users\<you>\qmk_firmware C:\Users\<you>\dev\keyboard\qmk_umiko"
```

## 5. Test compile

Requires setting a few env vars every time you run qmk in MSYS2. The `scripts/qmk_compile.sh` wrapper in this repo handles it — just run:

```
scripts/qmk_compile.sh
```

or if you prefer to do it by hand from an MSYS2 MINGW64 shell:

```
export USERPROFILE='C:\Users\<you>'
export HOME=/home/<you>
export PATH=/c/Users/<you>/.local/bin:/ucrt64/bin:$PATH
qmk compile -kb umiko -km default
```

Output UF2 lands at `qmk_umiko/umiko_default.uf2` (~74 KB).
