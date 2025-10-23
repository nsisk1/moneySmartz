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
    "BANK_BG": "BankDetails-0004.png",
    "CARD_IMAGE": "card_image.png",
    "DEBIT_BG": "debit_background.png",
    "GRADUATION_CAP": "graduation_cap_pixel.png",
    "INTRO_BG": "intro_background.png",
    "JOB_SEARCH_BG": "job_search_bg.png",
    "LIFE_EVENT_GREEN": "Life-Event-Green.jpg",
    "LIFE_EVENT_RED": "Life-Event-Red.jpg",
    "LOGO": "Money_Smarts_logo.png",
    "NAME_BG": "name_background.png",
    "START_MENU_BG": "StartMenuBG-Recovered.png",
    "WITHDRAW_BG": "WithdrawalBGV4.png",
    "ICON_INCOME": "income.png",
    "ICON_EXPENSE": "expense.png",
    "ICON_DEBT": "debt_balance.png",
    "ICON_INVEST": "investment.png",
    "ICON_PIGGY": "piggy_bank.png",
    "LOADING_SCREEN": "money_smarts_welcome.png",
}

ASSETS_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
IMAGES_DIR = os.path.join(ASSETS_ROOT, "images")
UI_DIR = os.path.join(IMAGES_DIR, "ui")

def get_image_path(key_or_path: str) -> str:
    theme = Config.get('theme', 'classic')

    is_ui_image = key_or_path in UI_IMAGES
    filename = UI_IMAGES.get(key_or_path) or IMAGES.get(key_or_path) or key_or_path

    paths_to_check = []

    if is_ui_image:
        paths_to_check.append(os.path.join(UI_DIR, theme, filename))
        if theme != 'classic':
            paths_to_check.append(os.path.join(UI_DIR, 'classic', filename))
        paths_to_check.append(os.path.join(UI_DIR, filename))

    paths_to_check.append(os.path.join(IMAGES_DIR, filename))
    paths_to_check.append(os.path.join(ASSETS_ROOT, filename))

    for path in paths_to_check:
        if os.path.exists(path):
            return path

    if is_ui_image:
        return os.path.join(UI_DIR, theme, filename)
    else:
        return os.path.join(IMAGES_DIR, filename)
