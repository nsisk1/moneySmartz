import pygame
import os
import math

# Settings
image_folder = os.path.join('assets', 'images', 'buildings', 'exteriors', 'modernexteriors-win', 'Modern_Exteriors_48x48', 'ME_Theme_Sorter_48x48')

pygame.init()
display_info = pygame.display.Info()
screen_width, screen_height = display_info.current_w, display_info.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption('MoneySmarts World Explorer')
font = pygame.font.SysFont(None, 24)

# Load all PNG images from the folder as single tiles
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

if not image_files:
    print(f"No PNG images found in {image_folder}")
    pygame.quit()
    exit(1)

# Load images
images = []
for img_path in image_files:
    try:
        img = pygame.image.load(img_path).convert_alpha()
        images.append(img)
        print(f"Loaded: {os.path.basename(img_path)} size: {img.get_width()}x{img.get_height()}")
    except Exception as e:
        print(f"Failed to load {img_path}: {e}")

num_images = len(images)

# Determine grid size (try to make it as square as possible)
grid_cols = math.ceil(math.sqrt(num_images * screen_width / screen_height))
grid_rows = math.ceil(num_images / grid_cols)

# Calculate max tile size to fit all images in the grid
tile_w = screen_width // grid_cols
tile_h = screen_height // grid_rows

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

    screen.fill((40, 40, 40))

    # Draw images in grid
    for idx, img in enumerate(images):
        row = idx // grid_cols
        col = idx % grid_cols
        x = col * tile_w
        y = row * tile_h
        scaled_img = pygame.transform.smoothscale(img, (tile_w, tile_h))
        screen.blit(scaled_img, (x, y))
        # Optionally draw filename or index
        # label = font.render(str(idx), True, (255, 255, 0))
        # screen.blit(label, (x + 2, y + 2))

    pygame.display.flip()

pygame.quit()
