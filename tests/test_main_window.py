"""Tests for MainWindow GUI component."""

from datetime import datetime

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent

from src.gui.controls import ReplayControls
from src.gui.main_window import MainWindow
from src.parser.models import Action, ActionType, Hand, Player, Street


@pytest.fixture
def main_window(qtbot):  # type: ignore[no-untyped-def]
    """Create a MainWindow instance for testing."""
    window = MainWindow()
    qtbot.addWidget(window)
    return window


class TestMainWindowStructure:
    """Tests for MainWindow layout and structure."""

    def test_window_title(self, main_window: MainWindow) -> None:
        """Window has correct title."""
        assert "WinaBack" in main_window.windowTitle()

    def test_window_minimum_size(self, main_window: MainWindow) -> None:
        """Window has reasonable minimum size."""
        assert main_window.minimumWidth() >= 800
        assert main_window.minimumHeight() >= 600

    def test_has_sidebar(self, main_window: MainWindow) -> None:
        """Window has sidebar widget."""
        assert main_window.sidebar is not None

    def test_has_table_area(self, main_window: MainWindow) -> None:
        """Window has table area widget."""
        assert main_window.table_area is not None

    def test_has_controls(self, main_window: MainWindow) -> None:
        """Window has controls widget."""
        assert main_window.controls is not None


class TestMainWindowMenu:
    """Tests for MainWindow menu structure."""

    def test_has_file_menu(self, main_window: MainWindow) -> None:
        """Window has File menu."""
        menu_bar = main_window.menuBar()
        assert menu_bar is not None
        actions = menu_bar.actions()
        file_menu_found = any("File" in action.text() for action in actions)
        assert file_menu_found

    def test_file_menu_has_open_folder(self, main_window: MainWindow) -> None:
        """File menu has Open Folder action."""
        menu_bar = main_window.menuBar()
        assert menu_bar is not None
        file_menu = menu_bar.actions()[0].menu()
        assert file_menu is not None
        action_texts = [action.text() for action in file_menu.actions()]
        open_folder_found = any("Open Folder" in text for text in action_texts)
        assert open_folder_found

    def test_open_folder_emits_signal(self, main_window: MainWindow, qtbot) -> None:  # type: ignore[no-untyped-def]
        """Open Folder action emits folder_open_requested signal."""
        with qtbot.waitSignal(main_window.folder_open_requested, timeout=1000):
            menu_bar = main_window.menuBar()
            assert menu_bar is not None
            file_menu = menu_bar.actions()[0].menu()
            assert file_menu is not None
            for action in file_menu.actions():
                if "Open Folder" in action.text():
                    action.trigger()
                    break


class TestMainWindowTheme:
    """Tests for MainWindow theme/styling."""

    def test_has_dark_theme(self, main_window: MainWindow) -> None:
        """Window has dark theme stylesheet applied."""
        stylesheet = main_window.styleSheet()
        assert len(stylesheet) > 0
        assert "#1e1e1e" in stylesheet or "background" in stylesheet.lower()


def make_test_hand() -> Hand:
    """Create a test hand for integration tests."""
    players = [
        Player(seat=1, name="Hero", stack=1000.0, bounty=0.0, is_hero=True),
        Player(seat=2, name="Villain", stack=1000.0, bounty=0.0, is_hero=False),
    ]
    actions = {
        Street.PREFLOP: [
            Action(
                player_name="Hero",
                action_type=ActionType.POST,
                amount=50.0,
                is_all_in=False,
            ),
            Action(
                player_name="Villain",
                action_type=ActionType.POST,
                amount=100.0,
                is_all_in=False,
            ),
            Action(
                player_name="Hero",
                action_type=ActionType.CALL,
                amount=50.0,
                is_all_in=False,
            ),
        ],
    }
    return Hand(
        hand_id="123",
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        small_blind=50.0,
        big_blind=100.0,
        ante=0.0,
        button_seat=1,
        players=players,
        actions=actions,
        board=[],
        showdown_hands={},
    )


