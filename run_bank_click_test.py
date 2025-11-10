"""Test whether the Banking button on GameScreen opens BankScreen when invoked."""
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
    # create a player minimal
    from moneySmarts.models import Player
    p = Player('Tester')
    p.cash = 100
    p.age = 20
    p.bank_account = None
    game.player = p
    game.screen = screen
    gui = GUIManager(game)
    game.gui_manager = gui

    gs = GameScreen(game)
    gui.set_screen(gs)
    # find banking button
    bank_btn = None
    for b in gs.buttons:
        if getattr(b, 'text', '') == 'Banking':
            bank_btn = b
            break
    print('Bank button found:', bool(bank_btn))
    if not bank_btn:
        print('Buttons:', [getattr(b,'text',None) for b in gs.buttons])
        return
    mp = bank_btn.rect.center
    try:
        act = None
        try:
            act = bank_btn.update(mp, True, [])
        except TypeError:
            act = bank_btn.update(mp, True)
        print('update returned callable:', callable(act))
        if callable(act):
            act()
            print('Invoked action; current screen:', type(gui.current_screen).__name__)
        else:
            print('No action returned; check hovered:', bank_btn.hovered)
    except Exception:
        print('Exception invoking action:')
        traceback.print_exc()

if __name__ == '__main__':
    main()

