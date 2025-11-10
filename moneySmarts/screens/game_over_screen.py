import pygame
from moneySmarts.constants import *
from moneySmarts.ui import Screen, Button
from moneySmarts.screens.screen_utils import load_ui_background, draw_background

class GameOverScreen(Screen):
    def __init__(self, game, reason=None):
        super().__init__(game)
        self.reason = reason or "Game Over! You can no longer continue."
        self.create_buttons()
        self._background_original = load_ui_background('GAME_OVER_BG')

    def create_buttons(self):
        self.buttons = []
        restart_btn = Button(
            SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 40, 100, 50, "Restart", action=self.restart_game
        )
        quit_btn = Button(
            SCREEN_WIDTH // 2 + 10, SCREEN_HEIGHT // 2 + 40, 100, 50, "Quit", action=self.quit_game
        )
        self.buttons.extend([restart_btn, quit_btn])

    def restart_game(self):
        self.game.restart()

    @staticmethod
    def quit_game():
        pygame.quit()
        exit()

    def draw(self, surface):
        draw_background(surface, self._background_original, default_color=(30, 30, 30))
        font = pygame.font.Font(None, 48)
        text = font.render(self.reason, True, (255, 0, 0))
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        surface.blit(text, rect)
        for btn in self.buttons:
            btn.draw(surface)

    def handle_events(self, events):
        """Handle list of pygame events for GameOverScreen."""
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mouse_click = True
            if ev.type == pygame.KEYDOWN:
                if ev.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]:
                    # treat escape as quit
                    self.quit_game()
                    return
        for btn in self.buttons:
            action = btn.update(mouse_pos, mouse_click)
            if action:
                action()
                return
