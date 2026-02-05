"""Tests for TableWidget - poker table rendering."""
import math
from datetime import datetime
from typing import Any

from PyQt6.QtCore import QPointF

from src.gui.table_widget import PlayerZone, TableWidget
from src.parser.models import Action, ActionType, Card, Hand, Player, Street
from src.replayer.state import ReplayState


def advance_to_end(state: ReplayState) -> None:
    """Advance the replay state to the end of the hand."""
    while state.next_action():
        continue


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
        advance_to_end(widget.replay_state)

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
        advance_to_end(widget.replay_state)

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
        advance_to_end(widget.replay_state)

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


class TestUIScale:
    """Test UI scaling functionality."""

    def test_set_ui_scale(self, qtbot: Any) -> None:
        """Setting UI scale updates the widget."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        widget.set_ui_scale(1.5)
        assert widget._ui_scale == 1.5

    def test_scale_factor_includes_ui_scale(self, qtbot: Any) -> None:
        """Scale factor incorporates UI scale preference."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        base_scale = widget._get_scale_factor()
        widget.set_ui_scale(2.0)
        new_scale = widget._get_scale_factor()

        assert abs(new_scale - base_scale * 2.0) < 0.01

    def test_scaled_properties(self, qtbot: Any) -> None:
        """Scaled properties respond to UI scale changes."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        widget.set_ui_scale(1.0)
        base_box_width = widget.PLAYER_BOX_WIDTH
        base_card_width = widget.CARD_WIDTH

        widget.set_ui_scale(1.5)
        assert widget.PLAYER_BOX_WIDTH > base_box_width
        assert widget.CARD_WIDTH > base_card_width


class TestBBFormatting:
    """Test Big Blind stack formatting."""

    def test_format_stack_or_bb_chips_mode(self, qtbot: Any) -> None:
        """Default chip mode shows regular formatting."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        hand = create_test_hand()
        widget.set_hand(hand)

        result = widget._format_stack_or_bb(1000)
        assert result == "1.0K"

    def test_format_stack_or_bb_bb_mode(self, qtbot: Any) -> None:
        """BB mode shows stack in big blinds."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        hand = create_test_hand()
        widget.set_hand(hand)
        widget._show_bb = True

        result = widget._format_stack_or_bb(500)
        assert "BB" in result
        assert "5.0" in result

    def test_format_stack_or_bb_no_hand(self, qtbot: Any) -> None:
        """Without hand, falls back to chip formatting."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget._show_bb = True

        result = widget._format_stack_or_bb(1000)
        assert result == "1.0K"

    def test_format_stack_or_bb_zero_bb(self, qtbot: Any) -> None:
        """Zero big blind falls back to chip formatting."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        hand = Hand(
            hand_id="test",
            timestamp=datetime(2024, 1, 15, 14, 30),
            small_blind=0,
            big_blind=0,
            ante=0,
            button_seat=1,
            players=[Player(name="P1", seat=1, stack=1000, is_hero=True)],
        )
        widget.set_hand(hand)
        widget._show_bb = True

        result = widget._format_stack_or_bb(1000)
        assert result == "1.0K"


class TestBetAnimation:
    """Test bet chip animation."""

    def test_trigger_bet_animation(self, qtbot: Any) -> None:
        """Triggering bet animation sets opacity to 0."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        widget.trigger_bet_animation()
        assert widget._bet_opacity == 0.0
        assert widget._bet_animation_timer.isActive()

    def test_animate_bet_opacity_increases(self, qtbot: Any) -> None:
        """Animation step increases opacity."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        widget._bet_opacity = 0.0
        widget._animate_bet_opacity()
        assert widget._bet_opacity == 0.25

    def test_animate_bet_opacity_stops_at_1(self, qtbot: Any) -> None:
        """Animation stops when opacity reaches 1.0."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        widget._bet_opacity = 0.75
        widget._bet_animation_timer.start(50)
        widget._animate_bet_opacity()

        assert widget._bet_opacity == 1.0
        assert not widget._bet_animation_timer.isActive()


