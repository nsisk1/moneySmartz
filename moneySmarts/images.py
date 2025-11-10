import os
from moneySmarts.config_manager import Config

# Non-themed images (e.g., game world assets)
IMAGES = {
    "HOME_FAMILY": "home_family.png",
    "HOME_LUXURY": "home_luxury.png",
    "HOME_STARTER": "home_starter.png",
    "VEHICLE_SEDAN": "vehicle_sedan.png",
    "VEHICLE_SUV": "vehicle_suv.png",
    "VEHICLE_USED": "vehicle_used_car.png",
}

# Theme-dependent UI images
UI_IMAGES = {
    "TITLE_BG": "title_background.jpg",
    "BANK_BG": "Bank_Screen.png",
    "CARD_IMAGE": "card_image.png",
    "DEBIT_BG": "debit_background.png",
    "GRADUATION_CAP": "graduation_cap_pixel.png",
    "INTRO_BG": "intro_background.png",
    "JOB_SEARCH_BG": "job_search_bg.png",
    "LIFE_EVENT_GREEN": "Life-Event-Green.jpg",
    "LIFE_EVENT_RED": "Life-Event-Red.jpg",
    "LOGO": "Money Smarts logo.png",
    "NAME_BG": "name_background.png",
    "START_MENU_BG": "title_background.jpg",
    "WITHDRAW_BG": "WithdrawalBGV4.png",
    "ICON_INCOME": "income.png",
    "ICON_EXPENSE": "expense.png",
    "ICON_DEBT": "debt_balance.png",
    "ICON_INVEST": "investment.png",
    "ICON_PIGGY": "piggy_bank.png",
    "LOADING_SCREEN": "money_smarts_welcome.png",

    # Additional per-screen backgrounds (themes should provide modern/classic variants)
    "GAME_BG": "game_background.png",
    "SHOP_BG": "shop_background.png",
    "VEHICLE_BG": "vehicle_shop_bg.png",
    "HOME_PURCHASE_BG": "home_purchase_bg.png",
    "INVENTORY_BG": "inventory_bg.png",
    "SETTINGS_BG": "settings_bg.png",
    "SELECTION_BG": "selection_bg.png",
    "RANDOM_EVENT_BG": "random_event_bg.png",
    "LIFE_EVENT_BG": "life_event_bg.png",
    "FINANCIAL_BG": "financial_bg.png",
    "GAME_OVER_BG": "game_over_bg.png",
    "BANK_SCREEN_BG": "bank_screen_bg.png",
    "DEBIT_SCREEN_BG": "debit_screen_bg.png",
    "VEHICLE_PURCHASE_BG": "vehicle_purchase_bg.png",
}

ASSETS_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
IMAGES_DIR = os.path.join(ASSETS_ROOT, "images")
UI_DIR = os.path.join(IMAGES_DIR, "ui")
ALT_UI_DIR = os.path.join(ASSETS_ROOT, "ui")

def get_image_path(key_or_path: str) -> str | None:
    # Use the same theme default as the UI module to avoid surprising mismatches
    theme = Config.get('theme', 'modern')

    is_ui_image = key_or_path in UI_IMAGES
    filename = UI_IMAGES.get(key_or_path) or IMAGES.get(key_or_path) or key_or_path

    paths_to_check = []

    if is_ui_image:
        # Prefer images/ui/<theme>/filename
        paths_to_check.append(os.path.join(UI_DIR, theme, filename))
        # Fallback to assets/ui/<theme>/filename
        paths_to_check.append(os.path.join(ALT_UI_DIR, theme, filename))
        # Fallback to images/ui/classic and assets/ui/classic
        if theme != 'classic':
            paths_to_check.append(os.path.join(UI_DIR, 'classic', filename))
            paths_to_check.append(os.path.join(ALT_UI_DIR, 'classic', filename))
        # Generic ui directories
        paths_to_check.append(os.path.join(UI_DIR, filename))
        paths_to_check.append(os.path.join(ALT_UI_DIR, filename))

    # Generic image locations
    paths_to_check.append(os.path.join(IMAGES_DIR, filename))
    paths_to_check.append(os.path.join(ASSETS_ROOT, filename))

    for path in paths_to_check:
        if os.path.exists(path):
            return path

    # Not found anywhere
    return None
