from __future__ import annotations
import os
import re
from typing import Dict, List, Optional, Tuple

from moneySmarts.tilemap import TileMap

# Road generation using "ME_Singles_City_Terrains_48x48_Asphalt" Singles images.
# - Discovers asphalt tiles (case-insensitive) under assets/images
# - Maps filenames to road variants (straight, corners, T, cross, ends, single)
# - Builds a road grid using neighbor bitmasking and returns a TileMap via TileMap.from_grid

TILE_SIZE = 48

# Bitmask bits for neighbors (N=1, E=2, S=4, W=8)
N, E, S, W = 1, 2, 4, 8

# Canonical variant keys we try to map to discovered images
VARIANT_ORDER = [
    "straight_h", "straight_v",
    "corner_ne", "corner_se", "corner_sw", "corner_nw",
    "t_n", "t_e", "t_s", "t_w",
    "cross",
    "end_n", "end_e", "end_s", "end_w",
    "single",
]

# Mapping from neighbor bitmask -> variant key
BITMASK_TO_VARIANT: Dict[int, str] = {
    0: "single",
    N: "end_n",
    E: "end_e",
    S: "end_s",
    W: "end_w",
    N | S: "straight_v",
    E | W: "straight_h",
    N | E: "corner_ne",
    E | S: "corner_se",
    S | W: "corner_sw",
    W | N: "corner_nw",
    N | E | S: "t_w",   # open toward W (missing W neighbor)
    E | S | W: "t_n",   # open toward N (missing N neighbor)
    S | W | N: "t_e",   # open toward E (missing E neighbor)
    W | N | E: "t_s",   # open toward S (missing S neighbor)
    N | E | S | W: "cross",
}


def _project_root() -> str:
    # moneySmarts package dir -> project root
    here = os.path.dirname(__file__)
    return os.path.abspath(os.path.join(here, os.pardir))


def _images_root() -> str:
    return os.path.join(_project_root(), "assets", "images")


def _rel_to_images(abs_path: str) -> str:
    root = _images_root()
    rel = os.path.relpath(abs_path, root)
    return rel.replace("\\", "/")


def find_asphalt_singles() -> List[str]:
    """
    Find all images whose filename contains 'ME_Singles_City_Terrains_48x48_Asphalt'
    under assets/images. Returns paths relative to assets/images for compatibility
    with get_image_path().
    """
    root = _images_root()
    results: List[str] = []
    pattern = re.compile(r"me_singles_city_terrains_48x48_asphalt", re.IGNORECASE)
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if not fn.lower().endswith(".png"):
                continue
            if pattern.search(fn):
                results.append(_rel_to_images(os.path.join(dirpath, fn)))
    results.sort()
    return results


def _parse_variant_from_name(filename: str) -> Optional[str]:
    """
    Attempt to parse a variant key from a filename.
    Supports a variety of token styles: 'corner_ne', 't_n', 'straight_h', 'end_w', 'cross'.
    Returns None if unknown.
    """
    base = os.path.splitext(os.path.basename(filename))[0].lower()
    # Normalize tokens
    tokens = re.split(r"[_\-\s]+", base)
    s = "_".join(tokens)

    # Helpers
    def has(*words: str) -> bool:
        return all(w in s for w in words)

    # Cross / intersection
    if "cross" in s or "intersection" in s or "4way" in s or "4_way" in s or "four_way" in s:
        return "cross"

    # Straight
    if "straight" in s or ("line" in s and "road" in s):
        if "h" in tokens or "horizontal" in s or "east_west" in s or "ew" in s:
            return "straight_h"
        if "v" in tokens or "vertical" in s or "north_south" in s or "ns" in s:
            return "straight_v"
        # Default unknown straight -> horizontal
        return "straight_h"

    # Ends (dead-ends)
    if "end" in s or "dead" in s or "cap" in s:
        if "n" in tokens or "north" in s:
            return "end_n"
        if "e" in tokens or "east" in s:
            return "end_e"
        if "s" in tokens or "south" in s:
            return "end_s"
        if "w" in tokens or "west" in s:
            return "end_w"

    # T-junctions (tee)
    if "t" in tokens or "tee" in s or "tjunction" in s or "t_junction" in s or "3way" in s or "3_way" in s:
        if "n" in tokens or "north" in s:
            return "t_n"
        if "e" in tokens or "east" in s:
            return "t_e"
        if "s" in tokens or "south" in s:
            return "t_s"
        if "w" in tokens or "west" in s:
            return "t_w"

    # Corners
    if "corner" in s or "turn" in s or "bend" in s:
        # direction pairs
        if "ne" in s or ("n" in tokens and "e" in tokens):
            return "corner_ne"
        if "se" in s or ("s" in tokens and "e" in tokens):
            return "corner_se"
        if "sw" in s or ("s" in tokens and "w" in tokens):
            return "corner_sw"
        if "nw" in s or ("n" in tokens and "w" in tokens):
            return "corner_nw"

    # Single/isolated tile
    if "single" in s or "island" in s or "dot" in s or "solo" in s:
        return "single"

    # If none of the above matched but name contains 'asphalt', consider generic straight
    if "asphalt" in s:
        return "straight_h"

    return None