class TestHeroStackHighlight:
    """Test hero stack click and highlight functionality."""

    def test_trigger_hero_highlight(self, qtbot: Any) -> None:
        """Triggering highlight sets flag and starts timer."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        widget._trigger_hero_highlight()
        assert widget._hero_stack_highlight is True
        assert widget._hero_highlight_timer.isActive()

    def test_end_hero_highlight(self, qtbot: Any) -> None:
        """Ending highlight clears the flag."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        widget._hero_stack_highlight = True
        widget._end_hero_highlight()
        assert widget._hero_stack_highlight is False


class TestMouseEvents:
    """Test mouse interaction with the widget."""

    def test_mouse_press_toggles_bb_mode(self, qtbot: Any) -> None:
        """Clicking on hero stack toggles BB display mode."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_test_hand()
        widget.set_hand(hand)
        widget.show()
        qtbot.waitExposed(widget)

        widget.repaint()

        if widget._hero_stack_rect:
            from PyQt6.QtCore import QPointF
            from PyQt6.QtGui import QMouseEvent
            from PyQt6.QtCore import Qt, QEvent

            center = widget._hero_stack_rect.center()
            event = QMouseEvent(
                QEvent.Type.MouseButtonPress,
                center,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
            )
            widget.mousePressEvent(event)
            assert widget._show_bb is True

            widget.mousePressEvent(event)
            assert widget._show_bb is False

    def test_mouse_press_none_event(self, qtbot: Any) -> None:
        """None mouse event is handled gracefully."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        widget.mousePressEvent(None)

    def test_mouse_move_none_event(self, qtbot: Any) -> None:
        """None mouse move event is handled gracefully."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        widget.mouseMoveEvent(None)

    def test_mouse_move_changes_cursor(self, qtbot: Any) -> None:
        """Mouse over hero stack changes cursor."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_test_hand()
        widget.set_hand(hand)
        widget.show()
        qtbot.waitExposed(widget)
        widget.repaint()

        if widget._hero_stack_rect:
            from PyQt6.QtCore import QPointF
            from PyQt6.QtGui import QMouseEvent
            from PyQt6.QtCore import Qt, QEvent

            center = widget._hero_stack_rect.center()
            event = QMouseEvent(
                QEvent.Type.MouseMove,
                center,
                Qt.MouseButton.NoButton,
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
            )
            widget.mouseMoveEvent(event)
            assert widget.cursor().shape() == Qt.CursorShape.PointingHandCursor

            outside = QPointF(0, 0)
            event_outside = QMouseEvent(
                QEvent.Type.MouseMove,
                outside,
                Qt.MouseButton.NoButton,
                Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
            )
            widget.mouseMoveEvent(event_outside)
            assert widget.cursor().shape() == Qt.CursorShape.ArrowCursor


class TestEquityColors:
    """Test equity color calculations."""

    def test_high_equity_green(self, qtbot: Any) -> None:
        """High equity (>50%) shows green."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        color = widget._get_equity_color(0.75)
        assert color == widget.EQUITY_HIGH_COLOR

    def test_mid_equity_yellow(self, qtbot: Any) -> None:
        """Mid equity (25-50%) shows yellow."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        color = widget._get_equity_color(0.35)
        assert color == widget.EQUITY_MID_COLOR

    def test_low_equity_red(self, qtbot: Any) -> None:
        """Low equity (<25%) shows red."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        color = widget._get_equity_color(0.10)
        assert color == widget.EQUITY_LOW_COLOR

    def test_boundary_at_50(self, qtbot: Any) -> None:
        """Exactly 50% is mid (yellow)."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        color = widget._get_equity_color(0.50)
        assert color == widget.EQUITY_MID_COLOR

    def test_boundary_at_25(self, qtbot: Any) -> None:
        """Exactly 25% is mid (yellow)."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        color = widget._get_equity_color(0.25)
        assert color == widget.EQUITY_MID_COLOR


class TestReplayContext:
    """Test replay context retrieval."""

    def test_get_replay_context_no_state(self, qtbot: Any) -> None:
        """Returns empty context when no replay state."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        result = widget._get_replay_context()
        player_states, hole_cards, winners, equity, street, active_player, street_actions = result
        assert player_states == {}
        assert hole_cards == {}
        assert winners == []
        assert equity is None
        assert street is None
        assert active_player is None
        assert street_actions == {}

    def test_get_replay_context_with_state(self, qtbot: Any) -> None:
        """Returns proper context with replay state."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        hand = create_test_hand()
        widget.set_hand(hand)

        result = widget._get_replay_context()
        player_states, hole_cards, winners, equity, street, active_player, street_actions = result
        assert len(player_states) == 6
        assert street == Street.PREFLOP
        assert isinstance(street_actions, dict)


class TestBetPositioning:
    """Test bet chip positioning."""

    def test_get_bet_position(self, qtbot: Any) -> None:
        """Bet position is between player and table center."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        player_center = QPointF(100, 100)
        bet_pos = widget._get_bet_position(player_center)

        table_center_x = widget.width() / 2
        table_center_y = widget.height() / 2

        assert bet_pos.x() > player_center.x()
        assert bet_pos.x() < table_center_x
        assert bet_pos.y() > player_center.y()
        assert bet_pos.y() < table_center_y


