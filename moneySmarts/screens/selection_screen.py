from typing import List, Dict, Optional
import pygame
from moneySmarts.ui import Screen, Button
from moneySmarts.ui_helpers import ModalPopup, create_selection_buttons
from moneySmarts.constants import *
from moneySmarts.screens.screen_utils import load_ui_background, draw_background

class SelectionScreen(Screen):
    """Generic selection screen for choosing items (homes, vehicles, etc.).

    Subclasses should override `draw_item_placeholder(surface, idx, x, y)` to
    provide a screen-specific visual for each item.
    """
    def __init__(self, game, options: List[Dict], title: str = "Select", create_buy_button: bool = True):
        super().__init__(game)
        self.options = options
        self.title = title
        self.selected_index: Optional[int] = None
        self.message = ""
        self.modal_popup: Optional[ModalPopup] = None
        labels = [f"{o['name']} - ${o['price']}" for o in options]
        self.buttons = create_selection_buttons(labels, 80, 150, 400, 60, 30, self.select_item)
        self.create_buy_button = create_buy_button
        if create_buy_button:
            self.buy_btn = Button(600, 200, 180, 50, "Buy", action=self.on_buy)
        else:
            self.buy_btn = None
        self.back_btn = Button(600, 350, 120, 40, "Back", action=self.go_back)
        self._background_original = load_ui_background('SELECTION_BG')

    def select_item(self, idx: int):
        self.selected_index = idx
        self.message = f"Selected: {self.options[idx]['name']}"

    def on_buy(self):
        # default buy handler; subclasses can override or provide specific payment flows
        if self.selected_index is None:
            self.modal_popup = ModalPopup("Select Item", "Select an item first.", on_ok=lambda: self._clear_message())
            return
        item = self.options[self.selected_index]
        # Default purchase attempts to deduct cash if available
        price = item.get('price', 0)
        cash_before = getattr(self.game.player, 'cash', 0)
        if cash_before >= price:
            self.game.player.cash -= price
            self.game.player.inventory = getattr(self.game.player, 'inventory', [])
            # default behavior: add name to inventory if exists
            if hasattr(self.game.player, 'inventory'):
                self.game.player.inventory.append(item['name'])
            popup_text = (
                f"Purchase Confirmation:\n"
                f"Before: ${cash_before:.2f}\n"
                f"Purchase: -${price:.2f}\n"
                f"After: ${self.game.player.cash:.2f}\n"
                f"Bought {item['name']} with cash!"
            )
            self.modal_popup = ModalPopup("Purchased", popup_text, on_ok=self._post_purchase)
            return
        # insufficient funds
        self.modal_popup = ModalPopup("Insufficient Funds", "Not enough cash.", on_ok=self._clear_message)

    def _post_purchase(self):
        # Default post-purchase action: clear selection and return to shop
        self.selected_index = None
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
            self.selected_index = None
            self.message = ""
            self.game.gui_manager.set_screen(ShopScreen(self.game))
        except Exception:
            pass

    def draw_item_placeholder(self, surface: pygame.Surface, idx: int, x: int, y: int):
        # Generic placeholder (subclasses should override)
        w, h = 200, 100
        pygame.draw.rect(surface, PRIMARY, (x, y, w, h), border_radius=12)
        pygame.draw.rect(surface, CARD_BORDER, (x, y, w, h), 2, border_radius=12)

    def draw(self, surface: pygame.Surface):
        # Basic layout and drawing of selectable items
        draw_background(surface, self._background_original, default_color=BG_TOP)
        font = pygame.font.SysFont('Arial', FONT_LARGE)
        title_surf = font.render(self.title, True, PRIMARY)
        surface.blit(title_surf, (80, 60))
        font_small = pygame.font.SysFont('Arial', FONT_MEDIUM)

        y = 150
        for idx, opt in enumerate(self.options):
            # draw placeholder specific to subclass
            self.draw_item_placeholder(surface, idx, 30, y - 20)
            desc = font_small.render(opt.get('desc', ''), True, BLACK)
            surface.blit(desc, (500, y+20))
            y += 90

        # draw selection buttons and highlight
        for btn in self.buttons:
            if self.selected_index is not None and btn.text.startswith(self.options[self.selected_index]['name']):
                pygame.draw.rect(surface, ACCENT, (btn.rect.x-4, btn.rect.y-4, btn.rect.width+8, btn.rect.height+8), 2, border_radius=10)
            btn.draw(surface)

        if self.buy_btn:
            self.buy_btn.draw(surface)
        self.back_btn.draw(surface)

        msg_font = pygame.font.SysFont('Arial', FONT_MEDIUM)
        if not self.modal_popup:
            msg = msg_font.render(self.message, True, DANGER if "Not" in self.message else SUCCESS)
            surface.blit(msg, (80, 420))
        else:
            self.modal_popup.draw(surface)

    def handle_events(self, events: List[pygame.event.Event]):
        # Modal first
        if self.modal_popup:
            handled = self.modal_popup.handle_events(events)
            if handled:
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
            if btn:
                action = btn.update(mouse_pos, mouse_click)
                if action:
                    action()
                    return
