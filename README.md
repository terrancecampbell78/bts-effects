# bts-effects

Downloadable effect plug-ins for **Backing Track Studio** (Android), built from the official
[Airwindows](https://github.com/airwindows/airwindows) source by Chris Johnson.

**This is an unofficial Android build, not an Airwindows release.** All credit for the effects goes to
Airwindows; the effects are MIT-licensed (see `LICENSE-airwindows`). Support Airwindows at
https://www.patreon.com/airwindows.

## What's here

- `glue/` – our small MIT glue: the plug-in interface (`bts_plugin.h`), a minimal VST2 stand-in
  (`audioeffectx.h`, so no Steinberg SDK is needed) and `aw_plugin.cpp`, which wraps one Airwindows effect.
  Airwindows' own files are compiled unmodified.
- `tools/build.py` – fetches the official Airwindows repo (or uses `--aw-src`), checks every effect on test audio
  (`tools/probe.cpp`: it must load, report its controls and stay finite), builds the ones that pass for Android
  (arm64-v8a, armeabi-v7a) and writes `dist/catalog.json`.
- `dist/` – the published build: `catalog.json` (every effect with its controls, size and SHA-256 per file),
  `catalog.sig` (ECDSA P-256 signature) and the plug-ins in `arm64-v8a/` and `armeabi-v7a/`.

## How the app uses it

The app's Effect manager downloads `catalog.json` + `catalog.sig` and only trusts the list if the signature
matches the public key built into the app. It downloads a plug-in only when you tap it, and loads the file only if
its size and SHA-256 match the signed list (checked again before every load). The signing key never leaves the
build server and is not in this repository.

Plug-ins link `libc++_shared.so`, which the app ships (NDK 27).

## Build

    tools/build.py --key /path/to/catalog-key.pem            # clones airwindows into work/
    tools/build.py --aw-src <airwindows>/plugins/LinuxVST/src --only LeadAmp Cabs

Needs the Android NDK (r27) and Python 3. The probe is built with the NDK's own clang for the host.
