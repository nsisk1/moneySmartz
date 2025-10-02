from typing import Callable

import pygame
import random
import os
import logging  # added for debug
from moneySmarts.constants import *
from moneySmarts.ui import Screen, Button, TextInput
from moneySmarts.sound_manager import SoundManager
from moneySmarts.ui import GUIManager
from moneySmarts.images import get_image_path
from moneySmarts.image_manager import image_manager  # NEW


class TitleScreen(Screen):
    play_startup_music = True  # Enable music for this screen

    def __init__(self, game: GUIManager) -> None:
        super().__init__(game)
        # Load background image via image_manager
        self.background_image = None
        self._background_original = image_manager.load_image('TITLE_BG')
        if self._background_original:
            self.background_image = self._background_original
        else:
            logging.debug("TitleScreen background not found via image_manager")
        # Fonts
        self.confirm_buttons = None
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(current_dir))
        assets_dir = os.path.join(root_dir, 'assets')
        font_path = os.path.join(assets_dir, PIXEL_FONT)
        try:
            self.title_font = pygame.font.Font(font_path, FONT_TITLE)
            self.subtitle_font = pygame.font.Font(font_path, FONT_LARGE)
            button_font = font_path
        except Exception:
            self.title_font = pygame.font.SysFont('Arial', FONT_TITLE)
            self.subtitle_font = pygame.font.SysFont('Arial', FONT_LARGE)
            button_font = None

        # Buttons with custom font
        start_button = Button(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50,
            200, 50, "Start New Game",
            font_name=button_font,
            action=self.confirm_start_new_game
        )
        load_button = Button(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 110,
            200, 50, "Load Game",
            font_name=button_font,
            action=self.load_game
        )
        save_button = Button(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 170,
            200, 50, "Save Game",
            font_name=button_font,
            action=self.save_game
        )
        quit_button = Button(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 230,
            200, 50, "Quit",
            font_name=button_font,
            action=self.confirm_quit_game
        )
        self.buttons = [start_button, load_button, save_button, quit_button]

        self.show_confirm = False
        self.confirm_action = None
        self.confirm_message = ""

        # Coin rain animation setup
        self.coins = []
        self.max_coins = 30
        self.coin_spawn_rate = 0.5
        self.coin_spawn_timer = 0

        # Logo/Title animation
        self.title_y = -100
        self.title_target_y = SCREEN_HEIGHT // 4
        self.title_speed = 5

        # Subtitle fade-in
        self.subtitle_alpha = 0
        self.subtitle_fade_speed = 2


    def start_new_game(self):
        """Start a new game (name input then intro)."""
        from moneySmarts.screens.base_screens import NameInputScreen
        self.game.gui_manager.set_screen(NameInputScreen(self.game, next_screen='intro'))

    def quit_game(self):
        """Quit the game."""
        self.game.gui_manager.running = False

    def confirm_start_new_game(self):
        if self.game.player is not None:
            self.show_confirm = True
            self.confirm_action = self.start_new_game
            self.confirm_message = "Start a new game? Unsaved progress will be lost. Continue?"
        else:
            self.start_new_game()

    def confirm_quit_game(self):
        self.show_confirm = True
        self.confirm_action = self.quit_game
        self.confirm_message = "Are you sure you want to quit? Unsaved progress will be lost."

    def save_game(self):
        try:
            self.game.save_state()
            self.confirm_message = "Game saved successfully!"
        except Exception as e:
            self.confirm_message = f"Save failed: {e}"
        self.show_confirm = True
        self.confirm_action = None

    def load_game(self):
        import pickle
        try:
            with open("savegame.dat", "rb") as f:
                loaded_game = pickle.load(f)
                self.game.__dict__.update(loaded_game.__dict__)
            self.confirm_message = "Game loaded successfully!"
        except Exception as e:
            self.confirm_message = f"Load failed: {e}"
        self.show_confirm = True
        self.confirm_action = None

    def update(self):
        """Update the title animation."""
        # Move title down to target position
        if self.title_y < self.title_target_y:
            self.title_y += self.title_speed
            if self.title_y > self.title_target_y:
                self.title_y = self.title_target_y

        # Fade in subtitle after title reaches target
        if self.title_y == self.title_target_y and self.subtitle_alpha < 255:
            self.subtitle_alpha += self.subtitle_fade_speed
            if self.subtitle_alpha > 255:
                self.subtitle_alpha = 255

        # Update coin rain animation
        current_time = pygame.time.get_ticks() / 1000
        if len(self.coins) < self.max_coins and current_time > self.coin_spawn_timer:
            self.coins.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(-100, -20),
                'speed': random.uniform(1.5, 3.5),
                'size': random.randint(6, 12),
                'rotation': random.randint(0, 360),
                'rotation_speed': random.uniform(-2, 2)
            })
            self.coin_spawn_timer = current_time + self.coin_spawn_rate
        for coin in self.coins[:]:
            coin['y'] += coin['speed']
            coin['rotation'] += coin['rotation_speed']
            if coin['y'] > SCREEN_HEIGHT + 50:
                self.coins.remove(coin)

    def draw(self, surface):
        # Dynamic resize of background to current window size
        if self._background_original:
            sw, sh = surface.get_size()
            if (not self.background_image) or self.background_image.get_width() != sw or self.background_image.get_height() != sh:
                try:
                    self.background_image = pygame.transform.smoothscale(self._background_original, (sw, sh))
                except Exception:
                    self.background_image = self._background_original
        # ...existing code...
        if self.background_image:
            try:
                surface.blit(self.background_image, (0, 0))
            except Exception:
                surface.fill(BG_TOP)
        else:
            surface.fill(BG_TOP)
        # Optional dark overlay for readability
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 60))
        surface.blit(overlay, (0, 0))
        # Draw coins in background (over image but under text/buttons)
        for coin in self.coins:
            pygame.draw.circle(surface, GOLD, (int(coin['x']), int(coin['y'])), coin['size'])
            pygame.draw.circle(surface, DARK_GOLD, (int(coin['x']), int(coin['y'])), coin['size'], 1)
            font_size = max(6, int(coin['size'] * 1.2))
            coin_font = pygame.font.SysFont('Arial', font_size)
            text = coin_font.render("$", True, DARK_GOLD)
            text_rect = text.get_rect(center=(int(coin['x']), int(coin['y'])))
            surface.blit(text, text_rect)
        # Title and subtitle
        title_surface = self.title_font.render("MONEY SMARTS", True, PRIMARY)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, self.title_y))
        surface.blit(title_surface, title_rect)
        subtitle_surface = self.subtitle_font.render("Financial Life Simulator", True, (0, 100, 0))
        subtitle_surface.set_alpha(self.subtitle_alpha)
        subtitle_rect = subtitle_surface.get_rect(center=(SCREEN_WIDTH // 2, self.title_y + 60))
        surface.blit(subtitle_surface, subtitle_rect)
        # Buttons
        for button in self.buttons:
            if button.text == "Save Game" and self.game.player is None:
                continue
            button.draw(surface)
        # Confirm dialog
        if self.show_confirm:
            self.draw_confirm_dialog(surface)

    def draw_confirm_dialog(self, surface):
        dialog_width, dialog_height = 480, 200
        dialog_x = (SCREEN_WIDTH - dialog_width) // 2
        dialog_y = (SCREEN_HEIGHT - dialog_height) // 2
        pygame.draw.rect(surface, CARD_BG, (dialog_x, dialog_y, dialog_width, dialog_height), border_radius=12)
        pygame.draw.rect(surface, CARD_BORDER, (dialog_x, dialog_y, dialog_width, dialog_height), 2, border_radius=12)
        font = pygame.font.SysFont('Arial', FONT_MEDIUM)
        text_surface = font.render(self.confirm_message, True, BLACK)
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
        surface.blit(text_surface, text_rect)
        yes_button = Button(dialog_x + 60, dialog_y + 120, 140, 44, "Yes", action=self.confirm_yes)
        no_button = Button(dialog_x + 280, dialog_y + 120, 140, 44, "No", action=self.confirm_no)
        yes_button.draw(surface)
        no_button.draw(surface)
        self.confirm_buttons = [yes_button, no_button]

    def confirm_yes(self):
        if self.confirm_action:
            self.confirm_action()
        self.show_confirm = False
        self.confirm_action = None
        self.confirm_message = ""

    def confirm_no(self):
        self.show_confirm = False
        self.confirm_action = None
        self.confirm_message = ""

    def handle_events(self, events):
        super().handle_events(events)
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_click = True
        # If confirmation dialog is shown, only handle events for confirm buttons
        if self.show_confirm and self.confirm_buttons:
            for button in self.confirm_buttons:
                action = button.update(mouse_pos, mouse_click)
                if action:
                    action()
        else:
            for button in self.buttons:
                # Only allow Save Game if player exists
                if button.text == "Save Game" and self.game.player is None:
                    continue
                action = button.update(mouse_pos, mouse_click)
                if action:
                    action()

class NameInputScreen(Screen):
    play_startup_music = True  # Enable music for this screen
    
    def __init__(self, game, next_screen: str = 'intro'):
        super().__init__(game)
        self.next_screen = next_screen  # 'intro' or 'overworld'
        # Load background image via image_manager
        self.background_image = None
        self._background_original = image_manager.load_image('name_background.png')
        if self._background_original:
            self.background_image = self._background_original
        else:
            logging.debug("NameInputScreen background not found via image_manager")
        # Fonts
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(current_dir))
        assets_dir = os.path.join(root_dir, 'assets')
        font_path = os.path.join(assets_dir, PIXEL_FONT)
        try:
            self.title_font = pygame.font.Font(font_path, FONT_LARGE)
            input_font = font_path
            button_font = font_path
        except:
            self.title_font = pygame.font.SysFont('Arial', FONT_LARGE)
            input_font = None
            button_font = None
        # Text input
        self.name_input = TextInput(
            SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 - 25,
            300, 50, 
            font_size=FONT_MEDIUM,
            font_name=input_font,
            max_length=20
        )
        start_button = Button(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50,
            200, 50, "Start Game",
            font_name=button_font,
            action=self.start_game
        )
        back_button = Button(
            SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 120,
            200, 50, "Back",
            font_name=button_font,
            action=self.go_back
        )
        self.buttons = [start_button, back_button]
        self.bg_color = BG_TOP

    def handle_events(self, events):
        """Handle pygame events."""
        super().handle_events(events)
        self.name_input.update(events)

    def start_game(self):
        """Start the game with the entered name, then route to intro or overworld."""
        name = self.name_input.text.strip()
        if name:
            from moneySmarts.models import Player
            self.game.player = Player(name)
            if self.next_screen == 'overworld':
                from moneySmarts.screens.overworld_screen import OverworldScreen
                self.game.gui_manager.set_screen(OverworldScreen(self.game))
            else:
                from moneySmarts.screens.base_screens import IntroScreen
                self.game.gui_manager.set_screen(IntroScreen(self.game))

    def go_back(self):
        """Go back to the title screen."""
        from moneySmarts.screens.base_screens import TitleScreen
        self.game.gui_manager.set_screen(TitleScreen(self.game))

    def draw(self, surface):
        # Dynamic scaling per current window size
        if self._background_original:
            sw, sh = surface.get_size()
            if (not self.background_image) or self.background_image.get_width() != sw or self.background_image.get_height() != sh:
                try:
                    self.background_image = pygame.transform.smoothscale(self._background_original, (sw, sh))
                except Exception:
                    self.background_image = self._background_original
        if self.background_image:
            surface.blit(self.background_image, (0, 0))
        else:
            surface.fill(self.bg_color)
        # Title
        if self.background_image:
            overlay_rect = pygame.Rect(surface.get_width() // 2 - 240, surface.get_height() // 2 - 80, 480, 200)
            overlay = pygame.Surface(overlay_rect.size, pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 140))
            surface.blit(overlay, overlay_rect.topleft)
            # Move the title text into the top of the gray box
            title_surface = self.title_font.render("Enter Your Name", True, BLACK)
            title_rect = title_surface.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 - 60))
            surface.blit(title_surface, title_rect)
        else:
            card_rect = pygame.Rect(surface.get_width() // 2 - 220, surface.get_height() // 2 - 70, 440, 180)
            pygame.draw.rect(surface, CARD_BG, card_rect, border_radius=12)
            pygame.draw.rect(surface, CARD_BORDER, card_rect, 2, border_radius=12)
            # Move the title text into the top of the card
            title_surface = self.title_font.render("Enter Your Name", True, BLACK)
            title_rect = title_surface.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 - 50))
            surface.blit(title_surface, title_rect)
        # Input
        self.name_input.draw(surface)
        # Buttons
        for button in self.buttons:
            button.draw(surface)


