"""Tests for ActionLogWidget and pot display."""

from datetime import datetime
from typing import Any

from src.gui.action_log import ActionLogWidget
from src.gui.table_widget import TableWidget
from src.parser.models import Action, ActionType, Card, Hand, Player, Street
from src.replayer.state import ReplayState


def create_hand_with_actions() -> Hand:
    """Create a test hand with actions for testing action log."""
    return Hand(
        hand_id="test-hand-actions",
        timestamp=datetime(2024, 1, 15, 14, 30),
        small_blind=50.0,
        big_blind=100.0,
        ante=10.0,
        button_seat=3,
        players=[
            Player(
                name="Hero",
                seat=1,
                stack=1000.0,
                is_hero=True,
                hole_cards=[Card(rank="A", suit="h"), Card(rank="K", suit="h")],
            ),
            Player(name="Villain", seat=2, stack=1500.0),
            Player(name="Other", seat=3, stack=2000.0),
        ],
        board=[
            Card(rank="A", suit="s"),
            Card(rank="K", suit="s"),
            Card(rank="Q", suit="s"),
            Card(rank="J", suit="s"),
            Card(rank="T", suit="s"),
        ],
        actions={
            Street.PREFLOP: [
                Action(player_name="Hero", action_type=ActionType.POST, amount=50),
                Action(player_name="Villain", action_type=ActionType.POST, amount=100),
                Action(player_name="Other", action_type=ActionType.FOLD),
                Action(player_name="Hero", action_type=ActionType.CALL, amount=50),
                Action(player_name="Villain", action_type=ActionType.CHECK),
            ],
            Street.FLOP: [
                Action(player_name="Hero", action_type=ActionType.CHECK),
                Action(player_name="Villain", action_type=ActionType.BET, amount=100),
                Action(player_name="Hero", action_type=ActionType.CALL, amount=100),
            ],
            Street.TURN: [
                Action(player_name="Hero", action_type=ActionType.CHECK),
                Action(player_name="Villain", action_type=ActionType.CHECK),
            ],
            Street.RIVER: [
                Action(player_name="Hero", action_type=ActionType.BET, amount=200),
                Action(player_name="Villain", action_type=ActionType.CALL, amount=200),
            ],
        },
    )


