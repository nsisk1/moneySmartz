from typing import NoReturn
import pygame
import random
from moneySmarts.constants import *
from moneySmarts.ui import Screen, Button, TextInput
from moneySmarts.models import BankAccount, Card
from moneySmarts.screens.screen_utils import load_ui_background, draw_background
from moneySmarts.ui_helpers import ModalPopup

class BankAccountScreen(Screen):
    """
    Screen for opening a bank account.
    """
    play_startup_music = False  # Disable music for this screen
    
    def __init__(self, game):
        super().__init__(game)
        print(f"[DEBUG] BankAccountScreen initialized. game: {game}, player: {getattr(game, 'player', None)}")

        # Title
        self.title_font = pygame.font.SysFont('Arial', FONT_LARGE)
        self.text_font = pygame.font.SysFont('Arial', FONT_MEDIUM)
        self._background_original = load_ui_background('BANK_SCREEN_BG')

        # Account type selection
        self.selected_account_type = "Checking"

        # Buttons
        checking_button = Button(
            SCREEN_WIDTH // 2 - 220,
            SCREEN_HEIGHT // 2 - 50,
            200, 50,
            "Checking Account",
            color=BLUE if self.selected_account_type == "Checking" else GRAY,
            action=self.select_checking
        )

        savings_button = Button(
            SCREEN_WIDTH // 2 + 20,
            SCREEN_HEIGHT // 2 - 50,
            200, 50,
            "Savings Account",
            color=BLUE if self.selected_account_type == "Savings" else GRAY,
            action=self.select_savings
        )

        open_button = Button(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT // 2 + 50,
            200, 50,
            "Open Account",
            action=self.open_account
        )

        back_button = Button(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT // 2 + 120,
            200, 50,
            "Back",
            action=self.go_back
        )

        self.buttons = [checking_button, savings_button, open_button, back_button]

        # Initial deposit input
        self.deposit_input = TextInput(
            SCREEN_WIDTH // 2 - 150,
            SCREEN_HEIGHT // 2 + 10,
            300, 30,
            font_size=FONT_MEDIUM,
            max_length=10,
            initial_text="50"
        )

    def select_checking(self):
        """Select checking account type."""
        self.selected_account_type = "Checking"
        self.buttons[0].color = BLUE
        self.buttons[1].color = GRAY

    def select_savings(self):
        """Select savings account type."""
        self.selected_account_type = "Savings"
        self.buttons[0].color = GRAY
        self.buttons[1].color = BLUE

    def open_account(self):
        """Open the selected account type."""
        try:
            deposit_amount = float(self.deposit_input.text)
            if deposit_amount <= 0:
                return  # Invalid amount
            if deposit_amount > self.game.player.cash:
                return  # Not enough cash

            # Create account
            if self.selected_account_type == "Checking":
                self.game.player.bank_account = BankAccount("Checking")
                self.game.player.cash -= deposit_amount
                self.game.player.bank_account.deposit(deposit_amount)
                from moneySmarts.screens.base_screens import DebitCardScreen
                self.game.gui_manager.set_screen(DebitCardScreen(self.game))
            else:
                self.game.player.savings_account = BankAccount("Savings")
                self.game.player.cash -= deposit_amount
                self.game.player.savings_account.deposit(deposit_amount)
                from moneySmarts.screens.game_screen import GameScreen
                self.game.gui_manager.set_screen(GameScreen(self.game))
        except ValueError:
            # Invalid input, do nothing
            pass

    def go_back(self):
        """Go back to the game screen."""
        from moneySmarts.screens.game_screen import GameScreen
        self.game.gui_manager.set_screen(GameScreen(self.game))

    def handle_events(self, events):
        """Handle pygame events."""
        super().handle_events(events)
        self.deposit_input.update(events)
        # Handle ESC key for back navigation
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.go_back()
                return

    def draw(self, surface):
        """Draw the bank account screen."""
        # Background
        draw_background(surface, self._background_original, default_color=WHITE)

        # Title
        title_surface = self.title_font.render("Open a Bank Account", True, BLACK)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 80))
        surface.blit(title_surface, title_rect)

        # Explanation text
        text_lines = [
            "You can open a checking account for everyday transactions",
            "or a savings account that earns interest.",
            "",
            f"Your current cash: ${self.game.player.cash:.2f}",
            "",
            "Initial deposit amount:"
        ]

        for i, line in enumerate(text_lines):
            text_surface = self.text_font.render(line, True, BLACK)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 150 + i * 30))
            surface.blit(text_surface, text_rect)

        # Draw deposit input
        self.deposit_input.draw(surface)

        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