# noinspection PyCompatibility
class IntroScreen(Screen):
    """
    Introduction screen that explains the game.
    """
    play_startup_music = True  # Enable music for this screen
    
    def __init__(self, game):
        super().__init__(game)
        # Background via image_manager
        self._background_original = image_manager.load_image('INTRO_BG')
        self.background_image = self._background_original
        # Get the assets path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(current_dir))
        assets_dir = os.path.join(root_dir, 'assets')
        font_path = os.path.join(assets_dir, PIXEL_FONT)
        
        # Load fonts
        try:
            self.title_font = pygame.font.Font(font_path, FONT_LARGE)
            self.text_font = pygame.font.Font(font_path, FONT_MEDIUM)
            button_font = font_path
        except Exception:
            self.title_font = pygame.font.SysFont('Arial', FONT_LARGE)
            self.text_font = pygame.font.SysFont('Arial', FONT_MEDIUM)
            button_font = None

        # Buttons with custom font
        open_account_button = Button(
            SCREEN_WIDTH // 2 - 150,
            SCREEN_HEIGHT - 150,
            300, 50,
            "Open Bank Account",
            font_name=button_font,
            action=self.open_bank_account
        )

        skip_button = Button(
            SCREEN_WIDTH // 2 - 150,
            SCREEN_HEIGHT - 80,
            300, 50,
            "Skip for Now",
            font_name=button_font,
            action=self.skip_bank_account
        )

        self.buttons = [open_account_button, skip_button]
        self.bg_color = BG_TOP

    def open_bank_account(self):
        """Open a bank account and continue."""
        from moneySmarts.models import BankAccount
        self.game.player.bank_account = BankAccount()
        self.game.player.bank_account.deposit(50)  # Parents give you $50 to start
        from moneySmarts.screens.base_screens import DebitCardScreen
        self.game.gui_manager.set_screen(DebitCardScreen(self.game))

    def skip_bank_account(self):
        """Skip opening a bank account and continue."""
        from moneySmarts.screens.game_screen import GameScreen
        self.game.gui_manager.set_screen(GameScreen(self.game))

    def draw(self, surface):
        """Draw the intro screen with a modern theme."""
        surface.fill(self.bg_color)
        # Title
        title_surface = self.title_font.render(f"Welcome, {self.game.player.name}!", True, BLACK)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 80))
        surface.blit(title_surface, title_rect)
        # Card panel for text
        panel = pygame.Rect(80, 130, SCREEN_WIDTH - 160, 360)
        pygame.draw.rect(surface, CARD_BG, panel, border_radius=12)
        pygame.draw.rect(surface, CARD_BORDER, panel, 2, border_radius=12)
        intro_lines = [
            "You're a 16-year-old high school student about to embark on your",
            "financial journey through life.",
            "",
            "Your parents suggest that you should open your first bank account.",
            "This will help you manage your money and start building good financial habits.",
            "",
            "Would you like to open a bank account now?"
        ]
        for i, line in enumerate(intro_lines):
            text_surface = self.text_font.render(line, True, BLACK)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 170 + i * 30))
            surface.blit(text_surface, text_rect)
        # Buttons
        for button in self.buttons:
            button.draw(surface)

