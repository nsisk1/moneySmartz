"""
AssetManager for preloading and managing game assets with error handling.
"""
import os
import pygame
import logging

class AssetManager:
    def __init__(self, asset_root="assets"):
        self.asset_root = asset_root
        self.images = {}
        self.sounds = {}
        self.fonts = {}

    def load_image(self, path, key=None):
        full_path = os.path.join(self.asset_root, path)
        try:
            image = pygame.image.load(full_path)
            if key is None:
                key = path
            self.images[key] = image
            return image
        except Exception as e:
            logging.error("Failed to load image '{}': {}".format(full_path, e))
            return None

    def get_image(self, key):
        return self.images.get(key)

    def load_sound(self, path, key=None):
        full_path = os.path.join(self.asset_root, path)
        try:
            sound = pygame.mixer.Sound(full_path)
            if key is None:
                key = path
            self.sounds[key] = sound
            return sound
        except Exception as e:
            logging.error("Failed to load sound '{}': {}".format(full_path, e))
            return None

    def get_sound(self, key):
        return self.sounds.get(key)

    def load_font(self, path, size, key=None):
        full_path = os.path.join(self.asset_root, path)
        try:
            font = pygame.font.Font(full_path, size)
            if key is None:
                key = "{}:{}".format(path, size)
            self.fonts[key] = font
            return font
        except Exception as e:
            logging.error("Failed to load font '{}': {}".format(full_path, e))
            return None

    def get_font(self, key):
        return self.fonts.get(key)
