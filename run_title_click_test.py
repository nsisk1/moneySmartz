"""Test script that synthesizes a mouse click on the TitleScreen "Start New Game" button
and reports whether the TitleScreen responded (show_confirm flag or screen transition).
"""
import traceback
import time
import pygame

from moneySmarts import Game, GUIManager
from moneySmarts.screens.base_screens import TitleScreen
from moneySmarts.constants import SCREEN_WIDTH, SCREEN_HEIGHT


def main():
    try:
        pygame.init()
        pygame.font.init()
        try:
            pygame.mixer.init()
        except Exception:
            pass
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Title Click Test")

        game = Game()
        game.screen = screen
        gui = GUIManager(game)
        game.gui_manager = gui

        title = TitleScreen(game)
        gui.set_screen(title)

        # Find the start button by its text label (exact match used in code)
        start_btn = None
        for b in title.buttons:
            if getattr(b, 'text', '') == 'Start New Game' or getattr(b, 'text', '') == 'Start Game':
                start_btn = b
                break

        if not start_btn:
            print('Start button not found; available:', [getattr(b,'text',None) for b in title.buttons])
            return

        # Simulate moving the mouse to the button's center then clicking
        x, y = start_btn.rect.center
        # Inject a MOUSEMOTION first so hover state could be updated by event-based handlers
        ev_motion = pygame.event.Event(pygame.MOUSEMOTION, {'pos': (x, y), 'rel': (0,0), 'buttons': (0,0,0)})
        ev_down = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': (x, y), 'button': 1})
        ev_up = pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (x, y), 'button': 1})

        # Call handle_events with the synthetic events
        print('Before click: show_confirm=', getattr(title, 'show_confirm', None))
        title.handle_events([ev_motion, ev_down, ev_up])
        print('After click: show_confirm=', getattr(title, 'show_confirm', None))
        # If show_confirm True, that indicates the button fired and asked for confirmation
        # If TitleScreen navigated away, gui.current_screen will not be title
        print('Current GUI screen:', type(gui.current_screen).__name__)

        # --- DIRECT CHECK: call Button.update directly to see returned action ---
        try:
            mouse_pos = (x, y)
            act = None
            try:
                act = start_btn.update(mouse_pos, True, [ev_motion, ev_down, ev_up])
            except TypeError:
                act = start_btn.update(mouse_pos, True)
            print('Direct start_btn.update returned:', 'callable' if callable(act) else act)
            if callable(act):
                print('Invoking direct action wrapper...')
                act()
                print('After direct invoke: show_confirm=', getattr(title, 'show_confirm', None))
        except Exception:
            print('Exception during direct update/invoke:')
            traceback.print_exc()

    except Exception:
        print('Exception during title click test:')
        traceback.print_exc()
    finally:
        try:
            pygame.quit()
        except Exception:
            pass


if __name__ == '__main__':
    main()
