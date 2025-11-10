import importlib
import time
import pygame
from moneySmarts.config_manager import Config
import os


def _play_click_inline():
    """Lightweight click sound player used where SoundManager may not be available.
    Attempts to play any file starting with 'click' in assets/sfx or assets/audio.
    Silent on failure.
    """
    try:
        if not pygame.mixer.get_init():
            return
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        sfx_dirs = [os.path.join(root_dir, 'assets', 'sfx'), os.path.join(root_dir, 'assets', 'audio'), os.path.join(root_dir, 'assets')]
        for d in sfx_dirs:
            if not os.path.isdir(d):
                continue
            for fname in os.listdir(d):
                if fname.lower().startswith('click') and fname.lower().endswith(('.wav', '.ogg', '.mp3')):
                    try:
                        pygame.mixer.Sound(os.path.join(d, fname)).play()
                    except Exception:
                        pass
                    return
    except Exception:
        pass

# Determine active theme and try to load its module
theme = Config.get('theme', 'modern')
try:
    theme_module = importlib.import_module(f'moneySmarts.themes.{theme}_theme')
except Exception:
    try:
        theme_module = importlib.import_module('moneySmarts.themes.modern_theme')
    except Exception:
        theme_module = None

# --- Small helpers ---

def _get_default_font(size=18):
    try:
        return pygame.font.Font(None, size)
    except Exception:
        return None

# --- Gradient helper (preferred from theme if available) ---
if theme_module and hasattr(theme_module, 'draw_vertical_gradient'):
    draw_vertical_gradient = theme_module.draw_vertical_gradient
else:
    def draw_vertical_gradient(surface, rect, top_color, bottom_color, alpha=255):
        """Draw a vertical gradient inside rect on surface."""
        try:
            if not isinstance(rect, pygame.Rect):
                rect = pygame.Rect(rect)
            w, h = rect.width, rect.height
            if w <= 0 or h <= 0:
                return
            grad = pygame.Surface((w, h), pygame.SRCALPHA)
            tr, tg, tb = top_color
            br, bg, bb = bottom_color
            for y in range(h):
                t = y / max(1, h - 1)
                r = int(tr * (1 - t) + br * t)
                g = int(tg * (1 - t) + bg * t)
                b = int(tb * (1 - t) + bb * t)
                grad.fill((r, g, b, alpha), rect=pygame.Rect(0, y, w, 1))
            surface.blit(grad, rect.topleft)
        except Exception:
            try:
                surface.fill(top_color, rect)
            except Exception:
                pass

