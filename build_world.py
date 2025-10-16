import pygame
import os
import csv

# Settings
image_folder = os.path.join('assets', 'images', 'buildings', 'exteriors', 'modernexteriors-win', 'Modern_Exteriors_48x48', 'ME_Theme_Sorter_48x48')
csv_map_file = os.path.join('assets', 'maps', 'sample_map.csv')

pygame.init()
display_info = pygame.display.Info()
screen_width, screen_height = display_info.current_w, display_info.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption('MoneySmarts World Explorer')

# Load tile images (first three PNGs for sample)
image_files = []
if os.path.exists(image_folder):
    for filename in sorted(os.listdir(image_folder)):
        if filename.endswith('.png'):
            img_path = os.path.join(image_folder, filename)
            image_files.append(img_path)
else:
    print(f"Image folder not found: {image_folder}")
    pygame.quit()
    exit(1)

if len(image_files) < 3:
    print(f"Not enough PNG images found in {image_folder}")
    pygame.quit()
    exit(1)

images = []
for img_path in image_files[:3]:
    try:
        img = pygame.image.load(img_path).convert_alpha()
        images.append(img)
    except Exception as e:
        print(f"Failed to load {img_path}: {e}")

# Load CSV map
tile_map = []
with open(csv_map_file, newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        tile_map.append([int(cell) for cell in row])

map_rows = len(tile_map)
map_cols = len(tile_map[0]) if map_rows > 0 else 0

tile_w = screen_width // map_cols if map_cols else 48
tile_h = screen_height // map_rows if map_rows else 48

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False
    screen.fill((40, 40, 40))
    # Draw map from CSV
    for row_idx, row in enumerate(tile_map):
        for col_idx, tile_idx in enumerate(row):
            if 0 <= tile_idx < len(images):
                scaled_img = pygame.transform.smoothscale(images[tile_idx], (tile_w, tile_h))
                screen.blit(scaled_img, (col_idx * tile_w, row_idx * tile_h))
    pygame.display.flip()
pygame.quit()
