# Quick import test for bank_screen
import importlib
import sys
import os
from pathlib import Path

# Ensure project root is on sys.path so the top-level package 'moneySmarts' can be imported
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    importlib.import_module('moneySmarts.screens.bank_screen')
    print('IMPORT OK')
except Exception as e:
    print('IMPORT FAILED')
    print(repr(e))
    sys.exit(2)
