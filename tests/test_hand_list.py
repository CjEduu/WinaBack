"""Tests for HandListWidget."""

from datetime import datetime
from typing import Any

import pytest

from src.gui.hand_list import HandListWidget
from src.parser.models import Action, ActionType, Card, Hand, Player, Street


@pytest.fixture
def sample_hands() -> list[Hand]:
    """Create sample hands for testing."""
    return [
        Hand(
            hand_id="12345-1",
            timestamp=datetime(2024, 1, 15, 14, 30),
            small_blind=50.0,
            big_blind=100.0,
            ante=10.0,
            button_seat=1,
            players=[
                Player(name="Hero", seat=1, stack=5000.0, is_hero=True),
                Player(name="Villain", seat=2, stack=4500.0),
            ],
            actions={
                Street.PREFLOP: [
                    Action(player_name="Hero", action_type=ActionType.POST, amount=50.0),
                    Action(player_name="Villain", action_type=ActionType.POST, amount=100.0),
                ],
                Street.FLOP: [
                    Action(player_name="Hero", action_type=ActionType.CHECK),
                ],
            },
            board=[Card("A", "s"), Card("K", "h"), Card("Q", "d")],
        ),
        Hand(
            hand_id="12345-2",
            timestamp=datetime(2024, 1, 15, 14, 35),
            small_blind=50.0,
            big_blind=100.0,
            ante=10.0,
            button_seat=2,
            players=[
                Player(name="Hero", seat=1, stack=4900.0, is_hero=True),
                Player(name="Villain", seat=2, stack=4600.0),
            ],
            actions={
                Street.PREFLOP: [
                    Action(player_name="Villain", action_type=ActionType.FOLD),
                ],
            },
        ),
        Hand(
            hand_id="12345-3",
            timestamp=datetime(2024, 1, 15, 14, 40),
            small_blind=100.0,
            big_blind=200.0,
            ante=20.0,
            button_seat=1,
            players=[
                Player(name="Hero", seat=1, stack=5050.0, is_hero=True),
                Player(name="Villain", seat=2, stack=4450.0),
            ],
            actions={
                Street.PREFLOP: [],
                Street.FLOP: [],
                Street.TURN: [],
                Street.RIVER: [
                    Action(player_name="Hero", action_type=ActionType.BET, amount=500.0),
                ],
            },
            board=[
                Card("2", "c"),
                Card("5", "d"),
                Card("8", "h"),
                Card("J", "s"),
                Card("K", "c"),
            ],
        ),
    ]


class TestHandListWidget:
    """Tests for HandListWidget."""

    def test_widget_is_created(self, qtbot: Any) -> None:
        """Test widget can be created."""
        widget = HandListWidget()
        qtbot.addWidget(widget)
        assert widget is not None

    def test_set_hands_populates_list(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test setting hands populates the list."""
        widget = HandListWidget()
        qtbot.addWidget(widget)

        widget.set_hands(sample_hands)

        assert widget.count() == 3

    def test_hand_entry_shows_hand_number(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test each entry shows hand number."""
        widget = HandListWidget()
        qtbot.addWidget(widget)

        widget.set_hands(sample_hands)

        item = widget.item(0)
        assert item is not None
        assert "#000" in item.text()

        item2 = widget.item(1)
        assert item2 is not None
        assert "#001" in item2.text()

    def test_hand_entry_shows_brief_summary(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test each entry shows a brief summary."""
        widget = HandListWidget()
        qtbot.addWidget(widget)

        widget.set_hands(sample_hands)

        item = widget.item(0)
        assert item is not None
        text = item.text()
        assert "50/100" in text

    def test_clicking_hand_emits_signal(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test clicking a hand emits hand_selected signal."""
        widget = HandListWidget()
        qtbot.addWidget(widget)
        widget.set_hands(sample_hands)

        with qtbot.waitSignal(widget.hand_selected, timeout=1000) as blocker:
            item = widget.item(1)
            assert item is not None
            widget.itemClicked.emit(item)

        assert blocker.args[0].hand_id == "12345-2"

    def test_selected_hand_is_highlighted(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test clicking a hand highlights it (sets current item)."""
        widget = HandListWidget()
        qtbot.addWidget(widget)
        widget.set_hands(sample_hands)

        item = widget.item(1)
        assert item is not None
        widget.setCurrentItem(item)

        assert widget.currentItem() == item
        assert widget.currentRow() == 1

    def test_get_selected_hand(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test get_selected_hand returns the correct hand."""
        widget = HandListWidget()
        qtbot.addWidget(widget)
        widget.set_hands(sample_hands)

        item = widget.item(2)
        assert item is not None
        widget.setCurrentItem(item)

        selected = widget.get_selected_hand()
        assert selected is not None
        assert selected.hand_id == "12345-3"

    def test_get_selected_hand_returns_none_when_empty(
        self, qtbot: Any
    ) -> None:
        """Test get_selected_hand returns None when nothing selected."""
        widget = HandListWidget()
        qtbot.addWidget(widget)

        assert widget.get_selected_hand() is None

    def test_hands_property(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test hands property returns the list."""
        widget = HandListWidget()
        qtbot.addWidget(widget)
        widget.set_hands(sample_hands)

        assert widget.hands == sample_hands

    def test_select_hand_by_index(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test select_hand_by_index selects the correct hand."""
        widget = HandListWidget()
        qtbot.addWidget(widget)
        widget.set_hands(sample_hands)

        widget.select_hand_by_index(1)

        assert widget.currentRow() == 1
        selected = widget.get_selected_hand()
        assert selected is not None
        assert selected.hand_id == "12345-2"

    def test_select_hand_by_index_out_of_bounds(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test select_hand_by_index with invalid index does nothing."""
        widget = HandListWidget()
        qtbot.addWidget(widget)
        widget.set_hands(sample_hands)

        widget.select_hand_by_index(10)

        assert widget.currentRow() == -1

    def test_clear_and_repopulate(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test setting hands twice clears and repopulates."""
        widget = HandListWidget()
        qtbot.addWidget(widget)

        widget.set_hands(sample_hands)
        assert widget.count() == 3

        new_hands = [sample_hands[0]]
        widget.set_hands(new_hands)
        assert widget.count() == 1