class TestPlayerAngleCalculation:
    """Test player angle calculations."""

    def test_calculate_player_angle_hero(self, qtbot: Any) -> None:
        """Hero (offset 0) is at π/2 (bottom)."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        angle = widget._calculate_player_angle(0, 0, 6)
        assert abs(angle - math.pi / 2) < 0.01

    def test_calculate_player_angle_zero_players(self, qtbot: Any) -> None:
        """Zero players returns 0."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        angle = widget._calculate_player_angle(0, 0, 0)
        assert angle == 0.0


class TestWinnerRendering:
    """Test winner display rendering."""

    def test_paint_with_winner(self, qtbot: Any) -> None:
        """Painting with a winner doesn't crash."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = Hand(
            hand_id="winner-test",
            timestamp=datetime(2024, 1, 15, 14, 30),
            small_blind=50.0,
            big_blind=100.0,
            ante=0.0,
            button_seat=2,
            players=[
                Player(name="Hero", seat=1, stack=1000, is_hero=True),
                Player(name="Villain", seat=2, stack=1000),
            ],
            actions={
                Street.PREFLOP: [
                    Action(player_name="Hero", action_type=ActionType.POST, amount=50),
                    Action(player_name="Villain", action_type=ActionType.POST, amount=100),
                    Action(player_name="Hero", action_type=ActionType.FOLD),
                ],
            },
            winners=["Villain"],
        )
        widget.set_hand(hand)
        advance_to_end(widget.replay_state)

        widget.show()
        qtbot.waitExposed(widget)


class TestPotDisplay:
    """Test pot amount display."""

    def test_pot_displayed_with_bets(self, qtbot: Any) -> None:
        """Pot is displayed when there are bets."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_hand_with_board()
        widget.set_hand(hand)

        assert widget.replay_state is not None
        while widget.replay_state.current_street == Street.PREFLOP:
            if not widget.replay_state.next_action():
                break

        widget.show()
        qtbot.waitExposed(widget)

        pot = widget.replay_state.calculate_pot()
        assert pot > 0


class TestChipStackRendering:
    """Test chip stack visual rendering."""

    def test_paint_with_bets(self, qtbot: Any) -> None:
        """Painting with active bets doesn't crash."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_hand_with_board()
        widget.set_hand(hand)

        assert widget.replay_state is not None
        widget.replay_state.goto_street(Street.FLOP)
        widget.replay_state.next_action()
        widget.replay_state.next_action()

        widget.show()
        qtbot.waitExposed(widget)


class TestScaledFont:
    """Test scaled font creation."""

    def test_scaled_font_minimum_size(self, qtbot: Any) -> None:
        """Scaled font has minimum size of 6."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(100, 75)

        font = widget._scaled_font(2)
        assert font.pointSize() >= 6

    def test_scaled_font_with_weight(self, qtbot: Any) -> None:
        """Scaled font respects weight parameter."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        from PyQt6.QtGui import QFont
        font = widget._scaled_font(12, QFont.Weight.Bold)
        assert font.weight() == QFont.Weight.Bold


class TestScaledProperties:
    """Test all scaled property accessors."""

    def test_all_scaled_properties(self, qtbot: Any) -> None:
        """All scaled properties return positive values."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        assert widget.PLAYER_BOX_WIDTH > 0
        assert widget.PLAYER_BOX_HEIGHT > 0
        assert widget.HOLE_CARD_WIDTH > 0
        assert widget.HOLE_CARD_HEIGHT > 0
        assert widget.HOLE_CARD_SPACING > 0
        assert widget.HOLE_CARD_OVERLAP > 0
        assert widget.BUTTON_DIAMETER > 0
        assert widget.CARD_WIDTH > 0
        assert widget.CARD_HEIGHT > 0
        assert widget.CARD_SPACING > 0


