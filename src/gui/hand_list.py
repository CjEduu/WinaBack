"""Hand list widget for displaying hands in a selected tournament."""

from typing import Any

from PyQt6.QtCore import QModelIndex, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QTextDocument
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)

from src.gui.tournament_list import SORT_BUTTON_LABELS, SortOrder
from src.parser.models import Hand, Street


class RichTextDelegate(QStyledItemDelegate):
    def paint(
        self,
        painter: QPainter | None,
        option: QStyleOptionViewItem,
        index: QModelIndex | Any,
    ) -> None:
        if painter is None:
            return
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if not text:
            return

        painter.save()

        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        doc = QTextDocument()
        doc.setHtml(text)

        painter.translate(option.rect.x(), option.rect.y())
        doc.setTextWidth(option.rect.width())
        doc.drawContents(painter)

        painter.restore()

    def sizeHint(
        self, option: QStyleOptionViewItem, index: QModelIndex | Any
    ) -> QSize:
        doc = QTextDocument()
        text = index.data(Qt.ItemDataRole.DisplayRole)
        doc.setHtml(text if text else "")
        doc.setTextWidth(option.rect.width())
        return doc.size().toSize()


# Custom data roles for storing hand and earned value
HAND_DATA_ROLE = 256  # Qt.ItemDataRole.UserRole
EARNED_VALUE_ROLE = 257  # Qt.ItemDataRole.UserRole + 1


class HandListWidget(QWidget):
    """Container widget with sortable hand list displaying hands with number and summary."""

    hand_selected = pyqtSignal(Hand)

    def __init__(self) -> None:
        super().__init__()
        self._hands: list[Hand] = []
        self._original_order: list[Hand] = []
        self._hand_diffs: dict[str, float] = {}  # hand_id -> earned value
        self._sort_order = SortOrder.DEFAULT

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header_label = QLabel("Hands")
        header.addWidget(header_label)
        header.addStretch()

        self._sort_button = QPushButton(SORT_BUTTON_LABELS[SortOrder.DEFAULT])
        self._sort_button.setFixedWidth(70)
        self._sort_button.clicked.connect(self._cycle_sort_order)
        header.addWidget(self._sort_button)

        layout.addLayout(header)

        self._list_widget = QListWidget()
        self._list_widget.setItemDelegate(RichTextDelegate())
        self._list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self._list_widget)

    def set_hands(self, hands: list[Hand]) -> None:
        """Populate the list with hands."""
        self._original_order = list(hands)
        self._hands = list(hands)
        self._hand_diffs.clear()
        self._sort_order = SortOrder.DEFAULT
        self._sort_button.setText(SORT_BUTTON_LABELS[SortOrder.DEFAULT])

        # Calculate earned values using lookahead
        self._calculate_earned_values(hands)
        self._refresh_list()

    def _calculate_earned_values(self, hands: list[Hand]) -> None:
        """Calculate earned value for each hand using lookahead."""
        for i in range(len(hands) - 1):
            current_hand = hands[i]
            _, hero_stack = self._get_hand_summary(current_hand)
            _, next_hero_stack = self._get_hand_summary(hands[i + 1])
            diff = next_hero_stack - hero_stack
            self._hand_diffs[current_hand.hand_id] = diff

        # Last hand has no diff (0)
        if hands:
            self._hand_diffs[hands[-1].hand_id] = 0.0

    def _refresh_list(self) -> None:
        """Refresh the list widget with current hand order."""
        self._list_widget.clear()

        for i, hand in enumerate(self._hands):
            is_last = i == len(self._hands) - 1

            if is_last:
                full_display = "<span style='color: #ffffff;'> Last Hand </span>"
                diff = 0.0
            else:
                summary, _ = self._get_hand_summary(hand)
                diff = self._hand_diffs.get(hand.hand_id, 0.0)

                color = "#2ec27e" if diff > 0 else "#e01b24"
                sign = "+" if diff > 0 else ""
                diff_html = f' <b style="color: {color};">{sign}{int(diff)}</b>'

                # Find original index for display number
                orig_idx = self._original_order.index(hand) if hand in self._original_order else i
                full_display = (
                    f"<span style='color: #ffffff;'>"
                    f"<b>#{orig_idx:03}</b>: {summary}"
                    f"</span>"
                    f"{diff_html}"
                )

            item = QListWidgetItem()
            item.setText(full_display)
            item.setData(HAND_DATA_ROLE, hand)
            item.setData(EARNED_VALUE_ROLE, diff)
            self._list_widget.addItem(item)

    def _get_hand_summary(self, hand: Hand) -> tuple[str, float]:
        """Generate a brief summary of the hand."""
        hero = next((p for p in hand.players if p.is_hero), None)
        hero_stack = hero.stack if hero else 0.0
        blinds = f"{int(hand.small_blind)}/{int(hand.big_blind)}"
        return f"{blinds}", hero_stack

    def _get_streets_reached(self, hand: Hand) -> list[Street]:
        """Get list of streets that have actions in this hand."""
        return [street for street in Street if street in hand.actions and hand.actions[street]]

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle item click by emitting hand_selected signal."""
        hand = item.data(HAND_DATA_ROLE)
        if hand is not None:
            self.hand_selected.emit(hand)

    def _cycle_sort_order(self) -> None:
        """Cycle through sort orders: DEFAULT -> ASCENDING -> DESCENDING -> DEFAULT."""
        if self._sort_order == SortOrder.DEFAULT:
            self._sort_order = SortOrder.ASCENDING
            self._hands = sorted(
                self._original_order,
                key=lambda h: self._hand_diffs.get(h.hand_id, 0.0),
            )
        elif self._sort_order == SortOrder.ASCENDING:
            self._sort_order = SortOrder.DESCENDING
            self._hands = sorted(
                self._original_order,
                key=lambda h: self._hand_diffs.get(h.hand_id, 0.0),
                reverse=True,
            )
        else:
            self._sort_order = SortOrder.DEFAULT
            self._hands = list(self._original_order)

        self._sort_button.setText(SORT_BUTTON_LABELS[self._sort_order])
        self._refresh_list()

    def get_selected_hand(self) -> Hand | None:
        """Get the currently selected hand."""
        current = self._list_widget.currentItem()
        if current is not None:
            data = current.data(HAND_DATA_ROLE)
            if isinstance(data, Hand):
                return data
        return None

    def select_hand_by_index(self, index: int) -> None:
        """Select a hand by its index in the list."""
        if 0 <= index < self._list_widget.count():
            item = self._list_widget.item(index)
            if item is not None:
                self._list_widget.setCurrentItem(item)

    @property
    def hands(self) -> list[Hand]:
        """Get the list of hands."""
        return self._hands

    @property
    def sort_order(self) -> SortOrder:
        """Get current sort order."""
        return self._sort_order

    # Delegate common list methods to _list_widget for compatibility
    def count(self) -> int:
        """Return the number of items in the list."""
        return self._list_widget.count()

    def item(self, index: int) -> QListWidgetItem | None:
        """Return the item at the given index."""
        return self._list_widget.item(index)

    def currentItem(self) -> QListWidgetItem | None:
        """Return the current item."""
        return self._list_widget.currentItem()

    def setCurrentItem(self, item: QListWidgetItem) -> None:
        """Set the current item."""
        self._list_widget.setCurrentItem(item)

    def currentRow(self) -> int:
        """Return the current row."""
        return self._list_widget.currentRow()

    @property
    def itemClicked(self) -> Any:
        """Expose itemClicked signal from internal list widget."""
        return self._list_widget.itemClicked
