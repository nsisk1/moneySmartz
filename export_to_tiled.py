import os
import xml.etree.ElementTree as ET

TILE_SIZE = 48
ASSET_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), 'assets', 'images'))
EXPORT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'tiled_export'))
MAP_WIDTH = 10  # in tiles
MAP_HEIGHT = 10  # in tiles

os.makedirs(EXPORT_DIR, exist_ok=True)

def find_tileset_images(asset_root):
    images = []
    for root, dirs, files in os.walk(asset_root):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                images.append(os.path.join(root, file))
    return images


def create_tsx(image_path: str, export_dir: str) -> str:
    image_name = os.path.basename(image_path)
    tsx_name = os.path.splitext(image_name)[0] + '.tsx'
    tsx_path = os.path.join(export_dir, tsx_name)
    # Get image size
    from PIL import Image
    im = Image.open(image_path)
    width, height = im.size
    tilecount = (width // TILE_SIZE) * (height // TILE_SIZE)
    tileset = ET.Element('tileset', {
        'version': '1.10',
        'tiledversion': '1.10.2',
        'name': os.path.splitext(image_name)[0],
        'tilewidth': str(TILE_SIZE),
        'tileheight': str(TILE_SIZE),
        'tilecount': str(tilecount),
        'columns': str(width // TILE_SIZE)
    })
    image = ET.SubElement(tileset, 'image', {
        'source': os.path.relpath(image_path, export_dir).replace('\\', '/'),
        'width': str(width),
        'height': str(height)
    })
    tree = ET.ElementTree(tileset)
    tree.write(tsx_path, encoding='utf-8', xml_declaration=True)
    return tsx_name

def create_tmx(tilesets, export_dir):
    map_ = ET.Element('map', {
        'version': '1.10',
        'tiledversion': '1.10.2',
        'orientation': 'orthogonal',
        'renderorder': 'right-down',
        'width': str(MAP_WIDTH),
        'height': str(MAP_HEIGHT),
        'tilewidth': str(TILE_SIZE),
        'tileheight': str(TILE_SIZE),
        'infinite': '0',
        'nextlayerid': '2',
        'nextobjectid': '1'
    })
    firstgid = 1
    for tsx in tilesets:
        ET.SubElement(map_, 'tileset', {
            'firstgid': str(firstgid),
            'source': tsx
        })
        # For demo, assume each tileset has 100 tiles
        firstgid += 100
    layer = ET.SubElement(map_, 'layer', {
        'id': '1',
        'name': 'Tile Layer 1',
        'width': str(MAP_WIDTH),
        'height': str(MAP_HEIGHT)
    })
    data = ET.SubElement(layer, 'data', {'encoding': 'csv'})
    data.text = ','.join(['0'] * (MAP_WIDTH * MAP_HEIGHT))
    tree = ET.ElementTree(map_)
    tmx_path = os.path.join(export_dir, 'map.tmx')
    tree.write(tmx_path, encoding='utf-8', xml_declaration=True)
    return tmx_path

def main():
    try:
        from PIL import Image
    except ImportError:
        print('Please install Pillow: pip install Pillow')
        return
    images = find_tileset_images(ASSET_ROOT)
    if not images:
        print('No tileset images found in', ASSET_ROOT)
        return
    tsx_files = []
    for img in images:
        tsx = create_tsx(img, EXPORT_DIR)
        tsx_files.append(tsx)
    tmx_path = create_tmx(tsx_files, EXPORT_DIR)
    print('Exported Tiled map to', tmx_path)
    print('Tilesets exported to', EXPORT_DIR)
    print('You can open map.tmx in Tiled and see your tilesets.')

if __name__ == '__main__':
    main()
