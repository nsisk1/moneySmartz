import pygame
import time
from moneySmarts.screens.vehicle_purchase_screen import VehiclePurchaseScreen
from moneySmarts.ui_helpers import ModalPopup

pygame.init()
surface = pygame.display.set_mode((800, 600))
pygame.display.set_caption('Modal Popup Smoke Test')

# Fake minimal game object expected by screens
class FakeGame:
    def __init__(self):
        self.player = type('P', (), {'cash': 5000, 'bank_account': None, 'credit_card': None, 'loans': [], 'assets': [], 'vehicle': None, 'credit_score': 700})()
        self.gui_manager = self
        self.running = True
    def set_screen(self, s):
        self.screen = s
    def quit(self):
        self.running = False

g = FakeGame()
screen = VehiclePurchaseScreen(g)
# select first vehicle programmatically
screen.select_vehicle(1)  # pick Sedan
# Simulate pressing Buy Cash which creates a ModalPopup
screen.buy_cash()

# Draw once so popup layout is computed
screen.draw(surface)
pygame.display.flip()

# Ensure popup exists
if not screen.modal_popup:
    print('No popup created; test failed')
else:
    popup = screen.modal_popup
    # compute layout
    popup.layout(surface)
    # get ok rect center
    ok = popup._ok_rect
    cx, cy = ok.center
    # send a mouse click event at the OK center
    ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (cx, cy), 'button': 1})
    handled = popup.handle_events([ev])
    print('Popup handled:', handled)

pygame.quit()

