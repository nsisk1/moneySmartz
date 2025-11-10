import sys
import pygame
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

pygame.init()
pygame.font.init()
pygame.display.set_mode((800, 600))

# Minimal game stub
class DummyGUI:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.current_screen = None
    def set_screen(self, s):
        self.current_screen = s

class DummyGame:
    def __init__(self):
        self.gui_manager = DummyGUI()
        self.player = type('P', (), {})()
        self.player.cash = 10000
        self.player.bank_account = None
        self.player.assets = []
        self.player.vehicle = None
        self.player.loans = []
        self.player.credit_score = 700

# Run the test
try:
    from moneySmarts.screens.vehicle_purchase_screen import VehiclePurchaseScreen
    game = DummyGame()
    screen = VehiclePurchaseScreen(game)
    if not screen.buttons:
        print('BUTTON TEST FAILED: no selection buttons created')
        sys.exit(2)
    btn = screen.buttons[0]
    # Simulate click inside the button
    mouse_pos = (btn.rect.centerx, btn.rect.centery)
    action = btn.update(mouse_pos, mouse_click=True)
    if not action:
        print('BUTTON TEST FAILED: button.update did not return action')
        sys.exit(2)
    # Invoke the action
    action()
    if not screen.selected_vehicle:
        print('BUTTON TEST FAILED: action did not select vehicle')
        sys.exit(2)
    print('BUTTON TEST PASSED:', screen.selected_vehicle['name'])
    sys.exit(0)
except Exception as e:
    print('BUTTON TEST FAILED:', repr(e))
    sys.exit(2)

