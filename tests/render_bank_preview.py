import pygame
import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from moneySmarts.screens.bank_screen import BankScreen, _BANK_BACKGROUND_PATH, _find_bank_interior_path
from moneySmarts.constants import SCREEN_WIDTH, SCREEN_HEIGHT

class DummyPlayer:
    def __init__(self):
        self.cash = 1000.0
        class BA:
            def __init__(self):
                self.balance = 250.0
        self.bank_account = BA()
        self.savings_account = BA()

class DummyGame:
    def __init__(self):
        self.player = DummyPlayer()
        self.gui_manager = None

pygame.init()
pygame.font.init()
# create a windowed surface (some backends require a display)
surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Bank Preview')

game = DummyGame()
screen = BankScreen(game)
# Ensure path is found
_find_bank_interior_path()
print('Candidate path:', _BANK_BACKGROUND_PATH)

# Draw once
screen.draw(surface)
# Save to file
out_path = os.path.abspath('bank_preview.png')
pygame.image.save(surface, out_path)
print('Saved preview to', out_path)
pygame.quit()

