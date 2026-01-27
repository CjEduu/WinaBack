"""Tests for FolderLoader functionality."""

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from src.gui.folder_loader import FolderLoader


@pytest.fixture
def folder_loader(qtbot):  # type: ignore[no-untyped-def]
    """Create a FolderLoader instance for testing."""
    loader = FolderLoader()
    return loader


@pytest.fixture
def sample_winamax_content() -> str:
    """Sample Winamax hand history content."""
    return (
        'Winamax Poker - Tournament "Freeroll" buyIn: 0.00€ + 0.00€ '
        "level: 1 - HandId: #123456-1-1234567890 - "
        "Holdem no limit (0/10/20) - 2024/01/15 18:30:00 UTC\n"
        "Table: 'Freeroll(123456)#0' 6-max (real money) Seat #1 is the button\n"
        "Seat 1: Player1 (1000)\n"
        "Seat 2: Hero (1500)\n"
        "*** ANTE/BLINDS ***\n"
        "Player1 posts small blind 10\n"
        "Hero posts big blind 20\n"
        "Dealt to Hero [Ah Kh]\n"
        "*** PRE-FLOP ***\n"
        "Player1 folds\n"
        "Hero wins 30\n"
        "*** SUMMARY ***\n"
    )


@pytest.fixture
def temp_tournament_folder(tmp_path: Path, sample_winamax_content: str) -> Path:
    """Create a temporary folder with tournament files."""
    valid_file = tmp_path / "tournament1.txt"
    valid_file.write_text(sample_winamax_content)

    valid_file2 = tmp_path / "tournament2.txt"
    valid_file2.write_text(sample_winamax_content.replace("123456", "789012"))

    invalid_file = tmp_path / "notes.txt"
    invalid_file.write_text("These are my poker notes, not a hand history.")

    non_txt = tmp_path / "image.png"
    non_txt.write_bytes(b"\x89PNG\r\n\x1a\n")

    return tmp_path


class TestFolderLoaderBasics:
    """Tests for basic FolderLoader functionality."""

    def test_loader_initializes(self, folder_loader: FolderLoader) -> None:
        """Loader initializes with empty tournament list."""
        assert folder_loader.tournaments == []

    def test_has_tournaments_loaded_signal(self, folder_loader: FolderLoader) -> None:
        """Loader has tournaments_loaded signal."""
        assert hasattr(folder_loader, "tournaments_loaded")

    def test_has_loading_error_signal(self, folder_loader: FolderLoader) -> None:
        """Loader has loading_error signal."""
        assert hasattr(folder_loader, "loading_error")


class TestFolderScanning:
    """Tests for folder scanning functionality."""

    def test_load_folder_finds_valid_files(
        self, folder_loader: FolderLoader, temp_tournament_folder: Path
    ) -> None:
        """Loader finds and parses valid Winamax files."""
        tournaments = folder_loader.load_folder(str(temp_tournament_folder))
        assert len(tournaments) == 2

    def test_load_folder_ignores_invalid_files(
        self, folder_loader: FolderLoader, temp_tournament_folder: Path
    ) -> None:
        """Loader silently ignores non-poker text files."""
        tournaments = folder_loader.load_folder(str(temp_tournament_folder))
        assert len(tournaments) == 2

    def test_load_folder_ignores_non_txt_files(
        self, folder_loader: FolderLoader, temp_tournament_folder: Path
    ) -> None:
        """Loader only scans .txt files."""
        tournaments = folder_loader.load_folder(str(temp_tournament_folder))
        assert len(tournaments) == 2

    def test_load_folder_updates_tournaments_property(
        self, folder_loader: FolderLoader, temp_tournament_folder: Path
    ) -> None:
        """Loaded tournaments are accessible via property."""
        folder_loader.load_folder(str(temp_tournament_folder))
        assert len(folder_loader.tournaments) == 2

    def test_load_folder_emits_signal(
        self, folder_loader: FolderLoader, temp_tournament_folder: Path, qtbot: Any
    ) -> None:
        """Loader emits tournaments_loaded signal."""
        with qtbot.waitSignal(folder_loader.tournaments_loaded, timeout=1000):
            folder_loader.load_folder(str(temp_tournament_folder))

    def test_load_invalid_directory_returns_empty(
        self, folder_loader: FolderLoader
    ) -> None:
        """Loading non-existent directory returns empty list."""
        tournaments = folder_loader.load_folder("/nonexistent/path")
        assert tournaments == []

    def test_load_empty_folder_returns_empty(
        self, folder_loader: FolderLoader, tmp_path: Path
    ) -> None:
        """Loading empty folder returns empty list."""
        tournaments = folder_loader.load_folder(str(tmp_path))
        assert tournaments == []


class TestFolderDialog:
    """Tests for folder dialog functionality."""

    def test_open_folder_dialog_returns_path_on_selection(
        self, folder_loader: FolderLoader, qtbot: Any
    ) -> None:
        """Dialog returns selected path."""
        with patch(
            "src.gui.folder_loader.QFileDialog.getExistingDirectory",
            return_value="/path/to/folder",
        ):
            from PyQt6.QtWidgets import QWidget

            parent = QWidget()
            qtbot.addWidget(parent)
            result = folder_loader.open_folder_dialog(parent)
            assert result == "/path/to/folder"

    def test_open_folder_dialog_returns_none_on_cancel(
        self, folder_loader: FolderLoader, qtbot: Any
    ) -> None:
        """Dialog returns None when cancelled."""
        with patch(
            "src.gui.folder_loader.QFileDialog.getExistingDirectory",
            return_value="",
        ):
            from PyQt6.QtWidgets import QWidget

            parent = QWidget()
            qtbot.addWidget(parent)
            result = folder_loader.open_folder_dialog(parent)
            assert result is None


class TestMainWindowIntegration:
    """Tests for FolderLoader integration with MainWindow."""

    def test_main_window_has_folder_loader(self, qtbot: Any) -> None:
        """MainWindow has folder_loader property."""
        from src.gui.main_window import MainWindow

        window = MainWindow()
        qtbot.addWidget(window)
        assert window.folder_loader is not None

    def test_main_window_has_tournaments_property(
        self, qtbot: Any, tmp_path: Path
    ) -> None:
        """MainWindow has tournaments property."""
        from src.gui.main_window import MainWindow
        from src.preferences import Preferences

        prefs = Preferences.load(tmp_path / "prefs.toml")
        window = MainWindow(preferences=prefs)
        qtbot.addWidget(window)
        assert window.tournaments == []

    def test_main_window_emits_tournaments_loaded(
        self, qtbot: Any, temp_tournament_folder: Path
    ) -> None:
        """MainWindow emits tournaments_loaded when folder is loaded."""
        from src.gui.main_window import MainWindow

        window = MainWindow()
        qtbot.addWidget(window)

        with qtbot.waitSignal(window.tournaments_loaded, timeout=1000):
            window.folder_loader.load_folder(str(temp_tournament_folder))
