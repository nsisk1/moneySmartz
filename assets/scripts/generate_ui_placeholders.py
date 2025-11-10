import os
import pygame

# configure
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
UI_CLASSIC = os.path.join(PROJECT_ROOT, 'ui', 'classic')
UI_MODERN = os.path.join(PROJECT_ROOT, 'ui', 'modern')

os.makedirs(UI_CLASSIC, exist_ok=True)
os.makedirs(UI_MODERN, exist_ok=True)

# filenames to generate (matching keys in moneySmarts.images.UI_IMAGES)
names = [
    'game_background.png', 'shop_background.png', 'vehicle_shop_bg.png',
    'home_purchase_bg.png', 'inventory_bg.png', 'settings_bg.png',
    'selection_bg.png', 'random_event_bg.png', 'life_event_bg.png',
    'financial_bg.png', 'game_over_bg.png', 'bank_screen_bg.png',
    'debit_screen_bg.png', 'vehicle_purchase_bg.png'
]

# sizes for background images
size = (1280, 720)

pygame.init()
# In headless environments, set a dummy video driver if possible
try:
    pygame.display.init()
    pygame.display.set_mode((1,1))
except Exception:
    pass

for i, fname in enumerate(names):
    # classic: warm color
    surf = pygame.Surface(size)
    surf.fill(((50 + i*10) % 200 + 30, 70, 90))
    try:
        pygame.image.save(surf, os.path.join(UI_CLASSIC, fname))
    except Exception:
        # try saving as BMP fallback
        pygame.image.save(surf, os.path.join(UI_CLASSIC, fname + '.bmp'))

    # modern: cool color
    surf2 = pygame.Surface(size)
    surf2.fill((30, (80 + i*7) % 200 + 30, 150))
    try:
        pygame.image.save(surf2, os.path.join(UI_MODERN, fname))
    except Exception:
        pygame.image.save(surf2, os.path.join(UI_MODERN, fname + '.bmp'))

print('Generated', len(names), 'placeholder images for classic and modern themes.')