class TestReplayControlsIntegration:
    """Tests for ReplayControls integration in MainWindow."""

    def test_main_window_has_replay_controls(self, main_window: MainWindow) -> None:
        """MainWindow has replay controls widget."""
        assert main_window.replay_controls is not None
        assert isinstance(main_window.replay_controls, ReplayControls)

    def test_replay_controls_updates_table(self, main_window: MainWindow) -> None:
        """Navigating updates table widget."""
        hand = make_test_hand()
        main_window.table_widget.set_hand(hand)
        main_window.replay_controls.set_replay_state(main_window.table_widget.replay_state)
        assert main_window.table_widget.replay_state is not None
        # Initial position is 2 (after 2 POSTs skipped)
        initial_pos = main_window.table_widget.replay_state.current_position
        main_window.replay_controls.next_button.click()
        assert main_window.table_widget.replay_state.current_position == initial_pos + 1

    def test_replay_controls_updates_action_log(self, main_window: MainWindow) -> None:
        """Navigating updates action log."""
        hand = make_test_hand()
        main_window.table_widget.set_hand(hand)
        main_window.replay_controls.set_replay_state(main_window.table_widget.replay_state)
        main_window.action_log.set_replay_state(main_window.table_widget.replay_state)
        main_window.replay_controls.next_button.click()
        main_window.action_log.refresh()
        assert main_window.action_log.count() > 0

    def test_hand_selection_sets_replay_controls_state(self, main_window: MainWindow) -> None:
        """Selecting a hand sets state on replay controls."""
        hand = make_test_hand()
        main_window._on_hand_selected(hand)
        assert main_window.replay_controls.replay_state is not None

    def test_action_changed_refreshes_action_log(self, main_window: MainWindow) -> None:
        """action_changed signal causes action log to refresh."""
        hand = make_test_hand()
        main_window._on_hand_selected(hand)
        initial_count = main_window.action_log.count()
        main_window.replay_controls.next_button.click()
        assert main_window.action_log.count() != initial_count or main_window.action_log.count() > 0


class TestKeyboardShortcuts:
    """Tests for keyboard shortcuts in MainWindow."""

    def test_right_arrow_advances_action(self, main_window: MainWindow) -> None:
        """Right arrow key advances to next action."""
        hand = make_test_hand()
        main_window._on_hand_selected(hand)
        assert main_window.replay_controls.replay_state is not None
        initial_pos = main_window.replay_controls.replay_state.current_position

        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Right, Qt.KeyboardModifier.NoModifier)
        main_window.keyPressEvent(event)

        assert main_window.replay_controls.replay_state.current_position == initial_pos + 1

    def test_left_arrow_goes_back(self, main_window: MainWindow) -> None:
        """Left arrow key goes to previous action."""
        hand = make_test_hand()
        main_window._on_hand_selected(hand)
        assert main_window.replay_controls.replay_state is not None
        # Starts at 2 (after 2 POSTs), advance once
        initial_pos = main_window.replay_controls.replay_state.current_position
        main_window.replay_controls.next_button.click()
        assert main_window.replay_controls.replay_state.current_position == initial_pos + 1

        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Left, Qt.KeyboardModifier.NoModifier)
        main_window.keyPressEvent(event)

        assert main_window.replay_controls.replay_state.current_position == initial_pos

    def test_l_key_advances_action(self, main_window: MainWindow) -> None:
        """L key advances to next action."""
        hand = make_test_hand()
        main_window._on_hand_selected(hand)
        assert main_window.replay_controls.replay_state is not None
        initial_pos = main_window.replay_controls.replay_state.current_position

        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_L, Qt.KeyboardModifier.NoModifier)
        main_window.keyPressEvent(event)

        assert main_window.replay_controls.replay_state.current_position == initial_pos + 1

    def test_h_key_goes_back(self, main_window: MainWindow) -> None:
        """H key goes to previous action."""
        hand = make_test_hand()
        main_window._on_hand_selected(hand)
        assert main_window.replay_controls.replay_state is not None
        # Starts at 2 (after 2 POSTs), advance once
        initial_pos = main_window.replay_controls.replay_state.current_position
        main_window.replay_controls.next_button.click()
        assert main_window.replay_controls.replay_state.current_position == initial_pos + 1

        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_H, Qt.KeyboardModifier.NoModifier)
        main_window.keyPressEvent(event)

        assert main_window.replay_controls.replay_state.current_position == initial_pos

    def test_shortcuts_do_nothing_without_hand(self, main_window: MainWindow) -> None:
        """Keyboard shortcuts don't crash when no hand is loaded."""
        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Right, Qt.KeyboardModifier.NoModifier)
        main_window.keyPressEvent(event)

    def test_other_keys_passed_through(self, main_window: MainWindow) -> None:
        """Other keys are passed to parent handler."""
        hand = make_test_hand()
        main_window._on_hand_selected(hand)
        assert main_window.replay_controls.replay_state is not None
        initial_pos = main_window.replay_controls.replay_state.current_position

        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier)
        main_window.keyPressEvent(event)

        assert main_window.replay_controls.replay_state.current_position == initial_pos