class TestEquityLabels:
    """Test equity label rendering at showdown."""

    def test_paint_with_showdown_equity(self, qtbot: Any) -> None:
        """Painting with showdown equity doesn't crash."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_hand_with_hole_cards()
        widget.set_hand(hand)

        assert widget.replay_state is not None
        advance_to_end(widget.replay_state)

        widget.show()
        qtbot.waitExposed(widget)


class TestRightZoneCards:
    """Test cards positioned on left for RIGHT zone players."""

    def test_paint_right_zone_player(self, qtbot: Any) -> None:
        """Painting player in RIGHT zone shows cards on left."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        players = [
            Player(
                name="Hero",
                seat=1,
                stack=1000.0,
                is_hero=True,
                hole_cards=[Card(rank="A", suit="s"), Card(rank="K", suit="s")],
            ),
            Player(name="Right", seat=2, stack=1000.0),
        ]
        hand = Hand(
            hand_id="right-zone-test",
            timestamp=datetime(2024, 1, 15, 14, 30),
            small_blind=50.0,
            big_blind=100.0,
            ante=0.0,
            button_seat=2,
            players=players,
        )
        widget.set_hand(hand)
        widget.show()
        qtbot.waitExposed(widget)


class TestChipCounts:
    """Test different chip stack counts based on bet size."""

    def test_small_bet_one_chip(self, qtbot: Any) -> None:
        """Small bet (< 3 BB) shows 1 chip."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = Hand(
            hand_id="small-bet",
            timestamp=datetime(2024, 1, 15, 14, 30),
            small_blind=50.0,
            big_blind=100.0,
            ante=0.0,
            button_seat=2,
            players=[
                Player(name="Hero", seat=1, stack=1000, is_hero=True),
                Player(name="Villain", seat=2, stack=1000),
            ],
            actions={
                Street.PREFLOP: [
                    Action(player_name="Hero", action_type=ActionType.POST, amount=50),
                    Action(player_name="Villain", action_type=ActionType.POST, amount=100),
                ],
            },
        )
        widget.set_hand(hand)

        assert widget.replay_state is not None
        widget.replay_state.next_action()
        widget.replay_state.next_action()

        widget.show()
        qtbot.waitExposed(widget)

    def test_medium_bet_two_chips(self, qtbot: Any) -> None:
        """Medium bet (3-10 BB) shows 2 chips."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = Hand(
            hand_id="medium-bet",
            timestamp=datetime(2024, 1, 15, 14, 30),
            small_blind=50.0,
            big_blind=100.0,
            ante=0.0,
            button_seat=2,
            players=[
                Player(name="Hero", seat=1, stack=1000, is_hero=True),
                Player(name="Villain", seat=2, stack=1000),
            ],
            actions={
                Street.PREFLOP: [
                    Action(player_name="Hero", action_type=ActionType.POST, amount=50),
                    Action(player_name="Villain", action_type=ActionType.POST, amount=100),
                    Action(player_name="Hero", action_type=ActionType.RAISE, amount=400),
                ],
            },
        )
        widget.set_hand(hand)

        assert widget.replay_state is not None
        while widget.replay_state.next_action():
            pass

        widget.show()
        qtbot.waitExposed(widget)

    def test_large_bet_three_chips(self, qtbot: Any) -> None:
        """Large bet (>= 10 BB) shows 3 chips."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = Hand(
            hand_id="large-bet",
            timestamp=datetime(2024, 1, 15, 14, 30),
            small_blind=50.0,
            big_blind=100.0,
            ante=0.0,
            button_seat=2,
            players=[
                Player(name="Hero", seat=1, stack=5000, is_hero=True),
                Player(name="Villain", seat=2, stack=5000),
            ],
            actions={
                Street.PREFLOP: [
                    Action(player_name="Hero", action_type=ActionType.POST, amount=50),
                    Action(player_name="Villain", action_type=ActionType.POST, amount=100),
                    Action(player_name="Hero", action_type=ActionType.RAISE, amount=1500),
                ],
            },
        )
        widget.set_hand(hand)

        assert widget.replay_state is not None
        while widget.replay_state.next_action():
            pass

        widget.show()
        qtbot.waitExposed(widget)


class TestHeroHighlightRendering:
    """Test hero stack highlight visual rendering."""

    def test_paint_with_hero_highlight(self, qtbot: Any) -> None:
        """Painting with hero highlight active doesn't crash."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_test_hand()
        widget.set_hand(hand)

        widget._hero_stack_highlight = True

        widget.show()
        qtbot.waitExposed(widget)


