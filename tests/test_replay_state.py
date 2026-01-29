from datetime import datetime

import pytest

from src.parser.models import Action, ActionType, Card, Hand, Player, Street
from src.replayer.state import ReplayState, ShowdownEquity


@pytest.fixture
def sample_hand() -> Hand:
    players = [
        Player(name="Hero", seat=1, stack=1000.0, is_hero=True, hole_cards=[
            Card(rank="A", suit="s"), Card(rank="K", suit="s")
        ]),
        Player(name="Villain1", seat=2, stack=1500.0),
        Player(name="Villain2", seat=3, stack=800.0),
    ]

    actions: dict[Street, list[Action]] = {
        Street.PREFLOP: [
            Action(player_name="Villain1", action_type=ActionType.POST, amount=50.0),
            Action(player_name="Villain2", action_type=ActionType.POST, amount=100.0),
            Action(player_name="Hero", action_type=ActionType.RAISE, amount=300.0),
            Action(player_name="Villain1", action_type=ActionType.FOLD),
            Action(player_name="Villain2", action_type=ActionType.CALL, amount=200.0),
        ],
        Street.FLOP: [
            Action(player_name="Villain2", action_type=ActionType.CHECK),
            Action(player_name="Hero", action_type=ActionType.BET, amount=400.0),
            Action(player_name="Villain2", action_type=ActionType.CALL, amount=400.0),
        ],
        Street.TURN: [
            Action(player_name="Villain2", action_type=ActionType.CHECK),
            Action(player_name="Hero", action_type=ActionType.BET, amount=100.0, is_all_in=True),
            Action(player_name="Villain2", action_type=ActionType.FOLD),
        ],
    }

    board = [
        Card(rank="Q", suit="h"),
        Card(rank="J", suit="d"),
        Card(rank="T", suit="s"),
        Card(rank="2", suit="c"),
    ]

    return Hand(
        hand_id="12345",
        timestamp=datetime.now(),
        small_blind=50.0,
        big_blind=100.0,
        ante=0.0,
        button_seat=1,
        players=players,
        actions=actions,
        board=board,
        showdown_hands={},
    )


@pytest.fixture
def showdown_hand() -> Hand:
    players = [
        Player(name="Hero", seat=1, stack=1000.0, is_hero=True, hole_cards=[
            Card(rank="A", suit="s"), Card(rank="K", suit="s")
        ]),
        Player(name="Villain", seat=2, stack=1000.0),
    ]

    actions: dict[Street, list[Action]] = {
        Street.PREFLOP: [
            Action(player_name="Hero", action_type=ActionType.POST, amount=50.0),
            Action(player_name="Villain", action_type=ActionType.POST, amount=100.0),
            Action(player_name="Hero", action_type=ActionType.CALL, amount=50.0),
            Action(player_name="Villain", action_type=ActionType.CHECK),
        ],
        Street.FLOP: [
            Action(player_name="Hero", action_type=ActionType.CHECK),
            Action(player_name="Villain", action_type=ActionType.CHECK),
        ],
        Street.TURN: [
            Action(player_name="Hero", action_type=ActionType.CHECK),
            Action(player_name="Villain", action_type=ActionType.CHECK),
        ],
        Street.RIVER: [
            Action(player_name="Hero", action_type=ActionType.CHECK),
            Action(player_name="Villain", action_type=ActionType.CHECK),
        ],
        Street.SHOWDOWN: [],
    }

    board = [
        Card(rank="2", suit="h"),
        Card(rank="3", suit="d"),
        Card(rank="4", suit="s"),
        Card(rank="5", suit="c"),
        Card(rank="6", suit="h"),
    ]

    showdown_hands = {
        "Villain": [Card(rank="7", suit="s"), Card(rank="8", suit="s")],
    }

    return Hand(
        hand_id="67890",
        timestamp=datetime.now(),
        small_blind=50.0,
        big_blind=100.0,
        ante=0.0,
        button_seat=1,
        players=players,
        actions=actions,
        board=board,
        showdown_hands=showdown_hands,
    )


