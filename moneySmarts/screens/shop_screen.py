import pygame
from moneySmarts.ui_helpers import ModalPopup

from moneySmarts.constants import *
from moneySmarts.ui import Screen, Button

# Define the shop items with prices and descriptions
# Using constants imported from moneySmarts.constants


SHOP_ITEMS = [
    {"name": "Groceries", "price": 50, "desc": "Weekly groceries for your family."},
    {"name": "Clothes", "price": 100, "desc": "A new set of clothes."},
    {"name": "Smartphone", "price": 600, "desc": "A modern smartphone.", "recurring": {"name": "Phone Plan", "amount": 30, "source": "bank_or_credit"}},
    {"name": "TV", "price": 400, "desc": "A 50-inch smart TV.", "recurring": {"name": "Streaming Service", "amount": 15, "source": "bank_or_credit"}},
    {"name": "Laptop", "price": 900, "desc": "A new laptop for work or school.", "recurring": {"name": "Software Subscription", "amount": 10, "source": "bank_or_credit"}},
    {"name": "Gift", "price": 30, "desc": "A gift for a friend or family member."},
    {"name": "Home", "price": 5000, "desc": "A place to call your own. Unlocks a new chapter!"},
    {"name": "Vehicle", "price": 1200, "desc": "Buy a new or used vehicle!"},
]

class ShopScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.ok_btn_rect = None
        self.popup_back_btn = None
        self.pay_credit_btn = None
        self.pay_bank_btn = None
        self.main_back_btn = None
        self.pay_cash_btn = None
        self.selected_item = None
        self.message = ""
        self.show_payment_popup = False
        self.show_confirmation_popup = False
        self.confirmation_text = ""
        self.buttons = []
        self.create_buttons()
        self.create_payment_buttons()
        self.show_insufficient_popup = False
        self.insufficient_text = ""
        self.insufficient_ok_btn = None
        self.modal_popup = None

    def create_buttons(self):
        self.buttons = []
        y = 140
        for idx, item in enumerate(SHOP_ITEMS):
            btn = Button(60, y, 320, 50, f"{item['name']} - ${item['price']}", action=lambda i=idx: self.select_item(i))
            self.buttons.append(btn)
            y += 60
        self.main_back_btn = Button(60, SCREEN_HEIGHT - 80, 180, 50, "Back", color=PRIMARY, hover_color=PRIMARY_HOVER, text_color=WHITE, action=self.go_back)
        inventory_btn = Button(
            SCREEN_WIDTH - 240, 20, 200, 44, "View Inventory", action=self.show_inventory_popup
        )
        self.buttons.append(inventory_btn)

    def create_payment_buttons(self):
        popup_x = SCREEN_WIDTH // 2 - 130
        popup_y = SCREEN_HEIGHT // 2 - 120
        self.pay_cash_btn = Button(popup_x, popup_y + 60, 260, 40, "Pay Cash", action=self.pay_cash)
        self.pay_bank_btn = Button(popup_x, popup_y + 110, 260, 40, "Pay Bank", action=self.pay_bank)
        self.pay_credit_btn = Button(popup_x, popup_y + 160, 260, 40, "Pay Credit", action=self.pay_credit)
        self.popup_back_btn = Button(popup_x + 70, popup_y + 220, 120, 40, "Back", action=self.close_popup)

    def select_item(self, idx):
        self.selected_item = SHOP_ITEMS[idx]
        # Only show a payment popup for items that are not Home or Vehicle
        if self.selected_item['name'] == "Home":
            from moneySmarts.screens.home_purchase_screen import HomePurchaseScreen
            self.game.gui_manager.set_screen(HomePurchaseScreen(self.game))
            self.selected_item = None
            self.show_payment_popup = False
            return
        if self.selected_item['name'] == "Vehicle":
            from moneySmarts.screens.vehicle_purchase_screen import VehiclePurchaseScreen
            self.game.gui_manager.set_screen(VehiclePurchaseScreen(self.game))
            self.selected_item = None
            self.show_payment_popup = False
            return
        self.message = f"Selected: {self.selected_item['name']}"
        self.show_payment_popup = True

    def close_popup(self):
        self.show_payment_popup = False
        self.selected_item = None
        self.message = ""
        # Redraw screen to ensure popup is gone
        self.game.gui_manager.set_screen(ShopScreen(self.game))

    def show_insufficient_funds_popup(self, item_name, required, available):
        self.insufficient_text = (
            f"Insufficient funds for {item_name}!\n"
            f"Required: ${required:,.2f}\nAvailable: ${available:,.2f}"
        )
        # Use ModalPopup instead of manual drawing
        self.modal_popup = ModalPopup("Insufficient Funds", self.insufficient_text, on_ok=self._clear_modal)

    def _clear_modal(self):
        self.modal_popup = None
        # reset any transient flags
        self.selected_item = None
        self.message = ""

    def pay_cash(self):
        if not self.selected_item:
            self.message = "Select an item first."
            return
        price = self.selected_item['price']
        cash_before = self.game.player.cash
        if cash_before >= price:
            self.game.player.cash -= price
            cash_after = self.game.player.cash
            self.game.player.inventory.append(self.selected_item['name'])
            if 'recurring' in self.selected_item:
                self.game.player.recurring_bills.append(self.selected_item['recurring'])
            self.confirmation_text = (
                f"Purchase Confirmation:\n"
                f"Before: ${cash_before:.2f}\n"
                f"Purchase: -${price:.2f}\n"
                f"After: ${cash_after:.2f}\n"
                f"Bought {self.selected_item['name']} with cash!"
            )
            # Show confirmation as modal
            self.modal_popup = ModalPopup("Purchased", self.confirmation_text, on_ok=self._clear_modal)
            self.show_payment_popup = False
        else:
            self.show_insufficient_funds_popup(self.selected_item['name'], price, cash_before)

    def pay_bank(self):
        if not self.selected_item:
            self.message = "Select an item first."
            return
        acct = self.game.player.bank_account
        price = self.selected_item['price']
        bank_before = acct.balance if acct else 0
        if acct and acct.withdraw(price):
            bank_after = acct.balance
            self.game.player.inventory.append(self.selected_item['name'])
            if 'recurring' in self.selected_item:
                self.game.player.recurring_bills.append(self.selected_item['recurring'])
            self.confirmation_text = (
                f"Purchase Confirmation:\n"
                f"Bank Before: ${bank_before:.2f}\n"
                f"Purchase: -${price:.2f}\n"
                f"Bank After: ${bank_after:.2f}\n"
                f"Bought {self.selected_item['name']} from bank!"
            )
            self.modal_popup = ModalPopup("Purchased", self.confirmation_text, on_ok=self._clear_modal)
            self.show_payment_popup = False
        else:
            self.show_insufficient_funds_popup(self.selected_item['name'], price, bank_before)

    def pay_credit(self):
        if not self.selected_item:
            self.message = "Select an item first."
            return
        card = self.game.player.credit_card
        price = self.selected_item['price']
        credit_before = card.balance if card else 0
        if card and card.charge(price):
            credit_after = card.balance
            self.game.player.inventory.append(self.selected_item['name'])
            if 'recurring' in self.selected_item:
                self.game.player.recurring_bills.append(self.selected_item['recurring'])
            self.confirmation_text = (
                f"Purchase Confirmation:\n"
                f"Credit Before: ${credit_before:.2f}\n"
                f"Purchase: -${price:.2f}\n"
                f"Credit After: ${credit_after:.2f}\n"
                f"Bought {self.selected_item['name']} on credit!"
            )
            self.modal_popup = ModalPopup("Purchased", self.confirmation_text, on_ok=self._clear_modal)
            self.show_payment_popup = False
        else:
            self.show_insufficient_funds_popup(self.selected_item['name'], price, credit_before)

    def go_back(self):
        self.show_payment_popup = False
        self.show_confirmation_popup = False
        self.selected_item = None
        self.message = ""
        from moneySmarts.screens.game_screen import GameScreen
        self.game.gui_manager.set_screen(GameScreen(self.game))

    def show_inventory_popup(self):
        self.show_inventory = True
        self.inventory_popup_btn = Button(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 80, 200, 50, "Close", action=self.close_inventory_popup
        )

    def close_inventory_popup(self):
        self.show_inventory = False
        self.inventory_popup_btn = None

    def handle_events(self, events):
        """Handle a list of pygame events for the shop screen (GUI manager calls this)."""
        # If modal popup present, delegate to it first
        if getattr(self, 'modal_popup', None):
            handled = self.modal_popup.handle_events(events)
            if handled:
                # modal on_ok may clear itself; ensure we reset flags
                if getattr(self, 'modal_popup', None) is None:
                    self.selected_item = None
                    self.message = ""
                return
        # otherwise fall back to previous handling
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_click = True
            if event.type == pygame.KEYDOWN and event.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]:
                # treat back as go_back
                self.go_back()
                return

        # Payment popup buttons
        if self.show_payment_popup:
            for btn in [self.pay_cash_btn, self.pay_bank_btn, self.pay_credit_btn, self.popup_back_btn]:
                action = btn.update(mouse_pos, mouse_click)
                if callable(action):
                    action()
                    return

        # Inventory popup
        if getattr(self, 'show_inventory', False) and getattr(self, 'inventory_popup_btn', None):
            action = self.inventory_popup_btn.update(mouse_pos, mouse_click)
            if callable(action):
                action()
                return

        # Main shop buttons
        for btn in self.buttons:
            if btn:
                action = btn.update(mouse_pos, mouse_click)
                if callable(action):
                    action()
                    return
        if self.main_back_btn:
            action = self.main_back_btn.update(mouse_pos, mouse_click)
            if callable(action):
                action()
                return

    def draw(self, surface):
        surface.fill(BG_TOP)
        title_font = pygame.font.SysFont('Arial', FONT_LARGE)
        title = title_font.render("Shop", True, PRIMARY)
        surface.blit(title, (60, 40))
        # Items panel
        panel = pygame.Rect(360, 120, SCREEN_WIDTH - 420, SCREEN_HEIGHT - 180)
        pygame.draw.rect(surface, CARD_BG, panel, border_radius=12)
        pygame.draw.rect(surface, CARD_BORDER, panel, 2, border_radius=12)
        desc_font = pygame.font.SysFont('Arial', FONT_MEDIUM)
        y = 140
        for idx, item in enumerate(SHOP_ITEMS):
            desc = desc_font.render(item['desc'], True, BLACK)
            surface.blit(desc, (380, y+10))
            y += 60
        for btn in self.buttons:
            if btn:
                btn.draw(surface)
        if self.main_back_btn:
            self.main_back_btn.draw(surface)
        msg_font = pygame.font.SysFont('Arial', FONT_MEDIUM)
        # Show message as popup if not enough funds
        if self.message and ("Not enough" in self.message or "low" in self.message):
            popup_rect = pygame.Rect(250, 250, 520, 160)
            pygame.draw.rect(surface, (255, 240, 240), popup_rect, border_radius=12)
            pygame.draw.rect(surface, DANGER, popup_rect, 3, border_radius=12)
            msg = msg_font.render(self.message, True, DANGER)
            surface.blit(msg, (popup_rect.x + 40, popup_rect.y + 40))
            # Draw OK button centered at bottom of popup
            ok_btn_width, ok_btn_height = 140, 40
            ok_btn_x = popup_rect.x + (popup_rect.width - ok_btn_width) // 2
            ok_btn_y = popup_rect.y + popup_rect.height - ok_btn_height - 20
            ok_btn_rect = pygame.Rect(ok_btn_x, ok_btn_y, ok_btn_width, ok_btn_height)
            pygame.draw.rect(surface, SUCCESS, ok_btn_rect, border_radius=8)
            ok_text = msg_font.render("OK", True, WHITE)
            surface.blit(ok_text, (ok_btn_rect.x + 45, ok_btn_rect.y + 5))
            self.ok_btn_rect = ok_btn_rect
            return  # Prevent drawing other popups/buttons
        else:
            msg = msg_font.render(self.message, True, DANGER if "Not" in self.message else SUCCESS)
            surface.blit(msg, (60, SCREEN_HEIGHT - 60))
        if self.selected_item:
            sel_font = pygame.font.SysFont('Arial', FONT_MEDIUM)
            sel_msg = sel_font.render(f"Selected: {self.selected_item['name']}", True, BLACK)
            surface.blit(sel_msg, (60, SCREEN_HEIGHT - 120))
        # Draw the payment popup if needed
        if self.show_payment_popup and self.selected_item:
            popup_x = SCREEN_WIDTH // 2 - 160
            popup_y = SCREEN_HEIGHT // 2 - 160
            popup_rect = pygame.Rect(popup_x, popup_y, 320, 300)
            pygame.draw.rect(surface, CARD_BG, popup_rect, border_radius=12)
            pygame.draw.rect(surface, CARD_BORDER, popup_rect, 2, border_radius=12)
            popup_font = pygame.font.SysFont('Arial', FONT_LARGE)
            popup_title = popup_font.render("Choose Payment", True, PRIMARY)
            surface.blit(popup_title, (popup_x + 20, popup_y + 10))
            for btn in [self.pay_cash_btn, self.pay_bank_btn, self.pay_credit_btn, self.popup_back_btn]:
                if btn:
                    btn.draw(surface)
        # Draw inventory popup if needed
        if hasattr(self, 'show_inventory') and self.show_inventory:
            inv_rect = pygame.Rect(SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT // 2 - 160, 440, 320)
            pygame.draw.rect(surface, CARD_BG, inv_rect, border_radius=12)
            pygame.draw.rect(surface, CARD_BORDER, inv_rect, 2, border_radius=12)
            title_font = pygame.font.SysFont('Arial', FONT_LARGE)
            title_surface = title_font.render("Inventory", True, PRIMARY)
            title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 120))
            surface.blit(title_surface, title_rect)
            items = self.game.player.inventory if hasattr(self.game.player, 'inventory') else []
            item_font = pygame.font.SysFont('Arial', FONT_MEDIUM)
            for i, item in enumerate(items):
                item_surface = item_font.render(f"- {item}", True, BLACK)
                item_rect = item_surface.get_rect(left=SCREEN_WIDTH // 2 - 200, top=SCREEN_HEIGHT // 2 - 90 + i * 28)
                surface.blit(item_surface, item_rect)
            self.inventory_popup_btn.draw(surface)
        # Draw confirmation popup if needed
        if self.show_confirmation_popup:
            msg_font = pygame.font.SysFont('Arial', FONT_MEDIUM)
            popup_rect = pygame.Rect(200, 180, 500, 280)
            pygame.draw.rect(surface, (245, 255, 240), popup_rect, border_radius=12)
            pygame.draw.rect(surface, ACCENT, popup_rect, 3, border_radius=12)
            lines = self.confirmation_text.split('\n')
            for i, line in enumerate(lines):
                line_surf = msg_font.render(line, True, BLACK)
                surface.blit(line_surf, (popup_rect.x + 30, popup_rect.y + 30 + i * 35))
            # Draw OK button centered at bottom of popup
            ok_btn_width, ok_btn_height = 140, 40
            ok_btn_x = popup_rect.x + (popup_rect.width - ok_btn_width) // 2
            ok_btn_y = popup_rect.y + popup_rect.height - ok_btn_height - 20
            ok_btn_rect = pygame.Rect(ok_btn_x, ok_btn_y, ok_btn_width, ok_btn_height)
            pygame.draw.rect(surface, SUCCESS, ok_btn_rect, border_radius=8)
            ok_text = msg_font.render("OK", True, WHITE)
            surface.blit(ok_text, (ok_btn_rect.x + 45, ok_btn_rect.y + 5))
            self.ok_btn_rect = ok_btn_rect
            return  # Prevent drawing other popups/buttons
        else:
            self.ok_btn_rect = None
        # Draw insufficient funds popup if needed
        if self.show_insufficient_popup and self.insufficient_text:
            popup_rect = pygame.Rect(SCREEN_WIDTH // 2 - 220, SCREEN_HEIGHT // 2 - 100, 440, 180)
            pygame.draw.rect(surface, (255, 240, 240), popup_rect, border_radius=12)
            pygame.draw.rect(surface, DANGER, popup_rect, 3, border_radius=12)
            font = pygame.font.SysFont('Arial', 24, bold=True)
            lines = self.insufficient_text.split('\n')
            for i, line in enumerate(lines):
                text_surf = font.render(line, True, DANGER)
                surface.blit(text_surf, (popup_rect.x + 30, popup_rect.y + 26 + i * 32))
            if self.insufficient_ok_btn:
                self.insufficient_ok_btn.draw(surface)

    def handle_event(self, event):
        # Handle OK button for insufficient funds popup and confirmation popup
        if (self.show_confirmation_popup or (self.message and ("Not enough" in self.message))) and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            if self.ok_btn_rect and self.ok_btn_rect.collidepoint(mouse_pos):
                self.show_confirmation_popup = False
                self.confirmation_text = ""
                self.selected_item = None
                self.message = ""
                self.game.gui_manager.set_screen(ShopScreen(self.game))
                return
