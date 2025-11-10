import pygame
from moneySmarts.ui import Screen
from moneySmarts.constants import FONT_LARGE, BG_TOP, BG_BOTTOM, PRIMARY
from moneySmarts.screens.screen_utils import load_ui_background, draw_background

class LoadingScreen(Screen):
    def __init__(self, game, message: str = "Loading..."):
        super(LoadingScreen, self).__init__(game)
        self.message = message
        self.angle = 0
        try:
            self.font = pygame.font.SysFont('Arial', FONT_LARGE)
        except Exception:
            self.font = pygame.font.SysFont('Arial', FONT_LARGE)
        self._background_original = load_ui_background('LOADING_SCREEN')

    def handle_events(self, events):
        # Swallow all events while loading
        return

    def on_enter(self):
        """Called when the GUIManager sets this screen; kept for API compatibility."""
        # no-op for now; prepared to start background loading tasks if needed
        return

    def update(self):
        # simple spinner animation
        self.angle = (self.angle + 6) % 360

    def draw(self, surface):
        # Draw themed background if available, otherwise gradient
        if self._background_original:
            draw_background(surface, self._background_original, default_color=BG_TOP)
        else:
            try:
                from moneySmarts.ui import draw_vertical_gradient
                draw_vertical_gradient(surface, (0, 0, surface.get_width(), surface.get_height()), BG_TOP, BG_BOTTOM)
            except Exception:
                surface.fill(BG_TOP)

        # Draw centered message
        sw, sh = surface.get_size()
        try:
            text_surf = self.font.render(self.message, True, PRIMARY)
            rect = text_surf.get_rect(center=(sw//2, sh//2))
            surface.blit(text_surf, rect)
        except Exception:
            pass

        # Draw a simple rotating bar as spinner
        cx, cy = sw // 2, sh // 2 + 60
        length = 30
        end_x = cx + int(length * pygame.math.Vector2(1, 0).rotate(self.angle)[0])
        end_y = cy + int(length * pygame.math.Vector2(1, 0).rotate(self.angle)[1])
        try:
            pygame.draw.line(surface, PRIMARY, (cx, cy), (end_x, end_y), 4)
        except Exception:
            pass
