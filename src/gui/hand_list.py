"""Hand list widget for displaying hands in a selected tournament."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QListWidget, QListWidgetItem

from src.parser.models import Hand, Street


class HandListWidget(QListWidget):
    """Scrollable list widget displaying hands with number and summary."""

    hand_selected = pyqtSignal(Hand)

    def __init__(self) -> None:
        super().__init__()
        self._hands: list[Hand] = []
        self.itemClicked.connect(self._on_item_clicked)

    def set_hands(self, hands: list[Hand]) -> None:
        """Populate the list with hands."""
        self._hands = hands
        self.clear()
        for i, hand in enumerate(hands, start=1):
            summary = self._get_hand_summary(hand)
            display_text = f"Hand #{i}: {summary}"
            item = QListWidgetItem(display_text)
            item.setData(256, hand)  # Qt.ItemDataRole.UserRole = 256
            self.addItem(item)

    def _get_hand_summary(self, hand: Hand) -> str:
        """Generate a brief summary of the hand."""
        hero = next((p for p in hand.players if p.is_hero), None)
        hero_name = hero.name if hero else "Unknown"

        streets_reached = self._get_streets_reached(hand)
        street_str = streets_reached[-1].name.capitalize() if streets_reached else "Preflop"

        blinds = f"{int(hand.small_blind)}/{int(hand.big_blind)}"

        return f"{blinds} - {hero_name} - {street_str}"

    def _get_streets_reached(self, hand: Hand) -> list[Street]:
        """Get list of streets that have actions in this hand."""
        return [street for street in Street if street in hand.actions and hand.actions[street]]

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle item click by emitting hand_selected signal."""
        hand = item.data(256)
        if hand is not None:
            self.hand_selected.emit(hand)

    def get_selected_hand(self) -> Hand | None:
        """Get the currently selected hand."""
        current = self.currentItem()
        if current is not None:
            data = current.data(256)
            if isinstance(data, Hand):
                return data
        return None

    def select_hand_by_index(self, index: int) -> None:
        """Select a hand by its index in the list."""
        if 0 <= index < self.count():
            item = self.item(index)
            if item is not None:
                self.setCurrentItem(item)

    @property
    def hands(self) -> list[Hand]:
        """Get the list of hands."""
        return self._hands
