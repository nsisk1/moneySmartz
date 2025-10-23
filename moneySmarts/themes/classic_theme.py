import logging
import pygame
import os
from pygame.surface import Surface
from pygame.locals import *
from moneySmarts.constants import *
from moneySmarts.sound_manager import SoundManager
from moneySmarts.event_manager import EventBus
from moneySmarts.config_manager import Config

def draw_vertical_gradient(surface, rect, top_color, bottom_color):
    x, y, w, h = rect
    if h <= 0:
        return
    for i in range(h):
        ratio = i / max(1, h - 1)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        pygame.draw.line(surface, (r, g, b), (x, y + i), (x + w - 1, y + i))

def draw_rounded_rect(surface, color, rect, radius=10, width=0):
    pygame.draw.rect(surface, color, rect, width, border_radius=radius)

class Button:
    def __init__(self, x, y, width, height, text, color=PRIMARY, hover_color=PRIMARY_HOVER,
                 text_color=PRIMARY_TEXT, font_size=FONT_MEDIUM, font_name=None, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        try:
            if font_name:
                self.font = pygame.font.Font(font_name, font_size)
            else:
                self.font = pygame.font.SysFont('Arial', font_size)
        except:
            self.font = pygame.font.SysFont('Arial', font_size)
        self.action = action
        self.hovered = False

    def draw(self, surface):
        color = self.hover_color if self.hovered else self.color
        if not (isinstance(color, tuple) and len(color) in (3, 4) and all(isinstance(c, int) and 0 <= c <= 255 for c in color)):
            color = PRIMARY
        shadow_rect = self.rect.move(0, 2)
        draw_rounded_rect(surface, (0, 0, 0, 0), shadow_rect, radius=10)
        draw_rounded_rect(surface, color, self.rect, radius=10)
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

    def update(self, mouse_pos, mouse_click):
        self.hovered = self.rect.collidepoint(mouse_pos)
        if self.hovered and mouse_click:
            if self.action:
                return self.action
        return None

class TextInput:
    def __init__(self, x, y, width, height, font_size=FONT_MEDIUM, max_length=20, 
                 initial_text="", font_name=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = initial_text
        try:
            if font_name:
                self.font = pygame.font.Font(font_name, font_size)
            else:
                self.font = pygame.font.SysFont('Arial', font_size)
        except:
            self.font = pygame.font.SysFont('Arial', font_size)
        self.active = False
        self.max_length = max_length

    def draw(self, surface):
        bg_color = WHITE if self.active else CARD_BG
        border_color = ACCENT if self.active else CARD_BORDER
        draw_rounded_rect(surface, bg_color, self.rect, radius=8)
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=8)
        text_surface = self.font.render(self.text, True, BLACK)
        text_rect = text_surface.get_rect(midleft=(self.rect.left + 10, self.rect.centery))
        surface.blit(text_surface, text_rect)

    def update(self, events):
        for event in events:
            if event.type == MOUSEBUTTONDOWN:
                self.active = self.rect.collidepoint(event.pos)
            if event.type == KEYDOWN and self.active:
                if event.key == K_BACKSPACE:
                    self.text = self.text[:-1]
                elif event.key == K_RETURN:
                    self.active = False
                elif len(self.text) < self.max_length:
                    self.text += event.unicode
        return self.text

from moneySmarts.images import get_image_path

SFX_CACHE = {}
def load_sfx(name):
    if name in SFX_CACHE:
        return SFX_CACHE[name]
    path = get_image_path(os.path.join('assets','sfx', name))
    try:
        SFX_CACHE[name] = pygame.mixer.Sound(path)
    except Exception:
        SFX_CACHE[name] = None
    return SFX_CACHE[name]

class ConfirmationPopup:
    def __init__(self, x, y, width, height, message, on_confirm, on_cancel, font_size=FONT_MEDIUM, font_name=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.message = message
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        try:
            if font_name:
                self.font = pygame.font.Font(font_name, font_size)
            else:
                self.font = pygame.font.SysFont('Arial', font_size)
        except:
            self.font = pygame.font.SysFont('Arial', font_size)
        self.confirm_btn = Button(x + 20, y + height - 60, 100, 40, "Yes", color=ACCENT, action=self.on_confirm)
        self.cancel_btn = Button(x + width - 120, y + height - 60, 100, 40, "No", color=PRIMARY, action=self.on_cancel)
        self.buttons = [self.confirm_btn, self.cancel_btn]

    def handle_events(self, events):
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = False
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_click = True
        for button in self.buttons:
            action = button.update(mouse_pos, mouse_click)
            if action:
                action()
                return True
        return False

    def draw(self, surface: Surface) -> None:
        draw_rounded_rect(surface, CARD_BG, self.rect, radius=12)
        pygame.draw.rect(surface, CARD_BORDER, self.rect, 2, border_radius=12)
        text_surface = self.font.render(self.message, True, BLACK)
        text_rect = text_surface.get_rect(center=(self.rect.centerx, self.rect.top + 40))
        surface.blit(text_surface, text_rect)
        for button in self.buttons:
            button.draw(surface)

class Screen:
    play_startup_music = False
    def __init__(self, game):
        self.game = game
        self.buttons = []
        self.next_screen = None
        self.popup = None
        EventBus.subscribe("random_event", self.on_random_event)
        
    def on_random_event(self, event, effect, player):
        pass

    def handle_events(self, events):
        if self.popup:
            handled = self.popup.handle_events(events)
            if handled:
                return
        else:
            mouse_pos = pygame.mouse.get_pos()
            mouse_click = False
            for event in events:
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    mouse_click = True
            for button in self.buttons:
                action = button.update(mouse_pos, mouse_click)
                if action:
                    action()
                    return

    def update(self):
        pass

    def draw(self, surface):
        draw_vertical_gradient(surface, (0, 0, surface.get_width(), surface.get_height()), BG_TOP, BG_BOTTOM)
        for button in self.buttons:
            button.draw(surface)
        if self.popup:
            self.popup.draw(surface)

class GUIManager:
    def __init__(self, game):
        self.game = game
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Money Smartz: Financial Life Simulator")
        self.clock = pygame.time.Clock()
        self.current_screen = None
        self.running = True
        self.sound_manager = SoundManager()
        self.load_sounds()

    def load_sounds(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(current_dir))
        assets_dir = os.path.join(root_dir, 'assets')
        sfx_dir = os.path.join(assets_dir, 'sfx')
        if not os.path.isdir(sfx_dir):
            print(f"Warning: SFX directory not found at {sfx_dir}")
            return
        for filename in os.listdir(sfx_dir):
            if filename.endswith(('.wav', '.mp3', '.ogg')):
                name = os.path.splitext(filename)[0]
                path = os.path.join(sfx_dir, filename)
                self.sound_manager.load_music(path, name)
                logging.info(f"Loaded music track: {name}")
        active_music = Config.get('music_track', 'ambient_city')
        if active_music in self.sound_manager.get_available_music():
            self.sound_manager.set_active_music(active_music)
        elif self.sound_manager.get_available_music():
            fallback_music = self.sound_manager.get_available_music()[0]
            self.sound_manager.set_active_music(fallback_music)
            Config.set('music_track', fallback_music)

    def set_screen(self, screen):
        self.current_screen = screen
        logging.debug(f"[DEBUG] set_screen called: switched to {type(screen).__name__}")
        if hasattr(screen, 'on_enter') and callable(screen.on_enter):
            screen.on_enter()
        if getattr(screen, 'play_startup_music', False):
            if not pygame.mixer.music.get_busy():
                active_music = Config.get('music_track', 'ambient_city')
                self.sound_manager.play_music(active_music)
        else:
            self.sound_manager.stop_music()
            
    def run(self):
        while self.running and not self.game.game_over:
            events = pygame.event.get()
            for event in events:
                if event.type == QUIT:
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                    self.screen_width = event.w
                    self.screen_height = event.h
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_BACKSPACE:
                        if hasattr(self.current_screen, 'back_btn') and self.current_screen.back_btn and hasattr(self.current_screen.back_btn, 'action'):
                            self.current_screen.back_btn.action()
            if self.current_screen:
                self.current_screen.handle_events(events)
                self.current_screen.update()
                self.current_screen.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

    def show_loading_task(self, func, message: str = "Loading...", on_complete=None):
        try:
            from moneySmarts.screens.loading_screen import LoadingScreen
        except Exception:
            try:
                result = func()
                if on_complete:
                    on_complete(result)
                return None
            except Exception:
                logging.exception("show_loading_task failed to import LoadingScreen and run task")
                return None

        prev_screen = self.current_screen
        loading = LoadingScreen(self.game, message=message)
        try:
            self.set_screen(loading)
        except Exception:
            logging.exception("Failed to set LoadingScreen")

        import threading

        def _worker():
            result = None
            try:
                result = func()
            except Exception:
                logging.exception("Background loading task raised an exception")
            finally:
                try:
                    if on_complete:
                        on_complete(result)
                except Exception:
                    logging.exception("on_complete callback raised an exception")
                try:
                    if prev_screen is not None:
                        self.set_screen(prev_screen)
                except Exception:
                    logging.exception("Failed to restore previous screen after loading task")

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return thread