# --- Fallback UI primitives ---
class _Button:
    """Minimal, theme-compatible button with update(mouse_pos, mouse_click, events) signature.
    Accept either:
      _Button(x, y, w, h, text, action=...)
    or
      _Button(rect, text, action=...)
    """
    def __init__(self, x, y=None, width=None, height=None, text=None, color=None, hover_color=None,
                 text_color=None, font_size=None, font_name=None, action=None):
        # detect rect-style call: first arg is rect-like and other dims not provided
        if isinstance(x, (tuple, list, pygame.Rect)):
            self.rect = pygame.Rect(x)
            # 2nd positional arg may be text
            if isinstance(y, str):
                self.text = y
            else:
                self.text = text or ""
        else:
            # themed-style signature
            if y is None or width is None or height is None:
                # fallback to a small default rect
                self.rect = pygame.Rect(0, 0, 100, 30)
            else:
                self.rect = pygame.Rect(x, y, width, height)
            self.text = text or (y if isinstance(y, str) else "")
        self.color = color if color is not None else (60, 60, 60)
        self.hover_color = hover_color if hover_color is not None else self.color
        self.text_color = text_color if text_color is not None else (255, 255, 255)
        fs = font_size or 20
        try:
            if font_name:
                self.font = pygame.font.Font(font_name, fs)
            else:
                self.font = pygame.font.SysFont('Arial', fs)
        except Exception:
            self.font = _get_default_font(fs)
        self.action = action
        self.hovered = False
        self.visible = True

    def draw(self, surface):
        if not self.visible:
            return
        try:
            # Defensive: update hover from current mouse position so visuals reflect pointer even
            # if event-based updates were missed.
            try:
                mp = pygame.mouse.get_pos()
                self.hovered = self.rect.collidepoint(mp)
            except Exception:
                pass
            color = self.hover_color if self.hovered else self.color
            pygame.draw.rect(surface, color, self.rect, border_radius=8)
            if self.font:
                txt = self.font.render(self.text, True, self.text_color)
                surface.blit(txt, txt.get_rect(center=self.rect.center))
        except Exception:
            pass

    def update(self, mouse_pos, mouse_click=False, events=None):
        try:
            self.hovered = self.rect.collidepoint(mouse_pos)
        except Exception:
            self.hovered = False

        clicked = False
        clicked_pos_inside = False
        # If events provided, prefer checking event positions for click location
        if events:
            for ev in events:
                if ev.type == pygame.MOUSEBUTTONDOWN and getattr(ev, 'button', None) == 1:
                    clicked = True
                    pos = getattr(ev, 'pos', mouse_pos)
                    try:
                        clicked_pos_inside = self.rect.collidepoint(pos)
                    except Exception:
                        clicked_pos_inside = False
                    break
        else:
            if mouse_click:
                clicked = True
                try:
                    clicked_pos_inside = self.rect.collidepoint(mouse_pos)
                except Exception:
                    clicked_pos_inside = False

        # Trigger the action if clicked and either hover state is true or the click position was inside the rect
        if clicked and (self.hovered or clicked_pos_inside) and callable(self.action):
            def _wrapped_action(*a, **k):
                try:
                    _play_click_inline()
                except Exception:
                    pass
                return self.action()
            return _wrapped_action
        return None

    def handle_event(self, event):
        # compatibility: basic event-based handling
        if not self.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and getattr(event, 'button', None) == 1:
            pos = getattr(event, 'pos', None) or pygame.mouse.get_pos()
            if self.rect.collidepoint(pos):
                if callable(self.action):
                    try:
                        try:
                            _play_click_inline()
                        except Exception:
                            pass
                        self.action()
                    except Exception:
                        pass
                return True
        return False

class _TextInput:
    def __init__(self, x, y, width, height, font_size=18, max_length=20, initial_text="", font_name=None):
        # Support both themed and legacy constructor signatures by accepting max_length
        if isinstance(x, (tuple, list, pygame.Rect)):
            self.rect = pygame.Rect(x)
        else:
            self.rect = pygame.Rect(x, y, width, height)
        self.text = initial_text or ""
        try:
            if font_name:
                self.font = pygame.font.Font(font_name, font_size)
            else:
                self.font = pygame.font.SysFont('Arial', font_size)
        except Exception:
            self.font = _get_default_font(font_size)
        self.active = False
        self.visible = True
        self.max_length = max_length

    def draw(self, surface):
        if not self.visible:
            return
        try:
            bg = (255, 255, 255) if self.active else (240, 240, 240)
            pygame.draw.rect(surface, bg, self.rect, border_radius=6)
            if self.font:
                txt = self.font.render(self.text, True, (0, 0, 0))
                surface.blit(txt, txt.get_rect(midleft=(self.rect.x + 8, self.rect.centery)))
        except Exception:
            pass

    def update(self, events):
        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN:
                self.active = self.rect.collidepoint(getattr(ev, 'pos', pygame.mouse.get_pos()))
            if ev.type == pygame.KEYDOWN and self.active:
                if ev.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                elif ev.key == pygame.K_RETURN:
                    self.active = False
                else:
                    if getattr(ev, 'unicode', '') and ev.unicode.isprintable():
                        if len(self.text) < getattr(self, 'max_length', 9999):
                            self.text += ev.unicode
        return self.text

