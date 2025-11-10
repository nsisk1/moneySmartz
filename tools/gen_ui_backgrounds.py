"""Generate placeholder UI background images for modern and classic themes.
Creates one PNG per UI image filename under assets/images/ui/modern and assets/images/ui/classic.
"""
import os
import pygame

ROOT = os.path.dirname(os.path.dirname(__file__))
OUT_BASE = os.path.join(ROOT, 'assets', 'images', 'ui')
MOD_PATH = os.path.join(OUT_BASE, 'modern')
CL_PATH = os.path.join(OUT_BASE, 'classic')
for d in (MOD_PATH, CL_PATH):
    os.makedirs(d, exist_ok=True)

# Filenames from moneySmarts/images.py UI_IMAGES mapping
filenames = [
    "title_background.jpg",
    "Bank_Screen.png",
    "card_image.png",
    "debit_background.png",
    "graduation_cap_pixel.png",
    "intro_background.png",
    "job_search_bg.png",
    "Life-Event-Green.jpg",
    "Life-Event-Red.jpg",
    "Money Smarts logo.png",
    "name_background.png",
    "title_background.jpg",
    "money_smarts_welcome.png",
    "game_background.png",
    "shop_background.png",
    "vehicle_shop_bg.png",
    "home_purchase_bg.png",
    "inventory_bg.png",
    "settings_bg.png",
    "selection_bg.png",
    "random_event_bg.png",
    "life_event_bg.png",
    "financial_bg.png",
    "game_over_bg.png",
    "bank_screen_bg.png",
    "debit_screen_bg.png",
    "vehicle_purchase_bg.png",
]

SIZE = (1280, 720)

pygame.init()
try:
    font = pygame.font.SysFont('Arial', 48)
except Exception:
    font = None

def make_modern(path, label):
    surf = pygame.Surface(SIZE)
    # cool blue gradient
    top = (30, 40, 80)
    bottom = (200, 220, 255)
    for y in range(SIZE[1]):
        t = y / (SIZE[1] - 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (SIZE[0], y))
    # subtle skyline block shapes
    import random
    random.seed(hash(label) & 0xffffffff)
    x = 0
    while x < SIZE[0]:
        w = random.randint(40, 180)
        h = random.randint(SIZE[1]//8, SIZE[1]//2)
        color = (20, 30 + (x % 80) // 3, 50 + (x % 60) // 2)
        pygame.draw.rect(surf, color, (x, SIZE[1] - h, w, h))
        x += w - random.randint(10, 40)
    # label
    if font:
        txt = font.render(label, True, (240, 240, 240))
        surf.blit(txt, txt.get_rect(center=(SIZE[0]//2, 80)))
    pygame.image.save(surf, path)

def make_classic(path, label):
    surf = pygame.Surface(SIZE)
    # warm paper gradient
    top = (245, 230, 200)
    bottom = (200, 170, 140)
    for y in range(SIZE[1]):
        t = y / (SIZE[1] - 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (SIZE[0], y))
    # rolling hills
    import math
    for i in range(6):
        amp = 30 + i * 14
        freq = 0.004 + i * 0.002
        color = (80 + i*8, 110 + i*6, 70 + i*4)
        points = []
        for x in range(0, SIZE[0]+10, 10):
            y = int(SIZE[1]*0.65 + math.sin(x*freq + i) * amp + i*10)
            points.append((x, y))
        points.append((SIZE[0], SIZE[1]))
        points.append((0, SIZE[1]))
        pygame.draw.polygon(surf, color, points)
    if font:
        txt = font.render(label, True, (50, 40, 30))
        surf.blit(txt, txt.get_rect(center=(SIZE[0]//2, 80)))
    pygame.image.save(surf, path)

for fname in filenames:
    # ensure extension is png for our generated images unless jpg
    base, ext = os.path.splitext(fname)
    if ext.lower() not in ('.png', '.jpg', '.jpeg'):
        fname = base + '.png'
    mod_path = os.path.join(MOD_PATH, fname)
    cls_path = os.path.join(CL_PATH, fname)
    try:
        make_modern(mod_path, base.replace('_', ' ').title())
    except Exception as e:
        print('Failed to write', mod_path, e)
    try:
        make_classic(cls_path, base.replace('_', ' ').title())
    except Exception as e:
        print('Failed to write', cls_path, e)

print('Generated UI backgrounds in:', MOD_PATH, CL_PATH)

