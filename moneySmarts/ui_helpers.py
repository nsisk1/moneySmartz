import pygame
from typing import List, Callable, Optional, Type
from moneySmarts.constants import WHITE, CARD_BG, CARD_BORDER, ACCENT, SUCCESS, BLACK, FONT_MEDIUM
from moneySmarts.ui import Button
from moneySmarts.config_manager import Config
import os


def _play_click():
    """Attempt to play a 'click' SFX from assets/sfx if available; fail silently.
    This is intentionally lightweight and does not rely on SoundManager so it can be
    used from early UI code or inside modal helpers.
    """
    try:
        if not pygame.mixer.get_init():
            return
        # Prefer configured name key and SoundManager if available
        try:
            click_name = Config.get('sfx_click', 'click')
        except Exception:
            click_name = 'click'

        # Try via GUIManager.SoundManager first
        try:
            # If a global GUI manager is set on the game, it may be accessible via pygame.display
            # but simplest: try to import and use a manager if available on common locations
            # We prefer callers to use their gui_manager.sound_manager when possible.
            # Check environment: if a current display surface exists and a game object is attached to it, skip.
            # Fallback to searching assets directory by filename prefix.
            # First attempt: if a GUI manager exists on the current module paths (best-effort)
            from moneySmarts.ui import GUIManager
            # If a GUIManager instance exists, try to obtain it via known singletons: this is heuristic; prefer direct calls
        except Exception:
            pass

        # Fallback search for a file starting with click_name
        current_dir = os.path.dirname(os.path.dirname(__file__))
        sfx_dir = os.path.join(current_dir, 'assets', 'sfx')
        if not os.path.isdir(sfx_dir):
            sfx_dir = os.path.join(current_dir, 'assets', 'audio')
            if not os.path.isdir(sfx_dir):
                return
        for fname in os.listdir(sfx_dir):
            base, ext = os.path.splitext(fname)
            if ext.lower() not in ('.wav', '.ogg', '.mp3'):
                continue
            if base.lower().startswith(click_name.lower()):
                path = os.path.join(sfx_dir, fname)
                try:
                    snd = pygame.mixer.Sound(path)
                    snd.play()
                except Exception:
                    pass
                return
    except Exception:
        pass