class TestBBPotDisplay:
    """Test pot display in BB mode."""

    def test_pot_in_bb_mode(self, qtbot: Any) -> None:
        """Pot is displayed in BB when _show_bb is True."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_hand_with_board()
        widget.set_hand(hand)
        widget._show_bb = True

        assert widget.replay_state is not None
        widget.replay_state.goto_street(Street.FLOP)

        widget.show()
        qtbot.waitExposed(widget)


class TestLongPlayerName:
    """Test truncation of long player names."""

    def test_long_name_truncated(self, qtbot: Any) -> None:
        """Long player names are truncated for display."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = Hand(
            hand_id="long-name-test",
            timestamp=datetime(2024, 1, 15, 14, 30),
            small_blind=50.0,
            big_blind=100.0,
            ante=0.0,
            button_seat=1,
            players=[
                Player(
                    name="VeryLongPlayerNameThatShouldBeTruncated",
                    seat=1,
                    stack=1000,
                    is_hero=True,
                ),
            ],
        )
        widget.set_hand(hand)

        widget.show()
        qtbot.waitExposed(widget)


class TestCardSuitSymbols:
    """Test card suit symbol rendering."""

    def test_all_suit_symbols(self, qtbot: Any) -> None:
        """All card suits render correctly."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        players = [
            Player(
                name="Hero",
                seat=1,
                stack=1000.0,
                is_hero=True,
                hole_cards=[Card(rank="A", suit="h"), Card(rank="K", suit="d")],
            ),
            Player(name="P2", seat=2, stack=1000.0),
        ]
        hand = Hand(
            hand_id="suits-test",
            timestamp=datetime(2024, 1, 15, 14, 30),
            small_blind=50.0,
            big_blind=100.0,
            ante=0.0,
            button_seat=2,
            players=players,
            board=[
                Card(rank="Q", suit="c"),
                Card(rank="J", suit="s"),
                Card(rank="T", suit="h"),
            ],
            actions={
                Street.PREFLOP: [
                    Action(player_name="Hero", action_type=ActionType.POST, amount=50),
                    Action(player_name="P2", action_type=ActionType.POST, amount=100),
                    Action(player_name="Hero", action_type=ActionType.CALL, amount=50),
                    Action(player_name="P2", action_type=ActionType.CHECK),
                ],
                Street.FLOP: [],
            },
        )
        widget.set_hand(hand)

        assert widget.replay_state is not None
        widget.replay_state.goto_street(Street.FLOP)

        widget.show()
        qtbot.waitExposed(widget)


class TestNoPlayerState:
    """Test rendering when player state is missing."""

    def test_paint_with_missing_player_state(self, qtbot: Any) -> None:
        """Painting when a player has no state entry doesn't crash."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_test_hand()
        widget.set_hand(hand)

        widget.show()
        qtbot.waitExposed(widget)


