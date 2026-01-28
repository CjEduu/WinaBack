"""Tests for TableWidget - poker table rendering."""
import math
from datetime import datetime
from typing import Any

from src.gui.table_widget import PlayerZone, TableWidget
from src.parser.models import Action, ActionType, Card, Hand, Player, Street
from src.replayer.state import ReplayState


def create_test_hand(num_players: int = 6, hero_seat: int = 1) -> Hand:
    """Create a test hand with specified number of players."""
    players = []
    for i in range(1, num_players + 1):
        players.append(
            Player(
                name=f"Player{i}",
                seat=i,
                stack=1000.0 * i,
                is_hero=(i == hero_seat),
            )
        )
    return Hand(
        hand_id="test-hand-1",
        timestamp=datetime(2024, 1, 15, 14, 30),
        small_blind=50.0,
        big_blind=100.0,
        ante=10.0,
        button_seat=num_players,
        players=players,
    )


class TestTableWidgetBasics:
    """Test basic widget functionality."""

    def test_initial_state(self, qtbot: Any) -> None:
        """Widget starts with no hand."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        assert widget.hand is None
        assert widget.replay_state is None

    def test_set_hand(self, qtbot: Any) -> None:
        """Setting a hand creates replay state."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        hand = create_test_hand()
        widget.set_hand(hand)

        assert widget.hand is hand
        assert widget.replay_state is not None
        assert isinstance(widget.replay_state, ReplayState)

    def test_set_replay_state(self, qtbot: Any) -> None:
        """Can set replay state directly."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        hand = create_test_hand()
        state = ReplayState(hand=hand)
        widget.set_replay_state(state)

        assert widget.hand is hand
        assert widget.replay_state is state

    def test_clear(self, qtbot: Any) -> None:
        """Clearing removes hand and state."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        widget.set_hand(create_test_hand())
        widget.clear()

        assert widget.hand is None
        assert widget.replay_state is None

    def test_minimum_size(self, qtbot: Any) -> None:
        """Widget has minimum size set."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        assert widget.minimumWidth() >= 400
        assert widget.minimumHeight() >= 300


class TestPlayerPositioning:
    """Test player position calculations."""

    def test_positions_for_3_players(self, qtbot: Any) -> None:
        """3 players are positioned around the table."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_test_hand(num_players=3, hero_seat=1)
        widget.set_hand(hand)

        positions = widget._get_player_positions()
        assert len(positions) == 3

    def test_positions_for_6_players(self, qtbot: Any) -> None:
        """6 players are positioned around the table."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_test_hand(num_players=6, hero_seat=1)
        widget.set_hand(hand)

        positions = widget._get_player_positions()
        assert len(positions) == 6

    def test_positions_for_8_players(self, qtbot: Any) -> None:
        """8 players are positioned around the table."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_test_hand(num_players=8, hero_seat=1)
        widget.set_hand(hand)

        positions = widget._get_player_positions()
        assert len(positions) == 8

    def test_hero_at_bottom_center(self, qtbot: Any) -> None:
        """Hero is positioned at bottom center of table."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_test_hand(num_players=6, hero_seat=3)
        widget.set_hand(hand)

        positions = widget._get_player_positions()

        hero_pos = None
        for player, pos in positions:
            if player.is_hero:
                hero_pos = pos
                break

        assert hero_pos is not None
        center_x = widget.width() / 2
        assert abs(hero_pos.x() - center_x) < 1.0
        assert hero_pos.y() > widget.height() / 2

    def test_empty_hand_returns_no_positions(self, qtbot: Any) -> None:
        """No positions returned when no hand is set."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        positions = widget._get_player_positions()
        assert positions == []

    def test_positions_are_unique(self, qtbot: Any) -> None:
        """Each player has a unique position."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_test_hand(num_players=6, hero_seat=1)
        widget.set_hand(hand)

        positions = widget._get_player_positions()
        coords = [(p.x(), p.y()) for _, p in positions]

        assert len(coords) == len(set(coords))


class TestStackFormatting:
    """Test chip stack formatting."""

    def test_format_small_stack(self, qtbot: Any) -> None:
        """Small stacks show exact amount."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        assert widget._format_stack(500) == "500"
        assert widget._format_stack(999) == "999"

    def test_format_thousands(self, qtbot: Any) -> None:
        """Thousands are formatted with K suffix."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        assert widget._format_stack(1000) == "1.0K"
        assert widget._format_stack(5500) == "5.5K"
        assert widget._format_stack(25000) == "25.0K"

    def test_format_millions(self, qtbot: Any) -> None:
        """Millions are formatted with M suffix."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        assert widget._format_stack(1_000_000) == "1.0M"
        assert widget._format_stack(2_500_000) == "2.5M"


