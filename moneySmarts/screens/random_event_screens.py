import pygame
from moneySmarts.constants import *
from moneySmarts.ui import Screen, Button
from moneySmarts.screens.screen_utils import load_ui_background, draw_background

class RandomEventScreen(Screen):
    """Screen displayed when a random event occurs during gameplay."""
    def __init__(self, game, event, cash_effect):
        super().__init__(game)
        self.event = event
        self.cash_effect = cash_effect
        self.font = pygame.font.SysFont('Arial', FONT_MEDIUM)
        self.title_font = pygame.font.SysFont('Arial', FONT_LARGE, bold=True)
        self._background_original = load_ui_background('RANDOM_EVENT_BG')
        # Effect already applied in Game.trigger_random_event; prepare messages only
        if cash_effect > 0:
            self.result_message = f"You received ${cash_effect}!"
            self.payment_message = None
        elif cash_effect < 0:
            self.result_message = f"Expense: ${abs(cash_effect)}"
            self.payment_message = "Funds adjusted automatically."
        else:
            self.result_message = "No financial impact this time."
            self.payment_message = None

        # Continue button
        continue_button = Button(
            SCREEN_WIDTH // 2 - 100, 
            SCREEN_HEIGHT - 100, 
            200, 60, 
            "Continue", 
            action=self.continue_game
        )
        
        self.buttons = [continue_button]
    
    def continue_game(self):
        """Return to the game screen."""
        from moneySmarts.screens.game_screen import GameScreen
        self.game.gui_manager.set_screen(GameScreen(self.game))
    
    def draw(self, surface):
        """Draw the random event screen."""
        draw_background(surface, self._background_original, default_color=WHITE)

        # Draw event header
        header_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 80)
        event_color = GREEN if self.cash_effect > 0 else RED
        pygame.draw.rect(surface, event_color, header_rect)
        
        header_text = self.title_font.render(f"LIFE EVENT: {self.event['name']}", True, WHITE)
        header_rect = header_text.get_rect(center=(SCREEN_WIDTH // 2, 40))
        surface.blit(header_text, header_rect)
        
        # Draw event description
        desc_text = self.font.render(self.event['description'], True, BLACK)
        desc_rect = desc_text.get_rect(center=(SCREEN_WIDTH // 2, 150))
        surface.blit(desc_text, desc_rect)
        
        # Draw result
        result_text = self.font.render(self.result_message, True, BLACK)
        result_rect = result_text.get_rect(center=(SCREEN_WIDTH // 2, 220))
        surface.blit(result_text, result_rect)
        
        # Draw payment message if applicable
        if self.payment_message:
            payment_text = self.font.render(self.payment_message, True, BLACK)
            payment_rect = payment_text.get_rect(center=(SCREEN_WIDTH // 2, 270))
            surface.blit(payment_text, payment_rect)
        
        # Draw buttons
        for button in self.buttons:
            button.draw(surface)
