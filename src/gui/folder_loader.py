"""Folder loading functionality for WinaBack."""

from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QWidget

from src.parser.models import Tournament
from src.parser.winamax import WinamaxParser


class FolderLoader(QObject):
    """Handles loading tournament folders and parsing files."""

    tournaments_loaded = pyqtSignal(list)  # list[Tournament]
    loading_error = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._parser = WinamaxParser()
        self._tournaments: list[Tournament] = []

    @property
    def tournaments(self) -> list[Tournament]:
        """Get the list of loaded tournaments."""
        return self._tournaments

    def open_folder_dialog(self, parent: QWidget) -> str | None:
        """Open a folder picker dialog and return the selected path.

        Args:
            parent: Parent widget for the dialog.

        Returns:
            Selected folder path, or None if cancelled.
        """
        folder_path = QFileDialog.getExistingDirectory(
            parent,
            "Select Tournament Folder",
            "",
            QFileDialog.Option.ShowDirsOnly,
        )
        return folder_path if folder_path else None

    def load_folder(self, folder_path: str) -> list[Tournament]:
        """Scan a folder for tournament files and parse them.

        Args:
            folder_path: Path to the folder containing tournament files.

        Returns:
            List of successfully parsed Tournament objects.
        """
        path = Path(folder_path)
        if not path.is_dir():
            self.loading_error.emit(f"Not a valid directory: {folder_path}")
            return []

        self._tournaments = []
        txt_files = list(path.glob("*.txt"))

        for txt_file in txt_files:
            tournament = self._try_parse_file(txt_file)
            if tournament is not None:
                self._tournaments.append(tournament)

        self.tournaments_loaded.emit(self._tournaments)
        return self._tournaments

    def _try_parse_file(self, file_path: Path) -> Tournament | None:
        """Attempt to parse a single file, returning None if it fails.

        Silently ignores files that are not valid Winamax tournament files.
        """
        try:
            if not self._parser.can_parse(file_path):
                return None
            return self._parser.parse_file(file_path)
        except Exception:
            return None
