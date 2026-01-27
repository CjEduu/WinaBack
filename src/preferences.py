"""User preferences management for WinaBack."""

from dataclasses import dataclass, field
from pathlib import Path

import toml


@dataclass
class Preferences:
    """User preferences for the application."""

    last_folder_path: str = ""
    window_x: int = 100
    window_y: int = 100
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    _config_path: Path = field(default_factory=lambda: Path("preferences.toml"))

    @classmethod
    def load(cls, config_path: Path | None = None) -> "Preferences":
        """Load preferences from TOML file."""
        path = config_path or Path("preferences.toml")
        prefs = cls(_config_path=path)

        if not path.exists():
            return prefs

        try:
            data = toml.load(path)
            user_prefs = data.get("user", {})
            prefs.last_folder_path = user_prefs.get("last_folder_path", "")

            window_prefs = data.get("window", {})
            prefs.window_x = window_prefs.get("x", 100)
            prefs.window_y = window_prefs.get("y", 100)
            prefs.window_width = window_prefs.get("width", 1200)
            prefs.window_height = window_prefs.get("height", 800)
            prefs.window_maximized = window_prefs.get("maximized", False)
        except (toml.TomlDecodeError, OSError):
            pass

        return prefs

    def save(self) -> None:
        """Save preferences to TOML file."""
        try:
            data: dict[str, dict[str, str | int | bool]] = {}

            if self._config_path.exists():
                existing = toml.load(self._config_path)
                for key, value in existing.items():
                    if isinstance(value, dict):
                        data[key] = value

            data["user"] = {
                "last_folder_path": self.last_folder_path,
            }

            data["window"] = {
                "x": self.window_x,
                "y": self.window_y,
                "width": self.window_width,
                "height": self.window_height,
                "maximized": self.window_maximized,
            }

            with open(self._config_path, "w") as f:
                toml.dump(data, f)
        except OSError:
            pass