class TestActionLogWidget:
    """Test ActionLogWidget functionality."""

    def test_initial_state(self, qtbot: Any) -> None:
        """Widget starts with no replay state."""
        widget = ActionLogWidget()
        qtbot.addWidget(widget)

        assert widget.replay_state is None
        assert widget.count() == 0

    def test_set_replay_state(self, qtbot: Any) -> None:
        """Setting replay state populates actions."""
        widget = ActionLogWidget()
        qtbot.addWidget(widget)

        hand = create_hand_with_actions()
        state = ReplayState(hand=hand)
        state.goto_position(5)

        widget.set_replay_state(state)

        assert widget.replay_state is state
        assert widget.count() > 0

    def test_shows_actions_up_to_current(self, qtbot: Any) -> None:
        """Shows only actions up to current position."""
        widget = ActionLogWidget()
        qtbot.addWidget(widget)

        hand = create_hand_with_actions()
        state = ReplayState(hand=hand)
        state.goto_position(3)

        widget.set_replay_state(state)

        action_count = 0
        for i in range(widget.count()):
            item = widget.item(i)
            assert item is not None
            if not item.text().startswith("---"):
                action_count += 1
        assert action_count == 3

    def test_street_headers_displayed(self, qtbot: Any) -> None:
        """Street headers are displayed between streets."""
        widget = ActionLogWidget()
        qtbot.addWidget(widget)

        hand = create_hand_with_actions()
        state = ReplayState(hand=hand)
        state.goto_street(Street.FLOP)
        state.next_action()
        state.next_action()

        widget.set_replay_state(state)

        items: list[str] = []
        for i in range(widget.count()):
            item = widget.item(i)
            assert item is not None
            items.append(item.text())
        assert any("PREFLOP" in item for item in items)
        assert any("FLOP" in item for item in items)

    def test_refresh_updates_display(self, qtbot: Any) -> None:
        """Refresh updates the display after navigation."""
        widget = ActionLogWidget()
        qtbot.addWidget(widget)

        hand = create_hand_with_actions()
        state = ReplayState(hand=hand)
        state.goto_position(2)
        widget.set_replay_state(state)

        initial_count = widget.count()

        state.next_action()
        state.next_action()
        widget.refresh()

        assert widget.count() > initial_count

    def test_clear_on_none(self, qtbot: Any) -> None:
        """Setting None clears the widget."""
        widget = ActionLogWidget()
        qtbot.addWidget(widget)

        hand = create_hand_with_actions()
        state = ReplayState(hand=hand)
        state.goto_position(5)
        widget.set_replay_state(state)

        assert widget.count() > 0

        widget.set_replay_state(None)
        assert widget.count() == 0

    def test_action_formatting_post(self, qtbot: Any) -> None:
        """Post actions are formatted correctly."""
        widget = ActionLogWidget()
        qtbot.addWidget(widget)

        action = Action(player_name="Hero", action_type=ActionType.POST, amount=50)
        text = widget._format_action(action)
        assert text == "Hero posts 50"

    def test_action_formatting_fold(self, qtbot: Any) -> None:
        """Fold actions are formatted correctly."""
        widget = ActionLogWidget()
        qtbot.addWidget(widget)

        action = Action(player_name="Other", action_type=ActionType.FOLD)
        text = widget._format_action(action)
        assert text == "Other folds"

    def test_action_formatting_check(self, qtbot: Any) -> None:
        """Check actions are formatted correctly."""
        widget = ActionLogWidget()
        qtbot.addWidget(widget)

        action = Action(player_name="Hero", action_type=ActionType.CHECK)
        text = widget._format_action(action)
        assert text == "Hero checks"

    def test_action_formatting_bet(self, qtbot: Any) -> None:
        """Bet actions are formatted correctly."""
        widget = ActionLogWidget()
        qtbot.addWidget(widget)

        action = Action(player_name="Villain", action_type=ActionType.BET, amount=100)
        text = widget._format_action(action)
        assert text == "Villain bets 100"

    def test_action_formatting_call(self, qtbot: Any) -> None:
        """Call actions are formatted correctly."""
        widget = ActionLogWidget()
        qtbot.addWidget(widget)

        action = Action(player_name="Hero", action_type=ActionType.CALL, amount=100)
        text = widget._format_action(action)
        assert text == "Hero calls 100"

    def test_action_formatting_raise(self, qtbot: Any) -> None:
        """Raise actions are formatted correctly."""
        widget = ActionLogWidget()
        qtbot.addWidget(widget)

        action = Action(player_name="Hero", action_type=ActionType.RAISE, amount=300)
        text = widget._format_action(action)
        assert text == "Hero raises to 300"

    def test_action_formatting_allin(self, qtbot: Any) -> None:
        """All-in actions show all-in suffix."""
        widget = ActionLogWidget()
        qtbot.addWidget(widget)

        action = Action(
            player_name="Hero", action_type=ActionType.CALL, amount=500, is_all_in=True
        )
        text = widget._format_action(action)
        assert text == "Hero calls 500 (all-in)"


class TestPotDisplay:
    """Test pot display on TableWidget."""

    def test_pot_colors_defined(self, qtbot: Any) -> None:
        """Pot display colors are properly defined."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        assert widget.POT_BG_COLOR.isValid()
        assert widget.POT_TEXT_COLOR.isValid()

    def test_pot_updates_with_actions(self, qtbot: Any) -> None:
        """Pot is calculated correctly based on actions."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_hand_with_actions()
        widget.set_hand(hand)

        assert widget.replay_state is not None
        # Initial position is after 2 POSTs (50+100=150)
        assert widget.replay_state.calculate_pot() == 150

        # Position 4: 2 POSTs + FOLD + CALL(50) = 200
        widget.replay_state.goto_position(4)
        assert widget.replay_state.calculate_pot() == 200

    def test_pot_display_at_various_positions(self, qtbot: Any) -> None:
        """Pot display works at various replay positions."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_hand_with_actions()
        widget.set_hand(hand)

        assert widget.replay_state is not None

        for pos in range(widget.replay_state.total_actions + 1):
            widget.replay_state.goto_position(pos)
            widget.show()

    def test_pot_display_renders(self, qtbot: Any) -> None:
        """Pot display renders without crashing."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_hand_with_actions()
        widget.set_hand(hand)

        assert widget.replay_state is not None
        widget.replay_state.goto_position(4)

        widget.show()
        qtbot.waitExposed(widget)
