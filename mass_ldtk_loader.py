import os
import json

# Configuration
ASSET_ROOT = os.path.join(os.path.dirname(__file__), 'assets', 'images')
LDTK_OUT = os.path.join(os.path.dirname(__file__), 'auto_generated.ldtk')
TILE_SIZE = 48  # Change if your tiles are a different size

# Helper to find all tileset images

from typing import List, Dict, Any


def find_tilesets(asset_root: str) -> List[Dict[str, str]]:
    if not os.path.exists(asset_root):
        print("ERROR: Asset folder not found: {asset_root}")
        return []
    tileset = []
    for root, dirs, files in os.walk(asset_root):
        for fileName in files:
            if fileName.lower().endswith(('.png', '.jpg', '.jpeg')):
                rel_path = os.path.relpath(os.path.join(root, fileName), os.path.dirname(__file__))
                tileset.append({
                    'rel_path': rel_path.replace('\\', '/'),
                    'name': os.path.splitext(fileName)[0]
                })
    return tileset

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
    ldtk = {
        "appBuildId": 0.0,
        "appJsonVersion": "1.5.3",
        "jsonVersion": "1.5.3",
        "defaultGridSize": TILE_SIZE,
        "defaultLevelWidth": 10,
        "defaultLevelHeight": 10,
        "externalLevels": False,  # LDtk expects a boolean
        "worlds": [],
        "defs": {
            "tilesets": [
                {
                    "identifier": ts["name"],
                    "relPath": ts["rel_path"],
                    "tileGridSize": TILE_SIZE
                } for ts in tilesets
            ],
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
    return ldtk

def main():
    print("Scanning building asset folders...")
    tilesets = find_building_tilesets()
    if not tilesets:
        print("No building tilesets found. Please check your asset folder path and contents.")
    else:
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
            "appBuildId": 0.0,
            "appJsonVersion": "1.5.3",
            "jsonVersion": "1.5.3",
            "defaultGridSize": TILE_SIZE,
            "defaultLevelWidth": 10,
            "defaultLevelHeight": 10,
            "externalLevels": False,  # LDtk expects a boolean
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
        with open('ldtk_minimal_test.ldtk', 'w', encoding='utf-8') as f:
            json.dump(ldtk_minimal, f, indent=2)
        print('Wrote ldtk_minimal_test.ldtk')
        print('defaultGridSize: {}'.format(ldtk_minimal['defaultGridSize']))
        print('File path: {}'.format(os.path.abspath('ldtk_minimal_test.ldtk')))

if __name__ == '__main__':
    main()