class BankDetailsScreen(Screen):
    """
    Screen for viewing bank account details.
    """
    play_startup_music = False  # Disable music for this screen
    
    def __init__(self, game):
        super().__init__(game)

        # Title
        self.title_font = pygame.font.SysFont('Arial', FONT_LARGE)
        self.text_font = pygame.font.SysFont('Arial', FONT_MEDIUM)

        # Transaction history scroll
        self.scroll_position = 0
        self.max_visible_transactions = 10

        # Buttons
        back_button = Button(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT - 80,
            200, 50,
            "Back",
            action=self.go_back
        )

        scroll_up_button = Button(
            SCREEN_WIDTH - 80,
            150,
            60, 30,
            "▲",
            action=self.scroll_up
        )

        scroll_down_button = Button(
            SCREEN_WIDTH - 80,
            SCREEN_HEIGHT - 150,
            60, 30,
            "▼",
            action=self.scroll_down
        )

        self.buttons = [back_button, scroll_up_button, scroll_down_button]
        self._background_original = load_ui_background('BANK_SCREEN_BG')

    def scroll_up(self):
        """Scroll transaction history up."""
        if self.scroll_position > 0:
            self.scroll_position -= 1

    def scroll_down(self):
        """Scroll transaction history down."""
        if self.scroll_position < max(0, len(self.game.player.bank_account.transaction_history) - self.max_visible_transactions):
            self.scroll_position += 1

    def go_back(self):
        """Go back to the game screen."""
        from moneySmarts.screens.game_screen import GameScreen
        self.game.gui_manager.set_screen(GameScreen(self.game))

    def handle_events(self, events):
        """Handle pygame events for this screen."""
        super().handle_events(events)

    def draw(self, surface):
        """Draw the bank details screen."""
        # Background
        draw_background(surface, self._background_original, default_color=WHITE)

        # Title
        title_surface = self.title_font.render("Bank Account Details", True, BLACK)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 50))
        surface.blit(title_surface, title_rect)

        # Account info
        account_type = self.game.player.bank_account.account_type
        balance = self.game.player.bank_account.balance

        info_lines = [
            f"Account Type: {account_type}",
            f"Current Balance: ${balance:.2f}"
        ]

        if account_type == "Savings":
            interest_rate = self.game.player.bank_account.interest_rate * 100
            annual_interest = balance * self.game.player.bank_account.interest_rate
            info_lines.extend([
                f"Interest Rate: {interest_rate:.1f}% annually",
                f"Projected Annual Interest: ${annual_interest:.2f}"
            ])

        if self.game.player.debit_card:
            info_lines.append("You have a debit card linked to this account.")

        for i, line in enumerate(info_lines):
            text_surface = self.text_font.render(line, True, BLACK)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 100 + i * 30))
            surface.blit(text_surface, text_rect)

        # Transaction history
        history_title = self.title_font.render("Transaction History", True, BLACK)
        history_rect = history_title.get_rect(center=(SCREEN_WIDTH // 2, 250))
        surface.blit(history_title, history_rect)

        # Draw transaction list
        if self.game.player.bank_account.transaction_history:
            # Draw scrollable area background
            scroll_area = pygame.Rect(100, 280, SCREEN_WIDTH - 200, 300)
            pygame.draw.rect(surface, LIGHT_GRAY, scroll_area)
            pygame.draw.rect(surface, BLACK, scroll_area, 2)  # Border

            # Get visible transactions
            visible_transactions = self.game.player.bank_account.transaction_history[
                self.scroll_position:self.scroll_position + self.max_visible_transactions
            ]

            for i, transaction in enumerate(visible_transactions):
                if transaction["type"] == "deposit":
                    text = f"Deposit: +${transaction['amount']:.2f}"
                    color = GREEN
                elif transaction["type"] == "withdrawal":
                    text = f"Withdrawal: -${transaction['amount']:.2f}"
                    color = RED
                elif transaction["type"] == "interest":
                    text = f"Interest: +${transaction['amount']:.2f}"
                    color = BLUE
                else:
                    text = f"{transaction['type']}: ${transaction['amount']:.2f}"
                    color = BLACK

                text_surface = self.text_font.render(text, True, color)
                text_rect = text_surface.get_rect(midleft=(120, 300 + i * 30))
                surface.blit(text_surface, text_rect)
        else:
            no_transactions = self.text_font.render("No transactions yet.", True, BLACK)
            no_transactions_rect = no_transactions.get_rect(center=(SCREEN_WIDTH // 2, 320))
            surface.blit(no_transactions, no_transactions_rect)

        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

class DepositScreen(Screen):
    """
    Screen for depositing money to a bank account.
    """
    play_startup_music = False  # Disable music for this screen
    
    def __init__(self, game):
        super().__init__(game)

        # Title
        self.title_font = pygame.font.SysFont('Arial', FONT_LARGE)
        self.text_font = pygame.font.SysFont('Arial', FONT_MEDIUM)

        # Amount input
        self.amount_input = TextInput(
            SCREEN_WIDTH // 2 - 150,
            SCREEN_HEIGHT // 2,
            300, 40,
            font_size=FONT_MEDIUM,
            max_length=10
        )

        # Buttons
        deposit_button = Button(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT // 2 + 60,
            200, 50,
            "Deposit",
            action=self.make_deposit
        )

        back_button = Button(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT // 2 + 130,
            200, 50,
            "Back",
            action=self.go_back
        )

        self.buttons = [deposit_button, back_button]

        # Status message
        self.status_message = ""
        self.status_color = BLACK
        self._background_original = load_ui_background('FINANCIAL_BG')

    def make_deposit(self):
        """Make a deposit to the bank account."""
        try:
            amount = float(self.amount_input.text)
            if amount <= 0:
                from moneySmarts.ui_helpers import ModalPopup
                self.modal_popup = ModalPopup("Invalid Amount", "Please enter a positive amount.", on_ok=lambda: setattr(self, 'modal_popup', None))
                return

            if amount > self.game.player.cash:
                from moneySmarts.ui_helpers import ModalPopup
                self.modal_popup = ModalPopup("Insufficient Cash", "You don't have that much cash.", on_ok=lambda: setattr(self, 'modal_popup', None))
                return

            # Make deposit
            self.game.player.cash -= amount
            self.game.player.bank_account.deposit(amount)

            from moneySmarts.ui_helpers import ModalPopup
            self.modal_popup = ModalPopup("Deposit Successful", f"Successfully deposited ${amount:.2f}.", on_ok=lambda: setattr(self, 'modal_popup', None))
            # Clear input
            self.amount_input.text = ""
        except ValueError:
            from moneySmarts.ui_helpers import ModalPopup
            self.modal_popup = ModalPopup("Invalid Input", "Please enter a valid number.", on_ok=lambda: setattr(self, 'modal_popup', None))

    def go_back(self):
        """Go back to the game screen."""
        from moneySmarts.screens.game_screen import GameScreen
        self.game.gui_manager.set_screen(GameScreen(self.game))

    def handle_events(self, events):
        """Handle pygame events."""
        # If modal present, delegate to it first
        if getattr(self, 'modal_popup', None):
            try:
                handled = self.modal_popup.handle_events(events)
            except Exception:
                handled = False
            if handled:
                if getattr(self, 'modal_popup', None) is None:
                    self.status_message = ""
                return
        super().handle_events(events)
        self.amount_input.update(events)

    def draw(self, surface):
        # Background
        draw_background(surface, self._background_original, default_color=WHITE)

        # Title
        title_surface = self.title_font.render("Deposit to Bank", True, BLACK)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 80))
        surface.blit(title_surface, title_rect)

        # Info text
        info_lines = [
            f"Your current cash: ${self.game.player.cash:.2f}",
            f"Your current bank balance: ${self.game.player.bank_account.balance:.2f}",
            "",
            "How much would you like to deposit?"
        ]

        for i, line in enumerate(info_lines):
            text_surface = self.text_font.render(line, True, BLACK)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 150 + i * 30))
            surface.blit(text_surface, text_rect)

        # Draw amount input
        self.amount_input.draw(surface)

        # If a legacy status_message is present, show it as a modal for consistency
        if self.status_message:
            try:
                from moneySmarts.ui_helpers import ModalPopup
                self.modal_popup = ModalPopup("Notice", self.status_message, on_ok=lambda: setattr(self, 'modal_popup', None))
                self.status_message = ""
            except Exception:
                pass

        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

        # If modal present, draw it on top
        if getattr(self, 'modal_popup', None):
            try:
                self.modal_popup.draw(surface)
            except Exception:
                pass

class WithdrawScreen(Screen):
    """
    Screen for withdrawing money from a bank account.
    """
    play_startup_music = False  # Disable music for this screen
    
    def __init__(self, game):
        super().__init__(game)

        # Title
        self.title_font = pygame.font.SysFont('Arial', FONT_LARGE)
        self.text_font = pygame.font.SysFont('Arial', FONT_MEDIUM)

        # Amount input
        self.amount_input = TextInput(
            SCREEN_WIDTH // 2 - 150,
            SCREEN_HEIGHT // 2,
            300, 40,
            font_size=FONT_MEDIUM,
            max_length=10
        )

        # Buttons
        withdraw_button = Button(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT // 2 + 60,
            200, 50,
            "Withdraw",
            action=self.make_withdrawal
        )

        back_button = Button(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT // 2 + 130,
            200, 50,
            "Back",
            action=self.go_back
        )

        self.buttons = [withdraw_button, back_button]

        # Status message
        self.status_message = ""
        self.status_color = BLACK
        self._background_original = load_ui_background('FINANCIAL_BG')

    def make_withdrawal(self) -> None:
        """Make a withdrawal from the bank account."""
        global ModalPopup
        try:
            amount = float(self.amount_input.text)
            if amount <= 0:
                from moneySmarts.ui_helpers import ModalPopup
                self.modal_popup = ModalPopup("Invalid Amount", "Please enter a positive amount.", on_ok=lambda: setattr(self, 'modal_popup', None))
                return

            if amount > self.game.player.bank_account.balance:
                from moneySmarts.ui_helpers import ModalPopup
                self.modal_popup = ModalPopup("Insufficient Funds", "You don't have that much in your account.", on_ok=lambda: setattr(self, 'modal_popup', None))
                return

            # Make withdrawal
            self.game.player.bank_account.withdraw(amount)
            self.game.player.cash += amount

            # Success modal
            self.modal_popup = ModalPopup("Withdrawal Successful", f"Successfully withdrew ${amount:.2f}.", on_ok=lambda: setattr(self, 'modal_popup', None))
            # Clear input
            self.amount_input.text = ""
        except ValueError:
            from moneySmarts.ui_helpers import ModalPopup
            self.modal_popup = ModalPopup("Invalid Input", "Please enter a valid number.", on_ok=lambda: setattr(self, 'modal_popup', None))

    def go_back(self):
        """Go back to the game screen."""
        from moneySmarts.screens.game_screen import GameScreen
        self.game.gui_manager.set_screen(GameScreen(self.game))

    def handle_events(self, events):
        """Handle pygame events."""
        # If modal present, delegate to it first
        if getattr(self, 'modal_popup', None):
            try:
                handled = self.modal_popup.handle_events(events)
            except Exception:
                handled = False
            if handled:
                return
        super().handle_events(events)
        self.amount_input.update(events)

    def draw(self, surface):
        """Draw the withdraw screen."""
        # Background
        draw_background(surface, self._background_original, default_color=WHITE)

        # Title
        title_surface = self.title_font.render("Withdraw from Bank", True, BLACK)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 80))
        surface.blit(title_surface, title_rect)

        # Info text
        info_lines = [
            f"Your current cash: ${self.game.player.cash:.2f}",
            f"Your current bank balance: ${self.game.player.bank_account.balance:.2f}",
            "",
            "How much would you like to withdraw?"
        ]

        for i, line in enumerate(info_lines):
            text_surface = self.text_font.render(line, True, BLACK)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 150 + i * 30))
            surface.blit(text_surface, text_rect)

        # Draw amount input
        self.amount_input.draw(surface)

        # Convert any legacy status_message into a modal
        if self.status_message:
            try:
                from moneySmarts.ui_helpers import ModalPopup
                self.modal_popup = ModalPopup("Notice", self.status_message, on_ok=lambda: setattr(self, 'modal_popup', None))
                self.status_message = ""
            except Exception:
                pass

        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

        # If modal present, draw it on top
        if getattr(self, 'modal_popup', None):
            try:
                self.modal_popup.draw(surface)
            except Exception:
                pass

