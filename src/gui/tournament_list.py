"""Tournament list widget for displaying loaded tournaments."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QListWidget, QListWidgetItem

from src.parser.models import Tournament


class TournamentListWidget(QListWidget):
    """Scrollable list widget displaying tournaments with name and date."""

    tournament_selected = pyqtSignal(Tournament)

    def __init__(self) -> None:
        super().__init__()
        self._tournaments: list[Tournament] = []
        self.itemClicked.connect(self._on_item_clicked)

    def set_tournaments(self, tournaments: list[Tournament]) -> None:
        """Populate the list with tournaments."""
        self._tournaments = tournaments
        self.clear()
        for tournament in tournaments:
            date_str = tournament.start_time.strftime("%Y-%m-%d %H:%M")
            display_text = f"{tournament.name}\n{date_str}"
            item = QListWidgetItem(display_text)
            item.setData(256, tournament)  # Qt.ItemDataRole.UserRole = 256
            self.addItem(item)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle item click by emitting tournament_selected signal."""
        tournament = item.data(256)
        if tournament is not None:
            self.tournament_selected.emit(tournament)

    def get_selected_tournament(self) -> Tournament | None:
        """Get the currently selected tournament."""
        current = self.currentItem()
        if current is not None:
            data = current.data(256)
            if isinstance(data, Tournament):
                return data
        return None

    def select_tournament_by_index(self, index: int) -> None:
        """Select a tournament by its index in the list."""
        if 0 <= index < self.count():
            item = self.item(index)
            if item is not None:
                self.setCurrentItem(item)

    @property
    def tournaments(self) -> list[Tournament]:
        """Get the list of tournaments."""
        return self._tournaments
