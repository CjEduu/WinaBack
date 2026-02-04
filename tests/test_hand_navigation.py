"""Tests for hand navigation (US-018)."""

from datetime import datetime
from typing import Any

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent

from src.gui.controls import ReplayControls
from src.gui.main_window import MainWindow
from src.parser.models import Hand, Player, Street, Tournament


@pytest.fixture
def sample_hands() -> list[Hand]:
    """Create sample hands for testing."""
    hands = []
    for i in range(5):
        hand = Hand(
            hand_id=f"hand_{i}",
            timestamp=datetime(2024, 1, i + 1),
            players=[
                Player(
                    name="Hero",
                    seat=1,
                    stack=1000.0,
                    is_hero=True,
                ),
                Player(
                    name="Villain",
                    seat=2,
                    stack=1500.0,
                    is_hero=False,
                ),
            ],
            button_seat=1,
            small_blind=50.0,
            big_blind=100.0,
            ante=0.0,
            actions={Street.PREFLOP: []},
            board=[],
            showdown_hands={},
        )
        hands.append(hand)
    return hands


@pytest.fixture
def sample_tournament(sample_hands: list[Hand]) -> Tournament:
    """Create sample tournament for testing."""
    return Tournament(
        tournament_id="12345",
        name="Test Tourney",
        buy_in=10.0,
        start_time=datetime(2024, 1, 1),
        hands=sample_hands,
    )


class TestReplayControlsHandNavigation:
    """Tests for hand navigation buttons in ReplayControls."""

    def test_has_prev_hand_button(self, qtbot: Any) -> None:
        """Controls should have a previous hand button."""
        controls = ReplayControls()
        qtbot.addWidget(controls)
        assert controls.prev_hand_button is not None
        assert controls.prev_hand_button.text() == "⏮ Prev Hand"

    def test_has_next_hand_button(self, qtbot: Any) -> None:
        """Controls should have a next hand button."""
        controls = ReplayControls()
        qtbot.addWidget(controls)
        assert controls.next_hand_button is not None
        assert controls.next_hand_button.text() == "Next Hand ⏭"

    def test_prev_hand_button_emits_signal(self, qtbot: Any) -> None:
        """Prev hand button should emit prev_hand_requested signal."""
        controls = ReplayControls()
        qtbot.addWidget(controls)

        with qtbot.waitSignal(controls.prev_hand_requested, timeout=500):
            controls.prev_hand_button.click()

    def test_next_hand_button_emits_signal(self, qtbot: Any) -> None:
        """Next hand button should emit next_hand_requested signal."""
        controls = ReplayControls()
        qtbot.addWidget(controls)

        with qtbot.waitSignal(controls.next_hand_requested, timeout=500):
            controls.next_hand_button.click()

    def test_set_hand_navigation_enabled(self, qtbot: Any) -> None:
        """set_hand_navigation_enabled should enable/disable buttons."""
        controls = ReplayControls()
        qtbot.addWidget(controls)

        controls.set_hand_navigation_enabled(prev_enabled=True, next_enabled=False)
        assert controls.prev_hand_button.isEnabled()
        assert not controls.next_hand_button.isEnabled()

        controls.set_hand_navigation_enabled(prev_enabled=False, next_enabled=True)
        assert not controls.prev_hand_button.isEnabled()
        assert controls.next_hand_button.isEnabled()


