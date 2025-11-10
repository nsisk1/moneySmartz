import pygame
from moneySmarts.constants import *
from moneySmarts.ui import Screen, Button, draw_vertical_gradient
import importlib
try:
    financial_screens_mod = importlib.import_module('moneySmarts.screens.financial_screens')
except Exception:
    financial_screens_mod = None
import os
import logging
from moneySmarts.models import BankAccount
from moneySmarts.images import get_image_path
from moneySmarts.screens.screen_utils import load_ui_background, draw_background
from moneySmarts.ui_helpers import ModalPopup

_BANK_BACKGROUND_PATH = None
_BANK_BACKGROUND_SURFACES = {}
_GRADIENT_CACHE = {}

ATM_PANEL = (30, 30, 30)
ATM_BEZEL = (18, 18, 18)
ATM_SCREEN_BG = (8, 18, 36)
ATM_SCREEN_GLOW = (18, 56, 100)
ATM_KEY = (70, 70, 70)
ATM_KEY_HOVER = PRIMARY_HOVER if 'PRIMARY_HOVER' in globals() else (100, 100, 100)
ATM_ACCENT = (200, 200, 200)

def _find_bank_interior_path():
    global _BANK_BACKGROUND_PATH
    try:
        cand = get_image_path('BANK_BG')
        if isinstance(cand, str) and os.path.exists(cand):
            _BANK_BACKGROUND_PATH = cand
            logging.info("Using BANK_BG background at %s", cand)
            return cand
        else:
            logging.info("BANK_BG candidate not found on disk: %s", cand)
            _BANK_BACKGROUND_PATH = None
            return None
    except Exception as e:
        logging.warning("Error resolving BANK_BG via get_image_path: %s", e)
        _BANK_BACKGROUND_PATH = None
        return None

def _load_image_from_path(path, size):
    if not path:
        return None
    key = tuple(size)
    if key in _BANK_BACKGROUND_SURFACES:
        return _BANK_BACKGROUND_SURFACES[key]
    try:
        img = pygame.image.load(path)
        try:
            img = img.convert_alpha()
        except Exception:
            img = img.convert()
        if img.get_size() != key:
            img = pygame.transform.smoothscale(img, key)
        _BANK_BACKGROUND_SURFACES[key] = img
        logging.info("Loaded bank interior surface from %s for size %s", path, key)
        return img
    except Exception as e:
        logging.warning("Failed to load bank interior image %s: %s", path, e)
        _BANK_BACKGROUND_SURFACES[key] = None
        return None

def _vertical_gradient_surface(size, top_color, bottom_color, alpha=255):
    key = (size, top_color, bottom_color, alpha)
    if key in _GRADIENT_CACHE:
        return _GRADIENT_CACHE[key]
    w, h = size
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    if h <= 1:
        r, g, b = top_color
        surf.fill((r, g, b, alpha))
        _GRADIENT_CACHE[key] = surf
        return surf
    tr, tg, tb = top_color
    br, bgc, bb = bottom_color
    for y in range(h):
        t = float(y) / float(h - 1)
        r = int(tr * (1 - t) + br * t)
        g = int(tg * (1 - t) + bgc * t)
        b = int(tb * (1 - t) + bb * t)
        surf.fill((r, g, b, alpha), rect=pygame.Rect(0, y, w, 1))
    _GRADIENT_CACHE[key] = surf
    return surf

