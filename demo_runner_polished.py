"""Polished demo runner
- Smooth fades between screens
- Plays startup/click/success SFX where appropriate
- Shows modal confirmations and waits for user-like acknowledgement
- Saves screenshots to release/demo_screenshots/
"""
import os
import time
import traceback
import pygame

from moneySmarts import Game
from moneySmarts.ui import GUIManager

OUT_DIR = os.path.join(os.path.dirname(__file__), 'release', 'demo_screenshots')
os.makedirs(OUT_DIR, exist_ok=True)

def fade(surface, gui, fade_in=True, duration=0.5):
    start = time.time()
    clock = pygame.time.Clock()
    while True:
        t = time.time() - start
        if t >= duration:
            break
        alpha = int(255 * (t / duration)) if fade_in else int(255 * (1 - (t / duration)))
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 255 - alpha) if fade_in else (0,0,0,alpha))
        try:
            gui.current_screen.draw(surface)
        except Exception:
            pass
        surface.blit(overlay, (0,0))
        try:
            pygame.display.flip()
        except Exception:
            pass
        clock.tick(60)


def wait_and_draw(gui, seconds=1.2, screenshot_name=None, caption=None):
    end = time.time() + seconds
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Arial', 20)
    while time.time() < end:
        try:
            events = pygame.event.get()
            for ev in events:
                if ev.type == pygame.QUIT:
                    return False
            if gui.current_screen:
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
            # draw caption overlay if provided
            if caption:
                try:
                    txt = font.render(caption, True, (240,240,240))
                    gui.screen.blit(txt, (18, gui.screen.get_height() - 36))
                except Exception:
                    pass
            try:
                pygame.display.flip()
            except Exception:
                pass
            clock.tick(60)
        except Exception:
            traceback.print_exc()
            return False
    if screenshot_name:
        try:
            path = os.path.join(OUT_DIR, screenshot_name)
            pygame.image.save(gui.screen, path)
        except Exception:
            traceback.print_exc()
    # After drawing, if a modal or modal_popup exists, try to auto-confirm it for smooth demo flow
    try:
        cur = getattr(gui, 'current_screen', None)
        modal = getattr(cur, 'modal', None) or getattr(cur, 'modal_popup', None) or getattr(cur, 'popup', None)
        if modal:
            # prefer well-known hooks
            if hasattr(modal, 'on_ok') and callable(modal.on_ok):
                try:
                    modal.on_ok()
                except Exception:
                    pass
            elif hasattr(modal, 'on_confirm') and callable(modal.on_confirm):
                try:
                    modal.on_confirm()
                except Exception:
                    pass
            elif hasattr(modal, 'on_accept') and callable(modal.on_accept):
                try:
                    modal.on_accept()
                except Exception:
                    pass
    except Exception:
        pass
    return True


def click_button_by_text(screen, text, gui):
    for b in getattr(screen, 'buttons', []):
        if getattr(b, 'text', '').strip().lower() == text.strip().lower():
            mp = b.rect.center
            try:
                act = None
                try:
                    act = b.update(mp, True, [])
                except TypeError:
                    act = b.update(mp, True)
                if callable(act):
                    act()
                    # small post-click pause
                    time.sleep(0.18)
                    try:
                        if getattr(gui, 'sound_manager', None):
                            gui.sound_manager.play_sfx('click')
                    except Exception:
                        pass
                    return True
            except Exception:
                traceback.print_exc()
                return False
    return False


def run_demo():
    pygame.init()
    pygame.font.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass
    screen = pygame.display.set_mode((1024, 720), pygame.RESIZABLE)
    pygame.display.set_caption('MoneySmartz Polished Demo')

    game = Game()
    game.screen = screen
    gui = GUIManager(game)
    game.gui_manager = gui

    # Show Title
    from moneySmarts.screens.base_screens import TitleScreen
    title = TitleScreen(game)
    gui.set_screen(title)
    # Play startup once
    try:
        if getattr(gui, 'sound_manager', None):
            gui.sound_manager.play_sfx('startup')
            time.sleep(0.12)
    except Exception:
        pass
    fade(screen, gui, fade_in=True, duration=0.6)
    wait_and_draw(gui, 1.4, '01_title.png')

    # Start New Game
    click_button_by_text(title, 'Start New Game', gui)
    wait_and_draw(gui, 0.8, caption='Starting new game...')

    # Name input
    if isinstance(gui.current_screen, object):
        from moneySmarts.screens.base_screens import NameInputScreen
        if isinstance(gui.current_screen, NameInputScreen):
            cur = gui.current_screen
            # fill name
            try:
                cur.name_input.text = 'Demo Player'
            except Exception:
                pass
            click_button_by_text(cur, 'Start Game', gui)
    wait_and_draw(gui, 1.0, '02_name.png')

    # Intro
    wait_and_draw(gui, 0.8, caption='Intro...')
    cur = gui.current_screen
    # prefer Open Bank Account if present
    click_button_by_text(cur, 'Open Bank Account', gui) or click_button_by_text(cur, 'Skip for Now', gui)
    wait_and_draw(gui, 1.0, '03_intro.png', caption='Intro complete')

    # If DebitCardScreen shown, accept card then proceed
    wait_and_draw(gui, 0.6, caption='Preparing debit card...')
    cur = gui.current_screen
    click_button_by_text(cur, 'Get Debit Card', gui) or click_button_by_text(cur, 'No Thanks', gui)
    wait_and_draw(gui, 1.0, '04_debitcard.png', caption='Debit card step')

    # Now at GameScreen; open banking via button
    cur = gui.current_screen
    # try Bank button
    click_button_by_text(cur, 'Banking', gui)
    wait_and_draw(gui, 1.2, '05_bank.png')

    # If bank screen has Deposit button, press it to show modal
    cur = gui.current_screen
    click_button_by_text(cur, 'Deposit', gui)
    wait_and_draw(gui, 0.8, '06_deposit.png', caption='Deposit dialog')
    # If modal appears on deposit screen, auto-confirm and capture it
    cur = gui.current_screen
    wait_and_draw(gui, 0.8, '07_modal.png', caption='Confirming deposit...')

    # Final frame at Title
    from moneySmarts.screens.base_screens import TitleScreen
    gui.set_screen(TitleScreen(game))
    fade(screen, gui, fade_in=True, duration=0.5)
    wait_and_draw(gui, 1.0, '08_end.png')

    # Play success sfx at end
    try:
        if getattr(gui, 'sound_manager', None):
            gui.sound_manager.play_sfx('success')
    except Exception:
        pass

    pygame.quit()
    print('Demo finished; screenshots in', OUT_DIR)

if __name__ == '__main__':
    run_demo()