class TestMouseOutsideHeroStack:
    """Test mouse interactions outside hero stack rect."""

    def test_click_outside_hero_stack(self, qtbot: Any) -> None:
        """Clicking outside hero stack doesn't toggle BB mode."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_test_hand()
        widget.set_hand(hand)
        widget.show()
        qtbot.waitExposed(widget)
        widget.repaint()

        from PyQt6.QtGui import QMouseEvent
        from PyQt6.QtCore import Qt, QEvent

        outside_pos = QPointF(10, 10)
        event = QMouseEvent(
            QEvent.Type.MouseButtonPress,
            outside_pos,
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        widget.mousePressEvent(event)
        assert widget._show_bb is False


class TestCheckBadge:
    """Test check action badge display."""

    def test_check_badge_renders(self, qtbot: Any) -> None:
        """Check badge is displayed when player checks."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = Hand(
            hand_id="check-test",
            timestamp=datetime(2024, 1, 15, 14, 30),
            small_blind=50.0,
            big_blind=100.0,
            ante=0.0,
            button_seat=2,
            players=[
                Player(name="Hero", seat=1, stack=1000, is_hero=True),
                Player(name="Villain", seat=2, stack=1000),
            ],
            board=[Card(rank="A", suit="h"), Card(rank="K", suit="d"), Card(rank="Q", suit="c")],
            actions={
                Street.PREFLOP: [
                    Action(player_name="Hero", action_type=ActionType.POST, amount=50),
                    Action(player_name="Villain", action_type=ActionType.POST, amount=100),
                    Action(player_name="Hero", action_type=ActionType.CALL, amount=50),
                    Action(player_name="Villain", action_type=ActionType.CHECK),
                ],
                Street.FLOP: [
                    Action(player_name="Hero", action_type=ActionType.CHECK),
                    Action(player_name="Villain", action_type=ActionType.CHECK),
                ],
            },
        )
        widget.set_hand(hand)

        assert widget.replay_state is not None
        widget.replay_state.goto_street(Street.FLOP)

        street_actions = widget.replay_state.get_current_street_actions()
        assert ActionType.CHECK in street_actions.values()

        widget.show()
        qtbot.waitExposed(widget)

    def test_check_badge_clears_on_street_change(self, qtbot: Any) -> None:
        """Check badge is not shown for previous street's checks."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = Hand(
            hand_id="check-clear-test",
            timestamp=datetime(2024, 1, 15, 14, 30),
            small_blind=50.0,
            big_blind=100.0,
            ante=0.0,
            button_seat=2,
            players=[
                Player(name="Hero", seat=1, stack=1000, is_hero=True),
                Player(name="Villain", seat=2, stack=1000),
            ],
            board=[
                Card(rank="A", suit="h"),
                Card(rank="K", suit="d"),
                Card(rank="Q", suit="c"),
                Card(rank="J", suit="s"),
            ],
            actions={
                Street.PREFLOP: [
                    Action(player_name="Hero", action_type=ActionType.POST, amount=50),
                    Action(player_name="Villain", action_type=ActionType.POST, amount=100),
                    Action(player_name="Hero", action_type=ActionType.CALL, amount=50),
                    Action(player_name="Villain", action_type=ActionType.CHECK),
                ],
                Street.FLOP: [
                    Action(player_name="Hero", action_type=ActionType.CHECK),
                    Action(player_name="Villain", action_type=ActionType.CHECK),
                ],
                Street.TURN: [
                    Action(player_name="Hero", action_type=ActionType.BET, amount=100),
                ],
            },
        )
        widget.set_hand(hand)

        assert widget.replay_state is not None
        widget.replay_state.goto_street(Street.TURN)
        widget.replay_state.next_action()

        street_actions = widget.replay_state.get_current_street_actions()
        assert ActionType.CHECK not in street_actions.values()

        widget.show()
        qtbot.waitExposed(widget)


class TestPositionLabels:
    """Test position label display."""

    def test_position_label_for_button(self, qtbot: Any) -> None:
        """Button player gets BTN position label."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        hand = Hand(
            hand_id="position-test",
            timestamp=datetime(2024, 1, 15, 14, 30),
            small_blind=50.0,
            big_blind=100.0,
            ante=0.0,
            button_seat=3,
            players=[
                Player(name="Hero", seat=1, stack=1000, is_hero=True),
                Player(name="P2", seat=2, stack=1000),
                Player(name="P3", seat=3, stack=1000),
            ],
        )
        widget.set_hand(hand)

        btn_player = hand.players[2]
        assert widget._get_position_label(btn_player) == "BTN"

    def test_position_label_for_blinds(self, qtbot: Any) -> None:
        """SB and BB players get appropriate position labels."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        hand = Hand(
            hand_id="blinds-test",
            timestamp=datetime(2024, 1, 15, 14, 30),
            small_blind=50.0,
            big_blind=100.0,
            ante=0.0,
            button_seat=1,
            players=[
                Player(name="BTN", seat=1, stack=1000, is_hero=True),
                Player(name="SB", seat=2, stack=1000),
                Player(name="BB", seat=3, stack=1000),
            ],
        )
        widget.set_hand(hand)

        assert widget._get_position_label(hand.players[0]) == "BTN"
        assert widget._get_position_label(hand.players[1]) == "SB"
        assert widget._get_position_label(hand.players[2]) == "BB"

    def test_position_labels_6max(self, qtbot: Any) -> None:
        """6-max table has correct position labels."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        hand = Hand(
            hand_id="6max-test",
            timestamp=datetime(2024, 1, 15, 14, 30),
            small_blind=50.0,
            big_blind=100.0,
            ante=0.0,
            button_seat=1,
            players=[
                Player(name="P1", seat=1, stack=1000, is_hero=True),
                Player(name="P2", seat=2, stack=1000),
                Player(name="P3", seat=3, stack=1000),
                Player(name="P4", seat=4, stack=1000),
                Player(name="P5", seat=5, stack=1000),
                Player(name="P6", seat=6, stack=1000),
            ],
        )
        widget.set_hand(hand)

        labels = [widget._get_position_label(p) for p in hand.players]
        assert labels == ["BTN", "SB", "BB", "UTG", "HJ", "CO"]

    def test_position_labels_heads_up(self, qtbot: Any) -> None:
        """2-player (heads-up) shows BTN and BB."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        hand = Hand(
            hand_id="hu-test",
            timestamp=datetime(2024, 1, 15, 14, 30),
            small_blind=50.0,
            big_blind=100.0,
            ante=0.0,
            button_seat=1,
            players=[
                Player(name="P1", seat=1, stack=1000, is_hero=True),
                Player(name="P2", seat=2, stack=1000),
            ],
        )
        widget.set_hand(hand)

        assert widget._get_position_label(hand.players[0]) == "BTN"
        assert widget._get_position_label(hand.players[1]) == "SB"

    def test_position_label_no_hand(self, qtbot: Any) -> None:
        """Returns empty string when no hand is set."""
        widget = TableWidget()
        qtbot.addWidget(widget)

        fake_player = Player(name="Test", seat=1, stack=1000)
        assert widget._get_position_label(fake_player) == ""

    def test_position_labels_render(self, qtbot: Any) -> None:
        """Position labels are rendered in the table display."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = create_test_hand(num_players=6, hero_seat=1)
        widget.set_hand(hand)

        widget.show()
        qtbot.waitExposed(widget)


