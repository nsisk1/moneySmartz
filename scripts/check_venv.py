#!/usr/bin/env python3
"""Check the project's virtualenv and print versions.

Run from CMD (Windows):
  C:\> .\venv\Scripts\activate.bat
  (venv) C:\> python scripts\\check_venv.py

This script will:
- Read venv/pyvenv.cfg to report the recorded Python home/version.
- Check that venv\Scripts\python.exe exists and, if so, run it to get its reported version.
- Print guidance for setting the IDE interpreter to the venv path.
"""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV_DIR = ROOT / 'venv'
PYVENV_CFG = VENV_DIR / 'pyvenv.cfg'
VENV_PY = VENV_DIR / 'Scripts' / 'python.exe'


def read_pyvencfg(path: Path) -> dict:
    cfg = {}
    if not path.exists():
        return cfg
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            k, v = [p.strip() for p in line.split('=', 1)]
            cfg[k] = v
    return cfg


def run_python_exe(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        out = subprocess.check_output([str(path), '--version'], stderr=subprocess.STDOUT, text=True)
        return out.strip()
    except Exception as exc:
        return f'Error running {path}: {exc}'


def main() -> int:
    print(f'Project root: {ROOT}')
    print(f'Venv dir: {VENV_DIR}')

    cfg = read_pyvencfg(PYVENV_CFG)
    if not cfg:
        print('No pyvenv.cfg found in the venv directory.')
    else:
        print('pyvenv.cfg contents:')
        for k in ('home', 'version', 'executable'):
            if k in cfg:
                print(f'  {k}: {cfg[k]}')
    print()

    if VENV_PY.exists():
        print(f'Venv python executable found: {VENV_PY}')
        vout = run_python_exe(VENV_PY)
        print('venv python reports:', vout)
    else:
        print(f'Venv python executable NOT found at: {VENV_PY}')

    print('\nRecommended IDE interpreter path (use this in PyCharm/IntelliJ):')
    print(f'  {VENV_PY}')
    print('\nTo test from a Windows Command Prompt:')
    print('  C:\\> venv\\Scripts\\activate.bat')
    print('  (venv) C:\\> python -V')

    print('\nIf you want the IDE to use Python 3.12 instead, recreate the venv with an installed 3.12:')
    print('  C:\\> py -3.12 -m venv venv')
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

