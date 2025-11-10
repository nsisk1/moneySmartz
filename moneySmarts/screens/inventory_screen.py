import pygame
from moneySmarts.ui import Screen, Button
from moneySmarts.constants import *
from moneySmarts.screens.screen_utils import load_ui_background, draw_background

class InventoryScreen(Screen):
    """Inventory screen showing player's purchased assets and a back button."""
    def __init__(self, game):
        """
        Initialize the inventory screen and create the back button.
        Args:
            game: The main game object.
        """
        super().__init__(game)
        self.back_btn = Button(40, 40, 120, 40, "Back", action=self.go_back)
        self._background_original = load_ui_background('INVENTORY_BG')

    def go_back(self):
        """
        Return to the main game screen.
        """
        from moneySmarts.screens.game_screen import GameScreen
        self.game.gui_manager.set_screen(GameScreen(self.game))

    def draw(self, surface):
        """
        Draw the inventory screen, showing all player assets and the back button.
        Args:
            surface: The pygame surface to draw on.
        """
        draw_background(surface, self._background_original, default_color=(245, 245, 255))
        font = pygame.font.SysFont('Arial', 32)
        title = font.render("Inventory", True, BLUE)
        surface.blit(title, (40, 100))
        y = 160
        font_small = pygame.font.SysFont('Arial', 24)
        if not self.game.player.assets:
            surface.blit(font_small.render("No items purchased yet.", True, BLACK), (40, y))
        else:
            for asset in self.game.player.assets:
                # Show asset name, type, value, and condition for realism
                asset_text = f"{asset.name} ({asset.asset_type}) - ${asset.current_value:.2f} - {asset.condition}"
                surface.blit(font_small.render(asset_text, True, BLACK), (40, y))
                y += 40
        self.back_btn.draw(surface)

    def handle_events(self, events):
        """
        Handle incoming pygame events (list) for the inventory screen.
        """
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mouse_click = True
            if ev.type == pygame.KEYDOWN and ev.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]:
                self.go_back()
                return

        if mouse_click and self.back_btn:
            action = self.back_btn.update(mouse_pos, True)
            if callable(action):
                action()