class GetDebitCardScreen(Screen):
    """
    Screen for getting a debit card.
    """
    play_startup_music = False  # Disable music for this screen
    
    def __init__(self, game):
        super().__init__(game)

        # Title
        self.title_font = pygame.font.SysFont('Arial', FONT_LARGE)
        self.text_font = pygame.font.SysFont('Arial', FONT_MEDIUM)

        # Buttons
        get_card_button = Button(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT // 2 + 50,
            200, 50,
            "Get Debit Card",
            action=self.get_debit_card
        )

        back_button = Button(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT // 2 + 120,
            200, 50,
            "Back",
            action=self.go_back
        )

        self.buttons = [get_card_button, back_button]
        self._background_original = load_ui_background('DEBIT_SCREEN_BG')

    def get_debit_card(self):
        """Get a debit card and go back to the game screen."""
        self.game.player.debit_card = Card("Debit")
        from moneySmarts.screens.game_screen import GameScreen
        self.game.gui_manager.set_screen(GameScreen(self.game))

    def go_back(self):
        """Go back to the game screen."""
        from moneySmarts.screens.game_screen import GameScreen
        self.game.gui_manager.set_screen(GameScreen(self.game))

    def draw(self, surface):
        """Draw the debit card screen."""
        # Background
        draw_background(surface, self._background_original, default_color=WHITE)

        # Title
        title_surface = self.title_font.render("Get a Debit Card", True, BLACK)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 80))
        surface.blit(title_surface, title_rect)

        # Card image (simple rectangle)
        card_rect = pygame.Rect(SCREEN_WIDTH // 2 - 125, 150, 250, 150)
        pygame.draw.rect(surface, BLUE, card_rect)
        pygame.draw.rect(surface, BLACK, card_rect, 2)  # Border

        # Card text
        card_title = self.text_font.render("DEBIT", True, WHITE)
        card_title_rect = card_title.get_rect(center=(SCREEN_WIDTH // 2, 180))
        surface.blit(card_title, card_title_rect)

        card_name = self.text_font.render(self.game.player.name, True, WHITE)
        card_name_rect = card_name.get_rect(center=(SCREEN_WIDTH // 2, 220))
        surface.blit(card_name, card_name_rect)

        card_number = self.text_font.render("**** **** **** 1234", True, WHITE)
        card_number_rect = card_number.get_rect(center=(SCREEN_WIDTH // 2, 260))
        surface.blit(card_number, card_number_rect)

        # Explanation text
        text_lines = [
            "A debit card allows you to make purchases directly from your checking account.",
            "There is no fee for this card.",
            "",
            "Would you like to get a debit card?"
        ]

        for i, line in enumerate(text_lines):
            text_surface = self.text_font.render(line, True, BLACK)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 350 + i * 30))
            surface.blit(text_surface, text_rect)

        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

class CreditCardScreen(Screen):
    """
    Screen for applying for a credit card.
    """
    play_startup_music = False  # Disable music for this screen
    
    def __init__(self, game):
        super().__init__(game)
        self._background_original = load_ui_background('FINANCIAL_BG')
        self.font = pygame.font.SysFont('Arial', FONT_MEDIUM)
        self.title_font = pygame.font.SysFont('Arial', FONT_LARGE, bold=True)
        self.small_font = pygame.font.SysFont('Arial', FONT_SMALL)
        self.message = ""
        self.message_color = BLACK
        self.approved = False
        self.credit_limit = 0

        # Create back button
        back_button = Button(
            SCREEN_WIDTH // 2 - 100, 
            SCREEN_HEIGHT - 70, 
            200, 50, 
            "Back", 
            action=self.go_back
        )

        self.buttons = [back_button]

        # Check eligibility and create apply button if eligible
        self.check_eligibility()

    def go_back(self):
        from moneySmarts.screens.game_screen import GameScreen
        self.game.gui_manager.set_screen(GameScreen(self.game))

    def check_eligibility(self):
        # Check if player exists and is eligible for a credit card
        if not self.game.player:
            self.message = "Game not started yet."
            self.message_color = RED
        elif self.game.player.age < 18:
            self.message = "You must be at least 18 years old to apply for a credit card."
            self.message_color = RED
        elif self.game.player.credit_card:
            self.message = "You already have a credit card."
            self.message_color = BLUE
        elif not self.game.player.job:
            self.message = "You need a job to qualify for a credit card."
            self.message_color = RED
        else:
            self.message = "You are eligible to apply for a credit card. Your approval and credit limit will be based on your income and credit score."
            self.message_color = GREEN

            # Add apply button
            apply_button = Button(
                SCREEN_WIDTH // 2 - 100,
                SCREEN_HEIGHT // 2,
                200, 50,
                "Apply Now",
                color=GREEN,
                hover_color=LIGHT_GREEN,
                action=self.apply_for_card
            )

            self.buttons.append(apply_button)

    def apply_for_card(self):
        # Calculate credit limit based on income and credit score
        base_limit = min(self.game.player.salary * 0.2, 5000)  # 20% of salary or $5000, whichever is lower

        # Adjust based on credit score
        if self.game.player.credit_score >= 750:
            self.credit_limit = base_limit * 1.5
        elif self.game.player.credit_score >= 700:
            self.credit_limit = base_limit * 1.2
        elif self.game.player.credit_score >= 650:
            self.credit_limit = base_limit
        elif self.game.player.credit_score >= 600:
            self.credit_limit = base_limit * 0.8
        else:
            self.credit_limit = base_limit * 0.5

        # Approve the card
        self.game.player.credit_card = Card("Credit", self.credit_limit)
        self.approved = True

        # Update message
        self.message = f"Congratulations! You've been approved for a credit card with a limit of ${self.credit_limit:.2f}. Use your credit card wisely to build your credit score."
        self.message_color = GREEN

        # Remove apply button
        self.buttons = [self.buttons[0]]  # Keep only the back button

        # Add view details button
        details_button = Button(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT // 2,
            200, 50,
            "View Card Details",
            action=self.view_card_details
        )

        self.buttons.append(details_button)

    def view_card_details(self):
        # CreditCardDetailsScreen is defined in this module
        self.game.gui_manager.set_screen(CreditCardDetailsScreen(self.game))

    def draw(self, surface):
        surface.fill(WHITE)

        # Draw header
        header_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 80)
        pygame.draw.rect(surface, PURPLE, header_rect)

        header_text = self.title_font.render("CREDIT CARD APPLICATION", True, WHITE)
        header_rect = header_text.get_rect(center=(SCREEN_WIDTH // 2, 40))
        surface.blit(header_text, header_rect)

        # Draw player info
        info_y = 100
        
        # Check if player exists before accessing attributes
        if self.game.player:
            credit_score_text = self.font.render(f"Your Credit Score: {self.game.player.credit_score}", True, BLACK)
            surface.blit(credit_score_text, (50, info_y))

            if self.game.player.job:
                income_text = self.font.render(f"Annual Income: ${self.game.player.salary}", True, BLACK)
                surface.blit(income_text, (50, info_y + 30))

        # Draw message
        message_lines = []
        words = self.message.split()
        current_line = []

        for word in words:
            current_line.append(word)
            if len(' '.join(current_line)) > 60:  # Adjust based on font size
                message_lines.append(' '.join(current_line[:-1]))
                current_line = [current_line[-1]]

        if current_line:
            message_lines.append(' '.join(current_line))

        for i, line in enumerate(message_lines):
            message_text = self.font.render(line, True, self.message_color)
            message_rect = message_text.get_rect(center=(SCREEN_WIDTH // 2, 180 + i * 30))
            surface.blit(message_text, message_rect)

        # If approved, draw the credit card
        if self.approved:
            card_rect = pygame.Rect(SCREEN_WIDTH // 2 - 125, 250, 250, 150)
            pygame.draw.rect(surface, PURPLE, card_rect)
            pygame.draw.rect(surface, BLACK, card_rect, 2)  # Border

            # Card text
            card_title = self.font.render("CREDIT CARD", True, WHITE)
            card_title_rect = card_title.get_rect(center=(SCREEN_WIDTH // 2, 280))
            surface.blit(card_title, card_title_rect)

            card_name = self.font.render(self.game.player.name, True, WHITE)
            card_name_rect = card_name.get_rect(center=(SCREEN_WIDTH // 2, 320))
            surface.blit(card_name, card_name_rect)

            card_number = self.font.render("**** **** **** 1234", True, WHITE)
            card_number_rect = card_number.get_rect(center=(SCREEN_WIDTH // 2, 350))
            surface.blit(card_number, card_number_rect)

            limit_text = self.small_font.render(f"Credit Limit: ${self.credit_limit:.2f}", True, WHITE)
            limit_rect = limit_text.get_rect(center=(SCREEN_WIDTH // 2, 380))
            surface.blit(limit_text, limit_rect)

        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

class CreditCardDetailsScreen(Screen):
    """
    Screen for viewing credit card details.
    """
    play_startup_music = False  # Disable music for this screen
    
    def __init__(self, game):
        super().__init__(game)
        
        # Title and fonts
        self.title_font = pygame.font.SysFont('Arial', FONT_LARGE)
        self.text_font = pygame.font.SysFont('Arial', FONT_MEDIUM)
        self.small_font = pygame.font.SysFont('Arial', FONT_SMALL)
        
        # Transaction history scroll
        self.scroll_position = 0
        self.max_visible_transactions = 8
        
        # Buttons
        back_button = Button(
            SCREEN_WIDTH // 2 - 220, 
            SCREEN_HEIGHT - 80, 
            200, 50, 
            "Back", 
            action=self.go_back
        )
        
        pay_button = Button(
            SCREEN_WIDTH // 2 + 20, 
            SCREEN_HEIGHT - 80, 
            200, 50, 
            "Make Payment", 
            action=self.make_payment
        )
        
        scroll_up_button = Button(
            SCREEN_WIDTH - 80, 
            200, 
            60, 30, 
            "▲", 
            action=self.scroll_up
        )
        
        scroll_down_button = Button(
            SCREEN_WIDTH - 80, 
            SCREEN_HEIGHT - 200, 
            60, 30, 
            "▼", 
            action=self.scroll_down
        )
        
        self.buttons = [back_button, pay_button, scroll_up_button, scroll_down_button]
        self._background_original = load_ui_background('FINANCIAL_BG')

    def scroll_up(self):
        """Scroll transaction history up."""
        if self.scroll_position > 0:
            self.scroll_position -= 1

    def scroll_down(self):
        """Scroll transaction history down."""
        if self.game.player and self.game.player.credit_card:
            if self.scroll_position < max(0, len(self.game.player.credit_card.transaction_history) - self.max_visible_transactions):
                self.scroll_position += 1

    def make_payment(self):
        """Navigate to the payment screen."""
        self.game.gui_manager.set_screen(PayCreditCardScreen(self.game))

    def go_back(self):
        from moneySmarts.screens.game_screen import GameScreen
        self.game.gui_manager.set_screen(GameScreen(self.game))

    def draw(self, surface):
        surface.fill(WHITE)
        
        # Title
        title_surface = self.title_font.render("Credit Card Details", True, BLACK)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 50))
        surface.blit(title_surface, title_rect)
        
        # Check if player exists and has been initialized
        if not self.game.player:
            no_player_text = self.text_font.render("Game not started yet.", True, BLACK)
            no_player_rect = no_player_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(no_player_text, no_player_rect)
            return
        
        # Check if player has a credit card
        if not self.game.player.credit_card:
            no_card_text = self.text_font.render("You don't have a credit card yet.", True, BLACK)
            no_card_rect = no_card_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(no_card_text, no_card_rect)
            return
        
        # Credit card visual
        card_rect = pygame.Rect(50, 100, 300, 180)
        pygame.draw.rect(surface, PURPLE, card_rect)
        pygame.draw.rect(surface, BLACK, card_rect, 2)  # Border
        
        # Card text
        card_title = self.text_font.render("CREDIT CARD", True, WHITE)
        card_title_rect = card_title.get_rect(center=(card_rect.centerx, card_rect.top + 30))
        surface.blit(card_title, card_title_rect)
        
        card_name = self.text_font.render(self.game.player.name, True, WHITE)
        card_name_rect = card_name.get_rect(center=(card_rect.centerx, card_rect.top + 80))
        surface.blit(card_name, card_name_rect)
        
        card_number = self.text_font.render("**** **** **** 1234", True, WHITE)
        card_number_rect = card_number.get_rect(center=(card_rect.centerx, card_rect.top + 120))
        surface.blit(card_number, card_number_rect)
        
        limit_text = self.small_font.render(f"Credit Limit: ${self.game.player.credit_card.limit:.2f}", True, WHITE)
        limit_rect = limit_text.get_rect(center=(card_rect.centerx, card_rect.top + 150))
        surface.blit(limit_text, limit_rect)

        # Account information
        info_x = 380
        info_y = 120
        
        info_lines = [
            f"Credit Limit: ${self.game.player.credit_card.limit:.2f}",
            f"Current Balance: ${self.game.player.credit_card.balance:.2f}",
            f"Available Credit: ${self.game.player.credit_card.limit - self.game.player.credit_card.balance:.2f}"
        ]
        
        # Add minimum payment if there's a balance
        if self.game.player.credit_card.balance > 0:
            min_payment = max(25, self.game.player.credit_card.balance * 0.03)
            info_lines.append(f"Minimum Payment: ${min_payment:.2f}")
        
        for i, line in enumerate(info_lines):
            color = RED if "Balance:" in line and self.game.player.credit_card.balance > 0 else BLACK
            text_surface = self.text_font.render(line, True, color)
            surface.blit(text_surface, (info_x, info_y + i * 35))
        
        # Transaction history
        history_title = self.text_font.render("Transaction History:", True, BLACK)
        surface.blit(history_title, (50, 300))
        
        # Transaction history area
        history_rect = pygame.Rect(50, 330, SCREEN_WIDTH - 150, 250)
        pygame.draw.rect(surface, LIGHT_GRAY, history_rect)
        pygame.draw.rect(surface, BLACK, history_rect, 2)
        
        # Display transactions
        if self.game.player.credit_card.transaction_history:
            visible_transactions = self.game.player.credit_card.transaction_history[
                self.scroll_position:self.scroll_position + self.max_visible_transactions
            ]
            
            for i, transaction in enumerate(visible_transactions):
                y_pos = 345 + i * 30
                if transaction["type"] == "charge":
                    text = f"Charge: ${transaction['amount']:.2f}"
                    color = RED
                elif transaction["type"] == "payment":
                    text = f"Payment: -${transaction['amount']:.2f}"
                    color = GREEN
                else:
                    text = f"{transaction['type']}: ${transaction['amount']:.2f}"
                    color = BLACK
                
                text_surface = self.small_font.render(text, True, color)
                surface.blit(text_surface, (60, y_pos))
        else:
            no_transactions = self.text_font.render("No transactions yet.", True, BLACK)
            no_transactions_rect = no_transactions.get_rect(center=(history_rect.centerx, history_rect.centery))
            surface.blit(no_transactions, no_transactions_rect)
        
        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

class PayCreditCardScreen(Screen):
    """
    Screen for paying a credit card.
    """
    play_startup_music = False  # Disable music for this screen
    
    def __init__(self, game):
        super().__init__(game)
        
        # Title and fonts
        self.title_font = pygame.font.SysFont('Arial', FONT_LARGE)
        self.text_font = pygame.font.SysFont('Arial', FONT_MEDIUM)
        
        # Calculate minimum payment (with null checks)
        if self.game.player and self.game.player.credit_card:
            self.min_payment = max(25, self.game.player.credit_card.balance * 0.03)
        else:
            self.min_payment = 25  # Default minimum payment
        
        # Amount input
        self.amount_input = TextInput(
            SCREEN_WIDTH // 2 - 150,
            SCREEN_HEIGHT // 2 + 50,
            300, 40,
            font_size=FONT_MEDIUM,
            max_length=10
        )
        
        # Buttons
        min_payment_button = Button(
            SCREEN_WIDTH // 2 - 320,
            SCREEN_HEIGHT // 2 - 20,
            200, 50,
            f"Pay Minimum (${self.min_payment:.2f})",
            color=BLUE,
            hover_color=LIGHT_BLUE,
            action=self.pay_minimum
        )
        
        # Calculate button text with null checks
        if self.game.player and self.game.player.credit_card:
            full_payment_text = f"Pay Full (${self.game.player.credit_card.balance:.2f})"
        else:
            full_payment_text = "Pay Full (N/A)"
        
        full_payment_button = Button(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT // 2 - 20,
            200, 50,
            full_payment_text,
            color=GREEN,
            hover_color=LIGHT_GREEN,
            action=self.pay_full
        )
        
        custom_payment_button = Button(
            SCREEN_WIDTH // 2 + 120,
            SCREEN_HEIGHT // 2 - 20,
            200, 50,
            "Pay Custom Amount",
            action=self.pay_custom
        )
        
        back_button = Button(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT - 80,
            200, 50,
            "Back",
            action=self.go_back
        )
        
        self.buttons = [min_payment_button, full_payment_button, custom_payment_button, back_button]

    def pay_minimum(self):
        """Pay the minimum payment amount."""
        self.make_payment(self.min_payment)

    def pay_full(self):
        """Pay the full balance."""
        self.make_payment(self.game.player.credit_card.balance)

    def pay_custom(self):
        """Pay a custom amount from the input field."""
        try:
            amount = float(self.amount_input.text)
            if amount <= 0:
                from moneySmarts.ui_helpers import ModalPopup
                self.modal_popup = ModalPopup("Invalid Amount", "Please enter a positive amount.", on_ok=lambda: setattr(self, 'modal_popup', None))
                return
            if amount < self.min_payment:
                from moneySmarts.ui_helpers import ModalPopup
                self.modal_popup = ModalPopup(f"Payment must be at least ${self.min_payment:.2f}.", on_ok=lambda: setattr(self, 'modal_popup', None))
                return
            if amount > self.game.player.credit_card.balance:
                from moneySmarts.ui_helpers import ModalPopup
                self.modal_popup = ModalPopup(f"Payment cannot exceed balance of ${self.game.player.credit_card.balance:.2f}.", on_ok=lambda: setattr(self, 'modal_popup', None))
                return
            
            self.make_payment(amount)
            self.amount_input.text = ""  # Clear input after successful payment
        except ValueError:
            from moneySmarts.ui_helpers import ModalPopup
            self.modal_popup = ModalPopup("Invalid Input", "Please enter a valid number.", on_ok=lambda: setattr(self, 'modal_popup', None))

    def make_payment(self, amount):
        """Make a payment using available funds."""
        # Try to pay from cash first
        if self.game.player.cash >= amount:
            self.game.player.cash -= amount
            self.game.player.credit_card.pay(amount)

            # Update credit score for on-time payment
            self.game.player.credit_score += 2
            
            from moneySmarts.ui_helpers import ModalPopup
            self.modal_popup = ModalPopup("Payment Successful", f"Payment of ${amount:.2f} made successfully from cash.", on_ok=lambda: setattr(self, 'modal_popup', None))

        # Try to pay from bank account
        elif self.game.player.bank_account and self.game.player.bank_account.balance >= amount:
            self.game.player.bank_account.withdraw(amount)
            self.game.player.credit_card.pay(amount)

            # Update credit score for on-time payment
            self.game.player.credit_score += 2
            
            from moneySmarts.ui_helpers import ModalPopup
            self.modal_popup = ModalPopup("Payment Successful", f"Payment of ${amount:.2f} made successfully from bank account.", on_ok=lambda: setattr(self, 'modal_popup', None))

        else:
            available_funds = self.game.player.cash
            if self.game.player.bank_account:
                available_funds += self.game.player.bank_account.balance
            
            from moneySmarts.ui_helpers import ModalPopup
            self.modal_popup = ModalPopup("Insufficient Funds", f"Insufficient funds. You have ${available_funds:.2f} available.", on_ok=lambda: setattr(self, 'modal_popup', None))

    def go_back(self):
        # CreditCardDetailsScreen is defined in this module
        self.game.gui_manager.set_screen(CreditCardDetailsScreen(self.game))

    def handle_events(self, events):
        """Handle pygame events."""
        # If modal present, delegate first
        if getattr(self, 'modal_popup', None):
            try:
                handled = self.modal_popup.handle_events(events)
            except Exception:
                handled = False
            if handled:
                return
        super().handle_events(events)
        self.amount_input.update(events)

    def draw(self, surface):
        surface.fill(WHITE)
        
        # Title
        title_surface = self.title_font.render("Pay Credit Card", True, BLACK)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 50))
        surface.blit(title_surface, title_rect)
        
        # Check if player exists and has credit card
        if not self.game.player:
            no_player_text = self.text_font.render("Game not started yet.", True, BLACK)
            no_player_rect = no_player_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(no_player_text, no_player_rect)
            return
        
        if not self.game.player.credit_card:
            no_card_text = self.text_font.render("You don't have a credit card yet.", True, BLACK)
            no_card_rect = no_card_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(no_card_text, no_card_rect)
            return
        
        # Current balance info
        balance_info = [
            f"Current Balance: ${self.game.player.credit_card.balance:.2f}",
            f"Credit Limit: ${self.game.player.credit_card.limit:.2f}",
            f"Minimum Payment: ${self.min_payment:.2f}",
            "",
            f"Available Cash: ${self.game.player.cash:.2f}"
        ]
        
        if self.game.player.bank_account:
            balance_info.append(f"Bank Balance: ${self.game.player.bank_account.balance:.2f}")
        
        for i, line in enumerate(balance_info):
            if line:  # Skip empty lines
                color = RED if "Current Balance:" in line else BLACK
                text_surface = self.text_font.render(line, True, color)
                text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 100 + i * 30))
                surface.blit(text_surface, text_rect)
        
        # Custom amount input label
        custom_label = self.text_font.render("Custom Amount:", True, BLACK)
        custom_label_rect = custom_label.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        surface.blit(custom_label, custom_label_rect)
        
        # Draw amount input
        self.amount_input.draw(surface)

        # If a legacy status_message exists, convert it into a modal
        if self.status_message:
            try:
                from moneySmarts.ui_helpers import ModalPopup
                self.modal_popup = ModalPopup("Notice", self.status_message, on_ok=lambda: setattr(self, 'modal_popup', None))
                self.status_message = ""
            except Exception:
                pass

        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

        # If modal present, draw it on top
        if getattr(self, 'modal_popup', None):
            try:
                self.modal_popup.draw(surface)
            except Exception:
                pass

class LoanDetailsScreen(Screen):
    """
    Screen for viewing loan details.
    """
    play_startup_music = False  # Disable music for this screen
    
    def __init__(self, game):
        super().__init__(game)
        
        # Title and fonts
        self.title_font = pygame.font.SysFont('Arial', FONT_LARGE)
        self.text_font = pygame.font.SysFont('Arial', FONT_MEDIUM)
        self.small_font = pygame.font.SysFont('Arial', FONT_SMALL)
        
        # Buttons
        back_button = Button(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT - 80,
            200, 50,
            "Back",
            action=self.go_back
        )
        
        extra_payment_button = Button(
            SCREEN_WIDTH // 2 + 20,
            SCREEN_HEIGHT - 80,
            200, 50,
            "Make Extra Payment",
            action=self.make_extra_payment
        )
        
        self.buttons = [back_button, extra_payment_button]
        self._background_original = load_ui_background('FINANCIAL_BG')

    def make_extra_payment(self):
        """Navigate to the extra payment screen."""
        self.game.gui_manager.set_screen(ExtraLoanPaymentScreen(self.game))

    def go_back(self):
        from moneySmarts.screens.game_screen import GameScreen
        self.game.gui_manager.set_screen(GameScreen(self.game))

    def draw(self, surface):
        surface.fill(WHITE)
        
        # Title
        title_surface = self.title_font.render("Loan Details", True, BLACK)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 50))
        surface.blit(title_surface, title_rect)
        
        # Check if player exists and has been initialized
        if not self.game.player:
            no_player_text = self.text_font.render("Game not started yet.", True, BLACK)
            no_player_rect = no_player_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(no_player_text, no_player_rect)
            return
        
        if not self.game.player.loans:
            no_loans_text = self.text_font.render("You don't have any loans.", True, BLACK)
            no_loans_rect = no_loans_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(no_loans_text, no_loans_rect)
        else:
            # Display loan information
            y_pos = 120
            total_monthly_payment = 0
            total_remaining_balance = 0
            
            for i, loan in enumerate(self.game.player.loans):
                # Loan header
                loan_header = self.text_font.render(f"{loan.loan_type} #{i+1}", True, BLUE)
                surface.blit(loan_header, (50, y_pos))
                y_pos += 40
                
                # Loan details
                loan_details = [
                    f"Original Amount: ${loan.original_amount:.2f}",
                    f"Current Balance: ${loan.current_balance:.2f}",
                    f"Interest Rate: {loan.interest_rate * 100:.1f}%",
                    f"Monthly Payment: ${loan.monthly_payment:.2f}",
                    f"Term: {loan.term_years} years"
                ]
                
                # Calculate remaining time
                if loan.monthly_payment > 0:
                    remaining_months = loan.current_balance / (loan.monthly_payment - (loan.current_balance * loan.interest_rate / 12))
                    remaining_years = remaining_months / 12
                    loan_details.append(f"Time Remaining: {remaining_years:.1f} years")
                    # Calculate total interest if paid normally
                    total_interest = (loan.monthly_payment * remaining_months) - loan.current_balance
                    loan_details.append(f"Remaining Interest: ${total_interest:.2f}")
                else:
                    loan_details.append("Time Remaining: N/A")
                    loan_details.append("Remaining Interest: N/A")

                for detail in loan_details:
                    color = RED if "Current Balance:" in detail else BLACK
                    detail_surface = self.small_font.render(detail, True, color)
                    surface.blit(detail_surface, (80, y_pos))
                    y_pos += 25
                
                y_pos += 20  # Space between loans
                total_monthly_payment += loan.monthly_payment
                total_remaining_balance += loan.current_balance
            
            # Summary section
            summary_y = SCREEN_HEIGHT - 200
            summary_title = self.text_font.render("Summary", True, BLUE)
            surface.blit(summary_title, (50, summary_y))
            
            summary_details = [
                f"Total Monthly Payments: ${total_monthly_payment:.2f}",
                f"Total Remaining Balance: ${total_remaining_balance:.2f}"
            ]
            
            for i, detail in enumerate(summary_details):
                color = RED if total_remaining_balance > 0 else BLACK
                detail_surface = self.text_font.render(detail, True, color)
                surface.blit(detail_surface, (50, summary_y + 30 + i * 25))
        
        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

class ExtraLoanPaymentScreen(Screen):
    """
    Screen for making an extra loan payment.
    """
    play_startup_music = False  # Disable music for this screen
    
    def __init__(self, game):
        super().__init__(game)
        
        # Title and fonts
        self.title_font = pygame.font.SysFont('Arial', FONT_LARGE)
        self.text_font = pygame.font.SysFont('Arial', FONT_MEDIUM)
        
        # Selected loan index
        self.selected_loan_index = 0
        
        # Amount input
        self.amount_input = TextInput(
            SCREEN_WIDTH // 2 - 150,
            SCREEN_HEIGHT // 2 + 100,
            300, 40,
            font_size=FONT_MEDIUM,
            max_length=10
        )
        
        # Status message
        self.status_message = ""
        self.status_color = BLACK
        
        # Create buttons
        self.create_buttons()

    def create_buttons(self):
        """Create buttons for loan selection and payment."""
        self.buttons = []
        
        # Check if player exists and has loans
        if not self.game.player or not self.game.player.loans:
            # Just create back button
            back_button = Button(
                SCREEN_WIDTH // 2 - 100,
                SCREEN_HEIGHT - 80,
                200, 50,
                "Back",
                action=self.go_back
            )
            self.buttons.append(back_button)
            return
        
        # Loan selection buttons
        if len(self.game.player.loans) > 1:
            for i, loan in enumerate(self.game.player.loans):
                color = BLUE if i == self.selected_loan_index else GRAY
                loan_button = Button(
                    50 + i * 200,
                    200,
                    180, 50,
                    f"{loan.loan_type[:12]}...",
                    color=color,
                    action=lambda idx=i: self.select_loan(idx)
                )
                self.buttons.append(loan_button)
        
        # Payment button
        pay_button = Button(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT // 2 + 160,
            200, 50,
            "Make Payment",
            action=self.make_payment
        )
        self.buttons.append(pay_button)
        
        # Back button
        back_button = Button(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT - 80,
            200, 50,
            "Back",
            action=self.go_back
        )
        self.buttons.append(back_button)
        self._background_original = load_ui_background('FINANCIAL_BG')

    def select_loan(self, index):
        """Select a loan for payment."""
        self.selected_loan_index = index
        self.create_buttons()  # Refresh buttons to show selection

    def make_payment(self):
        """Make an extra payment on the selected loan."""
        from moneySmarts.ui_helpers import ModalPopup
        if not self.game.player.loans:
            self.modal_popup = ModalPopup("No Loans", "You don't have any loans.", on_ok=lambda: setattr(self, 'modal_popup', None))
            return
        
        try:
            amount = float(self.amount_input.text)
            if amount <= 0:
                self.modal_popup = ModalPopup("Invalid Amount", "Please enter a positive amount.", on_ok=lambda: setattr(self, 'modal_popup', None))
                return
            
            selected_loan = self.game.player.loans[self.selected_loan_index]
            
            if amount > selected_loan.current_balance:
                self.modal_popup = ModalPopup("Invalid Amount", f"Payment cannot exceed loan balance of ${selected_loan.current_balance:.2f}.", on_ok=lambda: setattr(self, 'modal_popup', None))
                return
            
            # Try to pay from cash first
            if self.game.player.cash >= amount:
                self.game.player.cash -= amount
                selected_loan.make_payment(amount)
                self.modal_popup = ModalPopup("Payment Successful", f"Payment of ${amount:.2f} made successfully from cash.", on_ok=lambda: setattr(self, 'modal_popup', None))

                # Check if loan is paid off
                if selected_loan.current_balance <= 0:
                    self.game.player.loans.remove(selected_loan)
                    self.modal_popup = ModalPopup("Loan Paid Off", "Congratulations! You've paid off the loan.", on_ok=lambda: setattr(self, 'modal_popup', None))
                    self.game.player.credit_score += 10  # Credit score boost for paying off loan
                
            # Try to pay from bank account
            elif self.game.player.bank_account and self.game.player.bank_account.balance >= amount:
                self.game.player.bank_account.withdraw(amount)
                selected_loan.make_payment(amount)
                self.modal_popup = ModalPopup("Payment Successful", f"Payment of ${amount:.2f} made successfully from bank account.", on_ok=lambda: setattr(self, 'modal_popup', None))

                # Check if loan is paid off
                if selected_loan.current_balance <= 0:
                    self.game.player.loans.remove(selected_loan)
                    self.modal_popup = ModalPopup("Loan Paid Off", "Congratulations! You've paid off the loan.", on_ok=lambda: setattr(self, 'modal_popup', None))
                    self.game.player.credit_score += 10  # Credit score boost for paying off loan
                
            else:
                available_funds = self.game.player.cash
                if self.game.player.bank_account:
                    available_funds += self.game.player.bank_account.balance

                self.modal_popup = ModalPopup("Insufficient Funds", f"Insufficient funds. You have ${available_funds:.2f} available.", on_ok=lambda: setattr(self, 'modal_popup', None))

            # Clear input after successful payment only if modal created
            if getattr(self, 'modal_popup', None):
                self.amount_input.text = ""
                
        except ValueError:
            self.modal_popup = ModalPopup("Invalid Input", "Please enter a valid number.", on_ok=lambda: setattr(self, 'modal_popup', None))

    def go_back(self):
        # LoanDetailsScreen is defined in this module
        self.game.gui_manager.set_screen(LoanDetailsScreen(self.game))

    def handle_events(self, events):
        """Handle pygame events."""
        super().handle_events(events)
        self.amount_input.update(events)

    def draw(self, surface):
        surface.fill(WHITE)
        
        # Title
        title_surface = self.title_font.render("Make Extra Loan Payment", True, BLACK)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 50))
        surface.blit(title_surface, title_rect)
        
        # Check if player exists
        if not self.game.player:
            no_player_text = self.text_font.render("Game not started yet.", True, BLACK)
            no_player_rect = no_player_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(no_player_text, no_player_rect)
            return
        
        if not self.game.player.loans:
            no_loans_text = self.text_font.render("You don't have any loans.", True, BLACK)
            no_loans_rect = no_loans_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(no_loans_text, no_loans_rect)
        else:
            # Loan selection instruction
            if len(self.game.player.loans) > 1:
                instruction_text = self.text_font.render("Select the loan you want to pay:", True, BLACK)
                instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, 120))
                surface.blit(instruction_text, instruction_rect)
            
            # Selected loan details
            selected_loan = self.game.player.loans[self.selected_loan_index]
            
            loan_info = [
                f"Selected Loan: {selected_loan.loan_type}",
                f"Current Balance: ${selected_loan.current_balance:.2f}",
                f"Monthly Payment: ${selected_loan.monthly_payment:.2f}",
                f"Interest Rate: {selected_loan.interest_rate * 100:.1f}%",
                "",
                f"Available Cash: ${self.game.player.cash:.2f}"
            ]
            
            if self.game.player.bank_account:
                loan_info.append(f"Bank Balance: ${self.game.player.bank_account.balance:.2f}")
            
            for i, line in enumerate(loan_info):
                if line:  # Skip empty lines
                    color = RED if "Current Balance:" in line else BLACK
                    text_surface = self.text_font.render(line, True, color)
                    text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 280 + i * 30))
                    surface.blit(text_surface, text_rect)
            
            # Payment amount input label
            payment_label = self.text_font.render("Extra Payment Amount:", True, BLACK)
            payment_label_rect = payment_label.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 70))
            surface.blit(payment_label, payment_label_rect)
            
            # Draw amount input
            self.amount_input.draw(surface)
            
            # Benefit calculation
            if self.amount_input.text:
                try:
                    extra_payment = float(self.amount_input.text)
                    if extra_payment > 0 and extra_payment <= selected_loan.current_balance:
                        # Calculate interest saved
                        monthly_interest = selected_loan.interest_rate / 12
                        interest_saved = extra_payment * monthly_interest
                        
                        benefit_text = f"Interest saved this month: ${interest_saved:.2f}"
                        benefit_surface = self.text_font.render(benefit_text, True, GREEN)
                        benefit_rect = benefit_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 130))
                        surface.blit(benefit_surface, benefit_rect)
                except ValueError:
                    pass
        
        # Status message
        if self.status_message:
            # Split long messages into multiple lines
            words = self.status_message.split()
            lines = []
            current_line = []

            for word in words:
                current_line.append(word)
                if len(' '.join(current_line)) > 50:  # Adjust based on your font size
                    lines.append(' '.join(current_line[:-1]))
                    current_line = [current_line[-1]]

            if current_line:
                lines.append(' '.join(current_line))

            for i, line in enumerate(lines):
                status_surface = self.text_font.render(line, True, self.status_color)
                status_rect = status_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150 + i * 30))
                surface.blit(status_surface, status_rect)

        # If modal present, draw it on top
        if getattr(self, 'modal_popup', None):
            try:
                self.modal_popup.draw(surface)
            except Exception:
                pass

        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

