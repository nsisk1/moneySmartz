"""Lightweight tile map support (manual CSV + tileset slicing).
Not yet integrated; can be wired into OverworldScreen later.
"""
from __future__ import annotations
import os
import pygame
from typing import List
from moneySmarts.images import get_image_path

DEFAULT_TILE_SIZE = 48


def _load_csv(rel_path: str) -> List[List[int]]:
    path = get_image_path(rel_path)  # reuse path logic even if not images dir
    rows: List[List[int]] = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                rows.append([int(tok) for tok in line.split(',')])
    except FileNotFoundError:
        # Empty map fallback
        return [[-1 for _ in range(10)] for _ in range(10)]
    return rows


class TileMap:
    def __init__(self, map_csv: str, tileset_path: str, tile_size: int = DEFAULT_TILE_SIZE):
        self.tile_size = tile_size
        self.grid: List[List[int]] = _load_csv(map_csv)
        self.tiles = self._load_tileset(tileset_path, tile_size)
        self.width = len(self.grid[0]) if self.grid else 0
        self.height = len(self.grid)

    @staticmethod
    def _load_tileset(rel_path: str, tile: int):
        path = get_image_path(rel_path)
        try:
            atlas = pygame.image.load(path).convert_alpha()
        except Exception:
            surf = pygame.Surface((tile, tile), pygame.SRCALPHA)
            surf.fill((200, 0, 200, 255))
            return [surf]
        tiles = []
        h = atlas.get_height(); w = atlas.get_width()
        for y in range(0, h, tile):
            for x in range(0, w, tile):
                rect = pygame.Rect(x, y, tile, tile)
                tiles.append(atlas.subsurface(rect))
        return tiles

    def draw(self, surface: pygame.Surface, camx: int, camy: int):
        ts = self.tile_size
        sw, sh = surface.get_size()
        start_tx = max(0, camx // ts)
        start_ty = max(0, camy // ts)
        end_tx = min(self.width, (camx + sw) // ts + 1)
        end_ty = min(self.height, (camy + sh) // ts + 1)
        for ty in range(start_ty, end_ty):
            row = self.grid[ty]
            for tx in range(start_tx, end_tx):
                tid = row[tx]
                if tid < 0 or tid >= len(self.tiles):
                    continue
                surface.blit(self.tiles[tid], (tx * ts - camx, ty * ts - camy))

    def is_blocked(self, px: float, py: float) -> bool:
        ts = self.tile_size
        tx = int(px // ts); ty = int(py // ts)
        if tx < 0 or ty < 0 or ty >= self.height or tx >= self.width:
            return True
        tid = self.grid[ty][tx]
        # Example rule: negative = empty, >=0 collidable only if flagged via separate structure later
        return False

__all__ = ["TileMap", "DEFAULT_TILE_SIZE"]

