import json
import os
import logging
import tempfile
from moneySmarts.exceptions import ConfigError

class ConfigManager:
    """
    Loads and manages application/game configuration from JSON files.
    Supports default settings and user-customizable overrides.

    Attributes:
        default_path (str): Path to the default configuration file.
        user_path (str): Path to the user configuration file.
        config (dict): Dictionary holding the merged configuration.
    """
    def __init__(self, default_path='config_default.json', user_path='config_user.json'):
        """
        Initialize ConfigManager with paths to default and user config files.

        Args:
            default_path (str): Path to the default configuration file.
            user_path (str): Path to the user configuration file.
        """
        # Resolve relative paths to the package directory so callers can pass
        # simple filenames while tests use tmp paths.
        package_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isabs(default_path):
            default_path = os.path.join(package_dir, default_path)
        if not os.path.isabs(user_path):
            user_path = os.path.join(package_dir, user_path)

        self.default_path = default_path
        self.user_path = user_path
        self.config = {}
        self.load()

    def load(self):
        """Load configuration from default and user config files, with error handling and logging."""
        try:
            # Load default config
            if os.path.exists(self.default_path):
                with open(self.default_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                    logging.debug("Loaded default config from %s", self.default_path)
            else:
                logging.debug("Default config not found at %s", self.default_path)

            # Load user config and override defaults
            if os.path.exists(self.user_path):
                with open(self.user_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
                    logging.debug("Loaded user config from %s", self.user_path)
        except (json.JSONDecodeError, OSError) as e:
            logging.error("Failed to load configuration: %s", e)
            raise ConfigError("Failed to load configuration: {}".format(e))

    def reload(self):
        """Reload configuration from disk (re-reads default and user files)."""
        self.load()

    def save_user_config(self):
        """Save current config as user settings to the user config file, with error handling and logging.

        Uses an atomic write (write to a temp file then replace) to avoid partial writes.
        """
        try:
            user_dir = os.path.dirname(self.user_path) or os.getcwd()
            os.makedirs(user_dir, exist_ok=True)

            # Write to a temp file in the same directory then atomically replace
            fd, tmp_path = tempfile.mkstemp(prefix="cfg", suffix=".tmp", dir=user_dir)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=4)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, self.user_path)
                logging.debug("Saved user config atomically to %s", self.user_path)
            finally:
                # If tmp file still exists (on error), try to remove it
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass
        except OSError as e:
            logging.error("Failed to save user configuration: %s", e)
            raise ConfigError("Failed to save user configuration: {}".format(e))

    def get(self, key, default=None):
        """Get a configuration value by key, or return default if not found."""
        return self.config.get(key, default)

    def set(self, key, value):
        """Set a configuration value and save to user config."""
        self.config[key] = value
        logging.debug("Setting config key %s = %r", key, value)
        self.save_user_config()

# Singleton instance for global use
Config = ConfigManager()
