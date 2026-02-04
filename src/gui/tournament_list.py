"""Tournament list widget for displaying loaded tournaments."""

from enum import Enum, auto

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.parser.models import Tournament


class SortOrder(Enum):
    """Sort order states for tournament list."""

    DEFAULT = auto()
    ASCENDING = auto()
    DESCENDING = auto()


SORT_BUTTON_LABELS = {
    SortOrder.DEFAULT: "Sort: —",
    SortOrder.ASCENDING: "Sort: ↑",
    SortOrder.DESCENDING: "Sort: ↓",
}


class TournamentListWidget(QWidget):
    """Container widget with sortable tournament list."""

    tournament_selected = pyqtSignal(Tournament)

    def __init__(self) -> None:
        super().__init__()
        self._tournaments: list[Tournament] = []
        self._original_order: list[Tournament] = []
        self._sort_order = SortOrder.DEFAULT

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header_label = QLabel("Tournaments")
        header.addWidget(header_label)
        header.addStretch()

        self._sort_button = QPushButton(SORT_BUTTON_LABELS[SortOrder.DEFAULT])
        self._sort_button.setFixedWidth(70)
        self._sort_button.clicked.connect(self._cycle_sort_order)
        header.addWidget(self._sort_button)

        layout.addLayout(header)

        self._list_widget = QListWidget()
        self._list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list_widget)

    def set_tournaments(self, tournaments: list[Tournament]) -> None:
        """Populate the list with tournaments."""
        self._original_order = list(tournaments)
        self._tournaments = list(tournaments)
        self._sort_order = SortOrder.DEFAULT
        self._sort_button.setText(SORT_BUTTON_LABELS[SortOrder.DEFAULT])
        self._refresh_list()

    def _refresh_list(self) -> None:
        """Refresh the list widget with current tournament order."""
        self._list_widget.clear()
        for tournament in self._tournaments:
            date_str = tournament.start_time.strftime("%Y-%m-%d %H:%M")
            display_text = f"{tournament.name}\n{date_str}"
            item = QListWidgetItem(display_text)
            item.setData(256, tournament)  # Qt.ItemDataRole.UserRole = 256
            self._list_widget.addItem(item)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle item click by emitting tournament_selected signal."""
        tournament = item.data(256)
        if tournament is not None:
            self.tournament_selected.emit(tournament)

    def _cycle_sort_order(self) -> None:
        """Cycle through sort orders: DEFAULT -> ASCENDING -> DESCENDING -> DEFAULT."""
        if self._sort_order == SortOrder.DEFAULT:
            self._sort_order = SortOrder.ASCENDING
            self._tournaments = sorted(
                self._original_order, key=lambda t: t.start_time
            )
        elif self._sort_order == SortOrder.ASCENDING:
            self._sort_order = SortOrder.DESCENDING
            self._tournaments = sorted(
                self._original_order, key=lambda t: t.start_time, reverse=True
            )
        else:
            self._sort_order = SortOrder.DEFAULT
            self._tournaments = list(self._original_order)

        self._sort_button.setText(SORT_BUTTON_LABELS[self._sort_order])
        self._refresh_list()

    def get_selected_tournament(self) -> Tournament | None:
        """Get the currently selected tournament."""
        current = self._list_widget.currentItem()
        if current is not None:
            data = current.data(256)
            if isinstance(data, Tournament):
                return data
        return None

    def select_tournament_by_index(self, index: int) -> None:
        """Select a tournament by its index in the list."""
        if 0 <= index < self._list_widget.count():
            item = self._list_widget.item(index)
            if item is not None:
                self._list_widget.setCurrentItem(item)

    @property
    def tournaments(self) -> list[Tournament]:
        """Get the list of tournaments."""
        return self._tournaments

    @property
    def sort_order(self) -> SortOrder:
        """Get current sort order."""
        return self._sort_order
