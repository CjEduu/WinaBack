"""Main window for WinaBack Poker Tournament Replayer."""
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QCloseEvent, QKeyEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from typing_extensions import override

from src.gui.action_log import ActionLogWidget
from src.gui.controls import ReplayControls
from src.gui.folder_loader import FolderLoader
from src.gui.hand_list import HandListWidget
from src.gui.table_widget import TableWidget
from src.gui.tournament_list import TournamentListWidget
from src.parser.models import ActionType, Hand, Tournament
from src.preferences import VALID_UI_SCALES, Preferences

DARK_THEME_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1e1e1e;
    color: #d4d4d4;
}
QMenuBar {
    background-color: #2d2d2d;
    color: #d4d4d4;
}
QMenuBar::item:selected {
    background-color: #3e3e3e;
}
QLabel#helpBar {
    background-color: #2d2d2d;
    color: #808080;
    padding: 2px 8px;
    font-size: 11px;
}
QMenu {
    background-color: #2d2d2d;
    color: #d4d4d4;
}
QMenu::item:selected {
    background-color: #3e3e3e;
}
QSplitter::handle {
    background-color: #3e3e3e;
}
QListWidget {
    background-color: #252526;
    color: #d4d4d4;
    border: 1px solid #3e3e3e;
}
QListWidget::item:selected {
    background-color: #094771;
}
QPushButton {
    background-color: #3e3e3e;
    color: #d4d4d4;
    border: 1px solid #5e5e5e;
    padding: 5px 10px;
    border-radius: 3px;
}
QPushButton:hover {
    background-color: #4e4e4e;
}
QPushButton:pressed {
    background-color: #2e2e2e;
}
QPushButton:disabled {
    background-color: #2e2e2e;
    color: #6e6e6e;
}
QSlider::groove:horizontal {
    background-color: #3e3e3e;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background-color: #0078d4;
    width: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 12px;
}
QScrollBar::handle:vertical {
    background-color: #5e5e5e;
    border-radius: 6px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


class MainWindow(QMainWindow):
    """Main application window with three-panel layout."""

    folder_open_requested = pyqtSignal()
    tournaments_loaded = pyqtSignal(list)  # list[Tournament]
    tournament_selected = pyqtSignal(Tournament)
    hand_selected = pyqtSignal(Hand)

    def __init__(self, preferences: Preferences | None = None) -> None:
        super().__init__()
        self._preferences = preferences or Preferences.load()
        self._folder_loader = FolderLoader(self)
        self._tournaments: list[Tournament] = []
        self._setup_window()
        self._setup_menu()
        self._setup_layout()
        self._apply_theme()
        self._connect_signals()
        self._restore_window_state()

    def _setup_window(self) -> None:
        self.setWindowTitle("WinaBack - Poker Tournament Replayer")
        self.setMinimumSize(1200, 800)

    def _setup_menu(self) -> None:
        menu_bar = self.menuBar()
        assert menu_bar is not None
        file_menu = menu_bar.addMenu("&File")
        assert file_menu is not None

        open_folder_action = QAction("&Open Folder...", self)
        open_folder_action.setShortcut("Ctrl+O")
        open_folder_action.triggered.connect(self.folder_open_requested.emit)
        file_menu.addAction(open_folder_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_bar = QLabel("h/l: action  j/k: hand  g/G: start/end")
        help_bar.setObjectName("helpBar")
        menu_bar.setCornerWidget(help_bar, Qt.Corner.TopRightCorner)

    def _setup_layout(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        top_splitter = QSplitter()

        self._sidebar = QWidget()
        self._sidebar.setMinimumWidth(200)
        self._sidebar.setMaximumWidth(400)
        sidebar_layout = QVBoxLayout(self._sidebar)
        sidebar_layout.setContentsMargins(5, 5, 5, 5)

        tournament_label = QLabel("Tournaments")
        sidebar_layout.addWidget(tournament_label)
        self._tournament_list = TournamentListWidget()
        sidebar_layout.addWidget(self._tournament_list)

        hands_label = QLabel("Hands")
        sidebar_layout.addWidget(hands_label)
        self._hand_list = HandListWidget()
        sidebar_layout.addWidget(self._hand_list)

        top_splitter.addWidget(self._sidebar)

        self._table_area = QWidget()
        table_layout = QVBoxLayout(self._table_area)
        table_layout.setContentsMargins(5, 5, 5, 5)
        self._table_widget = TableWidget()
        self._table_widget.set_ui_scale(self._preferences.ui_scale)
        table_layout.addWidget(self._table_widget, stretch=1)

        action_log_label = QLabel("Action History")
        table_layout.addWidget(action_log_label)
        self._action_log = ActionLogWidget()
        self._action_log.setMaximumHeight(150)
        table_layout.addWidget(self._action_log)

        top_splitter.addWidget(self._table_area)

        top_splitter.setSizes([250, 950])

        main_layout.addWidget(top_splitter, stretch=1)

        self._controls = QWidget()
        self._controls.setMinimumHeight(80)
        self._controls.setMaximumHeight(120)
        controls_layout = QHBoxLayout(self._controls)
        controls_layout.setContentsMargins(10, 10, 10, 10)

        self._replay_controls = ReplayControls()
        controls_layout.addWidget(self._replay_controls)

        main_layout.addWidget(self._controls)

    def _apply_theme(self) -> None:
        self.setStyleSheet(DARK_THEME_STYLESHEET)

    def _restore_window_state(self) -> None:
        """Restore window size and position from preferences."""
        prefs = self._preferences
        self.setGeometry(
            prefs.window_x,
            prefs.window_y,
            prefs.window_width,
            prefs.window_height,
        )
        if prefs.window_maximized:
            self.showMaximized()

        if prefs.last_folder_path and Path(prefs.last_folder_path).is_dir():
            self._folder_loader.load_folder(prefs.last_folder_path)

    def _save_window_state(self) -> None:
        """Save window size and position to preferences."""
        prefs = self._preferences
        prefs.window_maximized = self.isMaximized()
        if not prefs.window_maximized:
            geometry = self.geometry()
            prefs.window_x = geometry.x()
            prefs.window_y = geometry.y()
            prefs.window_width = geometry.width()
            prefs.window_height = geometry.height()
        prefs.save()

    def _connect_signals(self) -> None:
        self.folder_open_requested.connect(self._on_folder_open_requested)
        self._folder_loader.tournaments_loaded.connect(self._on_tournaments_loaded)
        self._tournament_list.tournament_selected.connect(self._on_tournament_selected)
        self._hand_list.hand_selected.connect(self._on_hand_selected)
        self._replay_controls.action_changed.connect(self._on_action_changed)
        self._replay_controls.next_hand_requested.connect(self._on_next_hand_requested)
        self._replay_controls.prev_hand_requested.connect(self._on_prev_hand_requested)
        self._replay_controls.equity_calculated.connect(self._on_equity_calculated)

    def _on_folder_open_requested(self) -> None:
        """Handle folder open request by showing dialog and loading folder."""
        folder_path = self._folder_loader.open_folder_dialog(self)
        if folder_path:
            self._preferences.last_folder_path = folder_path
            self._preferences.save()
            self._folder_loader.load_folder(folder_path)

    def _on_tournaments_loaded(self, tournaments: list[Tournament]) -> None:
        """Handle tournaments being loaded."""
        self._tournaments = tournaments
        self._tournament_list.set_tournaments(tournaments)
        self.tournaments_loaded.emit(tournaments)

    def _on_tournament_selected(self, tournament: Tournament) -> None:
        """Handle tournament selection from the list."""
        self._hand_list.set_hands(tournament.hands)
        self.tournament_selected.emit(tournament)

    def _on_hand_selected(self, hand: Hand) -> None:
        """Handle hand selection from the list."""
        self._table_widget.set_hand(hand)
        self._replay_controls.set_replay_state(self._table_widget.replay_state)
        self._action_log.set_replay_state(self._table_widget.replay_state)
        self._update_hand_navigation_buttons()
        self.hand_selected.emit(hand)

    def _on_action_changed(self) -> None:
        """Handle replay navigation, update table and action log."""
        replay_state = self._replay_controls.replay_state
        if replay_state:
            current_action = replay_state.current_action
            if current_action and current_action.action_type in (
                ActionType.POST,
                ActionType.BET,
                ActionType.CALL,
                ActionType.RAISE,
                ActionType.ALL_IN,
            ):
                self._table_widget.trigger_bet_animation()
            else:
                self._table_widget.update()
        else:
            self._table_widget.update()
        self._action_log.refresh()

    def _on_equity_calculated(self) -> None:
        """Handle equity calculation completion, update table display."""
        self._table_widget.update()

    def _on_next_hand_requested(self) -> None:
        """Handle next hand navigation request."""
        current_row = self._hand_list.currentRow()
        if current_row < self._hand_list.count() - 1:
            self._hand_list.select_hand_by_index(current_row + 1)
            item = self._hand_list.currentItem()
            if item is not None:
                self._hand_list.itemClicked.emit(item)

    def _on_prev_hand_requested(self) -> None:
        """Handle previous hand navigation request."""
        current_row = self._hand_list.currentRow()
        if current_row > 0:
            self._hand_list.select_hand_by_index(current_row - 1)
            item = self._hand_list.currentItem()
            if item is not None:
                self._hand_list.itemClicked.emit(item)

    def _update_hand_navigation_buttons(self) -> None:
        """Update hand navigation button states based on current hand position."""
        current_row = self._hand_list.currentRow()
        total_hands = self._hand_list.count()
        prev_enabled = current_row > 0
        next_enabled = current_row < total_hands - 1 and total_hands > 0
        self._replay_controls.set_hand_navigation_enabled(prev_enabled, next_enabled)

    @property
    def tournaments(self) -> list[Tournament]:
        """Get the list of loaded tournaments."""
        return self._tournaments

    @property
    def folder_loader(self) -> FolderLoader:
        """Get the folder loader instance."""
        return self._folder_loader

    @property
    def sidebar(self) -> QWidget:
        """Get the left sidebar widget for tournament/hand lists."""
        return self._sidebar

    @property
    def table_area(self) -> QWidget:
        """Get the center table area widget for poker table display."""
        return self._table_area

    @property
    def controls(self) -> QWidget:
        """Get the bottom controls widget for playback controls."""
        return self._controls

    @property
    def tournament_list(self) -> TournamentListWidget:
        """Get the tournament list widget."""
        return self._tournament_list

    @property
    def hand_list(self) -> HandListWidget:
        """Get the hand list widget."""
        return self._hand_list

    @property
    def table_widget(self) -> TableWidget:
        """Get the poker table widget."""
        return self._table_widget

    @property
    def action_log(self) -> ActionLogWidget:
        """Get the action log widget."""
        return self._action_log

    @property
    def replay_controls(self) -> ReplayControls:
        """Get the replay controls widget."""
        return self._replay_controls

    @property
    def preferences(self) -> Preferences:
        """Get the preferences instance."""
        return self._preferences

    @override
    def closeEvent(self, event: QCloseEvent | None) -> None:
        """Save window state when closing."""
        self._save_window_state()
        if event is not None:
            event.accept()

    @override
    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        """Handle keyboard shortcuts for replay navigation."""
        if event is None:
            return

        key = event.key()

        match key:
            case Qt.Key.Key_Right | Qt.Key.Key_L:
                self._replay_controls.next_button.click()
            case Qt.Key.Key_Left | Qt.Key.Key_H:
                self._replay_controls.prev_button.click()
            case Qt.Key.Key_Up | Qt.Key.Key_K:
                self._replay_controls.prev_hand_button.click()
            case Qt.Key.Key_Down | Qt.Key.Key_J:
                self._replay_controls.next_hand_button.click()
            case Qt.Key.Key_G:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    self._replay_controls.go_to_end()
                else:
                    self._replay_controls.go_to_start()
            case Qt.Key.Key_Plus | Qt.Key.Key_Equal:
                self._adjust_ui_scale(0.25)
            case Qt.Key.Key_Minus:
                self._adjust_ui_scale(-0.25)
            case Qt.Key.Key_0:
                self._set_ui_scale(1.0)
            case _:
                super().keyPressEvent(event)

    def _adjust_ui_scale(self, delta: float) -> None:
        """Adjust UI scale by delta, clamped to valid values."""
        new_scale = self._preferences.ui_scale + delta
        new_scale = max(VALID_UI_SCALES[0], min(VALID_UI_SCALES[-1], new_scale))
        self._set_ui_scale(new_scale)

    def _set_ui_scale(self, scale: float) -> None:
        """Set UI scale to specific value, save, and update table."""
        if scale != self._preferences.ui_scale:
            self._preferences.ui_scale = scale
            self._preferences.save()
            self._table_widget.set_ui_scale(scale)
                
