Money Smartz — Packaging & Release Guide

Short summary
- This repo contains the Money Smartz game (pygame). The immediate goal is to stabilize and prepare release artifacts for PC (Windows), and provide concrete instructions and scripts to prepare Android (Play Store) and Web builds.

Quick start (developer)
1. Create and activate a Python 3.11/3.12 venv and install dependencies:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Run the game (dev):

```bash
python run_ui_test.py
# or
python demo_runner.py
```

Packaging for Windows (quick)
- We provide a helper .bat to run PyInstaller. You must have PyInstaller installed in your venv.

```bat
build_windows.bat
```

This runs:
- pip install pyinstaller (if missing)
- pyinstaller --onefile --windowed main.py
- collects the dist executable and zips into release/moneySmarts-windows-<version>.zip

Creating a distributable ZIP (cross-platform)
- Use the provided Python script `build_release_zip.py` to create a zip that bundles the game files (excluding venv, tests, and large tooling directories).

Android / Play Store (high level)
- Packaging a pygame app for Android requires additional tooling (python-for-android / buildozer or converting to Kivy). Steps:
  - Option A (recommended for full-featured Python): port to Kivy or use python-for-android + buildozer. This is non-trivial and typically takes >1 day.
  - Option B (experimental): use pygame-subset-for-android / pygame-ce port; requires building native libs and handling AndroidManifest, resources, signing.
- I can prepare a Play Store asset pack (high-res icons, screenshots, store listing) and a Buildozer spec to speed up the work, but I can't produce a signed AAB for Play Store automatically without environment and keys.

Web (high level)
- There is no official one-click export from pygame to web. Options:
  - Port the game to a Web-friendly runtime (e.g., p5.js, Phaser) — porting work required.
  - Try experimental approaches using Pyodide/wasm and a pygame-ce wasm build. This is complex and often fragile.

What I can do for you today
- Stabilize code and fix critical bugs (buttons, popups, hover). (done)
- Create a working Windows release pipeline using PyInstaller scripts. (added)
- Produce a distributable ZIP quickly. (added)
- Produce Play Store / Web instructions and asset templates so a build engineer can finish Android/Web builds.

Files added by the assistant
- README.md (this file)
- build_windows.bat (automates PyInstaller + zip)
- build_release_zip.py (packaging helper)
- playstore_instructions.md (how to approach Android build)
- web_instructions.md (how to approach web build and options)

Next steps (pick 1):
- I can run the test suite and produce a Windows ZIP (needs PyInstaller; I can attempt to install and run it here if allowed).
- I can produce Play Store graphics (icon, screenshots) and a Buildozer spec draft.
- I can add continuous-integration scripts (GitHub Actions) to automatically build Windows/Linux artifacts on push.

Tell me which next step to run now and I’ll do it.