class AssetDetailsScreen(Screen):
    """
    Screen for viewing asset details.
    """
    play_startup_music = False  # Disable music for this screen
    
    def __init__(self, game):
        super().__init__(game)
        
        # Title and fonts
        self.title_font = pygame.font.SysFont('Arial', FONT_LARGE)
        self.text_font = pygame.font.SysFont('Arial', FONT_MEDIUM)
        self.small_font = pygame.font.SysFont('Arial', FONT_SMALL)
        
        # Buttons
        back_button = Button(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT - 80,
            200, 50,
            "Back",
            action=self.go_back
        )
        
        self.buttons = [back_button]
        self._background_original = load_ui_background('FINANCIAL_BG')

    def go_back(self):
        from moneySmarts.screens.game_screen import GameScreen
        self.game.gui_manager.set_screen(GameScreen(self.game))

    def draw(self, surface):
        surface.fill(WHITE)
        
        # Title
        title_surface = self.title_font.render("Asset Details", True, BLACK)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 50))
        surface.blit(title_surface, title_rect)
        
        # Check if player exists and has been initialized
        if not self.game.player:
            no_player_text = self.text_font.render("Game not started yet.", True, BLACK)
            no_player_rect = no_player_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(no_player_text, no_player_rect)
            return
        
        if not self.game.player.assets:
            no_assets_text = self.text_font.render("You don't have any assets yet.", True, BLACK)
            no_assets_rect = no_assets_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(no_assets_text, no_assets_rect)
        else:
            # Display asset information
            y_pos = 120
            total_current_value = 0
            total_purchase_value = 0
            
            for i, asset in enumerate(self.game.player.assets):
                # Asset header with icon
                asset_header = self.text_font.render(f"{asset.asset_type}: {asset.name}", True, BLUE)
                surface.blit(asset_header, (50, y_pos))
                y_pos += 40
                
                # Asset details
                value_change = asset.current_value - asset.purchase_value
                value_change_percent = (value_change / asset.purchase_value) * 100 if asset.purchase_value > 0 else 0
                
                asset_details = [
                    f"Purchase Value: ${asset.purchase_value:.2f}",
                    f"Current Value: ${asset.current_value:.2f}",
                    f"Age: {asset.age} years",
                    f"Condition: {asset.condition}"
                ]
                
                # Add value change information
                if value_change >= 0:
                    asset_details.append(f"Appreciation: +${value_change:.2f} ({value_change_percent:.1f}%)")
                else:
                    asset_details.append(f"Depreciation: ${abs(value_change):.2f} ({abs(value_change_percent):.1f}%)")
                
                # Asset-specific information
                if asset.asset_type == "Car":
                    if asset.condition == "Poor":
                        asset_details.append("⚠️ Consider repairs or replacement")
                    elif asset.current_value < asset.purchase_value * 0.3:
                        asset_details.append("💡 Consider selling before further depreciation")
                elif asset.asset_type == "House":
                    if value_change > 0:
                        asset_details.append("🏠 Property has appreciated in value")
                    else:
                        asset_details.append("🏠 Property value has declined")
                
                for j, detail in enumerate(asset_details):
                    if "Appreciation:" in detail:
                        color = GREEN
                    elif "Depreciation:" in detail:
                        color = RED
                    elif "Current Value:" in detail:
                        color = BLUE
                    else:
                        color = BLACK
                    
                    detail_surface = self.small_font.render(detail, True, color)
                    surface.blit(detail_surface, (80, y_pos))
                    y_pos += 25
                
                y_pos += 20  # Space between assets
                total_current_value += asset.current_value
                total_purchase_value += asset.purchase_value
            
            # Summary section
            summary_y = SCREEN_HEIGHT - 200
            summary_title = self.text_font.render("Asset Portfolio Summary", True, BLUE)
            surface.blit(summary_title, (50, summary_y))
            
            total_change = total_current_value - total_purchase_value
            total_change_percent = (total_change / total_purchase_value) * 100 if total_purchase_value > 0 else 0
            
            summary_details = [
                f"Total Purchase Value: ${total_purchase_value:.2f}",
                f"Total Current Value: ${total_current_value:.2f}"
            ]
            
            if total_change >= 0:
                summary_details.append(f"Total Appreciation: +${total_change:.2f} ({total_change_percent:.1f}%)")
            else:
                summary_details.append(f"Total Depreciation: ${abs(total_change):.2f} ({abs(total_change_percent):.1f}%)")
            
            for i, detail in enumerate(summary_details):
                if "Total Appreciation:" in detail:
                    color = GREEN
                elif "Total Depreciation:" in detail:
                    color = RED
                elif "Total Current Value:" in detail:
                    color = BLUE
                else:
                    color = BLACK
                
                detail_surface = self.text_font.render(detail, True, color)
                surface.blit(detail_surface, (50, summary_y + 30 + i * 25))
            
            # Portfolio advice
            if total_change_percent > 10:
                advice = "📈 Your assets are performing well!"
                advice_color = GREEN
            elif total_change_percent < -20:
                advice = "📉 Consider diversifying your asset portfolio"
                advice_color = RED
            else:
                advice = "📊 Your asset portfolio is stable"
                advice_color = BLACK
            
            advice_surface = self.small_font.render(advice, True, advice_color)
            surface.blit(advice_surface, (50, summary_y + 120))
        
        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