class _ConfirmationPopup:
    """Centered modal with simple Yes/No buttons. Compatible with theme ConfirmationPopup where possible."""
    def __init__(self, message, on_confirm=None, on_cancel=None, font=None):
        self.message = message
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.font = font or _get_default_font(18)
        self.visible = True
        self.size = (420, 180)
        self.bg_color = (30, 30, 30)
        self.fg_color = (230, 230, 230)
        self.buttons = []
        self.rect = pygame.Rect(0, 0, *self.size)

    def layout(self, surface):
        sw, sh = surface.get_size()
        cx, cy = sw // 2, sh // 2
        self.rect = pygame.Rect(cx - self.size[0] // 2, cy - self.size[1] // 2, *self.size)
        bw, bh = 120, 40
        spacing = 16
        yes_rect = pygame.Rect(self.rect.x + spacing, self.rect.bottom - bh - spacing, bw, bh)
        no_rect = pygame.Rect(self.rect.right - bw - spacing, self.rect.bottom - bh - spacing, bw, bh)
        self.buttons = [(_Button(yes_rect, "Yes", action=self._confirm), _Button(no_rect, "No", action=self._cancel))]

    def draw(self, surface):
        if not self.visible:
            return
        try:
            pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=10)
            pygame.draw.rect(surface, (200, 200, 200), self.rect, 2, border_radius=10)
            if self.font:
                lines = self.message.split('\n')
                y = self.rect.y + 12
                for line in lines:
                    txt = self.font.render(line, True, self.fg_color)
                    surface.blit(txt, (self.rect.x + 12, y))
                    y += txt.get_height() + 6
            for pair in self.buttons:
                for b in pair:
                    b.draw(surface)
        except Exception:
            pass

    def handle_events(self, events):
        if not self.visible:
            return False
        handled = False
        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN and getattr(ev, 'button', None) == 1:
                pos = getattr(ev, 'pos', pygame.mouse.get_pos())
                for pair in self.buttons:
                    for b in pair:
                        if b.rect.collidepoint(pos):
                            if callable(b.action):
                                try:
                                    b.action()
                                except Exception:
                                    pass
                            handled = True
        return handled

    def _confirm(self):
        self.visible = False
        if callable(self.on_confirm):
            try:
                self.on_confirm()
            except Exception:
                pass

    def _cancel(self):
        self.visible = False
        if callable(self.on_cancel):
            try:
                self.on_cancel()
            except Exception:
                pass

class _Screen:
    """Minimal Screen fallback compatible with theme Screen API."""
    play_startup_music = False

    def __init__(self, game=None):
        self.game = game
        self.buttons = []
        self.next_screen = None
        # Support both current and legacy popup attribute names
        self.popup = None
        self.modal_popup = None

    def on_enter(self):
        pass

    def handle_events(self, events):
        # popups take priority (support legacy modal_popup)
        active_popup = getattr(self, 'popup', None) or getattr(self, 'modal_popup', None)
        if active_popup:
            try:
                handled = active_popup.handle_events(events)
                if handled:
                    return
            except Exception:
                pass
        # otherwise pass to buttons
        # Prefer event-provided positions (works with synthetic events); fall back to current mouse position
        mouse_pos = None
        mouse_click = False
        for ev in events:
            if hasattr(ev, 'pos') and ev.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN):
                mouse_pos = ev.pos
            if ev.type == pygame.MOUSEBUTTONDOWN and getattr(ev, 'button', None) == 1:
                mouse_click = True

        if mouse_pos is None:
            try:
                mouse_pos = pygame.mouse.get_pos()
            except Exception:
                mouse_pos = (0, 0)

        for btn in list(self.buttons):
            try:
                # Many Button implementations accept (mouse_pos, mouse_click) and some accept an extra events param
                try:
                    action = btn.update(mouse_pos, mouse_click, events)
                except TypeError:
                    # fallback: call without events
                    action = btn.update(mouse_pos, mouse_click)
                if action:
                    action()
                    return
            except Exception:
                pass

    def update(self):
        pass

    def draw(self, surface):
        # default background: simple fill so screens don't appear blank
        try:
            surface.fill((30, 30, 40))
        except Exception:
            pass
        # Refresh hover state for all buttons so visuals update even without motion events
        try:
            mp = pygame.mouse.get_pos()
        except Exception:
            mp = (0, 0)
        for btn in list(self.buttons):
            try:
                try:
                    btn.update(mp, False, [])
                except TypeError:
                    btn.update(mp, False)
            except Exception:
                pass
            try:
                btn.draw(surface)
            except Exception:
                pass
        # Draw any active popup (support legacy modal_popup)
        active_popup = getattr(self, 'popup', None) or getattr(self, 'modal_popup', None)
        if active_popup:
            try:
                if hasattr(active_popup, 'layout'):
                    try:
                        active_popup.layout(surface)
                    except Exception:
                        pass
                active_popup.draw(surface)
            except Exception:
                pass

