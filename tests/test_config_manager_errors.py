import json
import os
import tempfile
import pytest
from moneySmarts.config_manager import ConfigManager
from moneySmarts.exceptions import ConfigError


def test_load_with_malformed_user_config_raises(tmp_path):
    default_cfg = tmp_path / "default.json"
    user_cfg = tmp_path / "user.json"

    default_data = {"volume": 50}
    default_cfg.write_text(json.dumps(default_data), encoding="utf-8")

    # Write malformed JSON to user config
    user_cfg.write_text('{ "volume": 30,, }', encoding="utf-8")

    with pytest.raises(ConfigError):
        ConfigManager(default_path=str(default_cfg), user_path=str(user_cfg))


def test_save_failure_raises_config_error(tmp_path, monkeypatch):
    default_cfg = tmp_path / "default.json"
    user_cfg = tmp_path / "user.json"

    default_data = {"volume": 50}
    default_cfg.write_text(json.dumps(default_data), encoding="utf-8")

    cm = ConfigManager(default_path=str(default_cfg), user_path=str(user_cfg))

    # Force mkstemp to raise OSError to simulate a filesystem error during save
    def fake_mkstemp(*args, **kwargs):
        raise OSError("simulated filesystem error")

    monkeypatch.setattr("tempfile.mkstemp", fake_mkstemp)

    with pytest.raises(ConfigError):
        cm.set("difficulty", "insane")

