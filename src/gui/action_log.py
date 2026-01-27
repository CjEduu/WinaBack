"""Action log widget for displaying hand action history."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QWidget

from src.parser.models import Action, ActionType, Street
from src.replayer.state import ReplayState


class ActionLogWidget(QListWidget):
    """Widget that displays the action history up to the current replay position."""

    STREET_COLORS = {
        Street.PREFLOP: "#9370db",
        Street.FLOP: "#6aa84f",
        Street.TURN: "#f6b26b",
        Street.RIVER: "#6fa8dc",
        Street.SHOWDOWN: "#cc0000",
    }

    HIGHLIGHT_BG_COLOR = "#094771"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._replay_state: ReplayState | None = None
        self._action_item_count: int = 0

    def set_replay_state(self, replay_state: ReplayState | None) -> None:
        """Set the replay state and update the action log."""
        self._replay_state = replay_state
        self.refresh()

    def refresh(self) -> None:
        """Refresh the action log to show actions up to current position."""
        self.clear()
        self._action_item_count = 0

        if not self._replay_state:
            return

        actions = self._replay_state.get_actions_up_to_current()
        current_street: Street | None = None

        for street, action in actions:
            if street != current_street:
                self._add_street_header(street)
                current_street = street
            self._add_action_item(action, street)
            self._action_item_count += 1

        self._highlight_current_action()

        if self.count() > 0:
            self.scrollToBottom()

    def _add_street_header(self, street: Street) -> None:
        """Add a street header item."""
        item = QListWidgetItem(f"--- {street.name} ---")
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
        item.setForeground(Qt.GlobalColor.white)
        item.setBackground(Qt.GlobalColor.darkGray)
        self.addItem(item)

    def _add_action_item(self, action: Action, street: Street) -> None:
        """Add an action item to the log."""
        text = self._format_action(action)
        item = QListWidgetItem(text)
        self.addItem(item)

    def _format_action(self, action: Action) -> str:
        """Format an action for display."""
        name = action.player_name
        action_type = action.action_type

        if action_type == ActionType.POST:
            return f"{name} posts {action.amount:.0f}"
        elif action_type == ActionType.FOLD:
            return f"{name} folds"
        elif action_type == ActionType.CHECK:
            return f"{name} checks"
        elif action_type == ActionType.CALL:
            suffix = " (all-in)" if action.is_all_in else ""
            return f"{name} calls {action.amount:.0f}{suffix}"
        elif action_type == ActionType.BET:
            suffix = " (all-in)" if action.is_all_in else ""
            return f"{name} bets {action.amount:.0f}{suffix}"
        elif action_type == ActionType.RAISE:
            suffix = " (all-in)" if action.is_all_in else ""
            return f"{name} raises to {action.amount:.0f}{suffix}"
        elif action_type == ActionType.ALL_IN:
            return f"{name} all-in {action.amount:.0f}"
        else:
            return f"{name} {action_type.value} {action.amount:.0f}"

    def _highlight_current_action(self) -> None:
        """Highlight the last (most recent) action item in the log."""
        if self.count() == 0 or self._action_item_count == 0:
            return

        last_item = self.item(self.count() - 1)
        if last_item is not None:
            last_item.setBackground(QColor(self.HIGHLIGHT_BG_COLOR))
            last_item.setSelected(True)

    @property
    def replay_state(self) -> ReplayState | None:
        """Get the current replay state."""
        return self._replay_state