class _GUIManager:
    def __init__(self, game):
        self.game = game
        # runtime attributes expected by run()
        try:
            self.clock = pygame.time.Clock()
        except Exception:
            self.clock = None
        self.running = True
        self.current_screen = None
        self._temp_popup = None
        # Initialize SoundManager (safe; it handles mixer failures)
        try:
            from moneySmarts.sound_manager import SoundManager
            self.sound_manager = SoundManager()
        except Exception:
            self.sound_manager = None
        # prefer game.screen if provided
        self.screen = getattr(game, 'screen', None)
        # register this GUI manager on the game so screens can find it via game.gui_manager
        try:
            if self.game is not None:
                self.game.gui_manager = self
        except Exception:
            pass
        # Informative message if audio is unavailable
        try:
            import logging
            if not getattr(self.sound_manager, 'mixer_ok', True):
                print("Warning: Audio mixer unavailable. Sound will be disabled.")
                logging.warning("Audio mixer unavailable; SoundManager.mixer_ok is False")
        except Exception:
            pass

    def set_screen(self, screen):
        self.current_screen = screen
        if hasattr(screen, 'on_enter') and callable(screen.on_enter):
            try:
                screen.on_enter()
            except Exception:
                pass
        # Attempt to play a short startup SFX (e.g., 'startup') and also start music if configured.
        try:
            if getattr(screen, 'play_startup_music', False):
                # Try a startup sfx first
                try:
                    startup_name = Config.get('sfx_startup', 'startup')
                except Exception:
                    startup_name = 'startup'
                try:
                    if getattr(self, 'sound_manager', None):
                        self.sound_manager.play_sfx(startup_name)
                    else:
                        # fallback inline sfx player (use click as generic short sound)
                        _play_click_inline()
                except Exception:
                    pass
                if not pygame.mixer.music.get_busy():
                    active_music = Config.get('music_track', 'ambient_city')
                    try:
                        if getattr(self, 'sound_manager', None):
                            self.sound_manager.play_music(active_music)
                        else:
                            # no SoundManager; attempt inline music play if a file exists
                            pass
                    except Exception:
                        pass
        except Exception:
            pass

    def show_popup(self, popup):
        # Prefer to attach popup to the active screen; set both common attribute names
        if self.current_screen is not None:
            try:
                setattr(self.current_screen, 'popup', popup)
                setattr(self.current_screen, 'modal_popup', popup)
                return
            except Exception:
                pass

        # If no current screen, layout immediately so next draw can render it
        try:
            if hasattr(popup, 'layout') and self.screen is not None:
                try:
                    popup.layout(self.screen)
                except Exception:
                    pass
        except Exception:
            pass
        # store on manager for one-frame draw
        self._temp_popup = popup

    def load_sounds(self):
        import logging
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(os.path.dirname(current_dir))
        assets_dir = os.path.join(root_dir, 'assets')

        # Load music from assets/audio if present
        audio_dir = os.path.join(assets_dir, 'audio')
        if os.path.isdir(audio_dir):
            for filename in os.listdir(audio_dir):
                if filename.endswith(('.wav', '.mp3', '.ogg')):
                    name = os.path.splitext(filename)[0]
                    path = os.path.join(audio_dir, filename)
                    try:
                        self.sound_manager.load_music(path, name)
                        # Also register short audio files as sfx for convenience (e.g., click.wav)
                        try:
                            self.sound_manager.load_sfx(path, name)
                        except Exception:
                            pass
                        logging.info(f"Loaded music track: {name}")
                    except Exception:
                        logging.exception("Failed to load music %s", path)

        # Also load any SFX from assets/sfx
        sfx_dir = os.path.join(assets_dir, 'sfx')
        if os.path.isdir(sfx_dir):
            for filename in os.listdir(sfx_dir):
                if filename.endswith(('.wav', '.mp3', '.ogg')):
                    name = os.path.splitext(filename)[0]
                    path = os.path.join(sfx_dir, filename)
                    try:
                        self.sound_manager.load_sfx(path, name)
                        logging.info(f"Loaded sfx: {name}")
                    except Exception:
                        logging.exception("Failed to load sfx %s", path)

        # Activate configured music if available
        active_music = Config.get('music_track', 'ambient_city')
        available = self.sound_manager.get_available_music()
        if active_music in available:
            self.sound_manager.set_active_music(active_music)
        elif available:
            fallback_music = available[0]
            self.sound_manager.set_active_music(fallback_music)
            Config.set('music_track', fallback_music)

    def run(self):
        last = time.time()
        while getattr(self, 'running', True) and not getattr(self.game, 'game_over', False):
            now = time.time()
            dt = now - last
            last = now
            events = pygame.event.get()
            for ev in events:
                if ev.type == pygame.QUIT:
                    self.running = False
                elif ev.type == pygame.VIDEORESIZE:
                    try:
                        self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
                    except Exception:
                        pass
                elif ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                        if hasattr(self.current_screen, 'back_btn') and getattr(self.current_screen, 'back_btn', None) and hasattr(self.current_screen.back_btn, 'action'):
                            try:
                                try:
                                    _play_click_inline()
                                except Exception:
                                    pass
                                self.current_screen.back_btn.action()
                            except Exception:
                                pass
            if self.current_screen:
                try:
                    self.current_screen.handle_events(events)
                except Exception:
                    pass
                try:
                    self.current_screen.update()
                except Exception:
                    pass
                try:
                    self.current_screen.draw(self.screen)
                except Exception:
                    pass
            # draw any manager-level popup
            if self._temp_popup:
                try:
                    # ensure layout has been called
                    if hasattr(self._temp_popup, 'layout'):
                        try:
                            self._temp_popup.layout(self.screen)
                        except Exception:
                            pass
                    self._temp_popup.draw(self.screen)
                except Exception:
                    pass
                finally:
                    # clear after drawing so it doesn't persist forever
                    self._temp_popup = None
            try:
                if pygame.display.get_init():
                    pygame.display.flip()
            except Exception:
                pass
            try:
                if getattr(self, 'clock', None):
                    self.clock.tick(60)
            except Exception:
                pass

