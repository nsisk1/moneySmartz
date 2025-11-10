"""Automated demo runner for Money Smartz.
This script programmatically navigates a short path through the UI to produce
an interactive demo without manual clicks. It draws each screen for a few
seconds so you can present it or capture video/screenshots.

Sequence:
 - TitleScreen (show)
 - Start New Game (programmatically invoke)
 - NameInputScreen (fill name and Start)
 - IntroScreen (choose to open bank account)
 - DebitCardScreen -> skip or accept, then GameScreen
 - In GameScreen, open Banking screen

Run with: python demo_runner.py
"""
import time
import traceback
import pygame

from moneySmarts import Game, GUIManager
from moneySmarts.screens.base_screens import TitleScreen, NameInputScreen
from moneySmarts.screens.game_screen import GameScreen
from moneySmarts.constants import SCREEN_WIDTH, SCREEN_HEIGHT

DELAY = 1.2


def draw_and_wait(gui, seconds=DELAY):
    # Draw current screen a few frames so it is visible
    end = time.time() + seconds
    while time.time() < end:
        try:
            events = pygame.event.get()
            # allow window to be closed gracefully
            for ev in events:
                if ev.type == pygame.QUIT:
                    return False
            if getattr(gui, 'current_screen', None):
                try:
                    gui.current_screen.handle_events(events)
                except Exception:
                    pass
                try:
                    gui.current_screen.update()
                except Exception:
                    pass
                try:
                    gui.current_screen.draw(gui.screen)
                except Exception:
                    pass
            try:
                pygame.display.flip()
            except Exception:
                pass
            try:
                if getattr(gui, 'clock', None):
                    gui.clock.tick(30)
            except Exception:
                time.sleep(1 / 30)
        except Exception:
            traceback.print_exc()
            break
    return True


def click_button_by_text(screen, text):
    # Find a button by text and invoke its action wrapper if present
    for b in getattr(screen, 'buttons', []):
        if getattr(b, 'text', '').strip().lower() == text.strip().lower():
            # use center of rect as mouse pos
            mp = b.rect.center
            try:
                act = None
                try:
                    act = b.update(mp, True, [])
                except TypeError:
                    act = b.update(mp, True)
                if callable(act):
                    act()
                    return True
            except Exception:
                traceback.print_exc()
                return False
    return False


def demo():
    pygame.init()
    pygame.font.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Money Smartz - Demo")

    game = Game()
    game.screen = screen
    gui = GUIManager(game)
    game.gui_manager = gui

    # 1) Title
    title = TitleScreen(game)
    gui.set_screen(title)
    print('Showing TitleScreen')
    if not draw_and_wait(gui, 1.5):
        return

    # 2) Press Start New Game
    print('Invoking Start New Game')
    if not click_button_by_text(title, 'Start New Game') and not click_button_by_text(title, 'Start Game'):
        print('Start button click failed; aborting demo')
        return
    # Let NameInputScreen initialize
    if not draw_and_wait(gui, 0.8):
        return

    # 3) Fill name on NameInputScreen
    cur = gui.current_screen
    if isinstance(cur, NameInputScreen):
        print('Filling name and starting game')
        try:
            cur.name_input.text = 'Demo Player'
            # call the Start Game button (text may be 'Start Game')
            click_button_by_text(cur, 'Start Game')
        except Exception:
            traceback.print_exc()
    else:
        print('Unexpected screen after start:', type(cur).__name__)
    if not draw_and_wait(gui, 1.0):
        return

    # 4) We're likely at IntroScreen; if so choose Open Bank Account
    cur = gui.current_screen
    print('Current screen after name:', type(cur).__name__)
    try:
        # Try to click a button labelled 'Open Bank Account' or 'Skip for Now'
        if click_button_by_text(cur, 'Open Bank Account'):
            print('Chose Open Bank Account')
        else:
            click_button_by_text(cur, 'Skip for Now')
            print('Skipped bank account (if present)')
    except Exception:
        traceback.print_exc()
    if not draw_and_wait(gui, 1.2):
        return

    # 5) If we reached GameScreen, open Banking
    cur = gui.current_screen
    print('Current screen now:', type(cur).__name__)
    if isinstance(cur, GameScreen):
        print('Opening banking menu')
        try:
            cur.open_bank_account()
        except Exception:
            traceback.print_exc()
        draw_and_wait(gui, 1.5)
    else:
        # try to navigate to GameScreen manually
        try:
            from moneySmarts.screens.game_screen import GameScreen as GS
            gs = GS(game)
            gui.set_screen(gs)
            draw_and_wait(gui, 1.0)
        except Exception:
            traceback.print_exc()

    print('Demo finished — displaying Title briefly before exit')
    gui.set_screen(TitleScreen(game))
    draw_and_wait(gui, 1.2)

    pygame.quit()


if __name__ == '__main__':
    demo()

