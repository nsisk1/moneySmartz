"""Quick UI smoke tester that bypasses main.py's Python-version guard.
This script initializes pygame, creates a Game and GUIManager, sets the TitleScreen,
renders one frame and exits. It prints any exceptions to stdout for debugging.

Run with: python run_ui_test.py
"""
import traceback
import time

import pygame

from moneySmarts import Game, GUIManager
from moneySmarts.screens import TitleScreen


def main():
    try:
        pygame.init()
        pygame.font.init()
        try:
            pygame.mixer.init()
        except Exception:
            print("(Warning) mixer init failed; continuing without sound")
        screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
        pygame.display.set_caption("Money Smartz - Smoke Test")

        game = Game()
        game.screen = screen
        gui = GUIManager(game)
        game.gui_manager = gui

        # Set title screen
        gui.set_screen(TitleScreen(game))

        # Draw a single frame
        try:
            gui.current_screen.draw(gui.screen)
            pygame.display.flip()
            print("Rendered TitleScreen OK")
        except Exception as e:
            print("Error drawing TitleScreen:")
            traceback.print_exc()

        # Pause briefly so the window has time to appear in interactive runs
        time.sleep(0.5)

    except Exception:
        print("Exception during smoke test:")
        traceback.print_exc()
    finally:
        try:
            pygame.quit()
        except Exception:
            pass


if __name__ == '__main__':
    main()

