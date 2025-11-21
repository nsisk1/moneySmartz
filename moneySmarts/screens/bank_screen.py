import pygame
from moneySmarts.constants import *
from moneySmarts.screens import GameScreen
from moneySmarts.ui import Screen, Button
from moneySmarts.screens.financial_screens import DepositScreen, WithdrawScreen, BankAccountScreen, SavingsDetailsScreen, BankDetailsScreen
import os
from moneySmarts.models import BankAccount  # added import


# noinspection PyCompatibility
class BankScreen(Screen):
    """
    Main bank screen with banking options and buttons.
    """
    play_startup_music = False
    def __init__(self, game):
        super().__init__(game)
        # Fonts
        try:
            font_path = os.path.join(ASSETS_DIR, 'fonts', 'pixelated_font.ttf')
            self.title_font = pygame.font.Font(font_path, 48)
            self.balance_font = pygame.font.Font(font_path, 28)
            self.text_font = pygame.font.Font(font_path, 24)
        except Exception:
            self.title_font = pygame.font.SysFont('Arial', 48, bold=True)
            self.balance_font = pygame.font.SysFont('Arial', 28, bold=True)
            self.text_font = pygame.font.SysFont('Arial', 24)
        self.buttons = []
        self.create_buttons()
        self.status_message = None
        self.status_color = WHITE

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
        start_y = 160
        self.buttons = []
        for i, (label, callback) in enumerate(button_specs):
            btn = Button(
                SCREEN_WIDTH - 260,
                start_y + i * 60,
                200,
                50,
                label,
                color=PRIMARY,
                hover_color=PRIMARY_HOVER,
                text_color=PRIMARY_TEXT,
                action=callback
            )
            self.buttons.append(btn)

    def go_to_deposit(self):
        self.game.gui_manager.set_screen(DepositScreen(self.game))

    def go_to_withdraw(self):
        self.game.gui_manager.set_screen(WithdrawScreen(self.game))

    def go_to_deposit_savings(self):
        self.game.gui_manager.set_screen(DepositToSavingsScreen(self.game))

    def go_to_view_balance(self):
        self.game.gui_manager.set_screen(BankDetailsScreen(self.game))

    def go_to_view_savings(self):
        self.game.gui_manager.set_screen(SavingsDetailsScreen(self.game))

    def go_to_open_account(self):
        self.game.gui_manager.set_screen(BankAccountScreen(self.game))

    def go_back(self):
        from moneySmarts.screens.game_screen import GameScreen
        self.game.gui_manager.set_screen(GameScreen(self.game))

    def handle_events(self, events):
        # Handle ESC to go back to the game screen
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.go_back()
                return
        super().handle_events(events)

    def draw(self, surface):
        # Background gradient via base draw for buttons too
        surface.fill(BG_TOP)
        # Header bar
        header_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 80)
        pygame.draw.rect(surface, PRIMARY, header_rect)
        title_surface = self.title_font.render("Bank", True, PRIMARY_TEXT)
        title_rect = title_surface.get_rect(midleft=(40, 40))
        surface.blit(title_surface, title_rect)
        # Left card with balances
        card_rect = pygame.Rect(40, 110, SCREEN_WIDTH - 320, SCREEN_HEIGHT - 160)
        pygame.draw.rect(surface, CARD_BG, card_rect, border_radius=12)
        pygame.draw.rect(surface, CARD_BORDER, card_rect, 2, border_radius=12)
        # Player balances
        player = self.game.player
        info_lines = [
            f"Cash: ${player.cash:.2f}",
            f"Checking: ${player.bank_account.balance:.2f}" if getattr(player, 'bank_account', None) else "Checking: $0.00",
            f"Savings: ${player.savings_account.balance:.2f}" if getattr(player, 'savings_account', None) else "Savings: $0.00"
        ]
        for i, line in enumerate(info_lines):
            text_surface = self.balance_font.render(line, True, BLACK)
            surface.blit(text_surface, (60, 140 + i * 36))
        # Status message
        if self.status_message:
            status_surface = self.title_font.render(self.status_message, True, self.status_color)
            surface.blit(status_surface, (60, 260))
        # Draw buttons (right side)
        for button in self.buttons:
            button.draw(surface)

class DepositToSavingsScreen(Screen):
    """
    Screen for depositing money into savings account and showing interest.
    """
    def __init__(self, game):
        super().__init__(game)
        try:
            font_path = os.path.join(ASSETS_DIR, 'fonts', 'pixelated_font.ttf')
            self.title_font = pygame.font.Font(font_path, 40)
            self.text_font = pygame.font.Font(font_path, 24)
        except Exception:
            self.title_font = pygame.font.SysFont('Arial', 40, bold=True)
            self.text_font = pygame.font.SysFont('Arial', 24)
        self.input_active = False
        self.input_text = ""
        self.status_message = None
        self.status_color = BLACK
        self.interest_rate = 0.02  # 2% interest for demonstration

    def handle_events(self, events):
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
                if not player.savings_account:
                    player.savings_account = BankAccount("Savings")
                    # Override default interest rate with screen's promotional rate
                    player.savings_account.interest_rate = self.interest_rate
                # Ensure interest rate matches this screen's rate (could be dynamic)
                player.savings_account.interest_rate = self.interest_rate
                player.savings_account.deposit(amount)
                # Apply interest immediately (one-time promotional interest on deposit)
                interest = player.savings_account.apply_interest()
                self.status_message = f"Deposited ${amount:.2f} (+${interest:.2f} interest)"
                self.status_color = SUCCESS
            else:
                self.status_message = "Invalid amount."
                self.status_color = DANGER
        except Exception:
            self.status_message = "Invalid input."
            self.status_color = DANGER
        self.input_text = ""

    def draw(self, surface):
        # Background
        surface.fill(BG_TOP)
        # Title
        title_surface = self.title_font.render("Deposit to Savings", True, BLACK)
        surface.blit(title_surface, (40, 40))
        # Prompt
        prompt_surface = self.text_font.render("Enter amount to deposit:", True, BLACK)
        surface.blit(prompt_surface, (40, 120))
        # Input box
        input_box = pygame.Rect(40, 170, 260, 48)
        pygame.draw.rect(surface, CARD_BG, input_box, border_radius=8)
        pygame.draw.rect(surface, CARD_BORDER, input_box, 2, border_radius=8)
        input_surface = self.text_font.render(self.input_text, True, BLACK)
        surface.blit(input_surface, (input_box.x + 10, input_box.y + 10))
        # Status
        if self.status_message:
            status_surface = self.text_font.render(self.status_message, True, self.status_color)
            surface.blit(status_surface, (40, 240))
        # Show current savings balance
        player = self.game.player
        savings_balance = getattr(getattr(player, 'savings_account', None), 'balance', 0.0)
        balance_surface = self.text_font.render(f"Savings Balance: ${savings_balance:.2f}", True, BLACK)
        surface.blit(balance_surface, (40, 320))