class JobSearchScreen(Screen):
    """
    Screen for searching for a job.
    """
    play_startup_music = False  # Disable music for this screen
    
    def __init__(self, game):
        super().__init__(game)

        # Title and fonts
        self.title_font = pygame.font.SysFont('Arial', FONT_LARGE)
        self.text_font = pygame.font.SysFont('Arial', FONT_MEDIUM)

        # Generate job options based on education and experience
        self.job_options = self.generate_job_options()

        # Create buttons for job options
        self.buttons = [Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80, 200, 50, "Back", action=self.go_back)]

        # Add job option buttons if jobs are available
        if self.job_options:
            y_pos = 250
            for i, job in enumerate(self.job_options):
                self.buttons.append(
                    Button(
                        SCREEN_WIDTH // 2 - 200,
                        y_pos + i * 60,
                        400, 50,
                        f"{job['title']} - ${job['salary']}/year",
                        action=lambda j=job: self.apply_for_job(j)
                    )
                )

        # Status message
        self.status_message = ""
        self.status_color = BLACK
        self._background_original = load_ui_background('FINANCIAL_BG')

    def generate_job_options(self):
        """Generate job options based on player's education and experience."""
        # Check if player exists
        if not self.game.player:
            return []
        
        job_options = []

        # Current job info
        current_salary = self.game.player.salary if self.game.player.job else 0

        # Base salary multiplier based on years of experience
        experience_years = max(0, self.game.player.age - 18)  # Assume working age starts at 18
        experience_multiplier = 1.0 + (experience_years * 0.03)  # 3% increase per year of experience

        # Generate job options based on education
        if self.game.player.education == "High School" or self.game.player.education == "High School Graduate":
            job_options = [
                {"title": "Retail Associate", "salary": int(25000 * experience_multiplier)},
                {"title": "Food Service Worker", "salary": int(22000 * experience_multiplier)},
                {"title": "Warehouse Worker", "salary": int(28000 * experience_multiplier)},
                {"title": "Office Clerk", "salary": int(30000 * experience_multiplier)},
            ]
        elif self.game.player.education == "Trade School":
            job_options = [
                {"title": "Electrician", "salary": int(45000 * experience_multiplier)},
                {"title": "Plumber", "salary": int(48000 * experience_multiplier)},
                {"title": "HVAC Technician", "salary": int(50000 * experience_multiplier)},
                {"title": "Automotive Mechanic", "salary": int(42000 * experience_multiplier)},
            ]
        elif self.game.player.education == "College Graduate":
            job_options = [
                {"title": "Accountant", "salary": int(60000 * experience_multiplier)},
                {"title": "Marketing Manager", "salary": int(65000 * experience_multiplier)},
                {"title": "Software Developer", "salary": int(75000 * experience_multiplier)},
                {"title": "Financial Analyst", "salary": int(70000 * experience_multiplier)},
            ]
        else:  # Default/basic jobs
            job_options = [
                {"title": "Retail Associate", "salary": int(25000 * experience_multiplier)},
                {"title": "Food Service Worker", "salary": int(22000 * experience_multiplier)},
                {"title": "Warehouse Worker", "salary": int(28000 * experience_multiplier)},
            ]

        # Add some randomness to salaries (±10%)
        for job in job_options:
            job["salary"] = int(job["salary"] * random.uniform(0.9, 1.1))

        # Filter out jobs that don't offer at least 5% more than current salary (if employed)
        if self.game.player.job:
            job_options = [job for job in job_options if job["salary"] >= current_salary * 1.05]

        return job_options

    def apply_for_job(self, job):
        """Apply for the selected job."""
        # Job application success chance based on qualifications
        base_success_chance = 0.7  # 70% base chance

        # Adjust for education
        if self.game.player.education == "College Graduate":
            base_success_chance += 0.2
        elif self.game.player.education == "Trade School":
            base_success_chance += 0.1

        # Adjust for experience
        experience_years = max(0, self.game.player.age - 18)
        base_success_chance += min(0.2, experience_years * 0.01)  # Up to 20% bonus for experience

        # Cap at 95% chance
        success_chance = min(0.95, base_success_chance)

        # Determine if application is successful
        if random.random() < success_chance:
            old_job = self.game.player.job
            old_salary = self.game.player.salary

            self.game.player.job = job["title"]
            self.game.player.salary = job["salary"]

            if old_job:
                salary_increase = self.game.player.salary - old_salary
                percent_increase = (salary_increase / old_salary) * 100
                msg = f"Congratulations! You got the job! That's a raise of ${salary_increase}/year ({percent_increase:.1f}% )!"
            else:
                msg = f"Congratulations! You got the job! You are now earning ${self.game.player.salary}/year."
            self.modal_popup = ModalPopup("Job Offer", msg, on_ok=lambda: setattr(self, 'modal_popup', None))
            # Disable job buttons after getting a job
            self.buttons = [self.buttons[0]]  # Keep only the back button
        else:
            self.modal_popup = ModalPopup("Application Result", "Unfortunately, the company decided to go with another candidate. Try again!", on_ok=lambda: setattr(self, 'modal_popup', None))

    def go_back(self):
        """Go back to the game screen."""
        from moneySmarts.screens.game_screen import GameScreen
        self.game.gui_manager.set_screen(GameScreen(self.game))

    def draw(self, surface):
        """Draw the job search screen."""
        # Background
        draw_background(surface, self._background_original, default_color=WHITE)

        # Title
        title_surface = self.title_font.render("Job Search", True, BLACK)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 50))
        surface.blit(title_surface, title_rect)

        # Check if player exists
        if not self.game.player:
            no_player_text = self.text_font.render("Game not started yet.", True, BLACK)
            no_player_rect = no_player_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            surface.blit(no_player_text, no_player_rect)
            return

        # Current job info
        current_job_text = f"Current Job: {self.game.player.job if self.game.player.job else 'Unemployed'}"
        current_job_surface = self.text_font.render(current_job_text, True, BLACK)
        current_job_rect = current_job_surface.get_rect(center=(SCREEN_WIDTH // 2, 100))
        surface.blit(current_job_surface, current_job_rect)

        if self.game.player.job:
            salary_text = f"Current Salary: ${self.game.player.salary}/year"
            salary_surface = self.text_font.render(salary_text, True, BLACK)
            salary_rect = salary_surface.get_rect(center=(SCREEN_WIDTH // 2, 130))
            surface.blit(salary_surface, salary_rect)

        # Available jobs or no jobs message
        if self.job_options:
            jobs_title = self.text_font.render("Available Job Opportunities:", True, BLACK)
            jobs_title_rect = jobs_title.get_rect(center=(SCREEN_WIDTH // 2, 180))
            surface.blit(jobs_title, jobs_title_rect)

            jobs_subtitle = self.text_font.render("Click on a job to apply", True, BLACK)
            jobs_subtitle_rect = jobs_subtitle.get_rect(center=(SCREEN_WIDTH // 2, 210))
            surface.blit(jobs_subtitle, jobs_subtitle_rect)
        else:
            no_jobs_text = "No better job opportunities available at this time."
            no_jobs_surface = self.text_font.render(no_jobs_text, True, BLACK)
            no_jobs_rect = no_jobs_surface.get_rect(center=(SCREEN_WIDTH // 2, 200))
            surface.blit(no_jobs_surface, no_jobs_rect)

            advice_text = "Keep building your skills and try again later!"
            advice_surface = self.text_font.render(advice_text, True, BLACK)
            advice_rect = advice_surface.get_rect(center=(SCREEN_WIDTH // 2, 230))
            surface.blit(advice_surface, advice_rect)

        # Status message
        if self.status_message:
            # Split long messages into multiple lines
            words = self.status_message.split()
            lines = []
            current_line = []

            for word in words:
                current_line.append(word)
                if len(' '.join(current_line)) > 50:  # Adjust based on your font size
                    lines.append(' '.join(current_line[:-1]))
                    current_line = [current_line[-1]]

            if current_line:
                lines.append(' '.join(current_line))

            for i, line in enumerate(lines):
                status_surface = self.text_font.render(line, True, self.status_color)
                status_rect = status_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150 + i * 30))
                surface.blit(status_surface, status_rect)

        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

