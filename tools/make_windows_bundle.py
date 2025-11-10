"""Create a Windows runtime bundle directory and zip it (cross-platform, robust).
- Copies dist/moneySmarts.exe
- Copies assets/* excluding dev folders
- Copies moneySmarts/config_default.json and README.md
- Produces release/moneySmarts-windows.zip
"""
import os
import shutil
import zipfile

ROOT = os.path.dirname(os.path.dirname(__file__))
DIST = os.path.join(ROOT, 'dist')
RELEASE_DIR = os.path.join(ROOT, 'release')
TMP = os.path.join(os.environ.get('TEMP', '/tmp'), 'moneySmarts_bundle')
EXCLUDE_DIRS = {'.git', 'node_modules', '.idea', 'venv', '.venv', 'tests', 'build', 'dist', 'release'}

if os.path.exists(TMP):
    shutil.rmtree(TMP)
os.makedirs(TMP, exist_ok=True)

# Copy exe
exe_src = os.path.join(DIST, 'moneySmarts.exe')
if not os.path.exists(exe_src):
    print('ERROR: built exe not found at', exe_src)
    raise SystemExit(1)
shutil.copy2(exe_src, os.path.join(TMP, 'moneySmarts.exe'))
print('Copied exe')

# Copy assets excluding EXCLUDE_DIRS
assets_src = os.path.join(ROOT, 'assets')
ESSENTIAL_SUBDIRS = ['fonts', 'images', 'ui', 'sfx', 'audio']
if os.path.isdir(assets_src):
    for sub in ESSENTIAL_SUBDIRS:
        src = os.path.join(assets_src, sub)
        if os.path.exists(src):
            dst = os.path.join(TMP, 'assets', sub)
            try:
                shutil.copytree(src, dst)
                print('Copied assets/', sub)
            except Exception as e:
                print('Warning copying', sub, e)

# Copy config and README
os.makedirs(os.path.join(TMP, 'moneySmarts'), exist_ok=True)
if os.path.exists(os.path.join(ROOT, 'moneySmarts', 'config_default.json')):
    shutil.copy2(os.path.join(ROOT, 'moneySmarts', 'config_default.json'), os.path.join(TMP, 'moneySmarts', 'config_default.json'))
if os.path.exists(os.path.join(ROOT, 'README.md')):
    shutil.copy2(os.path.join(ROOT, 'README.md'), os.path.join(TMP, 'README.md'))

# Create zip
os.makedirs(RELEASE_DIR, exist_ok=True)
zip_path = os.path.join(RELEASE_DIR, 'moneySmarts-windows.zip')
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
    for dirpath, dirnames, filenames in os.walk(TMP):
        for f in filenames:
            full = os.path.join(dirpath, f)
            arc = os.path.relpath(full, TMP)
            z.write(full, arc)
print('Wrote', zip_path)

# cleanup tmp
shutil.rmtree(TMP)
print('Done')