class TestButtonIndicator:
    """Test dealer button indicator."""

    def test_button_indicator_renders_for_dealer(self, qtbot: Any) -> None:
        """Button indicator is rendered near the dealer player."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_test_hand(num_players=6, hero_seat=1)
        widget.set_hand(hand)

        widget.show()
        qtbot.waitExposed(widget)

    def test_button_updates_on_hand_change(self, qtbot: Any) -> None:
        """Button indicator updates when hand changes."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand1 = Hand(
            hand_id="hand1",
            timestamp=datetime(2024, 1, 15, 14, 30),
            small_blind=50.0,
            big_blind=100.0,
            ante=10.0,
            button_seat=1,
            players=[
                Player(name="P1", seat=1, stack=1000, is_hero=True),
                Player(name="P2", seat=2, stack=1000),
                Player(name="P3", seat=3, stack=1000),
            ],
        )
        widget.set_hand(hand1)
        assert widget.hand is not None
        assert widget.hand.button_seat == 1

        hand2 = Hand(
            hand_id="hand2",
            timestamp=datetime(2024, 1, 15, 14, 35),
            small_blind=50.0,
            big_blind=100.0,
            ante=10.0,
            button_seat=2,
            players=[
                Player(name="P1", seat=1, stack=1000, is_hero=True),
                Player(name="P2", seat=2, stack=1000),
                Player(name="P3", seat=3, stack=1000),
            ],
        )
        widget.set_hand(hand2)
        assert widget.hand is not None
        assert widget.hand.button_seat == 2

    def test_button_position_matches_dealer_seat(self, qtbot: Any) -> None:
        """Button is drawn at the correct player position (dealer seat)."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = Hand(
            hand_id="test",
            timestamp=datetime(2024, 1, 15, 14, 30),
            small_blind=50.0,
            big_blind=100.0,
            ante=10.0,
            button_seat=3,
            players=[
                Player(name="Hero", seat=1, stack=1000, is_hero=True),
                Player(name="P2", seat=2, stack=1000),
                Player(name="Dealer", seat=3, stack=1000),
            ],
        )
        widget.set_hand(hand)

        positions = widget._get_player_positions()
        dealer_found = False
        for player, _pos in positions:
            if player.seat == hand.button_seat:
                dealer_found = True
                assert player.name == "Dealer"
        assert dealer_found


class TestRendering:
    """Test that painting doesn't crash."""

    def test_paint_empty_table(self, qtbot: Any) -> None:
        """Painting empty table doesn't crash."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)
        widget.show()
        qtbot.waitExposed(widget)

    def test_paint_with_hand(self, qtbot: Any) -> None:
        """Painting table with hand doesn't crash."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_test_hand(num_players=6)
        widget.set_hand(hand)

        widget.show()
        qtbot.waitExposed(widget)

    def test_paint_with_varied_player_counts(self, qtbot: Any) -> None:
        """Painting works for 3-8 player tables."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        for num_players in range(3, 9):
            hand = create_test_hand(num_players=num_players)
            widget.set_hand(hand)
            widget.show()
            qtbot.waitExposed(widget)
            widget.hide()


def create_hand_with_board() -> Hand:
    """Create a test hand with board cards and actions for each street."""
    players = [
        Player(name="Hero", seat=1, stack=1000.0, is_hero=True),
        Player(name="Villain", seat=2, stack=1000.0),
        Player(name="Other", seat=3, stack=1000.0),
    ]
    return Hand(
        hand_id="board-test",
        timestamp=datetime(2024, 1, 15, 14, 30),
        small_blind=50.0,
        big_blind=100.0,
        ante=0.0,
        button_seat=3,
        players=players,
        board=[
            Card(rank="A", suit="h"),
            Card(rank="K", suit="s"),
            Card(rank="Q", suit="d"),
            Card(rank="J", suit="c"),
            Card(rank="T", suit="h"),
        ],
        actions={
            Street.PREFLOP: [
                Action(player_name="Hero", action_type=ActionType.POST, amount=50),
                Action(player_name="Villain", action_type=ActionType.POST, amount=100),
                Action(player_name="Other", action_type=ActionType.CALL, amount=100),
                Action(player_name="Hero", action_type=ActionType.CALL, amount=50),
                Action(player_name="Villain", action_type=ActionType.CHECK),
            ],
            Street.FLOP: [
                Action(player_name="Hero", action_type=ActionType.CHECK),
                Action(player_name="Villain", action_type=ActionType.BET, amount=100),
            ],
            Street.TURN: [
                Action(player_name="Hero", action_type=ActionType.CHECK),
            ],
            Street.RIVER: [
                Action(player_name="Hero", action_type=ActionType.BET, amount=200),
            ],
        },
    )


def create_hand_with_hole_cards() -> Hand:
    """Create a test hand with hero hole cards and showdown hands."""
    players = [
        Player(
            name="Hero",
            seat=1,
            stack=1000.0,
            is_hero=True,
            hole_cards=[Card(rank="A", suit="s"), Card(rank="K", suit="s")],
        ),
        Player(name="Villain", seat=2, stack=1000.0),
        Player(name="Other", seat=3, stack=1000.0),
    ]
    return Hand(
        hand_id="hole-cards-test",
        timestamp=datetime(2024, 1, 15, 14, 30),
        small_blind=50.0,
        big_blind=100.0,
        ante=0.0,
        button_seat=3,
        players=players,
        board=[
            Card(rank="Q", suit="h"),
            Card(rank="J", suit="h"),
            Card(rank="T", suit="h"),
            Card(rank="2", suit="c"),
            Card(rank="3", suit="d"),
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
            Street.SHOWDOWN: [],
        },
        showdown_hands={
            "Villain": [Card(rank="Q", suit="s"), Card(rank="Q", suit="c")],
        },
    )


class TestHoleCards:
    """Test player hole card display."""

    def test_hero_cards_always_visible(self, qtbot: Any) -> None:
        """Hero's hole cards are visible from the start."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_hand_with_hole_cards()
        widget.set_hand(hand)

        assert widget.replay_state is not None
        visible = widget.replay_state.get_visible_hole_cards()
        assert "Hero" in visible
        assert len(visible["Hero"]) == 2
        assert visible["Hero"][0].rank == "A"
        assert visible["Hero"][1].rank == "K"

    def test_opponent_cards_not_visible_before_showdown(self, qtbot: Any) -> None:
        """Opponent cards are not visible before showdown."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_hand_with_hole_cards()
        widget.set_hand(hand)

        assert widget.replay_state is not None
        widget.replay_state.goto_street(Street.RIVER)
        visible = widget.replay_state.get_visible_hole_cards()

        assert "Villain" not in visible

    def test_showdown_cards_visible_at_end(self, qtbot: Any) -> None:
        """Showdown hands are visible at end of hand."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_hand_with_hole_cards()
        widget.set_hand(hand)

        assert widget.replay_state is not None
        while widget.replay_state.next_action():
            pass

        visible = widget.replay_state.get_visible_hole_cards()
        assert "Villain" in visible
        assert len(visible["Villain"]) == 2
        assert visible["Villain"][0].rank == "Q"

    def test_folded_player_no_cards(self, qtbot: Any) -> None:
        """Folded players don't show cards."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_hand_with_hole_cards()
        widget.set_hand(hand)

        assert widget.replay_state is not None
        while widget.replay_state.next_action():
            pass

        visible = widget.replay_state.get_visible_hole_cards()
        assert "Other" not in visible

        player_states = widget.replay_state.get_player_states()
        assert player_states["Other"].is_folded

    def test_paint_with_hole_cards(self, qtbot: Any) -> None:
        """Painting table with hole cards doesn't crash."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_hand_with_hole_cards()
        widget.set_hand(hand)

        widget.show()
        qtbot.waitExposed(widget)

    def test_paint_at_showdown(self, qtbot: Any) -> None:
        """Painting at showdown with revealed cards doesn't crash."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_hand_with_hole_cards()
        widget.set_hand(hand)

        assert widget.replay_state is not None
        while widget.replay_state.next_action():
            pass

        widget.show()
        qtbot.waitExposed(widget)

    def test_card_back_colors_defined(self, qtbot: Any) -> None:
        """Card back colors are properly defined."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        assert widget.CARD_BACK_COLOR.isValid()
        assert widget.CARD_BACK_PATTERN_COLOR.isValid()