class ModalPopup:
    """Simple modal popup helper: draws a centered box with text lines and an OK (and optional Cancel) button.
    - text may contain '\n' which will be split into lines.
    - on_ok: optional callback invoked when OK is pressed.
    - on_cancel: optional callback invoked when Cancel is pressed or ESC is used.
    Usage:
        popup = ModalPopup("Title", "Line1\nLine2", on_ok=cb)
        popup.draw(surface)
        popup.handle_events(events)
    """

    def __init__(self, title: str, text: str, on_ok: Optional[Callable] = None,
                 on_cancel: Optional[Callable] = None, width: int = 500, height: int = 220):
        self.title = title
        self.text = text
        self.on_ok = on_ok
        self.on_cancel = on_cancel
        self.width = width
        self.height = height
        self._ok_rect = None
        self._cancel_rect = None
        self._popup_rect = None
        self._last_surface_size = None

    def layout(self, surface: pygame.Surface):
        """Compute popup and button rects for the given surface and cache them.
        This allows handle_events to work even before draw() has been called.
        """
        sw, sh = surface.get_size()
        if self._last_surface_size == (sw, sh) and self._popup_rect:
            return self._popup_rect
        popup_rect = pygame.Rect((sw - self.width) // 2, (sh - self.height) // 2, self.width, self.height)
        ok_w, ok_h = 140, 40
        spacing = 12
        total_buttons_width = ok_w + (ok_w + spacing if self.on_cancel else 0)
        ok_x = popup_rect.x + (self.width - total_buttons_width) // 2
        ok_y = popup_rect.y + self.height - ok_h - 16
        ok_rect = pygame.Rect(ok_x, ok_y, ok_w, ok_h)
        if self.on_cancel:
            cancel_x = ok_rect.right + spacing
            cancel_rect = pygame.Rect(cancel_x, ok_y, ok_w, ok_h)
        else:
            cancel_rect = None
        self._ok_rect = ok_rect
        self._cancel_rect = cancel_rect
        self._popup_rect = popup_rect
        self._last_surface_size = (sw, sh)
        return popup_rect

    def draw(self, surface: pygame.Surface):
        # Ensure layout computed
        popup_rect = self.layout(surface)
        pygame.draw.rect(surface, CARD_BG, popup_rect, border_radius=12)
        pygame.draw.rect(surface, CARD_BORDER, popup_rect, 2, border_radius=12)
        # Title
        title_font = pygame.font.SysFont('Arial', FONT_MEDIUM + 6)
        title_surf = title_font.render(self.title, True, ACCENT)
        surface.blit(title_surf, (popup_rect.x + 20, popup_rect.y + 16))
        # Text lines: position based on title height so messages sit a bit closer to title
        msg_font = pygame.font.SysFont('Arial', FONT_MEDIUM)
        lines = self.text.split('\n') if self.text else []
        title_h = title_surf.get_height() if title_surf else (FONT_MEDIUM + 6)
        text_start_y = popup_rect.y + 16 + title_h + 8
        for i, line in enumerate(lines):
            line_surf = msg_font.render(line, True, BLACK)
            surface.blit(line_surf, (popup_rect.x + 20, text_start_y + i * 28))
        # Buttons: OK always, optional Cancel
        ok_rect = self._ok_rect
        pygame.draw.rect(surface, SUCCESS, ok_rect, border_radius=8)
        ok_text = msg_font.render("OK", True, WHITE)
        surface.blit(ok_text, (ok_rect.x + (ok_rect.width - ok_text.get_width()) // 2, ok_rect.y + (ok_rect.height - ok_text.get_height()) // 2))
        if self._cancel_rect:
            cancel_rect = self._cancel_rect
            pygame.draw.rect(surface, CARD_BORDER, cancel_rect, border_radius=8)
            cancel_text = msg_font.render("Cancel", True, BLACK)
            surface.blit(cancel_text, (cancel_rect.x + (cancel_rect.width - cancel_text.get_width()) // 2, cancel_rect.y + (cancel_rect.height - cancel_text.get_height()) // 2))
        return popup_rect

    def handle_events(self, events: List[pygame.event.Event]) -> bool:
        """Return True if the popup handled an event (consumed input)."""
        # If rects haven't been computed yet, try to compute using the active display surface
        if self._ok_rect is None:
            try:
                surf = pygame.display.get_surface() or pygame.Surface((800, 600))
                self.layout(surf)
            except Exception:
                pass

        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                pos = getattr(ev, 'pos', None) or pygame.mouse.get_pos()
                if self._ok_rect and self._ok_rect.collidepoint(pos):
                    try:
                        _play_click()
                    except Exception:
                        pass
                    try:
                        if self.on_ok:
                            self.on_ok()
                    except Exception:
                        pass
                    return True
                if self._cancel_rect and self._cancel_rect.collidepoint(pos):
                    try:
                        _play_click()
                    except Exception:
                        pass
                    try:
                        if self.on_cancel:
                            self.on_cancel()
                    except Exception:
                        pass
                    return True
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    try:
                        _play_click()
                    except Exception:
                        pass
                    try:
                        if self.on_cancel:
                            self.on_cancel()
                        elif self.on_ok:
                            self.on_ok()
                    except Exception:
                        pass
                    return True
        return False


def create_selection_buttons(items: List[str], x: int, y: int, w: int, h: int, gap: int,
                             action_cb: Callable, button_cls: Type[Button] = Button) -> List[Button]:
    """Create a list of Button objects representing selectable items.
    - items: list of strings (labels)
    - action_cb: callable that will be called with index when button pressed
    - button_cls: optional Button class to instantiate (keeps this helper decoupled from theme)
    """
    buttons: List[Button] = []
    cur_y = y
    for idx, label in enumerate(items):
        # theme Button implementations accept signature (x, y, width, height, text, action=...)
        try:
            btn = button_cls(x, cur_y, w, h, label, action=lambda i=idx: action_cb(i))
        except TypeError:
            # fallback for alternate button signatures: attempt positional rect style
            btn = button_cls((x, cur_y, w, h), label, lambda i=idx: action_cb(i))
        buttons.append(btn)
        cur_y += h + gap
    return buttons
