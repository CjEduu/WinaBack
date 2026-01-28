"""Tests for user preferences persistence."""

from pathlib import Path
from typing import Any

import toml

from src.gui.main_window import MainWindow
from src.preferences import VALID_UI_SCALES, Preferences


class TestPreferences:
    """Tests for Preferences class."""

    def test_default_values(self, tmp_path: Path) -> None:
        """Preferences have sensible defaults when no file exists."""
        config_path = tmp_path / "prefs.toml"
        prefs = Preferences.load(config_path)

        assert prefs.last_folder_path == ""
        assert prefs.window_x == 100
        assert prefs.window_y == 100
        assert prefs.window_width == 1200
        assert prefs.window_height == 800
        assert prefs.window_maximized is False
        assert prefs.ui_scale == 1.0

    def test_save_creates_file(self, tmp_path: Path) -> None:
        """Saving preferences creates the TOML file."""
        config_path = tmp_path / "prefs.toml"
        prefs = Preferences.load(config_path)
        prefs.last_folder_path = "/home/user/tournaments"
        prefs.window_width = 1400
        prefs.save()

        assert config_path.exists()
        data = toml.load(config_path)
        assert data["user"]["last_folder_path"] == "/home/user/tournaments"
        assert data["window"]["width"] == 1400

    def test_load_restores_values(self, tmp_path: Path) -> None:
        """Loading preferences restores saved values."""
        config_path = tmp_path / "prefs.toml"

        prefs1 = Preferences.load(config_path)
        prefs1.last_folder_path = "/path/to/folder"
        prefs1.window_x = 200
        prefs1.window_y = 150
        prefs1.window_width = 1600
        prefs1.window_height = 900
        prefs1.window_maximized = True
        prefs1.save()

        prefs2 = Preferences.load(config_path)
        assert prefs2.last_folder_path == "/path/to/folder"
        assert prefs2.window_x == 200
        assert prefs2.window_y == 150
        assert prefs2.window_width == 1600
        assert prefs2.window_height == 900
        assert prefs2.window_maximized is True

    def test_preserves_existing_toml_sections(self, tmp_path: Path) -> None:
        """Save preserves existing sections in the TOML file."""
        config_path = tmp_path / "prefs.toml"
        with open(config_path, "w") as f:
            toml.dump(
                {
                    "application": {"tournaments_dir": "./tournaments"},
                    "gui": {"theme": "Dark"},
                }
                , f,
            )

        prefs = Preferences.load(config_path)
        prefs.last_folder_path = "/new/path"
        prefs.save()

        data = toml.load(config_path)
        assert data["application"]["tournaments_dir"] == "./tournaments"
        assert data["gui"]["theme"] == "Dark"
        assert data["user"]["last_folder_path"] == "/new/path"

    def test_handles_corrupt_file(self, tmp_path: Path) -> None:
        """Load handles corrupt TOML gracefully."""
        config_path = tmp_path / "prefs.toml"
        config_path.write_text("this is not valid toml {{{")

        prefs = Preferences.load(config_path)
        assert prefs.last_folder_path == ""
        assert prefs.window_width == 1200

    def test_ui_scale_saves_and_loads(self, tmp_path: Path) -> None:
        """ui_scale persists to preferences.toml."""
        config_path = tmp_path / "prefs.toml"
        prefs = Preferences.load(config_path)
        prefs.ui_scale = 1.5
        prefs.save()

        data = toml.load(config_path)
        assert data["gui"]["ui_scale"] == 1.5

        prefs2 = Preferences.load(config_path)
        assert prefs2.ui_scale == 1.5

    def test_ui_scale_valid_values(self) -> None:
        """VALID_UI_SCALES contains expected values."""
        assert VALID_UI_SCALES == (0.75, 1.0, 1.25, 1.5, 1.75, 2.0)

    def test_ui_scale_invalid_value_ignored(self, tmp_path: Path) -> None:
        """Invalid ui_scale values fall back to default."""
        config_path = tmp_path / "prefs.toml"
        with open(config_path, "w") as f:
            toml.dump({"gui": {"ui_scale": 0.5}}, f)

        prefs = Preferences.load(config_path)
        assert prefs.ui_scale == 1.0


class TestMainWindowPreferences:
    """Tests for MainWindow preferences integration."""

    def test_window_accepts_preferences(self, qtbot: Any) -> None:
        """MainWindow can be initialized with custom preferences."""
        prefs = Preferences()
        prefs.window_x = 50
        prefs.window_y = 60
        prefs.window_width = 1400
        prefs.window_height = 900

        window = MainWindow(preferences=prefs)
        qtbot.addWidget(window)

        assert window.preferences is prefs
        geometry = window.geometry()
        assert geometry.width() == 1400
        assert geometry.height() == 900

    def test_close_saves_geometry(self, qtbot: Any, tmp_path: Path) -> None:
        """Closing window saves window geometry to preferences."""
        config_path = tmp_path / "prefs.toml"
        prefs = Preferences.load(config_path)

        window = MainWindow(preferences=prefs)
        qtbot.addWidget(window)

        window.setGeometry(100, 100, 1500, 950)
        window.close()

        saved_prefs = Preferences.load(config_path)
        assert saved_prefs.window_width == 1500
        assert saved_prefs.window_height == 950

    def test_folder_path_saved_on_load(self, qtbot: Any, tmp_path: Path) -> None:
        """Loading a folder saves the path to preferences."""
        config_path = tmp_path / "prefs.toml"
        prefs = Preferences.load(config_path)

        window = MainWindow(preferences=prefs)
        qtbot.addWidget(window)

        folder_path = str(tmp_path / "tournaments")
        Path(folder_path).mkdir()

        window._preferences.last_folder_path = folder_path
        window._preferences.save()

        saved_prefs = Preferences.load(config_path)
        assert saved_prefs.last_folder_path == folder_path

    def test_last_folder_loaded_on_startup(self, qtbot: Any, tmp_path: Path) -> None:
        """Window loads last folder on startup if it exists."""
        tournaments_dir = tmp_path / "tournaments"
        tournaments_dir.mkdir()
        (tournaments_dir / "dummy.txt").write_text("dummy content")

        config_path = tmp_path / "prefs.toml"
        prefs = Preferences.load(config_path)
        prefs.last_folder_path = str(tournaments_dir)
        prefs.save()

        prefs2 = Preferences.load(config_path)
        window = MainWindow(preferences=prefs2)
        qtbot.addWidget(window)

        assert window._preferences.last_folder_path == str(tournaments_dir)

    def test_invalid_folder_path_ignored(self, qtbot: Any, tmp_path: Path) -> None:
        """Invalid folder paths are ignored on startup."""
        config_path = tmp_path / "prefs.toml"
        prefs = Preferences.load(config_path)
        prefs.last_folder_path = "/nonexistent/path/that/does/not/exist"
        prefs.save()

        prefs2 = Preferences.load(config_path)
        window = MainWindow(preferences=prefs2)
        qtbot.addWidget(window)

        assert window.tournaments == []
