"""Test clicking 'Look for a Job' and applying for the first listed job.
Prints whether a modal confirmation was created (job offer or rejection).
"""
import pygame
import traceback
from moneySmarts import Game, GUIManager
from moneySmarts.screens.game_screen import GameScreen


def main():
    try:
        pygame.init()
        pygame.font.init()
    except Exception:
        pass
    screen = pygame.display.set_mode((800, 600))
    game = Game()
    from moneySmarts.models import Player
    p = Player('Worker')
    p.age = 18
    p.education = 'High School'
    p.job = None
    p.salary = 0
    p.cash = 100
    game.player = p
    game.screen = screen
    gui = GUIManager(game)
    game.gui_manager = gui

    gs = GameScreen(game)
    gui.set_screen(gs)

    # find Look for a Job button
    job_btn = None
    for b in gs.buttons:
        if getattr(b, 'text', '').lower().startswith('look for'):
            job_btn = b
            break
    print('Job button found:', bool(job_btn))
    if not job_btn:
        print('Buttons:', [getattr(b,'text',None) for b in gs.buttons])
        return

    # invoke job button
    mp = job_btn.rect.center
    try:
        act = None
        try:
            act = job_btn.update(mp, True, [])
        except TypeError:
            act = job_btn.update(mp, True)
        print('update returned callable:', callable(act))
        if callable(act):
            act()
            print('Invoked job button; current screen:', type(gui.current_screen).__name__)
        else:
            print('No action returned; hovered:', job_btn.hovered)
            return
    except Exception:
        print('Exception invoking job button:')
        traceback.print_exc()
        return

    # Now on JobSearchScreen: find job option buttons (excluding Back)
    js = gui.current_screen
    print('JobScreen type:', type(js).__name__)
    job_option = None
    for b in js.buttons:
        t = getattr(b, 'text', '')
        if t.lower().startswith('back'):
            continue
        if '-' in t:
            job_option = b
            break
    print('Found job option:', bool(job_option))
    if not job_option:
        return

    # click first job
    mp = job_option.rect.center
    try:
        act = None
        try:
            act = job_option.update(mp, True, [])
        except TypeError:
            act = job_option.update(mp, True)
        print('job update returned callable:', callable(act))
        if callable(act):
            act()
            print('Applied for job; modal_popup present:', hasattr(js, 'modal_popup') and js.modal_popup is not None)
            if hasattr(js, 'modal_popup') and js.modal_popup:
                # print popup text if available
                try:
                    print('Popup text:', js.modal_popup.text)
                except Exception:
                    pass
    except Exception:
        print('Exception invoking job option:')
        traceback.print_exc()

if __name__ == '__main__':
    main()

