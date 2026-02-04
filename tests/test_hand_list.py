"""Tests for HandListWidget."""

from datetime import datetime
from typing import Any

import pytest

from src.gui.hand_list import EARNED_VALUE_ROLE, HandListWidget
from src.gui.tournament_list import SortOrder
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
        assert isinstance(widget, HandListWidget)

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


class TestHandListSorting:
    """Tests for hand list sorting by earned value."""

    def test_default_sort_order_on_creation(self, qtbot: Any) -> None:
        """Test widget starts with default sort order."""
        widget = HandListWidget()
        qtbot.addWidget(widget)
        assert widget.sort_order == SortOrder.DEFAULT

    def test_sort_button_shows_default_label(self, qtbot: Any) -> None:
        """Test sort button shows default label initially."""
        widget = HandListWidget()
        qtbot.addWidget(widget)
        assert widget._sort_button.text() == "Sort: —"

    def test_set_hands_resets_to_default_sort(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test set_hands resets sort order to default."""
        widget = HandListWidget()
        qtbot.addWidget(widget)
        widget.set_hands(sample_hands)

        # Cycle to ascending
        widget._cycle_sort_order()
        assert widget.sort_order == SortOrder.ASCENDING

        # Set hands again
        widget.set_hands(sample_hands)
        assert widget.sort_order == SortOrder.DEFAULT
        assert widget._sort_button.text() == "Sort: —"

    def test_cycle_to_ascending(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test cycling from default to ascending."""
        widget = HandListWidget()
        qtbot.addWidget(widget)
        widget.set_hands(sample_hands)

        widget._cycle_sort_order()

        assert widget.sort_order == SortOrder.ASCENDING
        assert widget._sort_button.text() == "Sort: ↑"

    def test_cycle_to_descending(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test cycling from ascending to descending."""
        widget = HandListWidget()
        qtbot.addWidget(widget)
        widget.set_hands(sample_hands)

        widget._cycle_sort_order()  # -> ASCENDING
        widget._cycle_sort_order()  # -> DESCENDING

        assert widget.sort_order == SortOrder.DESCENDING
        assert widget._sort_button.text() == "Sort: ↓"

    def test_cycle_back_to_default(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test cycling from descending back to default."""
        widget = HandListWidget()
        qtbot.addWidget(widget)
        widget.set_hands(sample_hands)

        widget._cycle_sort_order()  # -> ASCENDING
        widget._cycle_sort_order()  # -> DESCENDING
        widget._cycle_sort_order()  # -> DEFAULT

        assert widget.sort_order == SortOrder.DEFAULT
        assert widget._sort_button.text() == "Sort: —"

    def test_ascending_sorts_lowest_first(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test ascending order sorts by lowest earned value first."""
        widget = HandListWidget()
        qtbot.addWidget(widget)
        widget.set_hands(sample_hands)

        # sample_hands earned values (lookahead):
        # hand 0: 4900 - 5000 = -100
        # hand 1: 5050 - 4900 = +150
        # hand 2: 0 (last hand)

        widget._cycle_sort_order()  # -> ASCENDING

        hands = widget.hands
        # Ascending: -100, 0, +150
        assert hands[0].hand_id == "12345-1"  # -100
        assert hands[1].hand_id == "12345-3"  # 0
        assert hands[2].hand_id == "12345-2"  # +150

    def test_descending_sorts_highest_first(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test descending order sorts by highest earned value first."""
        widget = HandListWidget()
        qtbot.addWidget(widget)
        widget.set_hands(sample_hands)

        widget._cycle_sort_order()  # -> ASCENDING
        widget._cycle_sort_order()  # -> DESCENDING

        hands = widget.hands
        # Descending: +150, 0, -100
        assert hands[0].hand_id == "12345-2"  # +150
        assert hands[1].hand_id == "12345-3"  # 0
        assert hands[2].hand_id == "12345-1"  # -100

    def test_default_restores_original_order(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test default order restores original parse order."""
        widget = HandListWidget()
        qtbot.addWidget(widget)
        widget.set_hands(sample_hands)

        widget._cycle_sort_order()  # -> ASCENDING
        widget._cycle_sort_order()  # -> DESCENDING
        widget._cycle_sort_order()  # -> DEFAULT

        hands = widget.hands
        assert hands[0].hand_id == "12345-1"
        assert hands[1].hand_id == "12345-2"
        assert hands[2].hand_id == "12345-3"

    def test_earned_value_stored_in_item_data(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test earned value is stored in item data."""
        widget = HandListWidget()
        qtbot.addWidget(widget)
        widget.set_hands(sample_hands)

        item0 = widget.item(0)
        item1 = widget.item(1)
        item2 = widget.item(2)

        assert item0 is not None
        assert item1 is not None
        assert item2 is not None

        # hand 0: -100, hand 1: +150, hand 2: 0 (last)
        assert item0.data(EARNED_VALUE_ROLE) == -100.0
        assert item1.data(EARNED_VALUE_ROLE) == 150.0
        assert item2.data(EARNED_VALUE_ROLE) == 0.0

    def test_sort_button_click_cycles_order(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test clicking sort button cycles through orders."""
        widget = HandListWidget()
        qtbot.addWidget(widget)
        widget.set_hands(sample_hands)

        widget._sort_button.click()
        assert widget.sort_order == SortOrder.ASCENDING

        widget._sort_button.click()
        assert widget.sort_order == SortOrder.DESCENDING

        widget._sort_button.click()
        assert widget.sort_order == SortOrder.DEFAULT

    def test_original_index_preserved_after_sort(
        self, qtbot: Any, sample_hands: list[Hand]
    ) -> None:
        """Test original hand indices are preserved in display after sorting."""
        widget = HandListWidget()
        qtbot.addWidget(widget)
        widget.set_hands(sample_hands)

        widget._cycle_sort_order()  # -> ASCENDING
        # Now sorted: hand_id 12345-1, 12345-3, 12345-2
        # But display should still show #000, #002, #001 (original indices)

        item0 = widget.item(0)
        item1 = widget.item(1)

        assert item0 is not None
        assert item1 is not None

        # First item is 12345-1 which was #000 originally
        assert "#000" in item0.text()
        # Third item is 12345-3 which was #002 originally (but last hand shown differently)
        # Second slot has 12345-3 which is the last hand
        # Actually: hand 0: -100 (12345-1), hand 2: 0 (12345-3), hand 1: +150 (12345-2)
        # Second position is 12345-3 which is "Last Hand"
