"""
Money Smartz: Financial Life Simulator

This is the main entry point for the Money Smartz game.
It initializes the game and starts the main game loop.
"""

import sys
import logging
import traceback

# Load environment variables from .env if present (for cloud config)
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except ImportError:
    # dotenv not installed, which is fine if not using a .env file.
    pass

# --- Python version guard (pygame wheels not yet for 3.14; project targets 3.11/3.12) ---
if not ((3, 11) <= sys.version_info < (3, 13)):
    print(f"Unsupported Python version {sys.version.split()[0]} detected.\n"
          "Use Python 3.11 or 3.12. (Current pyproject requires >=3.11,<3.13)\n"
          "Fix: Install Python 3.12, recreate venv, then: pip install -r requirements.txt")
    sys.exit(1)

# Delay pygame import until after version check for clearer messaging
try:
    import pygame
except ModuleNotFoundError:
    print("pygame not installed. In an activated venv run: pip install -r requirements.txt")
    sys.exit(1)

from moneySmarts import Game, GUIManager
from moneySmarts.screens import TitleScreen
from moneySmarts.exceptions import GameError
from moneySmarts.constants import SCREEN_WIDTH, SCREEN_HEIGHT

def main() -> None:
    """
    Main function that initializes and runs the game.
    Sets up error logging and handles uncaught exceptions.
    """
    # Set up logging
    logging.basicConfig(
        filename='money_smarts.log',
        level=logging.ERROR,
        format='%(asctime)s %(levelname)s %(name)s %(message)s'
    )
    try:
        # Initialize pygame
        pygame.init()
        pygame.font.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            print("Warning: Audio mixer init failed - continuing without sound.")

        # Make the window resizable
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Money Smartz")

        # Create a game instance
        game = Game()
        game.screen = screen

        # Create a GUI manager
        gui_manager = GUIManager(game)
        game.gui_manager = gui_manager

        # Show the TitleScreen
        gui_manager.set_screen(TitleScreen(game))

        # Main game loop
        gui_manager.run()
    except (GameError, pygame.error) as e:
        logging.error(f"A critical error occurred: {e}", exc_info=True)
        print(f"A critical error occurred: {e}. Check logs for details.")
        traceback.print_exc()
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}. Please check money_smarts.log for details.")
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    main()
