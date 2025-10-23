"""Image management module providing caching, transformation utilities,
animation helpers, building image lookup, and diagnostics.

Key features:
- load_image(path_or_key, size=None): cached, auto-reload if mtime changes
- get_building_image(building_name, image_type, size): uses world_assets discovery
- slice_sheet / load_animation / get_animation_frame for sprite sheets
- Transform helpers: scaled, tinted, rotated, outline
- Placeholder generator for missing assets
- Prewarm cache, unload, verify_assets
- Atlas builder stub (future extension)

This is intentionally lightweight; expensive operations occur only once.
"""
from __future__ import annotations
import os
import pygame
import hashlib
import logging
from typing import Dict, Tuple, List, Optional

from moneySmarts.images import IMAGES, get_image_path
from moneySmarts.world_assets import discover_buildings

Surface = pygame.Surface


def _key(path: str, size: Optional[Tuple[int,int]]):
    return f"{path}|{size[0]}x{size[1]}" if size else path


class ImageManager:
    def __init__(self):
        self._cache: Dict[str, Surface] = {}
        self._mtimes: Dict[str, float] = {}
        self._usage: Dict[str, int] = {}
        self._anim_frames: Dict[str, List[Surface]] = {}
        self._animations: Dict[str, Dict[str, any]] = {}  # meta: frame_time, frames, loop
        self._sheet_cache: Dict[str, List[Surface]] = {}
        self._display_ready = False
        self._atlases: Dict[str, Tuple[Surface, Dict[str, pygame.Rect]]] = {}
        self._preload_queue: List[Tuple[str, Optional[Tuple[int,int]]]] = []
        self._preload_thread = None
        self._preload_running = False
        self._preload_progress = 0
        self._preload_total = 0

    # ---------------- Async preload ----------------
    def queue_preload(self, items: List[Tuple[str, Optional[Tuple[int,int]]]]):
        self._preload_queue.extend(items)
        self._preload_total = len(self._preload_queue)

    def _preload_worker(self):
        import time
        while self._preload_queue and self._preload_running:
            path, size = self._preload_queue.pop(0)
            self.load_image(path, size=size)
            self._preload_progress += 1
            time.sleep(0)  # yield
        self._preload_running = False

    def start_preload(self):
        if self._preload_running or not self._preload_queue:
            return
        import threading
        self._preload_running = True
        self._preload_thread = threading.Thread(target=self._preload_worker, daemon=True)
        self._preload_thread.start()

    def preload_status(self) -> Tuple[int,int]:
        return self._preload_progress, self._preload_total

    # ---------------- Core loading ----------------
    def _ensure_display(self):
        if not self._display_ready:
            try:
                if not pygame.get_init():
                    pygame.init()
                if not pygame.display.get_init():
                    pygame.display.set_mode((1,1), pygame.HIDDEN)
                self._display_ready = True
            except Exception:
                pass

    def load_image(self, path_or_key: str, size: Optional[Tuple[int,int]] = None, smooth: bool = True, colorkey=None) -> Optional[Surface]:
        """Load (or fetch cached) image. Accepts symbolic key in IMAGES or file path.
        Auto-reloads if file mtime changed. Returns None if not found.
        """
        self._ensure_display()
        # Absolute path short-circuit
        if os.path.isabs(path_or_key) and os.path.exists(path_or_key):
            path = path_or_key
        else:
            # Resolve symbolic key or relative path via images helper
            if path_or_key in IMAGES:
                path = get_image_path(path_or_key)
            else:
                path = get_image_path(path_or_key)
        if not os.path.exists(path):
            return None
        mtime = os.path.getmtime(path)
        cache_key = _key(path, size)
        if cache_key in self._cache and self._mtimes.get(cache_key) == mtime:
            self._usage[cache_key] = self._usage.get(cache_key,0)+1
            return self._cache[cache_key]
        # (Re)load
        try:
            img = pygame.image.load(path)
            if size and (img.get_width(), img.get_height()) != size:
                if smooth:
                    img = pygame.transform.smoothscale(img, size)
                else:
                    img = pygame.transform.scale(img, size)
            if img.get_alpha():
                img = img.convert_alpha()
            else:
                img = img.convert()
            if colorkey is not None:
                img.set_colorkey(colorkey)
            self._cache[cache_key] = img
            self._mtimes[cache_key] = mtime
            self._usage[cache_key] = 1
            return img
        except Exception as e:
            logging.debug(f"Image load failed {path}: {e}")
            return None

    # ---------------- Building helpers ----------------
    def get_building_image(self, building_name: str, image_type: str = 'exterior', size: Optional[Tuple[int,int]] = None) -> Optional[Surface]:
        """Fuzzy match building by name and load requested image type.
        image_type: 'exterior' | 'interior'
        """
        norm = building_name.lower().replace(' ','')
        candidates = discover_buildings()
        best = None
        for b in candidates:
            keyn = b.key.lower()
            if keyn in norm or norm in keyn or building_name.lower() in b.display_name.lower():
                best = b
                break
        if not best:
            # fallback: first with matching type
            for b in candidates:
                if image_type == 'exterior' and b.exterior_path:
                    best = b; break
                if image_type == 'interior' and b.interior_path:
                    best = b; break
        if not best:
            return None
        target = best.exterior_path if image_type == 'exterior' else best.interior_path
        if not target:
            return None
        rel = os.path.relpath(target, os.path.commonpath([target, os.getcwd()])) if os.path.exists(target) else target
        return self.load_image(rel, size=size, smooth=True)

    # ---------------- Sprite sheets / animations ----------------
    def slice_sheet(self, path_or_key: str, frame_w: int, frame_h: int, colorkey=None) -> List[Surface]:
        cache_id = f"sheet:{path_or_key}:{frame_w}x{frame_h}"
        if cache_id in self._sheet_cache:
            return self._sheet_cache[cache_id]
        sheet = self.load_image(path_or_key)
        if not sheet:
            return []
        frames = []
        for y in range(0, sheet.get_height(), frame_h):
            for x in range(0, sheet.get_width(), frame_w):
                sub = sheet.subsurface(pygame.Rect(x,y,frame_w,frame_h)).copy()
                if colorkey is not None:
                    sub.set_colorkey(colorkey)
                frames.append(sub)
        self._sheet_cache[cache_id] = frames
        return frames

    def load_animation(self, name: str, path_or_key: str, frame_w: int, frame_h: int, frame_time: float = 0.1, loop=True):
        frames = self.slice_sheet(path_or_key, frame_w, frame_h)
        if frames:
            self._animations[name] = { 'frames': frames, 'frame_time': frame_time, 'loop': loop }

    def get_animation_frame(self, name: str, elapsed: float) -> Optional[Surface]:
        anim = self._animations.get(name)
        if not anim:
            return None
        frames = anim['frames']
        if not frames:
            return None
        idx = int(elapsed / anim['frame_time'])
        if anim['loop']:
            idx %= len(frames)
        else:
            idx = min(idx, len(frames)-1)
        return frames[idx]

    # ---------------- Transform utilities ----------------
    def scaled(self, surf: Surface, size: Tuple[int,int], smooth=True) -> Surface:
        return pygame.transform.smoothscale(surf, size) if smooth else pygame.transform.scale(surf, size)

    def tinted(self, surf: Surface, color) -> Surface:
        tinted = surf.copy()
        tint = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        tint.fill(color)
        tinted.blit(tint, (0,0), special_flags=pygame.BLEND_RGBA_MULT)
        return tinted

    def rotated(self, surf: Surface, angle: float) -> Surface:
        return pygame.transform.rotate(surf, angle)

    def outline(self, surf: Surface, color, thickness=2) -> Surface:
        w,h = surf.get_size()
        mask = pygame.mask.from_surface(surf)
        outline_surf = pygame.Surface((w+thickness*2, h+thickness*2), pygame.SRCALPHA)
        for dx in range(-thickness, thickness+1):
            for dy in range(-thickness, thickness+1):
                if dx*dx+dy*dy > thickness*thickness: continue
                outline_surf.blit(mask.to_surface(setcolor=color, unsetcolor=(0,0,0,0)), (dx+thickness, dy+thickness))
        outline_surf.blit(surf, (thickness, thickness))
        return outline_surf

    # ---------------- Placeholders / diagnostics ----------------
    def placeholder(self, size: Tuple[int,int], text: str = "Missing") -> Surface:
        key = f"placeholder:{size}:{text}"
        if key in self._cache:
            return self._cache[key]
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill((50,50,60))
        pygame.draw.rect(surf, (180,60,60), surf.get_rect(), 2)
        font = pygame.font.SysFont('Arial', max(12, min(size[1]//4, 32)))
        label = font.render(text, True, (255,255,255))
        rect = label.get_rect(center=(size[0]//2, size[1]//2))
        surf.blit(label, rect)
        self._cache[key] = surf
        return surf

    def surface_info(self) -> List[Tuple[str, Tuple[int,int]]]:
        out = []
        for k,v in self._cache.items():
            out.append((k, v.get_size()))
        return out

    def prewarm(self, keys: List[str]):
        for k in keys:
            self.load_image(k)

    def unload(self, key_fragment: str):
        to_del = [k for k in self._cache if key_fragment in k]
        for k in to_del:
            self._cache.pop(k, None)
            self._mtimes.pop(k, None)
            self._usage.pop(k, None)

    def unload_unused(self, min_hits: int = 1):
        to_del = [k for k,u in self._usage.items() if u <= min_hits]
        for k in to_del:
            self._cache.pop(k, None)
            self._mtimes.pop(k, None)
            self._usage.pop(k, None)

    def verify_assets(self, manifest: List[str]) -> Dict[str, List[str]]:
        missing = []
        present = []
        for k in manifest:
            p = get_image_path(k if k in IMAGES else k)
            if os.path.exists(p):
                present.append(k)
            else:
                missing.append(k)
        return {'present': present, 'missing': missing}

    # ---------------- Atlas packing ----------------
    def build_atlas(self, name: str, paths: List[str], gap: int = 2, max_size: int = 2048, scale: Optional[Tuple[int,int]] = None) -> Optional[Tuple[Surface, Dict[str, pygame.Rect]]]:
        if name in self._atlases:
            return self._atlases[name]
        # Load images first
        images = []
        for p in paths:
            img = self.load_image(p, size=scale)
            if img:
                images.append((p, img))
        if not images:
            return None
        # Simple shelf packing (row by row)
        x = y = gap
        row_h = 0
        atlas_w = max_size
        atlas_h = gap
        placements = []
        for p, img in images:
            w, h = img.get_size()
            if x + w + gap > atlas_w:
                # new row
                y += row_h + gap
                x = gap
                row_h = 0
            placements.append((p, pygame.Rect(x,y,w,h)))
            x += w + gap
            row_h = max(row_h, h)
            atlas_h = max(atlas_h, y + row_h + gap)
            if atlas_h > max_size:
                logging.debug("Atlas overflow; truncating remaining images")
                break
        atlas = pygame.Surface((atlas_w, atlas_h), pygame.SRCALPHA)
        rect_map: Dict[str, pygame.Rect] = {}
        for p, rect in placements:
            img = self.load_image(p)
            if img:
                atlas.blit(img, rect.topleft)
                rect_map[p] = rect
        self._atlases[name] = (atlas, rect_map)
        return self._atlases[name]

    def get_from_atlas(self, atlas_name: str, path: str) -> Optional[Surface]:
        data = self._atlases.get(atlas_name)
        if not data:
            return None
        atlas, rects = data
        rect = rects.get(path)
        if not rect:
            return None
        return atlas.subsurface(rect)

# --- Image cache for loaded/scaled surfaces ---
_image_surface_cache = {}

def load_image_cached(path_or_key: str, size: Optional[Tuple[int,int]] = None, smooth: bool = True, colorkey=None) -> Optional[Surface]:
    """Load (or fetch cached) image. Accepts symbolic key in IMAGES or file path.
    Auto-reloads if file mtime changed. Returns None if not found.
    """
    cache_key = f"{path_or_key}|{size[0]}x{size[1]}" if size else path_or_key
    if cache_key in _image_surface_cache:
        return _image_surface_cache[cache_key]
    img = image_manager.load_image(path_or_key, size=size, smooth=smooth, colorkey=colorkey)
    if img:
        _image_surface_cache[cache_key] = img
    return img

# Global singleton
image_manager = ImageManager()

__all__ = ["ImageManager","image_manager"]