# Pick themed implementations when available
Button = getattr(theme_module, 'Button', _Button) if theme_module else _Button
TextInput = getattr(theme_module, 'TextInput', _TextInput) if theme_module else _TextInput
ConfirmationPopup = getattr(theme_module, 'ConfirmationPopup', _ConfirmationPopup) if theme_module else _ConfirmationPopup
Screen = getattr(theme_module, 'Screen', _Screen) if theme_module else _Screen
GUIManager = getattr(theme_module, 'GUIManager', _GUIManager) if theme_module else _GUIManager

# LoadingScreen helper for any loading periods (compatible with GUIManager.run calling update()/draw())
class LoadingScreen(Screen):
    def __init__(self, game=None, message="Loading...", font=None, bg_top=(20,20,40), bg_bottom=(40,40,60)):
        super().__init__(game)
        self.message = message
        self.font = font or _get_default_font(28)
        self.bg_top = bg_top
        self.bg_bottom = bg_bottom
        self._tick = 0.0

    def update(self):
        # increment tick for simple animation
        self._tick += 0.016

    def draw(self, surface):
        try:
            draw_vertical_gradient(surface, (0, 0, surface.get_width(), surface.get_height()), self.bg_top, self.bg_bottom)
        except Exception:
            try:
                surface.fill(self.bg_top)
            except Exception:
                pass
        if self.font:
            try:
                dots = int((self._tick * 2) % 4)
                text = self.message + ('.' * dots)
                txt_surf = self.font.render(text, True, (240, 240, 240))
                surface.blit(txt_surf, txt_surf.get_rect(center=surface.get_rect().center))
            except Exception:
                pass

# End of ui.py