class BankScreen(Screen):
    play_startup_music = False
    def __init__(self, game):
        super(BankScreen, self).__init__(game)
        try:
            font_path = os.path.join(ASSETS_DIR, 'fonts', 'pixelated_font.ttf')
            self.title_font = pygame.font.Font(font_path, 48)
            self.balance_font = pygame.font.Font(font_path, 28)
            self.text_font = pygame.font.Font(font_path, 24)
        except Exception:
            self.title_font = pygame.font.SysFont('Arial', 48, bold=True)
            self.balance_font = pygame.font.SysFont('Arial', 28, bold=True)
            self.text_font = pygame.font.SysFont('Arial', 24)
        self.debug_font = pygame.font.SysFont('Arial', 14)
        self.buttons = []
        self.create_buttons()
        self.status_message = None
        self.status_color = WHITE
        _find_bank_interior_path()
        self.background = None
        # themed background (UI image key) - will be used as fallback if bank interior not found
        self._background_original = load_ui_background('BANK_BG')

    def create_buttons(self):
        button_specs = [
            ("Deposit", self.go_to_deposit),
            ("Withdraw", self.go_to_withdraw),
            ("Deposit to Savings", self.go_to_deposit_savings),
            ("View Balance", self.go_to_view_balance),
            ("View Savings", self.go_to_view_savings),
            ("Open Account", self.go_to_open_account),
            ("Back", self.go_back)
        ]
        screen_w, screen_h = SCREEN_WIDTH, SCREEN_HEIGHT
        try:
            screen_w, screen_h = self.game.gui_manager.screen.get_size()
        except Exception:
            pass
        panel_w = min(760, screen_w - 80)
        panel_h = min(520, screen_h - 80)
        panel_left = (screen_w - panel_w) // 2
        panel_top = (screen_h - panel_h) // 2
        content_rect = pygame.Rect(panel_left + 40, panel_top + 40, panel_w - 80, panel_h - 80)

        btn_w = 220
        btn_h = 48
        spacing = 12
        start_x = content_rect.right - btn_w - 10
        start_y = content_rect.top + 20
        self.buttons = []
        for i, (label, callback) in enumerate(button_specs):
            if label == 'Back':
                x = panel_left + (panel_w - btn_w) // 2
                y = content_rect.bottom + 12
                w, h = btn_w, btn_h
            else:
                x = start_x
                y = start_y + i * (btn_h + spacing)
                w, h = btn_w, btn_h
            btn = Button(x, y, w, h, label, color=PRIMARY, hover_color=PRIMARY_HOVER, text_color=WHITE, action=callback)
            self.buttons.append(btn)

    def go_to_deposit(self):
        if financial_screens_mod and hasattr(financial_screens_mod, 'DepositScreen'):
            self.game.gui_manager.set_screen(financial_screens_mod.DepositScreen(self.game))
        else:
            try:
                mod = importlib.import_module('moneySmarts.screens.financial_screens')
                self.game.gui_manager.set_screen(getattr(mod, 'DepositScreen')(self.game))
            except Exception:
                logging.exception('Failed to open DepositScreen')

    def go_to_withdraw(self):
        if financial_screens_mod and hasattr(financial_screens_mod, 'WithdrawScreen'):
            self.game.gui_manager.set_screen(financial_screens_mod.WithdrawScreen(self.game))
        else:
            try:
                mod = importlib.import_module('moneySmarts.screens.financial_screens')
                self.game.gui_manager.set_screen(getattr(mod, 'WithdrawScreen')(self.game))
            except Exception:
                logging.exception('Failed to open WithdrawScreen')

    def go_to_deposit_savings(self):
        if financial_screens_mod and hasattr(financial_screens_mod, 'DepositToSavingsScreen'):
            self.game.gui_manager.set_screen(financial_screens_mod.DepositToSavingsScreen(self.game))
        else:
            try:
                mod = importlib.import_module('moneySmarts.screens.financial_screens')
                self.game.gui_manager.set_screen(getattr(mod, 'DepositToSavingsScreen')(self.game))
            except Exception:
                logging.exception('Failed to open DepositToSavingsScreen')

    def go_to_view_balance(self):
        if financial_screens_mod and hasattr(financial_screens_mod, 'BankDetailsScreen'):
            self.game.gui_manager.set_screen(financial_screens_mod.BankDetailsScreen(self.game))
        else:
            try:
                mod = importlib.import_module('moneySmarts.screens.financial_screens')
                self.game.gui_manager.set_screen(getattr(mod, 'BankDetailsScreen')(self.game))
            except Exception:
                logging.exception('Failed to open BankDetailsScreen')

    def go_to_view_savings(self):
        if financial_screens_mod and hasattr(financial_screens_mod, 'SavingsDetailsScreen'):
            self.game.gui_manager.set_screen(financial_screens_mod.SavingsDetailsScreen(self.game))
        else:
            try:
                mod = importlib.import_module('moneySmarts.screens.financial_screens')
                self.game.gui_manager.set_screen(getattr(mod, 'SavingsDetailsScreen')(self.game))
            except Exception:
                logging.exception('Failed to open SavingsDetailsScreen')

    def go_to_open_account(self):
        if financial_screens_mod and hasattr(financial_screens_mod, 'BankAccountScreen'):
            self.game.gui_manager.set_screen(financial_screens_mod.BankAccountScreen(self.game))
        else:
            try:
                mod = importlib.import_module('moneySmarts.screens.financial_screens')
                self.game.gui_manager.set_screen(getattr(mod, 'BankAccountScreen')(self.game))
            except Exception:
                logging.exception('Failed to open BankAccountScreen')

    def go_back(self):
        from moneySmarts.screens.game_screen import GameScreen
        self.game.gui_manager.set_screen(GameScreen(self.game))

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.go_back()
                return
        super(BankScreen, self).handle_events(events)

    def on_enter(self):
        try:
            size = self.game.gui_manager.screen.get_size()
        except Exception:
            size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        _find_bank_interior_path()
        self.background = None

    def draw(self, surface):
        sw, sh = surface.get_size()
        try:
            if isinstance(_BANK_BACKGROUND_PATH, str) and os.path.exists(_BANK_BACKGROUND_PATH):
                if not self.background or self.background.get_size() != (sw, sh):
                    loaded = _load_image_from_path(_BANK_BACKGROUND_PATH, (sw, sh))
                    self.background = loaded
                if self.background:
                    try:
                        surface.blit(self.background, (0, 0))
                        overlay = _vertical_gradient_surface((sw, sh), BG_TOP, BG_BOTTOM, alpha=140)
                        surface.blit(overlay, (0, 0))
                    except Exception:
                        draw_vertical_gradient(surface, (0, 0, sw, sh), BG_TOP, BG_BOTTOM)
                else:
                    # fallback to themed background if available
                    if self._background_original:
                        draw_background(surface, self._background_original, default_color=BG_TOP)
                    else:
                        draw_vertical_gradient(surface, (0, 0, sw, sh), BG_TOP, BG_BOTTOM)
            else:
                try:
                    if self._background_original:
                        draw_background(surface, self._background_original, default_color=BG_TOP)
                    else:
                        draw_vertical_gradient(surface, (0, 0, sw, sh), BG_TOP, BG_BOTTOM)
                except Exception:
                    surface.fill(BG_TOP)
        except Exception:
            try:
                if self._background_original:
                    draw_background(surface, self._background_original, default_color=BG_TOP)
                else:
                    draw_vertical_gradient(surface, (0, 0, sw, sh), BG_TOP, BG_BOTTOM)
            except Exception:
                surface.fill(BG_TOP)

        panel_w = min(760, sw - 120)
        panel_h = min(520, sh - 160)
        panel_left = (sw - panel_w) // 2
        panel_top = (sh - panel_h) // 2
        panel_rect = pygame.Rect(panel_left, panel_top, panel_w, panel_h)
        try:
            shadow = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 40))
            surface.blit(shadow, (panel_left + 4, panel_top + 6))
            pygame.draw.rect(surface, CARD_BG, panel_rect, border_radius=12)
        except Exception:
            pygame.draw.rect(surface, (245, 247, 250), panel_rect)
        pygame.draw.rect(surface, CARD_BORDER, panel_rect, 2, border_radius=12)

        title_surface = self.title_font.render("Bank", True, PRIMARY)
        title_rect = title_surface.get_rect(center=(sw // 2, panel_top - 20))
        try:
            title_bg = pygame.Surface((title_rect.width + 12, title_rect.height + 6), pygame.SRCALPHA)
            title_bg.fill((255, 255, 255, 220))
            surface.blit(title_bg, (title_rect.left - 6, title_rect.top - 3))
        except Exception:
            pass
        surface.blit(title_surface, title_rect)

        card_w = min(420, panel_w - 120)
        card_h = 180
        card_x = panel_left + 40
        card_y = panel_top + 80
        card_rect = pygame.Rect(card_x, card_y, card_w, card_h)
        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card_surf.fill((255, 255, 255, 230))
        pygame.draw.rect(card_surf, CARD_BORDER, card_surf.get_rect(), 2, border_radius=12)
        surface.blit(card_surf, (card_x, card_y))

        player = self.game.player
        checking_balance = player.bank_account.balance if hasattr(player, 'bank_account') and player.bank_account else 0.0
        savings_balance = player.savings_account.balance if hasattr(player, 'savings_account') and player.savings_account else 0.0

        info_lines = [
            f"Cash: ${player.cash:.2f}",
            f"Checking: ${checking_balance:.2f}",
            f"Savings: ${savings_balance:.2f}"
        ]
        for i, line in enumerate(info_lines):
            text_surface = self.balance_font.render(line, True, BLACK)
            surface.blit(text_surface, (card_x + 18, card_y + 14 + i * 34))

        for button in self.buttons:
            button.draw(surface)

        try:
            bg_name = os.path.basename(_BANK_BACKGROUND_PATH) if isinstance(_BANK_BACKGROUND_PATH, str) else 'none'
            dbg_surf = self.debug_font.render(f"BG: {bg_name}", True, BLACK)
            dbg_rect = dbg_surf.get_rect(bottomright=(sw - 8, sh - 8))
            box_rect = dbg_rect.inflate(8, 6)
            s = pygame.Surface(box_rect.size, pygame.SRCALPHA)
            s.fill((255, 255, 255, 180))
            surface.blit(s, box_rect.topleft)
            surface.blit(dbg_surf, dbg_rect.topleft)
        except Exception:
            pass

class DepositToSavingsScreen(Screen):
    def __init__(self, game):
        super(DepositToSavingsScreen, self).__init__(game)
        try:
            font_path = os.path.join(ASSETS_DIR, 'fonts', 'pixelated_font.ttf')
            self.title_font = pygame.font.Font(font_path, 40)
            self.text_font = pygame.font.Font(font_path, 24)
        except Exception:
            self.title_font = pygame.font.SysFont('Arial', 40, bold=True)
            self.text_font = pygame.font.SysFont('Arial', 24)
        self.debug_font = pygame.font.SysFont('Arial', 14)
        self.input_active = False
        self.input_text = ""
        # modal dialog shown after actions (ModalPopup)
        self.modal = None
        self.status_message = None
        self.status_color = BLACK
        self.interest_rate = 0.02
        _find_bank_interior_path()
        self.background = None

    def on_enter(self):
        self.background = None

    def handle_events(self, events):
        # If a modal is present, let it consume events first
        if getattr(self, 'modal', None):
            old_modal = self.modal
            handled = False
            try:
                handled = old_modal.handle_events(events)
            except Exception:
                handled = False
            if handled:
                # only clear if the modal wasn't replaced by the callback
                if getattr(self, 'modal', None) is old_modal:
                    self.modal = None
                return
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.gui_manager.set_screen(BankScreen(self.game))
                elif event.key == pygame.K_RETURN:
                    self.deposit_to_savings()
                elif event.key == pygame.K_BACKSPACE:
                    self.input_text = self.input_text[:-1]
                elif event.unicode.isdigit() or (event.unicode == '.' and '.' not in self.input_text):
                    self.input_text += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.input_active = True

    def deposit_to_savings(self):
        player = self.game.player
        try:
            amount = float(self.input_text)
            if amount > 0 and amount <= player.cash:
                player.cash -= amount
                if not hasattr(player, 'savings_account') or not player.savings_account:
                    player.savings_account = BankAccount("Savings")
                    player.savings_account.interest_rate = self.interest_rate
                player.savings_account.interest_rate = self.interest_rate
                player.savings_account.deposit(amount)
                interest = player.savings_account.apply_interest()
                msg = f"Deposited ${amount:.2f} (+${interest:.2f} interest)"
                # Show a centered modal confirmation
                self.modal = ModalPopup("Deposit Successful", msg, on_ok=lambda: setattr(self, 'modal', None))
                # Also set status_color for non-modal fallback
                self.status_color = SUCCESS
            else:
                msg = "Invalid amount."
                self.modal = ModalPopup("Deposit Failed", msg, on_ok=lambda: setattr(self, 'modal', None))
                self.status_color = DANGER
        except Exception:
            msg = "Invalid input."
            self.modal = ModalPopup("Deposit Failed", msg, on_ok=lambda: setattr(self, 'modal', None))
            self.status_color = DANGER
        self.input_text = ""

    def draw(self, surface):
        surface.fill(BG_TOP)
        title_surface = self.title_font.render("Deposit to Savings", True, BLACK)
        surface.blit(title_surface, (40, 40))
        prompt_surface = self.text_font.render("Enter amount to deposit:", True, BLACK)
        surface.blit(prompt_surface, (40, 120))
        input_box = pygame.Rect(40, 170, 260, 48)
        pygame.draw.rect(surface, CARD_BG, input_box, border_radius=8)
        pygame.draw.rect(surface, CARD_BORDER, input_box, 2, border_radius=8)
        input_surface = self.text_font.render(self.input_text, True, BLACK)
        surface.blit(input_surface, (input_box.x + 10, input_box.y + 10))
        # If we have a modal, draw it centered and return early
        if getattr(self, 'modal', None):
            self.modal.draw(surface)
            return
        # Fallback inline status message
        if getattr(self, 'status_message', None):
            status_surface = self.text_font.render(self.status_message, True, self.status_color)
            surface.blit(status_surface, (40, 240))
        player = self.game.player
        savings_balance = getattr(getattr(player, 'savings_account', None), 'balance', 0.0)
        balance_surface = self.text_font.render(f"Savings Balance: ${savings_balance:.2f}", True, BLACK)
        surface.blit(balance_surface, (40, 320))

        try:
            bg_name = os.path.basename(_BANK_BACKGROUND_PATH) if isinstance(_BANK_BACKGROUND_PATH, str) else 'none'
            dbg_surf = self.debug_font.render(f"BG: {bg_name}", True, BLACK)
            dbg_rect = dbg_surf.get_rect(bottomright=(SCREEN_WIDTH - 8, SCREEN_HEIGHT - 8))
            box_rect = dbg_rect.inflate(8, 6)
            s = pygame.Surface(box_rect.size, pygame.SRCALPHA)
            s.fill((255, 255, 255, 180))
            surface.blit(s, box_rect.topleft)
            surface.blit(dbg_surf, dbg_rect.topleft)
        except Exception:
            pass
