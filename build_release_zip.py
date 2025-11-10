"""Create a release zip for distribution (excludes venv, tests, build artifacts).
Run: python build_release_zip.py [--out release/moneySmarts-release.zip]
"""
import os
import zipfile
import argparse

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(ROOT, 'release', 'moneySmarts-release.zip')
EXCLUDE_DIRS = {'.git', 'build', 'dist', '__pycache__', '.venv', 'venv', 'release', 'tests', '.idea', 'node_modules'}
EXCLUDE_EXT = {'.pyc', '.pyo', '.log', '.tmp', '.swp'}


def should_skip_path(rel_path_parts):
    # Skip if any path segment matches an excluded directory name
    for part in rel_path_parts:
        if part in EXCLUDE_DIRS:
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description='Create a release zip for MoneySmarts')
    parser.add_argument('--out', '-o', default=DEFAULT_OUT, help='Output zip path')
    args = parser.parse_args()

    out_zip = os.path.abspath(args.out)
    out_dir = os.path.dirname(out_zip)
    os.makedirs(out_dir, exist_ok=True)

    # If output exists, remove it so we don't accidentally include it
    if os.path.exists(out_zip):
        try:
            os.remove(out_zip)
        except Exception:
            pass

    files_to_add = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        # normalize and compute rel path
        rel_dir = os.path.relpath(dirpath, ROOT)
        if rel_dir == '.':
            rel_dir = ''
            rel_parts = []
        else:
            rel_parts = rel_dir.replace('\\', '/').split('/')
        # Skip excluded directories entirely
        if should_skip_path(rel_parts):
            # prevent walking into excluded subdirs
            dirnames[:] = []
            continue
        for f in filenames:
            # compute full path and rel path
            full = os.path.join(dirpath, f)
            # Skip the output zip itself in case it's inside the repo
            if os.path.abspath(full) == out_zip:
                continue
            # Skip by extension
            _, ext = os.path.splitext(f)
            if ext.lower() in EXCLUDE_EXT:
                continue
            # Skip typical lock files, thumbs.db, etc.
            if f.lower() in ('thumbs.db', '.ds_store'):
                continue
            arcname = os.path.join(rel_dir, f) if rel_dir else f
            files_to_add.append((full, arcname))

    # Write zip with deterministic ordering
    files_to_add.sort(key=lambda x: x[1])
    count = 0
    with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as z:
        for full, arcname in files_to_add:
            try:
                z.write(full, arcname)
                count += 1
            except Exception:
                # if a file can't be added, print a message and continue
                print(f"Warning: failed to add {full}")
    print(f"Wrote {out_zip} with {count} files")


if __name__ == '__main__':
    main()
