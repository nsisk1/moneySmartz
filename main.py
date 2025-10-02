"""
Money Smartz: Financial Life Simulator

This is the main entry point for the Money Smartz game.
It initializes the game and starts the main game loop.
"""

import sys
from typing import NoReturn

# --- Python version guard (pygame wheels not yet for 3.14; project targets 3.11/3.12) ---
if not ((3, 11) <= sys.version_info < (3, 13)):
    print("Unsupported Python version {sys.version.split()[0]} detected.\n"
          "Use Python 3.11 or 3.12. (Current pyproject requires >=3.11,<3.13)\n"
          "Fix: Install Python 3.12, recreate venv, then: pip install -r requirements.txt")
    sys.exit(1)

# Delay pygame import until after version check for clearer messaging
try:
    import pygame
except ModuleNotFoundError:
    print("pygame not installed. In an activated venv run: pip install -r requirements.txt")
    sys.exit(1)

import traceback
import logging
from moneySmarts import Game, GUIManager
from moneySmarts.screens import TitleScreen
from moneySmarts.exceptions import GameError

# GUI Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60
# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_GRAY = (230, 230, 230)
DARK_GRAY = (100, 100, 100)
BLUE = (0, 120, 255)
LIGHT_BLUE = (100, 180, 255)
GREEN = (0, 200, 0)

def show_loading_screen(screen):
    """Display the welcome/loading image until the next screen is ready."""
    from moneySmarts.images import get_image_path
    img_path = get_image_path("LOADING_SCREEN")
    try:
        image = pygame.image.load(img_path)
        image = pygame.transform.scale(image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except Exception:
        screen.fill((255, 255, 255))
        pygame.display.flip()
        return
    screen.blit(image, (0, 0))
    pygame.display.flip()
    # Wait briefly or until a key/mouse event (optional: 1.5 s splash)
    pygame.time.wait(1500)

def play_intro_video(screen):
    """Play the welcome video as the loading screen. Falls back to the static image if the video fails."""
    try:
        import cv2
    except ImportError:
        show_loading_screen(screen)
        return
    video_path = 'assets/video/images/money smarts welcome screen.mp4'
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        show_loading_screen(screen)
        return
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    surf_size = (screen.get_width(), screen.get_height())
    clock = pygame.time.Clock()
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, surf_size)
        surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        screen.blit(surf, (0, 0))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()
        clock.tick(fps)
    cap.release()


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
        except Exception:
            print("Warning: Audio mixer init failed - continuing without sound.")

        # Make the window resizable (use constants)
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Money Smartz")

        # Create a game instance
        game = Game()
        game.screen = screen  # Pass screen to game if needed

        # Create a GUI manager
        gui_manager = GUIManager(game)
        game.gui_manager = gui_manager

        # Show loading/welcome video (auto-plays, no input required)
        play_intro_video(screen)

        # After video, show the TitleScreen with buttons
        gui_manager.set_screen(TitleScreen(game))

        # Main game loop
        gui_manager.run()
    except GameError as ge:
        logging.error("Game error: {ge}")
        print("A game error occurred: {ge}")
    except Exception:
        logging.error("Uncaught exception:", exc_info=True)
        print("An unexpected error occurred. Please check money_smarts.log for details.")
        traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()
