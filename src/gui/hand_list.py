"""Hand list widget for displaying hands in a selected tournament."""

from typing import Any

from PyQt6.QtCore import QModelIndex, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QTextDocument
from PyQt6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)

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

class HandListWidget(QListWidget):
    """Scrollable list widget displaying hands with number and summary."""

    hand_selected = pyqtSignal(Hand)

    def __init__(self) -> None:
        super().__init__()
        self._hands: list[Hand] = []
        self.setItemDelegate(RichTextDelegate())
        self.itemClicked.connect(self._on_item_clicked)

    def set_hands(self, hands: list[Hand]) -> None:
        """Populate the list with hands."""
        self._hands = hands
        self.clear()
        i = 0
        while i < len(hands) - 1:    
            current_hand = hands[i]
            summary, hero_stack = self._get_hand_summary(current_hand)
            
            # Determine Diff (Lookahead)
            _, next_hero_stack = self._get_hand_summary(hands[i+1])
            diff = next_hero_stack - hero_stack
            
            color = "#2ec27e" if diff > 0 else "#e01b24"
            sign = "+" if diff > 0 else ""
            diff_html = f' <b style="color: {color};">{sign}{diff}</b>'

            full_display = (
                        f"<span style='color: #ffffff;'>"
                        f"<b>#{i:03}</b>: {summary}"
                        f"</span>"
                        f"{diff_html}" # Diff has its own colors (Green/Red)
            )            
            item = QListWidgetItem()
            item.setText(full_display)
            # Store the Hand object in UserRole (256)
            item.setData(256, current_hand)
            self.addItem(item)
            i+=1
        
        current_hand = hands[i]
        full_display = "<span style='color: #ffffff;'> Last Hand </span>"
        item = QListWidgetItem()
        item.setText(full_display)
        # Store the Hand object in UserRole (256)
        item.setData(256, current_hand)
        self.addItem(item)    

    def _get_hand_summary(self, hand: Hand) -> tuple[str,float]:
        """Generate a brief summary of the hand."""

        hero = next((p for p in hand.players if p.is_hero), None)
        hero_stack = hero.stack if hero else 0.0
        blinds = f"{int(hand.small_blind)}/{int(hand.big_blind)}"

        return f"{blinds}",hero_stack

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
