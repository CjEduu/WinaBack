from datetime import datetime

import pytest

from src.parser.models import Action, ActionType, Card, Hand, Player, Street
from src.replayer.state import ReplayState


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
    def test_initial_position_is_zero(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        assert state.current_position == 0

    def test_total_actions_count(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        assert state.total_actions == 11

    def test_current_action_none_at_start(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        assert state.current_action is None

    def test_current_street_preflop_at_start(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        assert state.current_street == Street.PREFLOP


class TestNextPrevAction:
    def test_next_action_advances_position(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        result = state.next_action()
        assert result is True
        assert state.current_position == 1

    def test_next_action_returns_false_at_end(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        for _ in range(11):
            state.next_action()
        result = state.next_action()
        assert result is False
        assert state.current_position == 11

    def test_prev_action_decreases_position(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        state.next_action()
        state.next_action()
        result = state.prev_action()
        assert result is True
        assert state.current_position == 1

    def test_prev_action_returns_false_at_start(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        result = state.prev_action()
        assert result is False
        assert state.current_position == 0

    def test_current_action_after_next(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        state.next_action()
        action = state.current_action
        assert action is not None
        assert action.player_name == "Villain1"
        assert action.action_type == ActionType.POST


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
    def test_pot_zero_at_start(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        assert state.calculate_pot() == 0.0

    def test_pot_after_blinds(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        state.next_action()
        state.next_action()
        assert state.calculate_pot() == 150.0

    def test_pot_after_preflop(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        state.goto_street(Street.FLOP)
        assert state.calculate_pot() == 650.0

    def test_pot_after_flop_betting(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        state.goto_street(Street.TURN)
        assert state.calculate_pot() == 1450.0


class TestStackCalculation:
    def test_initial_stacks(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        stacks = state.calculate_player_stacks()
        assert stacks["Hero"] == 1000.0
        assert stacks["Villain1"] == 1500.0
        assert stacks["Villain2"] == 800.0

    def test_stacks_after_blinds(self, sample_hand: Hand) -> None:
        state = ReplayState(hand=sample_hand)
        state.next_action()
        state.next_action()
        stacks = state.calculate_player_stacks()
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
        for _ in range(3):
            state.next_action()
        actions = state.get_actions_up_to_current()
        assert len(actions) == 3
        assert actions[0][0] == Street.PREFLOP
        assert actions[0][1].action_type == ActionType.POST

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

    def test_bets_zero_at_start_of_hand(self, sample_hand: Hand) -> None:
        """At position 0, no bets have been made yet."""
        state = ReplayState(hand=sample_hand)
        player_states = state.get_player_states()
        for player_state in player_states.values():
            assert player_state.current_bet == 0.0

    def test_bets_zero_at_start_of_flop(self, sample_hand: Hand) -> None:
        """When going to FLOP, bets from PREFLOP should be cleared before any flop action."""
        state = ReplayState(hand=sample_hand)
        # PREFLOP has 5 actions, go to end of preflop
        for _ in range(5):
            state.next_action()
        # Villain2 called 200, so current_bet should be 300 (100 post + 200 call)
        player_states = state.get_player_states()
        assert player_states["Villain2"].current_bet == 300.0

        # Now advance to first action of FLOP (check by Villain2)
        state.next_action()
        # At the start of FLOP, bets should be reset
        player_states = state.get_player_states()
        assert player_states["Villain2"].current_bet == 0.0
        assert player_states["Hero"].current_bet == 0.0

    def test_bets_accumulate_within_street(self, sample_hand: Hand) -> None:
        """Bets should accumulate within the same street."""
        state = ReplayState(hand=sample_hand)
        # Go to FLOP: 5 preflop + 1 check + 1 bet + 1 call = 8 actions
        for _ in range(8):
            state.next_action()
        player_states = state.get_player_states()
        # Hero bet 400, Villain2 called 400
        assert player_states["Hero"].current_bet == 400.0
        assert player_states["Villain2"].current_bet == 400.0

    def test_bets_zero_at_start_of_turn(self, sample_hand: Hand) -> None:
        """When going to TURN, bets from FLOP should be cleared."""
        state = ReplayState(hand=sample_hand)
        # Go to first action of TURN: 5 preflop + 3 flop + 1 = 9 actions
        for _ in range(9):
            state.next_action()
        player_states = state.get_player_states()
        # First action on turn is CHECK, so bets should be 0
        assert player_states["Hero"].current_bet == 0.0
        assert player_states["Villain2"].current_bet == 0.0