class DebitCardScreen(Screen):
    """
    Screen for deciding whether to get a debit card.
    """
    play_startup_music = True  # Enable music for this screen
    
    def __init__(self, game):
        super().__init__(game)
        
        # Get assets path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(current_dir))
        assets_dir = os.path.join(root_dir, 'assets')
        font_path = os.path.join(assets_dir, PIXEL_FONT)
        
        # Load fonts
        try:
            self.title_font = pygame.font.Font(font_path, FONT_LARGE)
            self.text_font = pygame.font.Font(font_path, FONT_MEDIUM)
            self.card_font = pygame.font.Font(font_path, FONT_SMALL)
            button_font = font_path
        except Exception:
            self.title_font = pygame.font.SysFont('Arial', FONT_LARGE)
            self.text_font = pygame.font.SysFont('Arial', FONT_MEDIUM)
            self.card_font = pygame.font.SysFont('Arial', FONT_SMALL)
            button_font = None
            
        # Card dimensions
        self.card_width = 300
        self.card_height = 180

        # Buttons with custom font
        get_card_button = Button(
            SCREEN_WIDTH // 2 - 150,
            SCREEN_HEIGHT - 150,
            300, 50,
            "Get Debit Card",
            font_name=button_font,
            action=self.get_debit_card
        )

        skip_button = Button(
            SCREEN_WIDTH // 2 - 150,
            SCREEN_HEIGHT - 80,
            300, 50,
            "No Thanks",
            font_name=button_font,
            action=self.skip_debit_card
        )

        self.buttons = [get_card_button, skip_button]
        self.bg_color = BG_TOP

    def get_debit_card(self):
        """Get a debit card and continue."""
        from moneySmarts.models import Card
        self.game.player.debit_card = Card("Debit")
        from moneySmarts.screens.game_screen import GameScreen
        self.game.gui_manager.set_screen(GameScreen(self.game))

    def skip_debit_card(self):
        """Skip getting a debit card and continue."""
        from moneySmarts.screens.game_screen import GameScreen
        self.game.gui_manager.set_screen(GameScreen(self.game))

    def draw(self, surface):
        """Draw the debit card screen with modern theme."""
        surface.fill(self.bg_color)
        # Title
        title_surface = self.title_font.render("Congratulations!", True, BLACK)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 80))
        surface.blit(title_surface, title_rect)
        # Draw card
        card_x = SCREEN_WIDTH // 2 - self.card_width // 2
        card_y = 150
        card_rect = pygame.Rect(card_x, card_y, self.card_width, self.card_height)
        pygame.draw.rect(surface, PRIMARY, card_rect, border_radius=16)
        pygame.draw.rect(surface, PRIMARY_HOVER, card_rect, 3, border_radius=16)
        # Card text
        card_title = self.text_font.render("DEBIT", True, WHITE)
        card_title_rect = card_title.get_rect(center=(SCREEN_WIDTH // 2, card_y + 36))
        surface.blit(card_title, card_title_rect)
        name_text = self.card_font.render(self.game.player.name, True, WHITE)
        name_rect = name_text.get_rect(center=(SCREEN_WIDTH // 2, card_y + self.card_height // 2))
        surface.blit(name_text, name_rect)
        number_text = self.card_font.render("**** **** **** 1234", True, WHITE)
        number_rect = number_text.get_rect(center=(SCREEN_WIDTH // 2, card_y + self.card_height - 28))
        surface.blit(number_text, number_rect)
        # Explanation text
        text_lines = [
            "You've opened your first checking account!",
            "Your parents deposited $50 to get you started.",
            "",
            "Would you like a debit card with your account?",
            "A debit card lets you spend directly from checking."
        ]
        for i, line in enumerate(text_lines):
            text_surface = self.text_font.render(line, True, BLACK)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 360 + i * 28))
            surface.blit(text_surface, text_rect)
        # Buttons
        for button in self.buttons:
            button.draw(surface)

class EndGameScreen(Screen):
    """
    Screen shown at the end of the game.
    """
    play_startup_music = False  # Disable music for this screen    

    def __init__(self, game, reason):
        super().__init__(game)
        self.reason = reason

        # Fonts
        self.title_font = pygame.font.SysFont('Arial', FONT_TITLE)
        self.subtitle_font = pygame.font.SysFont('Arial', FONT_LARGE)
        self.text_font = pygame.font.SysFont('Arial', FONT_MEDIUM)

        # Calculate final stats
        self.cash = self.game.player.cash
        self.bank_balance = self.game.player.bank_account.balance if self.game.player.bank_account else 0
        self.credit_card_debt = self.game.player.credit_card.balance if self.game.player.credit_card else 0

        self.loan_debt = 0
        for loan in self.game.player.loans:
            self.loan_debt += loan.current_balance

        self.asset_value = 0
        for asset in self.game.player.assets:
            self.asset_value += asset.current_value

        self.net_worth = self.cash + self.bank_balance - self.credit_card_debt - self.loan_debt + self.asset_value

        # Financial rating
        if self.net_worth >= 1000000:
            self.rating = "Financial Wizard"
            self.rating_color = GREEN
        elif self.net_worth >= 500000:
            self.rating = "Financially Secure"
            self.rating_color = LIGHT_GREEN
        elif self.net_worth >= 100000:
            self.rating = "Financially Stable"
            self.rating_color = BLUE
        elif self.net_worth >= 0:
            self.rating = "Breaking Even"
            self.rating_color = YELLOW
        else:
            self.rating = "In Debt"
            self.rating_color = RED

        # Buttons
        quit_button = Button(
            SCREEN_WIDTH // 2 - 100,
            SCREEN_HEIGHT - 80,
            200, 50,
            "Quit Game",
            action=self.quit_game
        )

        self.buttons = [quit_button]

    def quit_game(self):
        """Quit the game."""
        self.game.gui_manager.running = False

    def draw_text(self, surface, text, x, y, center=False, is_title=False):
        """Helper method to draw text."""
        font = self.title_font if is_title else self.text_font
        text_surface = font.render(text, True, BLACK)
        if center:
            text_rect = text_surface.get_rect(center=(x, y))
        else:
            text_rect = text_surface.get_rect(topleft=(x, y))
        surface.blit(text_surface, text_rect)

    def draw(self, surface):
        """Draw the end game screen."""
        # Background
        surface.fill(WHITE)

        # Title
        if self.reason == "retirement":
            title = "CONGRATULATIONS ON YOUR RETIREMENT!"
            subtitle = "After {self.game.current_year} years, you've reached retirement age!"
        else:
            title = "GAME OVER"
            subtitle = "Your financial journey has ended after {self.game.current_year} years."

        title_surface = self.title_font.render(title, True, BLUE)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 60))
        surface.blit(title_surface, title_rect)

        subtitle_surface = self.subtitle_font.render(subtitle, True, BLACK)
        subtitle_rect = subtitle_surface.get_rect(center=(SCREEN_WIDTH // 2, 110))
        surface.blit(subtitle_surface, subtitle_rect)

        # Financial summary
        summary_title = self.subtitle_font.render("FINAL FINANCIAL SUMMARY", True, BLACK)
        summary_rect = summary_title.get_rect(center=(SCREEN_WIDTH // 2, 170))
        surface.blit(summary_title, summary_rect)

        summary_items = [
            f"Cash: ${self.cash:.2f}",
            f"Bank Balance: ${self.bank_balance:.2f}",
            f"Credit Card Debt: ${self.credit_card_debt:.2f}",
            f"Loan Debt: ${self.loan_debt:.2f}",
            f"Asset Value: ${self.asset_value:.2f}",
            f"Net Worth: ${self.net_worth:.2f}",
            f"Credit Score: {self.game.player.credit_score}"
        ]

        for i, item in enumerate(summary_items):
            text_surface = self.text_font.render(item, True, BLACK)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, 210 + i * 30))
            surface.blit(text_surface, text_rect)

        # Family summary
        if self.game.player.family:
            family_title = self.subtitle_font.render("FAMILY", True, BLACK)
            family_rect = family_title.get_rect(center=(SCREEN_WIDTH // 2, 430))
            surface.blit(family_title, family_rect)

            y_pos = 470
            for member in self.game.player.family:
                if member["relation"] == "Spouse":
                    text = f"Spouse: Age {member['age'] + self.game.current_year}"
                else:
                    text = f"{member['relation']}: {member['name']}, Age {member['age'] + self.game.current_year}"

                text_surface = self.text_font.render(text, True, BLACK)
                text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
                surface.blit(text_surface, text_rect)
                y_pos += 30

        # Financial rating
        rating_title = self.subtitle_font.render("Financial Rating:", True, BLACK)
        rating_rect = rating_title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 180))
        surface.blit(rating_title, rating_rect)

        rating_text = self.title_font.render(self.rating, True, self.rating_color)
        rating_text_rect = rating_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 140))
        surface.blit(rating_text, rating_text_rect)

        # Thank you message
        thanks_text = self.text_font.render("Thank you for playing MONEY SMARTZ!", True, BLACK)
        thanks_rect = thanks_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 110))
        surface.blit(thanks_text, thanks_rect)

        # Draw buttons
        for button in self.buttons:
            button.draw(surface)
