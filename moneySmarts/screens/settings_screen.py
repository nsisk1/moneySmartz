import os
import pygame
from moneySmarts.constants import *
from moneySmarts.ui import Screen, Button
from moneySmarts.config_manager import Config
from moneySmarts.screens.screen_utils import load_ui_background, draw_background
from moneySmarts.images import get_image_path

class SettingsScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self._background_original = load_ui_background('SETTINGS_BG')
        self.create_buttons()

    def create_buttons(self):
        current_theme = Config.get('theme', 'modern')
        current_music = Config.get('music_track', 'ambient_city')
        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 150, 150, 300, 50, f"Theme: {current_theme}", action=self.toggle_theme),
            Button(SCREEN_WIDTH // 2 - 150, 220, 300, 50, f"Music: {current_music}", action=self.next_music_track),
            Button(SCREEN_WIDTH // 2 - 150, 290, 300, 40, "Play Sample", action=self.test_play_music),
            Button(SCREEN_WIDTH // 2 - 150, 340, 300, 40, "Test SFX", action=self.test_play_sfx),
            Button(SCREEN_WIDTH // 2 - 150, 400, 140, 50, "- Volume", action=self.decrease_volume),
            Button(SCREEN_WIDTH // 2 + 10, 400, 140, 50, "+ Volume", action=self.increase_volume),
            Button(SCREEN_WIDTH // 2 - 150, 470, 300, 50, "Back", action=self.go_back),
        ]

    def handle_events(self, events):
        super().handle_events(events)

    def toggle_theme(self):
        current_theme = Config.get('theme', 'modern')
        new_theme = 'classic' if current_theme == 'modern' else 'modern'
        Config.set('theme', new_theme)
        # Play click SFX
        self._play_click()
        # Refresh UI: try to navigate back to the title screen so the theme takes effect.
        try:
            from moneySmarts.screens.base_screens import TitleScreen
            gm = getattr(self.game, 'gui_manager', None)
            if gm and getattr(gm, 'set_screen', None):
                gm.set_screen(TitleScreen(self.game))
                return
        except Exception:
            pass

        # Fallback: if the game provides a restart hook, call it; otherwise just refresh buttons
        try:
            if hasattr(self.game, 'restart') and callable(self.game.restart):
                self.game.restart()
                return
        except Exception:
            pass

        # Final fallback: update buttons to reflect new theme label
        try:
            self.create_buttons()
        except Exception:
            pass

    def next_music_track(self):
        gm = getattr(self.game, 'gui_manager', None)
        available_music = []
        if gm and getattr(gm, 'sound_manager', None):
            try:
                available_music = gm.sound_manager.get_available_music()
            except Exception:
                available_music = []
        if not available_music:
            return
        current_music = Config.get('music_track', available_music[0])
        try:
            current_index = available_music.index(current_music)
            next_index = (current_index + 1) % len(available_music)
        except ValueError:
            next_index = 0
        new_music = available_music[next_index]
        Config.set('music_track', new_music)
        # activate music and play click via helper
        if gm and getattr(gm, 'sound_manager', None):
            try:
                gm.sound_manager.set_active_music(new_music)
            except Exception:
                pass
        self._play_click()
        self.create_buttons() # Refresh buttons to show new music track

    def decrease_volume(self):
        gm = getattr(self.game, 'gui_manager', None)
        if gm and getattr(gm, 'sound_manager', None):
            try:
                vol = gm.sound_manager.get_volume()
                gm.sound_manager.set_volume(max(0.0, vol - 0.1))
            except Exception:
                pass
        self._play_click()

    def increase_volume(self):
        gm = getattr(self.game, 'gui_manager', None)
        if gm and getattr(gm, 'sound_manager', None):
            try:
                vol = gm.sound_manager.get_volume()
                gm.sound_manager.set_volume(min(1.0, vol + 0.1))
            except Exception:
                pass
        self._play_click()

    def go_back(self):
        from moneySmarts.screens.base_screens import TitleScreen
        gm = getattr(self.game, 'gui_manager', None)
        try:
            if gm and getattr(gm, 'sound_manager', None):
                gm.sound_manager.play_sfx('click')
        except Exception:
            pass
        try:
            if gm and getattr(gm, 'set_screen', None):
                gm.set_screen(TitleScreen(self.game))
        except Exception:
            # fallback: try to set via game.gui_manager if later available
            try:
                if getattr(self.game, 'gui_manager', None):
                    self.game.gui_manager.set_screen(TitleScreen(self.game))
            except Exception:
                pass

    def _play_click(self):
        """Try to play a 'click' SFX using GUI manager SoundManager; fallback to loading a 'click' file from assets/sfx."""
        gm = getattr(self.game, 'gui_manager', None)
        # Try GUI manager sound manager first
        try:
            if gm and getattr(gm, 'sound_manager', None):
                gm.sound_manager.play_sfx('click')
                return
        except Exception:
            pass

        # Fallback: try to play directly from assets/sfx/<click.*>
        try:
            if not pygame.mixer.get_init():
                return
            # Find assets/sfx directory relative to package
            current_dir = os.path.dirname(os.path.dirname(__file__))
            sfx_dir = os.path.join(current_dir, 'assets', 'sfx')
            if not os.path.isdir(sfx_dir):
                return
            for fname in os.listdir(sfx_dir):
                if fname.lower().startswith('click') and fname.lower().endswith(('.wav', '.ogg', '.mp3')):
                    path = os.path.join(sfx_dir, fname)
                    try:
                        snd = pygame.mixer.Sound(path)
                        snd.play()
                        return
                    except Exception:
                        continue
        except Exception:
            pass

    def draw(self, surface):
        draw_background(surface, self._background_original, default_color=BG_TOP)
        title_font = pygame.font.SysFont('Arial', FONT_TITLE)
        title_surface = title_font.render("Settings", True, BLACK)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 80))
        surface.blit(title_surface, title_rect)

        for button in self.buttons:
            button.draw(surface)

    def test_play_music(self):
        """Play the active music track immediately for testing."""
        gm = getattr(self.game, 'gui_manager', None)
        if gm and getattr(gm, 'sound_manager', None):
            active = Config.get('music_track', None)
            if not active:
                # pick first available
                av = gm.sound_manager.get_available_music()
                if av:
                    active = av[0]
            if active:
                try:
                    print(f"Settings: testing play music '{active}'")
                    gm.sound_manager.play_music(active)
                except Exception:
                    pass
        else:
            print("Settings: GUIManager or SoundManager not available for play_music test")

    def test_play_sfx(self):
        """Play a 'click' SFX immediately for testing."""
        gm = getattr(self.game, 'gui_manager', None)
        if gm and getattr(gm, 'sound_manager', None):
            try:
                print("Settings: testing play_sfx 'click'")
                gm.sound_manager.play_sfx('click')
            except Exception:
                pass
        else:
            # fallback direct attempt
            try:
                if pygame.mixer.get_init():
                    # try to find click in assets/audio or assets/sfx
                    current_dir = os.path.dirname(os.path.dirname(__file__))
                    for sub in ('audio', 'sfx'):
                        d = os.path.join(current_dir, 'assets', sub)
                        if os.path.isdir(d):
                            for fname in os.listdir(d):
                                if fname.lower().startswith('click') and fname.lower().endswith(('.wav', '.ogg', '.mp3')):
                                    try:
                                        snd = pygame.mixer.Sound(os.path.join(d, fname))
                                        snd.play()
                                        print(f"Settings: played fallback click from {fname}")
                                        return
                                    except Exception:
                                        continue
            except Exception:
                pass
            print("Settings: no audio available to play SFX")
