"""Generate game background PNGs for modern and classic themes.
Saves to assets/images/ui/modern/game_background.png and assets/images/ui/classic/game_background.png
Uses pygame to draw gradients and simple skyline shapes.
Run: python tools/gen_game_backgrounds.py
"""
import os
import pygame

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT_DIR = os.path.join(ROOT, 'assets', 'images', 'ui')
MODERN_DIR = os.path.join(OUT_DIR, 'modern')
CLASSIC_DIR = os.path.join(OUT_DIR, 'classic')
for d in (MODERN_DIR, CLASSIC_DIR):
    os.makedirs(d, exist_ok=True)

SIZE = (1280, 720)

def draw_vertical_gradient(surf, top_color, bottom_color):
    w, h = surf.get_size()
    for y in range(h):
        t = y / max(1, h-1)
        r = int(top_color[0] * (1-t) + bottom_color[0] * t)
        g = int(top_color[1] * (1-t) + bottom_color[1] * t)
        b = int(top_color[2] * (1-t) + bottom_color[2] * t)
        pygame.draw.line(surf, (r,g,b), (0,y), (w,y))


def make_modern(path):
    surf = pygame.Surface(SIZE)
    draw_vertical_gradient(surf, (30,40,80), (200,220,255))
    # simple city skyline silhouette
    import random
    w,h = SIZE
    skyline = []
    x = 0
    while x < w:
        bw = random.randint(40, 140)
        bh = random.randint(h//8, h//2)
        rect = pygame.Rect(x, h - bh, bw, bh)
        skyline.append(rect)
        x += bw - random.randint(10, 40)
    for i, r in enumerate(skyline):
        color = (20 + i % 6 * 5, 30 + i % 5 * 6, 50 + i % 4 * 10)
        pygame.draw.rect(surf, color, r)
    # soft vignette
    vign = pygame.Surface(SIZE, pygame.SRCALPHA)
    for y in range(h):
        a = int(120 * (1 - abs((y - h/2) / (h/2))))
        pygame.draw.line(vign, (0,0,0,a), (0,y), (w,y))
    vign.set_alpha(60)
    surf.blit(vign, (0,0), special_flags=pygame.BLEND_RGBA_SUB)
    pygame.image.save(surf, path)


def make_classic(path):
    surf = pygame.Surface(SIZE)
    draw_vertical_gradient(surf, (240,220,200), (200,180,160))
    # rolling hills
    w,h = SIZE
    import math
    for i in range(6):
        amp = 30 + i*18
        freq = 0.005 + i*0.003
        color = (80 + i*10, 120 + i*8, 60 + i*6)
        points = []
        for x in range(0, w+10, 10):
            y = int(h*0.65 + math.sin(x*freq + i)*amp + i*10)
            points.append((x, y))
        points.append((w, h))
        points.append((0, h))
        pygame.draw.polygon(surf, color, points)
    # subtle paper texture dots
    import random
    for _ in range(2000):
        x = random.randrange(0, w)
        y = random.randrange(0, h)
        a = random.randint(10, 35)
        surf.set_at((x,y), (200,200,190))
    pygame.image.save(surf, path)


def main():
    pygame.init()
    modern_path = os.path.join(MODERN_DIR, 'game_background.png')
    classic_path = os.path.join(CLASSIC_DIR, 'game_background.png')
    make_modern(modern_path)
    make_classic(classic_path)
    print('Wrote', modern_path)
    print('Wrote', classic_path)
    pygame.quit()

if __name__ == '__main__':
    main()

