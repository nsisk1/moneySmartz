from typing import Optional
import pygame
import time
import logging
from moneySmarts.ui import Screen
from moneySmarts.image_manager import image_manager
from moneySmarts.constants import FONT_MEDIUM, BLACK, WHITE


class LoadingScreen(Screen):
    """Simple loading screen displayed during long-running operations.

    Usage:
      screen = LoadingScreen(game, message="Loading...")
      gui_manager.set_screen(screen)
      # perform work in background or main thread, call screen.set_progress(pct)
      screen.set_progress(0.5)

    The screen will display the game's LOADING_SCREEN image (if present via
    image_manager), otherwise it falls back to a plain background with message.
    """

    def __init__(self, game, message: str = "Loading..."):
        super(LoadingScreen, self).__init__(game)
        self.message = message
        self._bg = None
        try:
            self._bg = image_manager.load_image('LOADING_SCREEN')
        except Exception as e:
            logging.debug("LoadingScreen: failed to load LOADING_SCREEN image: {}".format(e))
            self._bg = None
        self.progress = None  # None = indeterminate spinner
        self._spinner_angle = 0
        self._last_tick = time.time()

    def set_progress(self, fraction: Optional[float]):
        """Set progress as a float between 0.0 and 1.0, or None for indeterminate."""
        if fraction is None:
            self.progress = None
        else:
            try:
                self.progress = max(0.0, min(1.0, float(fraction)))
            except Exception:
                self.progress = None

    def update(self):
        # rotate spinner when indeterminate
        now = time.time()
        dt = now - self._last_tick
        self._last_tick = now
        self._spinner_angle = (self._spinner_angle + dt * 360 * 0.5) % 360

    def draw(self, surface: pygame.Surface):
        sw, sh = surface.get_size()
        # draw background image scaled if available
        if self._bg:
            try:
                if self._bg.get_width() != sw or self._bg.get_height() != sh:
                    bg = pygame.transform.smoothscale(self._bg, (sw, sh))
                else:
                    bg = self._bg
                surface.blit(bg, (0, 0))
            except Exception:
                surface.fill(WHITE)
        else:
            surface.fill(WHITE)

        # draw centered message box
        font = pygame.font.SysFont('Arial', FONT_MEDIUM)
        msg_surf = font.render(self.message, True, BLACK)
        msg_rect = msg_surf.get_rect(center=(sw // 2, sh // 2 - 20))
        surface.blit(msg_surf, msg_rect)

        # draw progress bar or spinner
        if self.progress is None:
            # draw spinner (simple rotating line)
            cx, cy = sw // 2, sh // 2 + 40
            radius = 20
            end_x = int(cx + radius * pygame.math.Vector2(1, 0).rotate(self._spinner_angle).x)
            end_y = int(cy + radius * pygame.math.Vector2(1, 0).rotate(self._spinner_angle).y)
            pygame.draw.circle(surface, BLACK, (cx, cy), radius, 2)
            pygame.draw.line(surface, BLACK, (cx, cy), (end_x, end_y), 3)
        else:
            bar_w, bar_h = min(400, sw - 160), 20
            bx = (sw - bar_w) // 2
            by = sh // 2 + 30
            pygame.draw.rect(surface, (200, 200, 200), (bx, by, bar_w, bar_h), border_radius=6)
            pygame.draw.rect(surface, (100, 180, 100), (bx + 2, by + 2, int((bar_w - 4) * self.progress), bar_h - 4), border_radius=6)

    def handle_events(self, events):
        # swallow input while loading
        return
