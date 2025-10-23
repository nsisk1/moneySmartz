import importlib
from moneySmarts.config_manager import Config

# Get the current theme from the configuration
theme = Config.get('theme', 'modern')

# Dynamically import the theme module
try:
    theme_module = importlib.import_module(f'moneySmarts.themes.{theme}_theme')
except ImportError:
    # Fallback to the modern theme if the specified theme doesn't exist
    theme_module = importlib.import_module('moneySmarts.themes.modern_theme')

# Expose the classes from the theme module
Button = theme_module.Button
TextInput = theme_module.TextInput
ConfirmationPopup = theme_module.ConfirmationPopup
Screen = theme_module.Screen
GUIManager = theme_module.GUIManager