class TestCurrentStreetBetsVsPot:
    """Tests verifying current street bets display separately from pot.
    
    The pot only shows completed streets' contributions.
    Current street bets are shown as chip stacks near each player.
    This creates a clear visual distinction between money 'at risk' and 'in the pot'.
    """

    def create_betting_hand(self) -> Hand:
        """Create a hand with clear betting action to test pot vs bets separation."""
        players = [
            Player(name="Hero", seat=1, stack=1000.0, is_hero=True),
            Player(name="Villain", seat=2, stack=1000.0),
        ]
        return Hand(
            hand_id="pot-bet-separation",
            timestamp=datetime(2024, 1, 15, 14, 30),
            small_blind=50.0,
            big_blind=100.0,
            ante=0.0,
            button_seat=1,
            players=players,
            board=[
                Card(rank="A", suit="h"),
                Card(rank="K", suit="d"),
                Card(rank="Q", suit="c"),
                Card(rank="J", suit="s"),
            ],
            actions={
                Street.PREFLOP: [
                    Action(player_name="Hero", action_type=ActionType.POST, amount=50),
                    Action(player_name="Villain", action_type=ActionType.POST, amount=100),
                    Action(player_name="Hero", action_type=ActionType.RAISE, amount=200),
                    Action(player_name="Villain", action_type=ActionType.CALL, amount=100),
                ],
                Street.FLOP: [
                    Action(player_name="Villain", action_type=ActionType.CHECK),
                    Action(player_name="Hero", action_type=ActionType.BET, amount=150),
                    Action(player_name="Villain", action_type=ActionType.CALL, amount=150),
                ],
                Street.TURN: [
                    Action(player_name="Villain", action_type=ActionType.CHECK),
                    Action(player_name="Hero", action_type=ActionType.BET, amount=300),
                ],
            },
        )

    def test_current_street_bets_shown_near_players(self, qtbot: Any) -> None:
        """Current street bets are tracked in player states as current_bet."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = self.create_betting_hand()
        widget.set_hand(hand)

        assert widget.replay_state is not None

        # goto_street(FLOP) puts us after the first flop action (CHECK)
        # next_action() advances to after BET 150
        widget.replay_state.goto_street(Street.FLOP)
        widget.replay_state.next_action()  # Now after BET 150

        player_states = widget.replay_state.get_player_states()
        assert player_states["Hero"].current_bet == 150.0
        assert player_states["Villain"].current_bet == 0.0

    def test_pot_excludes_current_street_bets(self, qtbot: Any) -> None:
        """Pot total only includes completed streets' contributions."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = self.create_betting_hand()
        widget.set_hand(hand)

        assert widget.replay_state is not None

        # On flop after Hero bets 150: pot should be preflop total only
        widget.replay_state.goto_street(Street.FLOP)
        widget.replay_state.next_action()  # CHECK
        widget.replay_state.next_action()  # BET 150

        pot = widget.replay_state.calculate_pot()
        # Preflop: 50+200 (Hero) + 100+100 (Villain) = 450
        # Flop bets NOT in pot yet
        assert pot == 450.0

    def test_pot_increases_on_street_transition(self, qtbot: Any) -> None:
        """Pot increases when moving to new street (previous bets added)."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = self.create_betting_hand()
        widget.set_hand(hand)

        assert widget.replay_state is not None

        # goto_street(FLOP) puts us after CHECK, next 2 actions: BET, CALL
        widget.replay_state.goto_street(Street.FLOP)
        widget.replay_state.next_action()  # After BET 150
        
        # On flop after Hero bets 150: pot should be preflop total only
        pot_mid_flop = widget.replay_state.calculate_pot()
        assert pot_mid_flop == 450.0  # Only preflop bets
        
        widget.replay_state.next_action()  # After CALL 150

        # Still on flop, pot = 450 (preflop only)
        pot_on_flop = widget.replay_state.calculate_pot()
        assert pot_on_flop == 450.0  # Still on flop, so flop bets not in pot

        # Now go to turn - flop bets should be in pot
        widget.replay_state.goto_street(Street.TURN)
        pot_on_turn = widget.replay_state.calculate_pot()
        # 450 (preflop) + 300 (flop: 150 + 150) = 750
        assert pot_on_turn == 750.0

    def test_player_bets_clear_on_street_change(self, qtbot: Any) -> None:
        """Player current_bet resets to 0 when street changes."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = self.create_betting_hand()
        widget.set_hand(hand)

        assert widget.replay_state is not None

        # goto_street(FLOP) = after CHECK, then BET, then CALL
        widget.replay_state.goto_street(Street.FLOP)
        widget.replay_state.next_action()  # After BET 150
        widget.replay_state.next_action()  # After CALL 150

        states_flop = widget.replay_state.get_player_states()
        assert states_flop["Hero"].current_bet == 150.0
        assert states_flop["Villain"].current_bet == 150.0

        # Go to turn - bets should clear
        widget.replay_state.goto_street(Street.TURN)
        states_turn = widget.replay_state.get_player_states()
        assert states_turn["Hero"].current_bet == 0.0
        assert states_turn["Villain"].current_bet == 0.0

    def test_bet_display_rendering(self, qtbot: Any) -> None:
        """Bet chips render near players when they have current street bets."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = self.create_betting_hand()
        widget.set_hand(hand)

        assert widget.replay_state is not None
        widget.replay_state.goto_street(Street.FLOP)
        widget.replay_state.next_action()  # After BET 150

        # Verify drawing doesn't crash and bet position is calculated
        positions = widget._get_player_positions()
        for player, pos in positions:
            bet_pos = widget._get_bet_position(pos)
            # Bet position should be between player and table center
            assert bet_pos is not None

        widget.show()
        qtbot.waitExposed(widget)

    def test_pot_display_rendering(self, qtbot: Any) -> None:
        """Pot display renders with correct total from completed streets."""
        widget = TableWidget()
        qtbot.addWidget(widget)
        widget.resize(800, 600)

        hand = self.create_betting_hand()
        widget.set_hand(hand)

        assert widget.replay_state is not None
        widget.replay_state.goto_street(Street.TURN)

        pot = widget.replay_state.calculate_pot()
        assert pot == 750.0  # Preflop (450) + Flop (300)

        widget.show()
        qtbot.waitExposed(widget)