def build_variant_index(paths: List[str]) -> Tuple[List[str], Dict[str, int]]:
    """
    Given discovered image paths, build:
    - tileset_paths: ordered list of paths (relative to assets/images)
    - variant_to_index: map of variant key -> index in tileset_paths
    Only variants we can identify are included, in VARIANT_ORDER order.
    """
    variant_to_path: Dict[str, str] = {}
    for p in paths:
        v = _parse_variant_from_name(p)
        if v and v not in variant_to_path:
            variant_to_path[v] = p

    tileset_paths: List[str] = []
    variant_to_index: Dict[str, int] = {}
    for v in VARIANT_ORDER:
        if v in variant_to_path:
            variant_to_index[v] = len(tileset_paths)
            tileset_paths.append(variant_to_path[v])

    # Fallback: if nothing was recognized, at least include everything to allow manual indexing
    if not tileset_paths and paths:
        tileset_paths = list(paths)
        variant_to_index = {f"tile_{i}": i for i in range(len(paths))}

    return tileset_paths, variant_to_index


def _neighbor_mask(road_mask: List[List[int]], x: int, y: int) -> int:
    h = len(road_mask)
    w = len(road_mask[0]) if h else 0

    def is_road(cx: int, cy: int) -> bool:
        return 0 <= cx < w and 0 <= cy < h and road_mask[cy][cx] > 0

    m = 0
    if is_road(x, y - 1):
        m |= N
    if is_road(x + 1, y):
        m |= E
    if is_road(x, y + 1):
        m |= S
    if is_road(x - 1, y):
        m |= W
    return m


def _choose_variant(mask: int) -> str:
    return BITMASK_TO_VARIANT.get(mask, "single")


def _default_plus_mask(width: int, height: int) -> List[List[int]]:
    """
    Simple default: a plus-shaped road through the center.
    """
    grid = [[0 for _ in range(width)] for _ in range(height)]
    cx = width // 2
    cy = height // 2
    for x in range(width):
        grid[cy][x] = 1
    for y in range(height):
        grid[y][cx] = 1
    return grid


def generate_road_grid(
    width: int,
    height: int,
    road_mask: Optional[List[List[int]]] = None,
    variant_to_index: Optional[Dict[str, int]] = None,
) -> List[List[int]]:
    """
    Build a grid of tile indices for a road network based on a boolean/int mask (1=in-road).
    """
    if road_mask is None:
        road_mask = _default_plus_mask(width, height)

    grid: List[List[int]] = [[-1 for _ in range(width)] for _ in range(height)]
    if not variant_to_index:
        # No mapping yet: leave indices -1; caller must set after mapping
        return grid

    for y in range(height):
        for x in range(width):
            if road_mask[y][x] > 0:
                mask = _neighbor_mask(road_mask, x, y)
                variant = _choose_variant(mask)
                # Prefer the exact variant; if missing, try reasonable fallbacks
                idx = variant_to_index.get(variant)
                if idx is None:
                    # Straight fallback
                    if "straight_h" in variant_to_index:
                        idx = variant_to_index["straight_h"]
                    elif "straight_v" in variant_to_index:
                        idx = variant_to_index["straight_v"]
                    else:
                        # Any available tile
                        idx = next(iter(variant_to_index.values()))
                grid[y][x] = idx
    return grid


def build_asphalt_road_tilemap(
    width: int,
    height: int,
    road_mask: Optional[List[List[int]]] = None,
) -> Tuple[TileMap, List[str], Dict[str, int]]:
    """
    High-level helper:
    - Discovers asphalt tiles
    - Builds variant mapping
    - Generates a road grid
    - Returns (TileMap, tileset_paths, variant_to_index)
    """
    asphalt_paths = find_asphalt_singles()
    tileset_paths, variant_to_index = build_variant_index(asphalt_paths)
    grid = generate_road_grid(width, height, road_mask, variant_to_index)
    tmap = TileMap.from_grid(grid, tileset_paths, tile_size=TILE_SIZE)
    return tmap, tileset_paths, variant_to_index
