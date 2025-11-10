import pygame
import logging
from typing import Optional, Tuple
from moneySmarts.image_manager import image_manager


def load_ui_background(key: str) -> Optional[pygame.Surface]:
    """Load a UI background by key via the project's image manager."""
    try:
        img = image_manager.load_image(key)
        if img:
            return img
        # fall through to placeholder
    except Exception:
        logging.debug(f"Failed to load background for key {key}")
        # fall through to placeholder

    # If image is not available, create a simple placeholder Surface so screens are not blank.
    try:
        surf = pygame.Surface((800, 600))
        surf.fill((40, 40, 60))
        try:
            font = pygame.font.SysFont('Arial', 28)
            txt = font.render(f"Missing background: {key}", True, (220, 220, 220))
            surf.blit(txt, (20, 20))
        except Exception:
            pass
        return surf
    except Exception:
        return None


def draw_background(surface: pygame.Surface, original: Optional[pygame.Surface], default_color: Tuple[int,int,int] = (30,30,40)) -> None:
    """Scale and draw the provided original background onto surface, or fill default_color if missing.
    This centralizes the repeated background-scaling logic used across screens.
    """
    if original:
        try:
            sw, sh = surface.get_size()
            if original.get_width() == sw and original.get_height() == sh:
                surface.blit(original, (0, 0))
                return
            # attempt smoothscale but fall back to original
            try:
                bg = pygame.transform.smoothscale(original, (sw, sh))
            except Exception:
                bg = original
            surface.blit(bg, (0, 0))
            return
        except Exception:
            logging.exception("Error drawing background; falling back to solid fill")
    # fallback: fill with default color
    try:
        surface.fill(default_color)
    except Exception:
        pass


def load_font_safe(path: Optional[str], size: int) -> pygame.font.Font:
    """Try to load a TTF from path; fall back to system font."""
    try:
        if path:
            return pygame.font.Font(path, size)
    except Exception:
        logging.debug(f"Failed to load font from {path}; using SysFont")
    return pygame.font.SysFont('Arial', size)
