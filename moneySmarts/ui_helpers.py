import pygame
from typing import List, Callable, Optional
from moneySmarts.constants import WHITE, CARD_BG, CARD_BORDER, ACCENT, SUCCESS, BLACK, FONT_MEDIUM, SCREEN_WIDTH, SCREEN_HEIGHT
from moneySmarts.ui import Button


class ModalPopup:
    """Simple modal popup helper: draws a centered box with text lines and an OK button.
    - text may contain '\n' which will be split into lines.
    - on_ok: optional callback invoked when OK is pressed.
    Usage:
        popup = ModalPopup("Title", "Line1\nLine2", on_ok=cb)
        popup.draw(surface)
        popup.handle_events(events)
    """

    def __init__(self, title: str, text: str, on_ok: Optional[Callable] = None, width: int = 500, height: int = 220):
        self.title = title
        self.text = text
        self.on_ok = on_ok
        self.width = width
        self.height = height
        self._ok_rect = None

    def draw(self, surface: pygame.Surface):
        sw, sh = surface.get_size()
        popup_rect = pygame.Rect((sw - self.width) // 2, (sh - self.height) // 2, self.width, self.height)
        pygame.draw.rect(surface, CARD_BG, popup_rect, border_radius=12)
        pygame.draw.rect(surface, CARD_BORDER, popup_rect, 2, border_radius=12)
        # Title
        title_font = pygame.font.SysFont('Arial', FONT_MEDIUM + 6)
        title_surf = title_font.render(self.title, True, ACCENT)
        surface.blit(title_surf, (popup_rect.x + 20, popup_rect.y + 16))
        # Text lines
        msg_font = pygame.font.SysFont('Arial', FONT_MEDIUM)
        lines = self.text.split('\n') if self.text else []
        for i, line in enumerate(lines):
            line_surf = msg_font.render(line, True, BLACK)
            surface.blit(line_surf, (popup_rect.x + 20, popup_rect.y + 56 + i * 30))
        # OK button
        ok_w, ok_h = 140, 40
        ok_x = popup_rect.x + (self.width - ok_w) // 2
        ok_y = popup_rect.y + self.height - ok_h - 16
        ok_rect = pygame.Rect(ok_x, ok_y, ok_w, ok_h)
        pygame.draw.rect(surface, SUCCESS, ok_rect, border_radius=8)
        ok_text = msg_font.render("OK", True, WHITE)
        surface.blit(ok_text, (ok_rect.x + (ok_w - ok_text.get_width()) // 2, ok_rect.y + (ok_h - ok_text.get_height()) // 2))
        self._ok_rect = ok_rect
        return popup_rect

    def handle_events(self, events: List[pygame.event.Event]) -> bool:
        """Return True if the popup handled an event (consumed input)."""
        for ev in events:
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if self._ok_rect and self._ok_rect.collidepoint(pygame.mouse.get_pos()):
                    try:
                        if self.on_ok:
                            self.on_ok()
                    except Exception:
                        pass
                    return True
        return False


def create_selection_buttons(items: List[str], x: int, y: int, w: int, h: int, gap: int, action_cb: Callable) -> List[Button]:
    """Create a list of Button objects representing selectable items.
    - items: list of strings (labels)
    - action_cb: callable that will be called with index when button pressed
    """
    buttons: List[Button] = []
    cur_y = y
    for idx, label in enumerate(items):
        btn = Button(x, cur_y, w, h, label, action=lambda i=idx: action_cb(i))
        buttons.append(btn)
        cur_y += h + gap
    return buttons