class TestReplayStateBasics:
    def test_initial_position_skips_posts(self, sample_hand: Hand) -> None:
        """Position starts at first non-POST action (skipping blinds/antes)."""
        state = ReplayState(hand=sample_hand)
        # sample_hand has 2 POSTs at start, so we skip to position 2
        assert state.current_position == 2

    def test_total_actions_count(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        assert state.total_actions == 11

    def test_current_action_is_first_non_post_at_start(self, sample_hand: Hand) -> None:
        """At initial position, current action is the POST at position-1 (last skipped)."""
        state = ReplayState(hand=sample_hand)
        # Position is 2, so current_action is at index 1 (Villain2 POST)
        action = state.current_action
        assert action is not None
        assert action.action_type == ActionType.POST

    def test_current_street_preflop_at_start(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        assert state.current_street == Street.PREFLOP


class TestNextPrevAction:
    def test_next_action_advances_position(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        # Starts at 2 (after 2 POSTs)
        result = state.next_action()
        assert result is True
        assert state.current_position == 3

    def test_next_action_returns_false_at_end(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        # Starts at 2, need to advance 9 more times to reach end (11 total)
        for _ in range(9):
            state.next_action()
        result = state.next_action()
        assert result is False
        assert state.current_position == 11

    def test_prev_action_decreases_position(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        # Starts at 2, advance twice to 4, then go back
        state.next_action()
        state.next_action()
        result = state.prev_action()
        assert result is True
        assert state.current_position == 3

    def test_prev_action_allowed_back_to_posts(self, sample_hand: Hand) -> None:
        """Can navigate back into POST actions from initial position."""
        state = ReplayState(hand=sample_hand)
        # Starts at 2, can go back to 1
        result = state.prev_action()
        assert result is True
        assert state.current_position == 1

    def test_current_action_after_next(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        # Starts at 2, next() goes to 3, which is Hero RAISE
        state.next_action()
        action = state.current_action
        assert action is not None
        assert action.player_name == "Hero"
        assert action.action_type == ActionType.RAISE


class TestGotoStreet:
    def test_goto_flop(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        result = state.goto_street(Street.FLOP)
        assert result is True
        assert state.current_street == Street.FLOP

    def test_goto_turn(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        result = state.goto_street(Street.TURN)
        assert result is True
        assert state.current_street == Street.TURN

    def test_goto_nonexistent_street_returns_false(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        result = state.goto_street(Street.RIVER)
        assert result is False

    def test_goto_preflop_from_flop(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        state.goto_street(Street.FLOP)
        result = state.goto_street(Street.PREFLOP)
        assert result is True
        assert state.current_street == Street.PREFLOP


class TestPotCalculation:
    def test_pot_includes_blinds_at_start(self, sample_hand: Hand) -> None:
        """Pot includes blind posts even at initial position (after skip)."""
        state = ReplayState(hand=sample_hand)
        # Starts at position 2, so pot includes 2 POSTs (50+100)
        assert state.calculate_pot() == 150.0

    def test_pot_after_raise(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        # Position 2 -> 3 (Hero RAISE 300)
        state.next_action()
        # Pot = 150 (posts) + 300 (raise) = 450
        assert state.calculate_pot() == 450.0

    def test_pot_after_preflop(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        state.goto_street(Street.FLOP)
        assert state.calculate_pot() == 650.0

    def test_pot_after_flop_betting(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        state.goto_street(Street.TURN)
        assert state.calculate_pot() == 1450.0


class TestStackCalculation:
    def test_stacks_reflect_blinds_at_start(self, sample_hand: Hand) -> None:
        """Stacks already reflect blind posts at initial position."""
        state = ReplayState(hand=sample_hand)
        stacks = state.calculate_player_stacks()
        # Position 2 means POSTs already deducted
        assert stacks["Hero"] == 1000.0  # No bet yet
        assert stacks["Villain1"] == 1450.0  # Posted 50
        assert stacks["Villain2"] == 700.0  # Posted 100

    def test_stacks_after_raise(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        # Position 2 -> 3 (Hero RAISE 300)
        state.next_action()
        stacks = state.calculate_player_stacks()
        assert stacks["Hero"] == 700.0
        assert stacks["Villain1"] == 1450.0
        assert stacks["Villain2"] == 700.0

    def test_stacks_after_preflop(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        state.goto_street(Street.FLOP)
        stacks = state.calculate_player_stacks()
        assert stacks["Hero"] == 700.0
        assert stacks["Villain1"] == 1450.0
        assert stacks["Villain2"] == 500.0


class TestPlayerStates:
    def test_folded_player_marked(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        state.goto_street(Street.FLOP)
        player_states = state.get_player_states()
        assert player_states["Villain1"].is_folded is True
        assert player_states["Villain2"].is_folded is False
        assert player_states["Hero"].is_folded is False

    def test_current_bet_tracked(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        for _ in range(3):
            state.next_action()
        player_states = state.get_player_states()
        assert player_states["Hero"].current_bet == 300.0


class TestVisibleCards:
    def test_no_board_at_preflop(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        board = state.get_visible_board()
        assert len(board) == 0

    def test_flop_shows_three_cards(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        state.goto_street(Street.FLOP)
        board = state.get_visible_board()
        assert len(board) == 3

    def test_turn_shows_four_cards(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        state.goto_street(Street.TURN)
        board = state.get_visible_board()
        assert len(board) == 4

    def test_hero_cards_always_visible(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        hole_cards = state.get_visible_hole_cards()
        assert "Hero" in hole_cards
        assert len(hole_cards["Hero"]) == 2

    def test_villain_cards_not_visible_preflop(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        hole_cards = state.get_visible_hole_cards()
        assert "Villain1" not in hole_cards
        assert "Villain2" not in hole_cards


class TestShowdown:
    def test_showdown_reveals_villain_cards(self, showdown_hand: Hand) -> None:
        state = ReplayState(hand=showdown_hand)
        state.goto_position(state.total_actions)
        assert state.current_street == Street.SHOWDOWN
        hole_cards = state.get_visible_hole_cards()
        assert "Villain" in hole_cards
        assert len(hole_cards["Villain"]) == 2

    def test_river_shows_full_board(self, showdown_hand: Hand) -> None:
        state = ReplayState(hand=showdown_hand)
        state.goto_street(Street.RIVER)
        board = state.get_visible_board()
        assert len(board) == 5


class TestUtilityMethods:
    def test_get_actions_up_to_current(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        # Starts at 2, advance 1 more to position 3
        state.next_action()
        actions = state.get_actions_up_to_current()
        # Should include all 3 actions: 2 POSTs + 1 RAISE
        assert len(actions) == 3
        assert actions[0][0] == Street.PREFLOP
        assert actions[0][1].action_type == ActionType.POST
        assert actions[2][1].action_type == ActionType.RAISE

    def test_get_available_streets(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        streets = state.get_available_streets()
        assert Street.PREFLOP in streets
        assert Street.FLOP in streets
        assert Street.TURN in streets
        assert Street.RIVER not in streets

    def test_goto_position(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        result = state.goto_position(5)
        assert result is True
        assert state.current_position == 5

    def test_goto_position_invalid(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        result = state.goto_position(100)
        assert result is False


class TestBetsResetPerStreet:
    """Verify that player bets reset at the start of each new street."""

    def test_bets_zero_at_initial_position(self, sample_hand: Hand) -> None:
        """At initial position (after posts skipped), no betting chips shown."""
        state = ReplayState(hand=sample_hand)
        # Posts don't count as current_bet, so all bets should be 0
        player_states = state.get_player_states()
        bb_found = False
        sb_found = False
        for player_state in player_states.values():
            if player_state.current_bet == sample_hand.small_blind:
                sb_found = True
                continue
            if player_state.current_bet == sample_hand.big_blind:
                bb_found = True
                continue
            assert player_state.current_bet == 0.0

        assert bb_found and sb_found
        
    def test_bets_at_end_of_preflop(self, sample_hand: Hand) -> None:
        """Bets accumulate during preflop (excluding posts)."""
        state = ReplayState(hand=sample_hand)
        # Starts at 2, advance 3 more to reach end of preflop (pos 5)
        # Actions: RAISE(300), FOLD, CALL(200)
        for _ in range(3):
            state.next_action()
        player_states = state.get_player_states()
        assert player_states["Hero"].current_bet == 300.0
        assert player_states["Villain2"].current_bet == 300.0

    def test_bets_zero_at_start_of_flop(self, sample_hand: Hand) -> None:
        """When going to FLOP, bets from PREFLOP should be cleared."""
        state = ReplayState(hand=sample_hand)
        state.goto_street(Street.FLOP)
        player_states = state.get_player_states()
        assert player_states["Villain2"].current_bet == 0.0
        assert player_states["Hero"].current_bet == 0.0

    def test_bets_accumulate_within_street(self, sample_hand: Hand) -> None:
        """Bets should accumulate within the same street."""
        state = ReplayState(hand=sample_hand)
        # Go to end of FLOP: goto_street puts at pos 6 (first flop action done)
        # Then advance 2 more: CHECK + BET + CALL
        state.goto_street(Street.FLOP)
        state.next_action()  # Hero BET 400
        state.next_action()  # Villain2 CALL 400
        player_states = state.get_player_states()
        assert player_states["Hero"].current_bet == 400.0
        assert player_states["Villain2"].current_bet == 400.0

    def test_bets_zero_at_start_of_turn(self, sample_hand: Hand) -> None:
        """When going to TURN, bets from FLOP should be cleared."""
        state = ReplayState(hand=sample_hand)
        state.goto_street(Street.TURN)
        player_states = state.get_player_states()
        # First action on turn is CHECK, so bets should be 0
        assert player_states["Hero"].current_bet == 0.0
        assert player_states["Villain2"].current_bet == 0.0


class TestWinnerDisplay:
    """Tests for winner detection and display at hand end."""

    def test_is_at_end_returns_false_at_start(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        assert not state.is_at_end()

    def test_is_at_end_returns_true_at_end(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        while state.next_action():
            pass
        assert state.is_at_end()

    def test_get_winners_empty_when_not_at_end(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        assert state.get_winners() == []

    def test_get_winners_returns_winners_at_end(self) -> None:
        players = [
            Player(name="Hero", seat=1, stack=1000.0, is_hero=True),
            Player(name="Villain", seat=2, stack=1000.0),
        ]
        actions: dict[Street, list[Action]] = {
            Street.PREFLOP: [
                Action(player_name="Hero", action_type=ActionType.POST, amount=50.0),
                Action(player_name="Villain", action_type=ActionType.POST, amount=100.0),
                Action(player_name="Hero", action_type=ActionType.RAISE, amount=300.0),
                Action(player_name="Villain", action_type=ActionType.FOLD),
            ],
        }
        hand = Hand(
            hand_id="test",
            timestamp=datetime.now(),
            small_blind=50.0,
            big_blind=100.0,
            ante=0.0,
            button_seat=1,
            players=players,
            actions=actions,
            board=[],
            showdown_hands={},
            winners=["Hero"],
        )
        state = ReplayState(hand=hand)
        while state.next_action():
            pass
        assert state.is_at_end()
        assert state.get_winners() == ["Hero"]


class TestShowdownEquity:
    """Tests for showdown equity calculation."""

    @pytest.fixture
    def showdown_hand_with_equity(self) -> Hand:
        """Hand with two players reaching showdown."""
        players = [
            Player(name="Hero", seat=1, stack=1000.0, is_hero=True, hole_cards=[
                Card(rank="A", suit="s"), Card(rank="A", suit="h")
            ]),
            Player(name="Villain", seat=2, stack=1000.0),
        ]

        actions: dict[Street, list[Action]] = {
            Street.PREFLOP: [
                Action(player_name="Hero", action_type=ActionType.POST, amount=50.0),
                Action(player_name="Villain", action_type=ActionType.POST, amount=100.0),
                Action(player_name="Hero", action_type=ActionType.RAISE, amount=200.0),
                Action(player_name="Villain", action_type=ActionType.CALL, amount=100.0),
            ],
            Street.FLOP: [
                Action(player_name="Hero", action_type=ActionType.BET, amount=200.0),
                Action(player_name="Villain", action_type=ActionType.CALL, amount=200.0),
            ],
            Street.TURN: [
                Action(player_name="Hero", action_type=ActionType.CHECK),
                Action(player_name="Villain", action_type=ActionType.CHECK),
            ],
            Street.RIVER: [
                Action(player_name="Hero", action_type=ActionType.CHECK),
                Action(player_name="Villain", action_type=ActionType.CHECK),
            ],
            Street.SHOWDOWN: [],
        }

        board = [
            Card(rank="2", suit="h"),
            Card(rank="7", suit="d"),
            Card(rank="T", suit="s"),
            Card(rank="3", suit="c"),
            Card(rank="5", suit="h"),
        ]

        showdown_hands = {
            "Hero": [Card(rank="A", suit="s"), Card(rank="A", suit="h")],
            "Villain": [Card(rank="K", suit="s"), Card(rank="K", suit="h")],
        }

        return Hand(
            hand_id="equity_test",
            timestamp=datetime.now(),
            small_blind=50.0,
            big_blind=100.0,
            ante=0.0,
            button_seat=1,
            players=players,
            actions=actions,
            board=board,
            showdown_hands=showdown_hands,
            winners=["Hero"],
        )

    def test_has_showdown_true(self, showdown_hand_with_equity: Hand) -> None:
        state = ReplayState(hand=showdown_hand_with_equity)
        assert state.has_showdown() is True

    def test_has_showdown_false(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        assert state.has_showdown() is False

    def test_get_showdown_equity_returns_equity(self, showdown_hand_with_equity: Hand) -> None:
        state = ReplayState(hand=showdown_hand_with_equity)
        while state.next_action():
            pass
        equity = state.get_showdown_equity()
        assert equity is not None
        assert len(equity.player_names) == 2
        assert "Hero" in equity.player_names
        assert "Villain" in equity.player_names

    def test_showdown_equity_preflop(self, showdown_hand_with_equity: Hand) -> None:
        state = ReplayState(hand=showdown_hand_with_equity)
        while state.next_action():
            pass
        equity = state.get_showdown_equity()
        assert equity is not None
        # AA vs KK preflop - AA should be ~80% favorite
        hero_eq = equity.get_player_equity("Hero", Street.PREFLOP)
        assert hero_eq is not None
        assert hero_eq > 0.75

    def test_showdown_equity_cached(self, showdown_hand_with_equity: Hand) -> None:
        state = ReplayState(hand=showdown_hand_with_equity)
        while state.next_action():
            pass
        eq1 = state.get_showdown_equity()
        eq2 = state.get_showdown_equity()
        assert eq1 is eq2  # Same object (cached)

    def test_no_showdown_returns_none(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        assert state.get_showdown_equity() is None

    def test_showdown_equity_for_street(self) -> None:
        equity = ShowdownEquity(
            player_names=["A", "B"],
            preflop=[0.5, 0.5],
            flop=[0.6, 0.4],
            turn=[0.7, 0.3],
            river=[0.8, 0.2],
        )
        assert equity.get_equity_for_street(Street.PREFLOP) == [0.5, 0.5]
        assert equity.get_equity_for_street(Street.FLOP) == [0.6, 0.4]
        assert equity.get_equity_for_street(Street.TURN) == [0.7, 0.3]
        assert equity.get_equity_for_street(Street.RIVER) == [0.8, 0.2]
        assert equity.get_equity_for_street(Street.SHOWDOWN) == [0.8, 0.2]

    def test_showdown_equity_get_player_equity(self) -> None:
        equity = ShowdownEquity(
            player_names=["A", "B"],
            preflop=[0.5, 0.5],
            flop=[0.6, 0.4],
        )
        assert equity.get_player_equity("A", Street.PREFLOP) == 0.5
        assert equity.get_player_equity("B", Street.FLOP) == 0.4
        assert equity.get_player_equity("Unknown", Street.PREFLOP) is None
