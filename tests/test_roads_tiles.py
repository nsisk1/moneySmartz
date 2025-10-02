import pytest
from moneySmarts import roads

def test_asphalt_tiles_variants():
    # Discover all asphalt singles
    asphalt_paths = roads.find_asphalt_singles()
    assert asphalt_paths, "No asphalt singles found."
    # Build variant index
    tileset_paths, variant_to_index = roads.build_variant_index(asphalt_paths)
    print("Tileset paths:", tileset_paths)
    print("Variant to index:", variant_to_index)
    # Check that at least some canonical variants are present
    found_variants = set(variant_to_index.keys())
    canonical = set(roads.VARIANT_ORDER)
    print("Found variants:", found_variants)
    print("Canonical variants:", canonical)
    assert found_variants & canonical, "No canonical variants found in asphalt singles."
    # Optionally, print mapping for manual inspection
    for v in roads.VARIANT_ORDER:
        idx = variant_to_index.get(v)
        if idx is not None:
            print(f"{v}: {tileset_paths[idx]}")

def test_generate_road_grid():
    # Use a small grid for visual inspection
    tmap, tileset_paths, variant_to_index = roads.build_asphalt_road_tilemap(5, 5)
    grid = tmap.grid
    print("Generated road grid:")
    for row in grid:
        print(row)
    # Check that grid indices are valid
    for row in grid:
        for idx in row:
            if idx != -1:
                assert 0 <= idx < len(tileset_paths)