class TestMainWindowHandNavigation:
    """Tests for hand navigation in MainWindow."""

    def test_navigate_to_next_hand(
        self, qtbot: Any, sample_tournament: Tournament
    ) -> None:
        """Next hand button should navigate to the next hand."""
        window = MainWindow()
        qtbot.addWidget(window)

        window._on_tournaments_loaded([sample_tournament])
        window.tournament_list.select_tournament_by_index(0)
        item = window.tournament_list._list_widget.currentItem()
        assert item is not None
        window.tournament_list._list_widget.itemClicked.emit(item)

        window.hand_list.select_hand_by_index(0)
        item = window.hand_list.currentItem()
        assert item is not None
        window.hand_list.itemClicked.emit(item)

        assert window.hand_list.currentRow() == 0

        window.replay_controls.next_hand_button.click()
        assert window.hand_list.currentRow() == 1

    def test_navigate_to_prev_hand(
        self, qtbot: Any, sample_tournament: Tournament
    ) -> None:
        """Prev hand button should navigate to the previous hand."""
        window = MainWindow()
        qtbot.addWidget(window)

        window._on_tournaments_loaded([sample_tournament])
        window.tournament_list.select_tournament_by_index(0)
        item = window.tournament_list._list_widget.currentItem()
        assert item is not None
        window.tournament_list._list_widget.itemClicked.emit(item)

        window.hand_list.select_hand_by_index(2)
        item = window.hand_list.currentItem()
        assert item is not None
        window.hand_list.itemClicked.emit(item)

        assert window.hand_list.currentRow() == 2

        window.replay_controls.prev_hand_button.click()
        assert window.hand_list.currentRow() == 1

    def test_hand_list_selection_updates(
        self, qtbot: Any, sample_tournament: Tournament
    ) -> None:
        """Hand list selection should update when navigating hands."""
        window = MainWindow()
        qtbot.addWidget(window)

        window._on_tournaments_loaded([sample_tournament])
        window.tournament_list.select_tournament_by_index(0)
        item = window.tournament_list._list_widget.currentItem()
        assert item is not None
        window.tournament_list._list_widget.itemClicked.emit(item)

        window.hand_list.select_hand_by_index(1)
        item = window.hand_list.currentItem()
        assert item is not None
        window.hand_list.itemClicked.emit(item)

        window.replay_controls.next_hand_button.click()

        assert window.hand_list.currentRow() == 2
        current_item = window.hand_list.currentItem()
        assert current_item is not None
        assert current_item.isSelected()

    def test_prev_disabled_at_first_hand(
        self, qtbot: Any, sample_tournament: Tournament
    ) -> None:
        """Prev hand button should be disabled at first hand."""
        window = MainWindow()
        qtbot.addWidget(window)

        window._on_tournaments_loaded([sample_tournament])
        window.tournament_list.select_tournament_by_index(0)
        item = window.tournament_list._list_widget.currentItem()
        assert item is not None
        window.tournament_list._list_widget.itemClicked.emit(item)

        window.hand_list.select_hand_by_index(0)
        item = window.hand_list.currentItem()
        assert item is not None
        window.hand_list.itemClicked.emit(item)

        assert not window.replay_controls.prev_hand_button.isEnabled()

    def test_next_disabled_at_last_hand(
        self, qtbot: Any, sample_tournament: Tournament
    ) -> None:
        """Next hand button should be disabled at last hand."""
        window = MainWindow()
        qtbot.addWidget(window)

        window._on_tournaments_loaded([sample_tournament])
        window.tournament_list.select_tournament_by_index(0)
        item = window.tournament_list._list_widget.currentItem()
        assert item is not None
        window.tournament_list._list_widget.itemClicked.emit(item)

        window.hand_list.select_hand_by_index(4)  # Last hand (0-indexed)
        item = window.hand_list.currentItem()
        assert item is not None
        window.hand_list.itemClicked.emit(item)

        assert not window.replay_controls.next_hand_button.isEnabled()

    def test_both_enabled_in_middle(
        self, qtbot: Any, sample_tournament: Tournament
    ) -> None:
        """Both buttons should be enabled when in the middle of hand list."""
        window = MainWindow()
        qtbot.addWidget(window)

        window._on_tournaments_loaded([sample_tournament])
        window.tournament_list.select_tournament_by_index(0)
        item = window.tournament_list._list_widget.currentItem()
        assert item is not None
        window.tournament_list._list_widget.itemClicked.emit(item)

        window.hand_list.select_hand_by_index(2)  # Middle hand
        item = window.hand_list.currentItem()
        assert item is not None
        window.hand_list.itemClicked.emit(item)

        assert window.replay_controls.prev_hand_button.isEnabled()
        assert window.replay_controls.next_hand_button.isEnabled()


class TestKeyboardShortcutsHandNavigation:
    """Tests for keyboard shortcuts for hand navigation."""

    def test_bracket_right_navigates_next_hand(
        self, qtbot: Any, sample_tournament: Tournament
    ) -> None:
        """'J' or Down arrow key should navigate to next hand."""
        window = MainWindow()
        qtbot.addWidget(window)

        window._on_tournaments_loaded([sample_tournament])
        window.tournament_list.select_tournament_by_index(0)
        item = window.tournament_list._list_widget.currentItem()
        assert item is not None
        window.tournament_list._list_widget.itemClicked.emit(item)

        window.hand_list.select_hand_by_index(0)
        item = window.hand_list.currentItem()
        assert item is not None
        window.hand_list.itemClicked.emit(item)

        event = QKeyEvent(
            QKeyEvent.Type.KeyPress, Qt.Key.Key_J, Qt.KeyboardModifier.NoModifier
        )
        window.keyPressEvent(event)

        assert window.hand_list.currentRow() == 1

    def test_up_key_navigates_prev_hand(
        self, qtbot: Any, sample_tournament: Tournament
    ) -> None:
        """'K' or Up arrow key should navigate to previous hand."""
        window = MainWindow()
        qtbot.addWidget(window)

        window._on_tournaments_loaded([sample_tournament])
        window.tournament_list.select_tournament_by_index(0)
        item = window.tournament_list._list_widget.currentItem()
        assert item is not None
        window.tournament_list._list_widget.itemClicked.emit(item)

        window.hand_list.select_hand_by_index(2)
        item = window.hand_list.currentItem()
        assert item is not None
        window.hand_list.itemClicked.emit(item)

        event = QKeyEvent(
            QKeyEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier
        )
        window.keyPressEvent(event)

        assert window.hand_list.currentRow() == 1

    def test_shortcuts_work_with_main_focus(
        self, qtbot: Any, sample_tournament: Tournament
    ) -> None:
        """Shortcuts should work when main window has focus."""
        window = MainWindow()
        qtbot.addWidget(window)
        window.show()
        window.activateWindow()

        window._on_tournaments_loaded([sample_tournament])
        window.tournament_list.select_tournament_by_index(0)
        item = window.tournament_list._list_widget.currentItem()
        assert item is not None
        window.tournament_list._list_widget.itemClicked.emit(item)

        window.hand_list.select_hand_by_index(1)
        item = window.hand_list.currentItem()
        assert item is not None
        window.hand_list.itemClicked.emit(item)

        event = QKeyEvent(
            QKeyEvent.Type.KeyPress, Qt.Key.Key_Down, Qt.KeyboardModifier.NoModifier
        )
        window.keyPressEvent(event)
        assert window.hand_list.currentRow() == 2

        event = QKeyEvent(
            QKeyEvent.Type.KeyPress, Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier
        )
        window.keyPressEvent(event)
        assert window.hand_list.currentRow() == 1
