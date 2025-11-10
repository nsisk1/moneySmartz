"""Create a minimal release zip quickly by adding only essential runtime files.
Includes:
 - dist/moneySmarts.exe
 - moneySmarts/config_default.json
 - README.md
 - assets/fonts/**/*
 - assets/sfx/**/*
 - assets/audio/**/*
 - assets/images/ui/modern/game_background.png
 - assets/images/ui/classic/game_background.png
Produces: release/moneySmarts-windows-minimal.zip
"""
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(__file__))
DIST = os.path.join(ROOT, 'dist')
RELEASE_DIR = os.path.join(ROOT, 'release')
ZIP_PATH = os.path.join(RELEASE_DIR, 'moneySmarts-windows-minimal.zip')

paths_to_include = []
# exe
exe = os.path.join(DIST, 'moneySmarts.exe')
if os.path.exists(exe):
    paths_to_include.append((exe, 'moneySmarts.exe'))
# config and readme
cfg = os.path.join(ROOT, 'moneySmarts', 'config_default.json')
if os.path.exists(cfg):
    paths_to_include.append((cfg, os.path.join('moneySmarts','config_default.json')))
readme = os.path.join(ROOT, 'README.md')
if os.path.exists(readme):
    paths_to_include.append((readme, 'README.md'))

# helper to collect files under a dir
def collect(src_dir, arc_root):
    for dirpath, dirnames, filenames in os.walk(src_dir):
        for f in filenames:
            full = os.path.join(dirpath, f)
            arc = os.path.join(arc_root, os.path.relpath(full, src_dir))
            paths_to_include.append((full, arc))

# fonts, sfx, audio
for sub in ('fonts','sfx','audio'):
    p = os.path.join(ROOT, 'assets', sub)
    if os.path.isdir(p):
        collect(p, os.path.join('assets', sub))

# some UI images and backgrounds
ui_mod = os.path.join(ROOT, 'assets', 'images', 'ui', 'modern', 'game_background.png')
ui_class = os.path.join(ROOT, 'assets', 'images', 'ui', 'classic', 'game_background.png')
if os.path.exists(ui_mod):
    paths_to_include.append((ui_mod, os.path.join('assets','images','ui','modern','game_background.png')))
if os.path.exists(ui_class):
    paths_to_include.append((ui_class, os.path.join('assets','images','ui','classic','game_background.png')))

# Ensure release dir exists
os.makedirs(RELEASE_DIR, exist_ok=True)

with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as z:
    for full, arc in paths_to_include:
        try:
            z.write(full, arc)
        except Exception as e:
            print('Warning: failed to add', full, '->', e)
print('Wrote', ZIP_PATH)
print('Files included:', len(paths_to_include))

