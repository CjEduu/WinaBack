"""User preferences management for WinaBack."""

from dataclasses import dataclass, field
from pathlib import Path

import toml

VALID_UI_SCALES: tuple[float, ...] = (0.75, 1.0, 1.25, 1.5, 1.75, 2.0)


@dataclass
class Preferences:
    """User preferences for the application."""

    last_folder_path: str = ""
    window_x: int = 100
    window_y: int = 100
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    ui_scale: float = 1.0
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

            gui_prefs = data.get("gui", {})
            loaded_scale = gui_prefs.get("ui_scale", 1.0)
            if loaded_scale in VALID_UI_SCALES:
                prefs.ui_scale = loaded_scale
        except (toml.TomlDecodeError, OSError):
            pass

        return prefs

    def save(self) -> None:
        """Save preferences to TOML file."""
        try:
            data: dict[str, dict[str, str | int | bool | float]] = {}

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

            if "gui" not in data:
                data["gui"] = {}
            data["gui"]["ui_scale"] = self.ui_scale

            with open(self._config_path, "w") as f:
                toml.dump(data, f)
        except OSError:
            pass
