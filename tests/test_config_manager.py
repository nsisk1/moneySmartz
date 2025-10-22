import json
import os
from moneySmarts.config_manager import ConfigManager


def test_config_manager_load_and_save(tmp_path):
    # Prepare default and user config files
    default_cfg = tmp_path / "default.json"
    user_cfg = tmp_path / "user.json"

    default_data = {"volume": 50, "resolution": "720p"}
    user_data = {"volume": 30}

    default_cfg.write_text(json.dumps(default_data), encoding="utf-8")
    user_cfg.write_text(json.dumps(user_data), encoding="utf-8")

    # Instantiate ConfigManager with explicit paths
    cm = ConfigManager(default_path=str(default_cfg), user_path=str(user_cfg))

    # User override should take precedence
    assert cm.get("volume") == 30
    assert cm.get("resolution") == "720p"

    # Setting a new value should persist to user config
    cm.set("difficulty", "hard")

    # Ensure the user config file contains the new value
    with open(str(user_cfg), "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("difficulty") == "hard"

    # Reload and verify value is still present
    cm.reload()
    assert cm.get("difficulty") == "hard"