class TestCommunityCards:
    """Test community card (board) display."""

    def test_no_board_at_preflop(self, qtbot: Any) -> None:
        """No community cards shown during preflop."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_hand_with_board()
        widget.set_hand(hand)

        assert widget.replay_state is not None
        visible = widget.replay_state.get_visible_board()
        assert len(visible) == 0

    def test_flop_shows_3_cards(self, qtbot: Any) -> None:
        """Flop shows 3 community cards."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_hand_with_board()
        widget.set_hand(hand)

        assert widget.replay_state is not None
        widget.replay_state.goto_street(Street.FLOP)

        visible = widget.replay_state.get_visible_board()
        assert len(visible) == 3
        assert visible[0].rank == "A"
        assert visible[1].rank == "K"
        assert visible[2].rank == "Q"

    def test_turn_shows_4_cards(self, qtbot: Any) -> None:
        """Turn shows 4 community cards."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_hand_with_board()
        widget.set_hand(hand)

        assert widget.replay_state is not None
        widget.replay_state.goto_street(Street.TURN)

        visible = widget.replay_state.get_visible_board()
        assert len(visible) == 4
        assert visible[3].rank == "J"

    def test_river_shows_5_cards(self, qtbot: Any) -> None:
        """River shows all 5 community cards."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_hand_with_board()
        widget.set_hand(hand)

        assert widget.replay_state is not None
        widget.replay_state.goto_street(Street.RIVER)

        visible = widget.replay_state.get_visible_board()
        assert len(visible) == 5
        assert visible[4].rank == "T"

    def test_paint_with_board(self, qtbot: Any) -> None:
        """Painting table with board cards doesn't crash."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_hand_with_board()
        widget.set_hand(hand)

        assert widget.replay_state is not None
        widget.replay_state.goto_street(Street.FLOP)

        widget.show()
        qtbot.waitExposed(widget)

    def test_card_suits_have_correct_colors(self, qtbot: Any) -> None:
        """Red suits (hearts, diamonds) and black suits (clubs, spades) are distinguished."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        assert widget.CARD_RED_COLOR.red() > 150
        assert widget.CARD_BLACK_COLOR.red() == 0

    def test_board_updates_on_replay_navigation(self, qtbot: Any) -> None:
        """Board updates when navigating through replay."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_hand_with_board()
        widget.set_hand(hand)

        assert widget.replay_state is not None

        assert len(widget.replay_state.get_visible_board()) == 0

        widget.replay_state.goto_street(Street.FLOP)
        widget.update()
        assert len(widget.replay_state.get_visible_board()) == 3

        widget.replay_state.goto_street(Street.RIVER)
        widget.update()
        assert len(widget.replay_state.get_visible_board()) == 5


class TestPlayerZone:
    """Test player zone determination based on angle."""

    def test_bottom_zone_at_90_degrees(self, qtbot: Any) -> None:
        """Angle near π/2 (90°) returns BOTTOM zone."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        assert widget._get_player_zone(math.pi / 2) == PlayerZone.BOTTOM

    def test_left_zone_at_180_degrees(self, qtbot: Any) -> None:
        """Angle near π (180°) returns LEFT zone."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        assert widget._get_player_zone(math.pi) == PlayerZone.LEFT

    def test_top_zone_at_270_degrees(self, qtbot: Any) -> None:
        """Angle near 3π/2 (270°) returns TOP zone."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        assert widget._get_player_zone(3 * math.pi / 2) == PlayerZone.TOP

    def test_right_zone_at_0_degrees(self, qtbot: Any) -> None:
        """Angle near 0 returns RIGHT zone."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        assert widget._get_player_zone(0) == PlayerZone.RIGHT

    def test_right_zone_at_360_degrees(self, qtbot: Any) -> None:
        """Angle near 2π (360°) returns RIGHT zone."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        assert widget._get_player_zone(2 * math.pi) == PlayerZone.RIGHT

    def test_boundary_bottom_left(self, qtbot: Any) -> None:
        """Boundary at 3π/4 (135°) falls in LEFT zone."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        assert widget._get_player_zone(3 * math.pi / 4) == PlayerZone.LEFT

    def test_boundary_left_top(self, qtbot: Any) -> None:
        """Boundary at 5π/4 (225°) falls in TOP zone."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        assert widget._get_player_zone(5 * math.pi / 4) == PlayerZone.TOP

    def test_boundary_top_right(self, qtbot: Any) -> None:
        """Boundary at 7π/4 (315°) falls in RIGHT zone."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        assert widget._get_player_zone(7 * math.pi / 4) == PlayerZone.RIGHT

    def test_boundary_right_bottom(self, qtbot: Any) -> None:
        """Boundary at π/4 (45°) falls in BOTTOM zone."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        assert widget._get_player_zone(math.pi / 4) == PlayerZone.BOTTOM

    def test_negative_angle_normalized(self, qtbot: Any) -> None:
        """Negative angles are normalized correctly."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        assert widget._get_player_zone(-math.pi / 2) == PlayerZone.TOP

    def test_large_angle_normalized(self, qtbot: Any) -> None:
        """Angles > 2π are normalized correctly."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        assert widget._get_player_zone(5 * math.pi / 2) == PlayerZone.BOTTOM
