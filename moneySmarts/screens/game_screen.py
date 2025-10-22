import pygame
import random
from moneySmarts.constants import *
from moneySmarts.ui import Screen, Button
from moneySmarts.utils import compute_net_worth


def draw_text(surface, text, x, y, is_title=False):
    """Helper method to draw text."""
    font = pygame.font.SysFont('Arial', FONT_LARGE if is_title else FONT_MEDIUM)
    text_surface = font.render(text, True, BLACK)
    surface.blit(text_surface, (x, y))


class GameScreen(Screen):
    """
    The main game screen that shows the player's status and allows them to take actions.
    """
    play_startup_music = False  # Disable music for this screen
    
    def __init__(self, game):
        super().__init__(game)
        self.utility_pay_btn = None
        self.create_buttons()
        self.show_utility_popup = False
        self.utility_bills = [
            {"name": "Electric", "min": 50, "max": 120},
            {"name": "Internet", "min": 40, "max": 80},
            {"name": "Water", "min": 25, "max": 60},
            {"name": "Gas", "min": 20, "max": 70}
        ]
        self.current_utility_bill = None
        # Quit confirmation
        self.show_quit_confirm = False
        self.quit_yes_btn = None
        self.quit_no_btn = None

    def create_buttons(self):
        """Create the buttons for the game screen."""
        # Clear existing buttons
        self.buttons = []
        continue_button = Button(
            SCREEN_WIDTH - 220, SCREEN_HEIGHT - 60, 200, 50,
            "Continue to Next Month", action=self.continue_to_next_month)
        self.buttons.append(continue_button)
        # (Explorer/Overworld mode removed) -- no explore button
        if not self.game.player:
            return
        # --- Banking Menu Button ---
        banking_button = Button(
            20, SCREEN_HEIGHT - 270, 200, 50,
            "Banking", action=self.open_banking_menu)
        self.buttons.append(banking_button)
        # --- Other Feature Buttons ---
        x_base = 240
        y_base = SCREEN_HEIGHT - 270
        y_step = 60
        btns = []
        if not self.game.player.credit_card and self.game.player.age >= 18:
            btns.append(Button(x_base, y_base, 200, 50, "Apply for Credit Card", action=self.apply_for_credit_card))
        elif self.game.player.credit_card:
            btns.append(Button(x_base, y_base, 200, 50, "View Credit Card", action=self.view_credit_card))
            if self.game.player.credit_card.balance > 0:
                btns.append(Button(x_base, y_base + y_step, 200, 50, "Pay Credit Card", action=self.pay_credit_card))
        if self.game.player.loans:
            btns.append(Button(x_base, y_base + 2*y_step, 200, 50, "View Loans", action=self.view_loans))
            btns.append(Button(x_base, y_base + 3*y_step, 200, 50, "Make Extra Loan Payment", action=self.make_extra_loan_payment))
        if self.game.player.assets:
            btns.append(Button(x_base + 220, y_base, 200, 50, "View Assets", action=self.view_assets))
        if not self.game.player.job and self.game.player.age >= 16:
            btns.append(Button(x_base + 220, y_base + y_step, 200, 50, "Look for a Job", action=self.look_for_job))
        elif self.game.player.job and random.random() < 0.1:
            btns.append(Button(x_base + 220, y_base + y_step, 200, 50, "Look for a Better Job", action=self.look_for_job))
        # --- System Control Buttons ---
        self.buttons.extend([
            Button(SCREEN_WIDTH - 220, 100, 90, 40, "Pause", action=self.pause_game),
            Button(SCREEN_WIDTH - 220, 150, 90, 40, "Save", action=self.save_game),
            Button(SCREEN_WIDTH - 120, 150, 90, 40, "Load", action=self.load_game),
            Button(SCREEN_WIDTH - 220, 200, 190, 40, "Quit", action=self.quit_game),
            Button(SCREEN_WIDTH - 220, SCREEN_HEIGHT - 120, 200, 50, "View Inventory", action=self.open_inventory),
            Button(SCREEN_WIDTH - 220, SCREEN_HEIGHT - 180, 200, 50, "Shop", action=self.open_shop)
        ])
        self.buttons.extend(btns)

    def create_utility_popup_buttons(self):
        self.utility_pay_btn = Button(SCREEN_WIDTH//2-120, SCREEN_HEIGHT//2+40, 100, 50, "Pay", action=self.pay_utility_bill)
        self.utility_skip_btn = Button(SCREEN_WIDTH//2+20, SCREEN_HEIGHT//2+40, 100, 50, "Skip", action=self.skip_utility_bill)

    def trigger_utility_popup(self):
        self.current_utility_bill = random.choice(self.utility_bills)
        self.utility_bill_amount = random.randint(self.current_utility_bill["min"], self.current_utility_bill["max"])
        self.utility_popup_message = f"{self.current_utility_bill['name']} bill due: ${self.utility_bill_amount}. Pay now?"
        self.create_utility_popup_buttons()
        self.show_utility_popup = True

    def pay_utility_bill(self):
        if self.game.player.cash >= self.utility_bill_amount:
            self.game.player.cash -= self.utility_bill_amount
        self.show_utility_popup = False
        self.create_buttons()

    def skip_utility_bill(self):
        # Utility shutoff chance if skipped
        if random.random() < 0.5:  # 50% chance
            self.game.end_game_gui("Your utilities were shut off due to non-payment. Game Over.")
        self.show_utility_popup = False
        self.create_buttons()

    def check_game_over_conditions(self):
        """Check for game over conditions and transition if needed."""
        reason = None
        # Bankruptcy: cash below zero and no assets
        if self.game.player.cash < 0 and not self.game.player.assets:
            reason = "Bankruptcy! You have no cash or assets left."
        # Excessive debt: credit card or loan debt exceeds $10,000
        total_debt = 0
        if self.game.player.credit_card:
            total_debt += self.game.player.credit_card.balance
        for loan in self.game.player.loans:
            # Use correct attribute name
            total_debt += loan.current_balance
        if total_debt > 10000:
            reason = "Game Over: Your debts are too high to continue."
        # Unpaid utility bills (simulate shutoff)
        if hasattr(self, 'utility_bill_amount') and self.utility_bill_amount and self.show_utility_popup:
            if self.game.player.cash < self.utility_bill_amount:
                reason = "Game Over: Utilities shut off due to unpaid bills."
        # Retirement age
        if self.game.player.age >= 65:
            reason = "Congratulations! You reached retirement age."
        if reason:
            from moneySmarts.screens.game_over_screen import GameOverScreen
            self.game.gui_manager.set_screen(GameOverScreen(self.game, reason=reason))
            return True
        return False

    def continue_to_next_month(self):
        """Continue to the next month."""
        # Check if player exists before processing
        if not self.game.player:
            return
            
        # Increment month
        self.game.current_month += 1
        if self.game.current_month > 12:
            self.game.current_month = 1
            self.game.current_year += 1
            self.game.player.age += 1
            
            # Apply interest to savings
            if self.game.player.bank_account and self.game.player.bank_account.account_type == "Savings":
                self.game.player.bank_account.apply_interest()
            
            # Age assets
            for asset in self.game.player.assets:
                asset.age_asset()
        
        # Process monthly finances
        self.game.process_monthly_finances()
        
        # Random events
        if random.random() < 0.3:  # 30% chance of an event each month
            self.game.trigger_random_event()
            # Don't proceed further until event is handled
            return
        
        # Life stage events based on age
        life_event_triggered = self.game.check_life_stage_events_gui()
        
        # If no life event was triggered, refresh the game screen
        if not life_event_triggered:
            # Check game over conditions
            if self.check_game_over_conditions():
                return
            # Refresh buttons (in case player status changed)
            self.create_buttons()

        # Show utility bill popup every month
        self.trigger_utility_popup()

    def open_bank_account(self):
        """Open a bank account screen."""
        from moneySmarts.screens.financial_screens import BankAccountScreen
        self.game.gui_manager.set_screen(BankAccountScreen(self.game))

    def view_bank_account(self):
        """View bank account details."""
        from moneySmarts.screens.financial_screens import BankDetailsScreen
        self.game.gui_manager.set_screen(BankDetailsScreen(self.game))

    def deposit_to_bank(self):
        """Deposit money to bank account."""
        from moneySmarts.screens.financial_screens import DepositScreen
        self.game.gui_manager.set_screen(DepositScreen(self.game))

    def withdraw_from_bank(self):
        """Withdraw money from bank account."""
        from moneySmarts.screens.financial_screens import WithdrawScreen
        self.game.gui_manager.set_screen(WithdrawScreen(self.game))

    def get_debit_card(self):
        """Get a debit card."""
        from moneySmarts.screens.financial_screens import GetDebitCardScreen
        self.game.gui_manager.set_screen(GetDebitCardScreen(self.game))

    def apply_for_credit_card(self):
        """Apply for a credit card."""
        from moneySmarts.screens.financial_screens import CreditCardScreen
        self.game.gui_manager.set_screen(CreditCardScreen(self.game))

    def view_credit_card(self):
        """View credit card details."""
        from moneySmarts.screens.financial_screens import CreditCardDetailsScreen
        self.game.gui_manager.set_screen(CreditCardDetailsScreen(self.game))

    def pay_credit_card(self):
        """Make a payment on the credit card."""
        from moneySmarts.screens.financial_screens import PayCreditCardScreen
        self.game.gui_manager.set_screen(PayCreditCardScreen(self.game))

    def view_loans(self):
        """View loan details."""
        from moneySmarts.screens.financial_screens import LoanDetailsScreen
        self.game.gui_manager.set_screen(LoanDetailsScreen(self.game))

    def make_extra_loan_payment(self):
        """Make an extra payment on a loan."""
        from moneySmarts.screens.financial_screens import ExtraLoanPaymentScreen
        self.game.gui_manager.set_screen(ExtraLoanPaymentScreen(self.game))

    def view_assets(self):
        """View asset details."""
        from moneySmarts.screens.financial_screens import AssetDetailsScreen
        self.game.gui_manager.set_screen(AssetDetailsScreen(self.game))

    def look_for_job(self):
        """Look for a job or a better job."""
        from moneySmarts.screens.financial_screens import JobSearchScreen
        self.game.gui_manager.set_screen(JobSearchScreen(self.game))

    def open_shop(self):
        """Open the shop screen."""
        from moneySmarts.screens.shop_screen import ShopScreen
        self.game.gui_manager.set_screen(ShopScreen(self.game))

    def pause_game(self):
        """Pause the game (stops updates, disables actions)."""
        self.game.paused = True
        # Optionally, show a pause overlay or message

    def play_game(self):
        """Resume the game from pause."""
        self.game.paused = False
        # Optionally, hide pause overlay or message

    def save_game(self):
        """Save the current game state."""
        self.game.save_state()
        # Optionally, show a 'Game Saved' message

    def load_game(self):
        """Load the saved game state."""
        self.game.load_state()
        self.create_buttons()  # Refresh buttons after loading

    def quit_game(self):
        """Initiate quit confirmation instead of immediate quit."""
        if not self.show_quit_confirm:
            self.show_quit_confirm = True
            self._create_quit_confirm_buttons()

    def _create_quit_confirm_buttons(self):
        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2 + 40
        self.quit_yes_btn = Button(cx - 110, cy, 100, 45, "Yes", action=self._confirm_quit_execute)
        self.quit_no_btn = Button(cx + 10, cy, 100, 45, "No", action=self._cancel_quit)

    def _cancel_quit(self):
        self.show_quit_confirm = False
        self.quit_yes_btn = None
        self.quit_no_btn = None

    def _confirm_quit_execute(self):
        # proceed with original quit
        self.game.quit()

    def draw(self, surface):
        """Draw the game screen."""
        # Background
        surface.fill(WHITE)

        # Header
        pygame.draw.rect(surface, BLUE, (0, 0, SCREEN_WIDTH, 80))

        # Title
        title_font = pygame.font.SysFont('Arial', FONT_LARGE)
        title_surface = title_font.render(f"MONTH: {self.game.current_month}/YEAR: {self.game.current_year + 2023}", True, WHITE)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 25))
        surface.blit(title_surface, title_rect)

        # Check if player exists before drawing player info
        if not self.game.player:
            no_player_text = title_font.render("Please start a new game", True, WHITE)
            no_player_rect = no_player_text.get_rect(center=(SCREEN_WIDTH // 2, 55))
            surface.blit(no_player_text, no_player_rect)
            
            # Draw buttons (only continue button will be present)
            for button in self.buttons:
                button.draw(surface)
            return

        age_surface = title_font.render(f"AGE: {self.game.player.age}", True, WHITE)
        age_rect = age_surface.get_rect(center=(SCREEN_WIDTH // 2, 55))
        surface.blit(age_surface, age_rect)

        # Player info section
        info_font = pygame.font.SysFont('Arial', FONT_MEDIUM)

        # Name and education
        draw_text(surface, f"Name: {self.game.player.name}", 20, 100)
        draw_text(surface, f"Education: {self.game.player.education}", 20, 130)

        # Job and salary
        job_text = f"Job: {self.game.player.job if self.game.player.job else 'Unemployed'}"
        draw_text(surface, job_text, 20, 160)

        if self.game.player.job:
            salary_text = f"Salary: ${self.game.player.salary}/year (${self.game.player.salary/12:.2f}/month)"
            draw_text(surface, salary_text, 40, 190)

        # Financial info
        draw_text(surface, f"Cash: ${self.game.player.cash:.2f}", 20, 230)

        if self.game.player.bank_account:
            bank_text = f"Bank Account ({self.game.player.bank_account.account_type}): ${self.game.player.bank_account.balance:.2f}"
            draw_text(surface, bank_text, 20, 260)

        if self.game.player.credit_card:
            credit_text = f"Credit Card: ${self.game.player.credit_card.balance:.2f}/{self.game.player.credit_card.limit:.2f}"
            draw_text(surface, credit_text, 20, 290)

        draw_text(surface, f"Credit Score: {self.game.player.credit_score}", 20, 320)

        # Loans
        if self.game.player.loans:
            draw_text(surface, "LOANS:", 400, 100)
            for i, loan in enumerate(self.game.player.loans):
                loan_text = f"{loan.loan_type}: ${loan.current_balance:.2f} (${loan.monthly_payment:.2f}/month)"
                draw_text(surface, loan_text, 420, 130 + i * 30)

        # Assets
        if self.game.player.assets:
            draw_text(surface, "ASSETS:", 400, 230)
            for i, asset in enumerate(self.game.player.assets):
                asset_text = f"{asset.name}: ${asset.current_value:.2f} ({asset.condition})"
                draw_text(surface, asset_text, 420, 260 + i * 30)

        # Family
        if self.game.player.family:
            draw_text(surface, "FAMILY:", 700, 100)
            for i, member in enumerate(self.game.player.family):
                if member["relation"] == "Spouse":
                    family_text = f"Spouse: Age {member['age'] + self.game.current_year}"
                else:
                    family_text = f"{member['relation']}: {member['name']}, Age {member['age'] + self.game.current_year}"
                draw_text(surface, family_text, 720, 130 + i * 30)

        # Calculate and display net worth
        net_worth = compute_net_worth(self.game.player)
        net_worth_color = GREEN if net_worth >= 0 else RED
        net_worth_font = pygame.font.SysFont('Arial', FONT_LARGE)
        net_worth_text = f"NET WORTH: ${net_worth:.2f}"
        net_worth_surface = net_worth_font.render(net_worth_text, True, net_worth_color)
        net_worth_rect = net_worth_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 330))
        surface.blit(net_worth_surface, net_worth_rect)

        # Draw buttons
        for button in self.buttons:
            button.draw(surface)

        # Draw utility bill popup if needed
        if self.show_utility_popup:
            pygame.draw.rect(surface, LIGHT_GRAY, (SCREEN_WIDTH//2-200, SCREEN_HEIGHT//2-100, 400, 200))
            font = pygame.font.SysFont('Arial', FONT_MEDIUM)
            msg_surface = font.render(self.utility_popup_message, True, BLACK)
            msg_rect = msg_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2-30))
            surface.blit(msg_surface, msg_rect)
            self.utility_pay_btn.draw(surface)
            self.utility_skip_btn.draw(surface)

        # After existing drawing including utility popup, add quit confirmation overlay
        if self.show_quit_confirm:
            # Dim background
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(160)
            overlay.fill((0, 0, 0))
            surface.blit(overlay, (0, 0))
            # Dialog box
            box_w, box_h = 420, 200
            box_x = (SCREEN_WIDTH - box_w) // 2
            box_y = (SCREEN_HEIGHT - box_h) // 2
            pygame.draw.rect(surface, LIGHT_GRAY, (box_x, box_y, box_w, box_h), border_radius=12)
            pygame.draw.rect(surface, DARK_GRAY, (box_x, box_y, box_w, box_h), 3, border_radius=12)
            font = pygame.font.SysFont('Arial', FONT_MEDIUM)
            msg = "Are you sure you want to quit?"
            msg_surface = font.render(msg, True, BLACK)
            msg_rect = msg_surface.get_rect(center=(SCREEN_WIDTH//2, box_y + 60))
            surface.blit(msg_surface, msg_rect)
            # Buttons
            if not self.quit_yes_btn or not self.quit_no_btn:
                self._create_quit_confirm_buttons()
            self.quit_yes_btn.draw(surface)
            self.quit_no_btn.draw(surface)

    def handle_events(self, events):
        if self.show_quit_confirm:
            # Only process quit confirmation buttons
            mouse_pos = pygame.mouse.get_pos()
            mouse_click = False
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_click = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._cancel_quit()
                        return
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        self._confirm_quit_execute()
                        return
            for btn in (self.quit_yes_btn, self.quit_no_btn):
                if btn:
                    action = btn.update(mouse_pos, mouse_click)
                    if action:
                        action()
                        return
            return  # Do not propagate to base while confirming
        # Existing logic
        super().handle_events(events)
        # Handle utility bill popup
        if self.show_utility_popup:
            mouse_pos = pygame.mouse.get_pos()
            mouse_click = False
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mouse_click = True
            if self.utility_pay_btn and self.utility_pay_btn.update(mouse_pos, mouse_click):
                self.pay_utility_bill()
                return
            if self.utility_skip_btn and self.utility_skip_btn.update(mouse_pos, mouse_click):
                self.skip_utility_bill()
                return

    def open_banking_menu(self):
        from moneySmarts.screens.bank_screen import BankScreen
        self.game.gui_manager.set_screen(BankScreen(self.game))

    def open_savings_account(self):
        """Open a savings account screen."""
        from moneySmarts.screens.financial_screens import BankAccountScreen
        self.game.gui_manager.set_screen(BankAccountScreen(self.game))

    def view_savings_account(self):
        """View savings account details."""
        from moneySmarts.screens.financial_screens import SavingsDetailsScreen
        self.game.gui_manager.set_screen(SavingsDetailsScreen(self.game))

    def deposit_to_savings(self):
        """Deposit money to savings account."""
        from moneySmarts.screens.financial_screens import DepositToSavingsScreen
        self.game.gui_manager.set_screen(DepositToSavingsScreen(self.game))

    def withdraw_from_savings(self):
        """Withdraw money from savings account."""
        from moneySmarts.screens.financial_screens import WithdrawFromSavingsScreen
        self.game.gui_manager.set_screen(WithdrawFromSavingsScreen(self.game))

    def open_inventory(self):
        from moneySmarts.screens.inventory_screen import InventoryScreen
        self.game.gui_manager.set_screen(InventoryScreen(self.game))

    # Overworld/explorer mode removed: the method that used to switch to the
    # overworld screen was intentionally removed. Any attempt to call it will
    # raise an AttributeError (method not present).
