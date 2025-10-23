import os
import pygame
from moneySmarts.constants import *
from moneySmarts.ui import Screen, Button
from moneySmarts.ui_helpers import ModalPopup, create_selection_buttons

VEHICLE_OPTIONS = [
    {"name": "Used Car", "price": 1200, "desc": "Reliable but basic transportation."},
    {"name": "Sedan", "price": 6000, "desc": "A comfortable family sedan."},
    {"name": "SUV", "price": 15000, "desc": "Spacious and powerful SUV."},
]

class VehiclePurchaseScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.selected_vehicle = None
        self.message = ""
        self.modal_popup = None
        self.create_buttons()

    def create_buttons(self):
        labels = [f"{v['name']} - ${v['price']}" for v in VEHICLE_OPTIONS]
        self.buttons = create_selection_buttons(labels, 80, 150, 400, 60, 30, self.select_vehicle)
        self.buy_cash_btn = Button(600, 150, 180, 40, "Buy Cash", action=self.buy_cash)
        self.buy_bank_btn = Button(600, 210, 180, 40, "Buy Bank", action=self.buy_bank)
        self.buy_credit_btn = Button(600, 270, 180, 40, "Buy Credit", action=self.buy_credit)
        self.finance_btn = Button(600, 330, 180, 40, "Finance", action=self.finance_vehicle)
        self.back_btn = Button(600, 400, 120, 40, "Back", action=self.go_back)

    def select_vehicle(self, idx):
        self.selected_vehicle = VEHICLE_OPTIONS[idx]
        self.message = f"Selected: {self.selected_vehicle['name']}"

    def buy_cash(self):
        if not self.selected_vehicle:
            self.modal_popup = ModalPopup("Select Vehicle", "Select a vehicle first.", on_ok=lambda: self._clear_message())
            return
        price = self.selected_vehicle['price']
        cash_before = getattr(self.game.player, 'cash', 0)
        if cash_before >= price:
            self.game.player.cash -= price
            cash_after = self.game.player.cash
            self.game.player.vehicle = self.selected_vehicle['name']
            from moneySmarts.models import Asset
            self.game.player.assets.append(Asset("Car", self.selected_vehicle['name'], price))
            popup_text = (
                f"Purchase Confirmation:\n"
                f"Before: ${cash_before:.2f}\n"
                f"Purchase: -${price:.2f}\n"
                f"After: ${cash_after:.2f}\n"
                f"You bought the {self.selected_vehicle['name']} with cash!"
            )
            self.modal_popup = ModalPopup("Purchased", popup_text, on_ok=self._post_purchase)
            self.selected_vehicle = None
        else:
            self.modal_popup = ModalPopup("Insufficient", "Not enough cash.", on_ok=lambda: self._clear_message())

    def buy_bank(self):
        if not self.selected_vehicle:
            self.modal_popup = ModalPopup("Select Vehicle", "Select a vehicle first.", on_ok=lambda: self._clear_message())
            return
        acct = getattr(self.game.player, 'bank_account', None)
        price = self.selected_vehicle['price']
        bank_before = acct.balance if acct else 0
        if acct and acct.balance >= price:
            acct.withdraw(price)
            bank_after = acct.balance
            self.game.player.vehicle = self.selected_vehicle['name']
            from moneySmarts.models import Asset
            self.game.player.assets.append(Asset("Car", self.selected_vehicle['name'], price))
            popup_text = (
                f"Purchase Confirmation:\n"
                f"Bank Before: ${bank_before:.2f}\n"
                f"Purchase: -${price:.2f}\n"
                f"Bank After: ${bank_after:.2f}\n"
                f"You bought the {self.selected_vehicle['name']} from bank!"
            )
            self.modal_popup = ModalPopup("Purchased", popup_text, on_ok=self._post_purchase)
            self.selected_vehicle = None
            # Navigate back to shop after purchase
        else:
            self.modal_popup = ModalPopup("Insufficient", "Not enough in bank account.", on_ok=lambda: self._clear_message())

    def buy_credit(self):
        if not self.selected_vehicle:
            self.modal_popup = ModalPopup("Select Vehicle", "Select a vehicle first.", on_ok=lambda: self._clear_message())
            return
        card = getattr(self.game.player, 'credit_card', None)
        price = self.selected_vehicle['price']
        credit_before = card.balance if card else 0
        if card and getattr(card, 'charge', lambda x: False)(price):
            credit_after = card.balance
            self.game.player.vehicle = self.selected_vehicle['name']
            from moneySmarts.models import Asset
            self.game.player.assets.append(Asset("Car", self.selected_vehicle['name'], price))
            popup_text = (
                f"Purchase Confirmation:\n"
                f"Credit Before: ${credit_before:.2f}\n"
                f"Purchase: -${price:.2f}\n"
                f"Credit After: ${credit_after:.2f}\n"
                f"You bought the {self.selected_vehicle['name']} on credit!"
            )
            self.modal_popup = ModalPopup("Purchased", popup_text, on_ok=self._post_purchase)
            self.selected_vehicle = None
        else:
            self.modal_popup = ModalPopup("Insufficient", "Not enough credit or no card.", on_ok=lambda: self._clear_message())

    def finance_vehicle(self):
        if not self.selected_vehicle:
            self.modal_popup = ModalPopup("Select Vehicle", "Select a vehicle first.", on_ok=lambda: self._clear_message())
            return
        price = self.selected_vehicle['price']
        if hasattr(self.game.player, 'credit_score') and self.game.player.credit_score >= 650:
            # keep loans in models format if available; this is a simple placeholder
            try:
                from moneySmarts.models import Loan, Asset
                loan = Loan("Auto", price, 0.05, 5)
                self.game.player.loans.append(loan)
                self.game.player.vehicle = self.selected_vehicle['name']
                self.game.player.assets.append(Asset("Car", self.selected_vehicle['name'], price))
            except Exception:
                # fallback: minimal loan representation
                self.game.player.loans.append({'type': 'vehicle', 'amount': price, 'name': self.selected_vehicle['name']})
                from moneySmarts.models import Asset
                self.game.player.assets.append(Asset("Car", self.selected_vehicle['name'], price))
            popup_text = (
                f"Purchase Confirmation:\n"
                f"Financed Amount: ${price:.2f}\n"
                f"Financed {self.selected_vehicle['name']}! Loan added."
            )
            self.modal_popup = ModalPopup("Financed", popup_text, on_ok=self._post_purchase)
            self.selected_vehicle = None
        else:
            self.modal_popup = ModalPopup("Denied", "Credit score too low for financing.", on_ok=lambda: self._clear_message())

    def _post_purchase(self):
        self.selected_vehicle = None
        self.message = ""
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
            self.selected_vehicle = None
            self.message = ""
            self.game.gui_manager.set_screen(ShopScreen(self.game))
        except Exception:
            pass

    def draw_vehicle_placeholder(self, surface, x, y, w=200, h=100, color=PRIMARY):
        # Draw a simple vehicle placeholder
        car_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, color, car_rect, border_radius=12)
        pygame.draw.rect(surface, CARD_BORDER, car_rect, 2, border_radius=12)
        # Wheels
        pygame.draw.circle(surface, BLACK, (x + int(w*0.25), y + h + 10), 14)
        pygame.draw.circle(surface, BLACK, (x + int(w*0.75), y + h + 10), 14)

    def draw(self, surface):
        surface.fill(BG_TOP)
        font = pygame.font.SysFont('Arial', FONT_LARGE)
        title = font.render("Choose Your Vehicle", True, PRIMARY)
        surface.blit(title, (80, 60))
        font_small = pygame.font.SysFont('Arial', FONT_MEDIUM)
        y = 150
        colors = [PRIMARY, ACCENT, BLUE]
        for idx, vehicle in enumerate(VEHICLE_OPTIONS):
            # Draw vehicle placeholder
            self.draw_vehicle_placeholder(surface, 30, y - 20, color=colors[idx % len(colors)])
            desc = font_small.render(vehicle['desc'], True, BLACK)
            surface.blit(desc, (500, y+20))
            y += 90
        for btn in self.buttons:
            # highlight selected
            if self.selected_vehicle and btn.text.startswith(self.selected_vehicle['name']):
                pygame.draw.rect(surface, ACCENT, (btn.rect.x-4, btn.rect.y-4, btn.rect.width+8, btn.rect.height+8), 2, border_radius=10)
            btn.draw(surface)
        self.buy_cash_btn.draw(surface)
        self.buy_bank_btn.draw(surface)
        self.buy_credit_btn.draw(surface)
        self.finance_btn.draw(surface)
        self.back_btn.draw(surface)
        msg_font = pygame.font.SysFont('Arial', FONT_MEDIUM)
        if not self.modal_popup:
            msg = msg_font.render(self.message, True, DANGER if "Not" in self.message or "low" in self.message else SUCCESS)
            surface.blit(msg, (80, 480))
        else:
            self.modal_popup.draw(surface)

    def handle_events(self, events):
        # Modal first
        if self.modal_popup:
            handled = self.modal_popup.handle_events(events)
            if handled:
                self.modal_popup = None
            return

        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_click = True
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]:
                    self.go_back()
                    return

        # Check vehicle selection buttons
        for btn in self.buttons:
            action = btn.update(mouse_pos, mouse_click)
            if action:
                action()
                return

        # Check purchase/finance/back buttons
        for btn in [self.buy_cash_btn, self.buy_bank_btn, self.buy_credit_btn, self.finance_btn, self.back_btn]:
            action = btn.update(mouse_pos, mouse_click)
            if action:
                action()
                return
