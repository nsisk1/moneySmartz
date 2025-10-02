import os
import json

# Configuration
ASSET_ROOT = os.path.join(os.path.dirname(__file__), 'assets', 'images')
LDTK_OUT = os.path.join(os.path.dirname(__file__), 'auto_generated.ldtk')
TILE_SIZE = 48  # Change if your tiles are a different size

# Helper to find all tileset images

from typing import List, Dict, Any


def find_tilesets(asset_root: str, tilesets=None) -> List[Dict[str, str]]:
    tileset_dir = asset_root  # Changed from os.path.join(asset_root, '..', 'tilesets')
    tileset_defs = []
    if not os.path.exists(tileset_dir):
        print("ERROR: Tileset folder not found: {}".format(tileset_dir))
        return []
    def gen_uid(start=1000):
        while True:
            yield start
            start += 1
    uid_gen = gen_uid()
    def gen_iid(prefix, num):
        return "{}_{}".format(prefix, num)
    if tilesets:
        for idx, ts in enumerate(tilesets):
            uid = next(uid_gen)
            tileset_defs.append({
                "identifier": ts["name"],
                "iid": gen_iid("tileset", uid),
                "uid": uid,
                "relPath": ts["rel_path"],
                "tileGridSize": TILE_SIZE,
                "pxWid": ts["pxWid"],
                "pxHei": ts["pxHei"],
                "spacing": 0,
                "padding": 0,
                "tags": [],
                "savedSelections": [],
                "customData": [],
                "embedAtlas": "",
                "tilesetDefUid": 0
            })
    for fileName in os.listdir(tileset_dir):
        if fileName.lower().endswith('.png'):
            rel_path = os.path.relpath(os.path.join(tileset_dir, fileName), os.path.dirname(__file__))
            # Get image dimensions
            try:
                from PIL import Image
                img = Image.open(os.path.join(tileset_dir, fileName))
                pxWid, pxHei = img.size
            except Exception:
                pxWid, pxHei = 48, 48
            tileset_defs.append({
                'rel_path': rel_path.replace('\\', '/'),
                'name': os.path.splitext(fileName)[0],
                'pxWid': pxWid,
                'pxHei': pxHei
            })
    return tileset_defs

def find_building_tilesets() -> List[Dict[str, str]]:
    building_dirs = [
        os.path.join(ASSET_ROOT, 'buildings', 'exteriors'),
        os.path.join(ASSET_ROOT, 'buildings', 'interiors')
    ]
    tileset = []
    for dir_path in building_dirs:
        if not os.path.exists(dir_path):
            print("WARNING: Directory not found: {}".format(dir_path))
            continue
        for fileName in os.listdir(dir_path):
            if fileName.lower().endswith('.png'):
                rel_path = os.path.relpath(os.path.join(dir_path, fileName), os.path.dirname(__file__))
                tileset.append({
                    'rel_path': rel_path.replace('\\', '/'),
                    'name': os.path.splitext(fileName)[0]
                })
    return tileset

# Build LDtk project JSON

def build_ldtk_project(tilesets: List[Dict[str, str]]) -> Dict[str, Any]:
    # Ensure all required fields are present and never null
    ldtk = {
        "appBuildId": 0,
        "appJsonVersion": "1.5.3",
        "jsonVersion": "1.5.3",
        "defaultGridSize": TILE_SIZE,
        "defaultLevelWidth": 10,
        "defaultLevelHeight": 10,
        "externalLevels": False,
        "worlds": [],
        "defs": {
            "tilesets": [
                {
                    "identifier": ts["name"],
                    "relPath": ts["rel_path"],
                    "tileGridSize": TILE_SIZE
                } for ts in tilesets
            ] if tilesets else [],
            "layers": [
                {
                    "type": "Tiles",
                    "identifier": "Ground",
                    "gridSize": TILE_SIZE,
                    "visible": True,
                    "optional": False
                }
            ],
            "entities": []
        },
        "levels": [
            {
                "identifier": "Level_0",
                "iid": "level_0",
                "worldX": 0,
                "worldY": 0,
                "pxWid": 10 * TILE_SIZE,
                "pxHei": 10 * TILE_SIZE,
                "layerInstances": [],
                "bgColor": "#000000"
            }
        ]
    }
    # Guarantee all arrays are at least empty arrays
    if "worlds" not in ldtk or ldtk["worlds"] is None:
        ldtk["worlds"] = []
    if "levels" not in ldtk or ldtk["levels"] is None:
        ldtk["levels"] = []
    if "defs" not in ldtk or ldtk["defs"] is None:
        ldtk["defs"] = {"tilesets": [], "layers": [], "entities": []}
    for key in ["tilesets", "layers", "entities"]:
        if key not in ldtk["defs"] or ldtk["defs"][key] is None:
            ldtk["defs"][key] = []
    return ldtk

def main():
    print("Scanning building asset folders...")
    tilesets = find_building_tilesets()
    ldtk_project = build_ldtk_project(tilesets)
    # Print the generated JSON for inspection
    print(json.dumps(ldtk_project, indent=2))
    with open(LDTK_OUT, 'w', encoding='utf-8') as f:
        json.dump(ldtk_project, f, indent=2)
    print('LDtk project generated: {}'.format(LDTK_OUT))
    print('Open this file in LDtk to start editing your world!')
    # Force overwrite ldtk_minimal_test.ldtk only when explicitly requested
    if os.environ.get('WRITE_MINIMAL_LDTK') == '1':
        ldtk_minimal = {
            "appBuildId": 0,
            "appJsonVersion": "1.5.3",
            "jsonVersion": "1.5.3",
            "defaultGridSize": TILE_SIZE,
            "defaultLevelWidth": 10,
            "defaultLevelHeight": 10,
            "externalLevels": False,
            "worlds": [],
            "defs": {
                "tilesets": [],
                "layers": [
                    {
                        "type": "Tiles",
                        "identifier": "Ground",
                        "gridSize": TILE_SIZE,
                        "visible": True,
                        "optional": False
                    }
                ],
                "entities": []
            },
            "levels": []
        }
        with open('ldtk_minimal_test.ldtk', 'w', encoding='utf-8') as f:
            json.dump(ldtk_minimal, f, indent=2)
        print('Wrote ldtk_minimal_test.ldtk')
        print('defaultGridSize: {}'.format(ldtk_minimal['defaultGridSize']))
        print('File path: {}'.format(os.path.abspath('ldtk_minimal_test.ldtk')))

if __name__ == '__main__':
    main()
