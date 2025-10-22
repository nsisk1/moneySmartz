"""
Centralized image file references for MoneySmarts game.
Change the file name here to update the image everywhere in the game.
All image assets should physically live under assets/images now.
"""
import os

IMAGES = {
    "TITLE_BG": "title_background.jpg",
     # Reverted: restore the original bank background filename
    "BANK_BG": "BankDetails-0004.png",
    "CARD_IMAGE": "card_image.png",
    "DEBIT_BG": "debit_background.png",
    "GRADUATION_CAP": "graduation_cap_pixel.png",
    "HOME_FAMILY": "home_family.png",
    "HOME_LUXURY": "home_luxury.png",
    "HOME_STARTER": "home_starter.png",
    "INTRO_BG": "intro_background.png",
    "JOB_SEARCH_BG": "job search bg.png",
    "LIFE_EVENT_GREEN": "Life-Event-Green.jpg",
    "LIFE_EVENT_RED": "Life-Event-Red.jpg",
    "LOGO": "Money Smarts logo.png",
    "NAME_BG": "name_background.png",
    "START_MENU_BG": "StartMenuBG-Recovered.png",
    "VEHICLE_SEDAN": "vehicle_sedan.png",
    "VEHICLE_SUV": "vehicle_suv.png",
    "VEHICLE_USED": "vehicle_used_car.png",
    "WITHDRAW_BG": "WithdrawalBGV4.png",
    # Extra financial icons (now moved into images/)
    "ICON_INCOME": "income.png",
    "ICON_EXPENSE": "expense.png",
    "ICON_DEBT": "debt_balance.png",
    "ICON_INVEST": "investment.png",
    "ICON_PIGGY": "piggy_bank.png",
    "LOADING_SCREEN": "money_smarts_welcome.png",  # New: loading/title screen image
}

# Root assets directory (fonts, audio, etc.)
ASSETS_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
# Central images directory (new canonical location)
IMAGES_DIR = os.path.join(ASSETS_ROOT, "images")


def _candidate_paths(filename: str):
    """Generate candidate absolute paths for a raw filename or relative path.
    Order:
    1. assets/images/<path>
    2. assets/<path>  (legacy fallback)
    """
    # Normalise slashes
    rel = filename.replace("\\", "/")
    # Strip any leading 'assets/' so we can re-anchor
    if rel.startswith("assets/"):
        rel = rel[len("assets/"):]
    # First try images folder
    yield os.path.join(IMAGES_DIR, rel)
    # Then legacy root (only if not already inside images)
    yield os.path.join(ASSETS_ROOT, rel)


def get_image_path(key_or_path: str) -> str:
    """Return full path to an image.
    Accepts either a symbolic key present in IMAGES or a direct relative path.
    Always prefers the canonical assets/images directory; falls back to legacy
    root only if needed. Returns the first candidate path (even if non-existent)
    so callers can still attempt to load & handle errors uniformly.
    """
    if key_or_path in IMAGES:
        filename = IMAGES[key_or_path]
        for cand in _candidate_paths(filename):
            if os.path.exists(cand):
                return cand
        # None exist, still return canonical intended location
        return os.path.join(IMAGES_DIR, filename)
    # Treat as raw filename / relative path
    for cand in _candidate_paths(key_or_path):
        if os.path.exists(cand):
            return cand
    return os.path.join(IMAGES_DIR, key_or_path)


def migrate_images(delete_duplicates: bool = True):
    """Move any legacy images sitting directly under assets/ into assets/images.
    If duplicate already exists in images/, optionally delete the legacy copy.
    Safe no-op if directories missing.
    """
    if not os.path.isdir(ASSETS_ROOT):
        return
    if not os.path.isdir(IMAGES_DIR):
        try:
            os.makedirs(IMAGES_DIR, exist_ok=True)
        except OSError:
            return
    # Collect image-like files in root assets
    for fname in os.listdir(ASSETS_ROOT):
        lower = fname.lower()
        if not lower.endswith((".png", ".jpg", ".jpeg", ".gif")):
            continue
        src = os.path.join(ASSETS_ROOT, fname)
        dst = os.path.join(IMAGES_DIR, fname)
        if os.path.isdir(src):
            continue
        if os.path.exists(dst):
            # duplicate
            if delete_duplicates:
                try:
                    os.remove(src)
                except OSError:
                    pass
            continue
        try:
            os.replace(src, dst)  # atomic move
        except OSError:
            pass

# Perform migration at import so codebase stays consistent.
try:
    migrate_images()
except Exception:
    # Never fail import due to migration issues.
    pass

# Usage example:
# pygame.image.load(get_image_path("TITLE_BG"))
