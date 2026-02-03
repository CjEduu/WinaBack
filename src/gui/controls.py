"""Playback controls for action-by-action replay navigation."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from src.parser.models import Street
from src.replayer.state import ReplayState


class ReplayControls(QWidget):
    """Widget providing VCR-style controls for replay navigation."""

    action_changed = pyqtSignal()
    next_hand_requested = pyqtSignal()
    prev_hand_requested = pyqtSignal()
    equity_calculated = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._replay_state: ReplayState | None = None
        self._street_buttons: dict[Street, QPushButton] = {}
        self._setup_ui()
        self._update_button_states()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        street_layout = QHBoxLayout()
        street_layout.setSpacing(4)
        street_layout.addStretch()

        street_names = [
            (Street.PREFLOP, "Preflop"),
            (Street.FLOP, "Flop"),
            (Street.TURN, "Turn"),
            (Street.RIVER, "River"),
            (Street.SHOWDOWN, "Showdown"),
        ]
        for street, label in street_names:
            btn = QPushButton(label)
            btn.setToolTip(f"Jump to {label}")
            btn.clicked.connect(lambda checked, s=street: self._on_street_clicked(s))
            street_layout.addWidget(btn)
            self._street_buttons[street] = btn

        street_layout.addStretch()
        main_layout.addLayout(street_layout)

        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)
        action_layout.addStretch()

        self._prev_btn = QPushButton("⏮ Prev")
        self._prev_btn.setToolTip("Previous action")
        self._prev_btn.clicked.connect(self._on_prev_clicked)
        action_layout.addWidget(self._prev_btn)

        self._next_btn = QPushButton("Next ⏭")
        self._next_btn.setToolTip("Next action")
        self._next_btn.clicked.connect(self._on_next_clicked)
        action_layout.addWidget(self._next_btn)

        action_layout.addStretch()
        main_layout.addLayout(action_layout)

        hand_layout = QHBoxLayout()
        hand_layout.setSpacing(8)
        hand_layout.addStretch()

        self._prev_hand_btn = QPushButton("⏮ Prev Hand")
        self._prev_hand_btn.setToolTip("Previous hand")
        self._prev_hand_btn.clicked.connect(self._on_prev_hand_clicked)
        hand_layout.addWidget(self._prev_hand_btn)

        self._next_hand_btn = QPushButton("Next Hand ⏭")
        self._next_hand_btn.setToolTip("Next hand")
        self._next_hand_btn.clicked.connect(self._on_next_hand_clicked)
        hand_layout.addWidget(self._next_hand_btn)

        hand_layout.addStretch()
        main_layout.addLayout(hand_layout)

        equity_layout = QHBoxLayout()
        equity_layout.setSpacing(8)
        equity_layout.addStretch()

        self._calc_equity_btn = QPushButton("Calculate Equity")
        self._calc_equity_btn.setToolTip("Calculate showdown equity for all streets")
        self._calc_equity_btn.clicked.connect(self._on_calc_equity_clicked)
        equity_layout.addWidget(self._calc_equity_btn)

        equity_layout.addStretch()
        main_layout.addLayout(equity_layout)

    def set_replay_state(self, replay_state: ReplayState | None) -> None:
        """Set the replay state to control."""
        self._replay_state = replay_state
        self._update_button_states()

    @property
    def replay_state(self) -> ReplayState | None:
        """Get the current replay state."""
        return self._replay_state

    def _on_prev_clicked(self) -> None:
        """Handle previous button click."""
        if self._replay_state and self._replay_state.prev_action():
            self._update_button_states()
            self.action_changed.emit()

    def _on_next_clicked(self) -> None:
        """Handle next button click."""
        if self._replay_state and self._replay_state.next_action():
            self._update_button_states()
            self.action_changed.emit()

    def _on_street_clicked(self, street: Street) -> None:
        """Handle street button click."""
        if self._replay_state and self._replay_state.goto_street(street):
            self._update_button_states()
            self.action_changed.emit()

    def _on_prev_hand_clicked(self) -> None:
        """Handle previous hand button click."""
        self.prev_hand_requested.emit()

    def _on_next_hand_clicked(self) -> None:
        """Handle next hand button click."""
        self.next_hand_requested.emit()

    def _on_calc_equity_clicked(self) -> None:
        """Handle calculate equity button click."""
        if self._replay_state and self._replay_state.has_showdown():
            self._replay_state.get_showdown_equity()
            self._update_button_states()
            self.equity_calculated.emit()

    def _update_button_states(self) -> None:
        """Update button enabled/disabled states based on current position."""
        if not self._replay_state:
            self._prev_btn.setEnabled(False)
            self._next_btn.setEnabled(False)
            self._calc_equity_btn.setEnabled(False)
            self._calc_equity_btn.setVisible(False)
            for btn in self._street_buttons.values():
                btn.setEnabled(False)
            return

        self._prev_btn.setEnabled(self._replay_state.current_position > 0)
        self._next_btn.setEnabled(
            self._replay_state.current_position < self._replay_state.total_actions
        )

        available_streets = self._replay_state.get_available_streets()
        for street, btn in self._street_buttons.items():
            btn.setEnabled(street in available_streets)

        has_showdown = self._replay_state.has_showdown()
        equity_already_calculated = self._replay_state.get_cached_equity() is not None
        self._calc_equity_btn.setVisible(has_showdown)
        self._calc_equity_btn.setEnabled(has_showdown and not equity_already_calculated)

    @property
    def prev_button(self) -> QPushButton:
        """Get the previous action button."""
        return self._prev_btn

    @property
    def next_button(self) -> QPushButton:
        """Get the next action button."""
        return self._next_btn

    @property
    def street_buttons(self) -> dict[Street, QPushButton]:
        """Get the street navigation buttons."""
        return self._street_buttons

    def get_street_button(self, street: Street) -> QPushButton:
        """Get a specific street button."""
        return self._street_buttons[street]

    @property
    def prev_hand_button(self) -> QPushButton:
        """Get the previous hand button."""
        return self._prev_hand_btn

    @property
    def next_hand_button(self) -> QPushButton:
        """Get the next hand button."""
        return self._next_hand_btn

    @property
    def calc_equity_button(self) -> QPushButton:
        """Get the calculate equity button."""
        return self._calc_equity_btn

    def set_hand_navigation_enabled(
        self, prev_enabled: bool, next_enabled: bool
    ) -> None:
        """Set the enabled state of hand navigation buttons."""
        self._prev_hand_btn.setEnabled(prev_enabled)
        self._next_hand_btn.setEnabled(next_enabled)

    def go_to_start(self) -> None:
        """Go to the beginning (before first action)."""
        if self._replay_state:
            self._replay_state.goto_position(0)
            self._update_button_states()
            self.action_changed.emit()

    def go_to_end(self) -> None:
        """Go to the end (after last action)."""
        if self._replay_state:
            self._replay_state.goto_position(self._replay_state.total_actions)
            self._update_button_states()
            self.action_changed.emit()
