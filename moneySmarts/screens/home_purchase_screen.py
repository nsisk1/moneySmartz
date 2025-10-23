import pygame
import os
from moneySmarts.constants import *
from moneySmarts.ui import Screen, Button
from moneySmarts.ui_helpers import ModalPopup, create_selection_buttons

HOME_OPTIONS = [
    {"name": "Starter Home", "price": 3000, "desc": "A cozy starter home. Affordable and simple."},
    {"name": "Family House", "price": 7000, "desc": "A spacious house for a growing family."},
    {"name": "Luxury Villa", "price": 20000, "desc": "A luxurious villa with all amenities."},
]

class HomePurchaseScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.selected_home = None
        self.message = ""
        self.modal_popup = None  # ModalPopup instance when a popup is active
        self.create_buttons()

    def create_buttons(self):
        labels = [f"{h['name']} - ${h['price']}" for h in HOME_OPTIONS]
        # Create selectable buttons using helper
        self.buttons = create_selection_buttons(labels, 80, 150, 400, 60, 30, self.select_home)
        self.buy_btn = Button(600, 200, 180, 50, "Buy Home", action=self.buy_home)
        self.back_btn = Button(600, 350, 120, 40, "Back", action=self.go_back)

    def select_home(self, idx):
        self.selected_home = HOME_OPTIONS[idx]
        self.message = f"Selected: {self.selected_home['name']}"

    def buy_home(self):
        if not self.selected_home:
            # show modal telling user to select first
            self.modal_popup = ModalPopup("Select Home", "Select a home first.", on_ok=lambda: self._clear_message())
            return
        price = self.selected_home['price']
        cash_before = getattr(self.game.player, 'cash', 0)
        if cash_before >= price:
            self.game.player.cash -= price
            cash_after = self.game.player.cash
            self.game.player.home = self.selected_home['name']
            popup_text = (
                f"Purchase Confirmation:\n"
                f"Before: ${cash_before:.2f}\n"
                f"Purchase: -${price:.2f}\n"
                f"After: ${cash_after:.2f}\n"
                f"Congratulations! You bought the {self.selected_home['name']}!"
            )
            # show modal; on_ok clears selection and returns to shop
            self.modal_popup = ModalPopup("Purchased", popup_text, on_ok=self._post_purchase)
        else:
            # insufficient funds modal
            self.modal_popup = ModalPopup("Insufficient Funds", "Not enough cash.", on_ok=self._clear_message)

    def _post_purchase(self):
        self.selected_home = None
        self.message = ""
        # return to shop screen
        try:
            from moneySmarts.screens.shop_screen import ShopScreen
            self.game.gui_manager.set_screen(ShopScreen(self.game))
        except Exception:
            self.modal_popup = None

    def _clear_message(self):
        self.message = ""
        self.modal_popup = None

    def go_back(self):
        try:
            from moneySmarts.screens.shop_screen import ShopScreen
            self.selected_home = None
            self.message = ""
            self.game.gui_manager.set_screen(ShopScreen(self.game))
        except Exception:
            pass

    def draw_house_placeholder(self, surface, x, y):
        # Draw a simple house placeholder at (x, y)
        body = pygame.Rect(x, y + 20, 120, 80)
        pygame.draw.rect(surface, LIGHT_BLUE, body, border_radius=6)
        roof = [(x - 10, y + 20), (x + 60, y - 20), (x + 130, y + 20)]
        pygame.draw.polygon(surface, RED, roof)
        # Door
        pygame.draw.rect(surface, BROWN, (x + 50, y + 60, 20, 40))
        # Windows
        pygame.draw.rect(surface, WHITE, (x + 15, y + 40, 20, 20))
        pygame.draw.rect(surface, WHITE, (x + 85, y + 40, 20, 20))
        pygame.draw.rect(surface, BLACK, (x + 15, y + 40, 20, 20), 2)
        pygame.draw.rect(surface, BLACK, (x + 85, y + 40, 20, 20), 2)

    def draw(self, surface):
        surface.fill(BG_TOP)
        font = pygame.font.SysFont('Arial', FONT_LARGE)
        title = font.render("Choose Your Home", True, PRIMARY)
        surface.blit(title, (80, 60))
        font_small = pygame.font.SysFont('Arial', FONT_MEDIUM)
        y = 150
        for idx, home in enumerate(HOME_OPTIONS):
            # Draw placeholder house
            self.draw_house_placeholder(surface, 30, y - 20)
            desc = font_small.render(home['desc'], True, BLACK)
            surface.blit(desc, (500, y+20))
            y += 90

        for btn in self.buttons:
            # highlight selected
            if self.selected_home and btn.text.startswith(self.selected_home['name']):
                # draw subtle outline
                pygame.draw.rect(surface, ACCENT, (btn.rect.x-4, btn.rect.y-4, btn.rect.width+8, btn.rect.height+8), 2, border_radius=10)
            btn.draw(surface)

        self.buy_btn.draw(surface)
        self.back_btn.draw(surface)

        msg_font = pygame.font.SysFont('Arial', FONT_MEDIUM)
        if not self.modal_popup:
            # draw status message
            msg = msg_font.render(self.message, True, DANGER if "Not" in self.message else SUCCESS)
            surface.blit(msg, (80, 420))
        else:
            # modal popup blocks other UI
            self.modal_popup.draw(surface)

    def handle_events(self, events):
        # Modal first
        if self.modal_popup:
            handled = self.modal_popup.handle_events(events)
            if handled:
                # clear modal after handling
                self.modal_popup = None
            return

        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mouse_click = True
            if ev.type == pygame.KEYDOWN and ev.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]:
                self.go_back()
                return

        # selection buttons
        for btn in self.buttons:
            action = btn.update(mouse_pos, mouse_click)
            if action:
                action()
                return

        # buy/back
        for btn in [self.buy_btn, self.back_btn]:
            action = btn.update(mouse_pos, mouse_click)
            if action:
                action()
                return
