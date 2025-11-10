import sys
import os
from pathlib import Path
PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pygame
from moneySmarts.images import get_image_path, UI_IMAGES

print('PYPROJECT ROOT:', PROJECT_ROOT)
print('UI image keys sample:')
keys = ['BANK_BG', 'START_MENU_BG', 'INTRO_BG', 'LOADING_SCREEN']
for k in keys:
    path = get_image_path(k)
    print(k, '->', path, 'exists?', os.path.exists(path))

# Test vehicle purchase popup
pygame.init()
pygame.font.init()
surf = pygame.Surface((1024, 768))

from moneySmarts.screens.vehicle_purchase_screen import VehiclePurchaseScreen

class DummyGUI:
    def __init__(self):
        self.screen = surf
        self.current_screen = None
    def set_screen(self, s):
        self.current_screen = s

class DummyGame:
    def __init__(self):
        self.gui_manager = DummyGUI()
        self.player = type('P', (), {})()
        self.player.cash = 20000
        self.player.bank_account = None
        self.player.assets = []
        self.player.vehicle = None
        self.player.loans = []
        self.player.credit_score = 700

print('\nTesting VehiclePurchaseScreen modal popup flow')
try:
    game = DummyGame()
    screen = VehiclePurchaseScreen(game)
    print('Initial modal_popup:', screen.modal_popup)
    # select vehicle
    screen.select_vehicle(0)
    print('Selected vehicle:', screen.selected_vehicle)
    # buy cash
    screen.buy_cash()
    print('After buy_cash, modal_popup set?', screen.modal_popup is not None)
    # draw once
    screen.draw(surf)
    print('After draw, modal_popup._ok_rect:', getattr(screen.modal_popup, '_ok_rect', None))
    # Simulate click at center of OK rect if present
    ok = getattr(screen.modal_popup, '_ok_rect', None)
    if ok:
        mx, my = ok.center
        ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button':1, 'pos':(mx,my)})
        handled = screen.modal_popup.handle_events([ev])
        print('Popup handled click?', handled)
    else:
        print('OK rect not set; popup likely not rendered')
except Exception as e:
    print('Exception during test:', repr(e))
    raise

