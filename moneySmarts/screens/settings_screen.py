import pygame
from moneySmarts.constants import *
from moneySmarts.ui import Screen, Button
from moneySmarts.config_manager import Config

class SettingsScreen(Screen):
    def __init__(self, game):
        super().__init__(game)
        self.create_buttons()

    def create_buttons(self):
        current_theme = Config.get('theme', 'modern')
        current_music = Config.get('music_track', 'ambient_city')
        self.buttons = [
            Button(SCREEN_WIDTH // 2 - 150, 150, 300, 50, f"Theme: {current_theme}", self.toggle_theme),
            Button(SCREEN_WIDTH // 2 - 150, 220, 300, 50, f"Music: {current_music}", self.next_music_track),
            Button(SCREEN_WIDTH // 2 - 150, 290, 140, 50, "- Volume", self.decrease_volume),
            Button(SCREEN_WIDTH // 2 + 10, 290, 140, 50, "+ Volume", self.increase_volume),
            Button(SCREEN_WIDTH // 2 - 150, 400, 300, 50, "Back", self.go_back),
        ]

    def handle_events(self, events):
        super().handle_events(events)

    def toggle_theme(self):
        current_theme = Config.get('theme', 'modern')
        new_theme = 'classic' if current_theme == 'modern' else 'modern'
        Config.set('theme', new_theme)
        self.game.restart()

    def next_music_track(self):
        available_music = self.game.gui_manager.sound_manager.get_available_music()
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
        self.game.gui_manager.sound_manager.set_active_music(new_music)
        self.create_buttons() # Refresh buttons to show new music track

    def decrease_volume(self):
        volume = self.game.gui_manager.sound_manager.get_volume()
        self.game.gui_manager.sound_manager.set_volume(max(0.0, volume - 0.1))

    def increase_volume(self):
        volume = self.game.gui_manager.sound_manager.get_volume()
        self.game.gui_manager.sound_manager.set_volume(min(1.0, volume + 0.1))

    def go_back(self):
        from moneySmarts.screens.base_screens import TitleScreen
        self.game.gui_manager.set_screen(TitleScreen(self.game))

    def draw(self, surface):
        surface.fill(BG_TOP)
        title_font = pygame.font.SysFont('Arial', FONT_TITLE)
        title_surface = title_font.render("Settings", True, BLACK)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 80))
        surface.blit(title_surface, title_rect)

        for button in self.buttons:
            button.draw(surface)
