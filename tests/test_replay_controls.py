"""Tests for ReplayControls widget."""

from datetime import datetime
from typing import Any

from src.gui.controls import ReplayControls
from src.parser.models import Action, ActionType, Hand, Player, Street
from src.replayer.state import ReplayState


def make_test_hand() -> Hand:
    """Create a test hand with a few actions."""
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
            Action(
                player_name="Villain",
                action_type=ActionType.CHECK,
                amount=0.0,
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


class TestReplayControlsBasics:
    """Test basic ReplayControls widget behavior."""

    def test_widget_created(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        assert isinstance(controls, ReplayControls)

    def test_has_prev_button(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        assert controls.prev_button is not None
        assert "Prev" in controls.prev_button.text()

    def test_has_next_button(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        assert controls.next_button is not None
        assert "Next" in controls.next_button.text()

    def test_buttons_disabled_without_state(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        assert not controls.prev_button.isEnabled()
        assert not controls.next_button.isEnabled()

    def test_set_replay_state(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_test_hand()
        state = ReplayState(hand=hand)
        controls.set_replay_state(state)
        assert controls.replay_state is state


class TestReplayControlsNavigation:
    """Test navigation with ReplayControls."""

    def test_next_button_enabled_with_state(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_test_hand()
        state = ReplayState(hand=hand)
        controls.set_replay_state(state)
        assert controls.next_button.isEnabled()

    def test_prev_button_enabled_at_initial_position(self, qtbot: Any) -> None:
        """Prev button is enabled since we can navigate back to posts."""
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_test_hand()
        state = ReplayState(hand=hand)
        controls.set_replay_state(state)
        # Initial position is 2 (after 2 POSTs), so prev is enabled
        assert controls.prev_button.isEnabled()

    def test_next_button_advances_position(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_test_hand()
        state = ReplayState(hand=hand)
        controls.set_replay_state(state)
        initial_pos = state.current_position
        controls.next_button.click()
        assert state.current_position == initial_pos + 1

    def test_prev_button_goes_back(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_test_hand()
        state = ReplayState(hand=hand)
        state.goto_position(2)
        controls.set_replay_state(state)
        controls.prev_button.click()
        assert state.current_position == 1

    def test_action_changed_signal_emitted_on_next(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_test_hand()
        state = ReplayState(hand=hand)
        controls.set_replay_state(state)
        with qtbot.waitSignal(controls.action_changed, timeout=1000):
            controls.next_button.click()

    def test_action_changed_signal_emitted_on_prev(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_test_hand()
        state = ReplayState(hand=hand)
        state.goto_position(2)
        controls.set_replay_state(state)
        with qtbot.waitSignal(controls.action_changed, timeout=1000):
            controls.prev_button.click()

    def test_next_disabled_at_end(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_test_hand()
        state = ReplayState(hand=hand)
        state.goto_position(state.total_actions)
        controls.set_replay_state(state)
        assert not controls.next_button.isEnabled()

    def test_prev_enabled_when_not_at_start(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_test_hand()
        state = ReplayState(hand=hand)
        state.goto_position(2)
        controls.set_replay_state(state)
        assert controls.prev_button.isEnabled()


class TestReplayControlsUpdates:
    """Test button state updates as navigation occurs."""

    def test_button_states_update_after_next(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_test_hand()
        state = ReplayState(hand=hand)
        controls.set_replay_state(state)
        # prev is already enabled (can go back to posts)
        assert controls.prev_button.isEnabled()
        controls.next_button.click()
        # Still enabled after advancing
        assert controls.prev_button.isEnabled()

    def test_button_states_update_after_prev(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_test_hand()
        state = ReplayState(hand=hand)
        state.goto_position(1)
        controls.set_replay_state(state)
        controls.prev_button.click()
        assert not controls.prev_button.isEnabled()

    def test_go_to_start(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_test_hand()
        state = ReplayState(hand=hand)
        state.goto_position(3)
        controls.set_replay_state(state)
        controls.go_to_start()
        assert state.current_position == 0

    def test_go_to_end(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_test_hand()
        state = ReplayState(hand=hand)
        controls.set_replay_state(state)
        controls.go_to_end()
        assert state.current_position == state.total_actions


def make_multi_street_hand() -> Hand:
    """Create a test hand with multiple streets for street navigation tests."""
    players = [
        Player(seat=1, name="Hero", stack=1000.0, bounty=0.0, is_hero=True),
        Player(seat=2, name="Villain", stack=1000.0, bounty=0.0, is_hero=False),
    ]
    actions = {
        Street.PREFLOP: [
            Action(player_name="Hero", action_type=ActionType.POST, amount=50.0),
            Action(player_name="Villain", action_type=ActionType.POST, amount=100.0),
            Action(player_name="Hero", action_type=ActionType.CALL, amount=50.0),
            Action(player_name="Villain", action_type=ActionType.CHECK, amount=0.0),
        ],
        Street.FLOP: [
            Action(player_name="Hero", action_type=ActionType.BET, amount=100.0),
            Action(player_name="Villain", action_type=ActionType.CALL, amount=100.0),
        ],
        Street.TURN: [
            Action(player_name="Hero", action_type=ActionType.CHECK, amount=0.0),
            Action(player_name="Villain", action_type=ActionType.BET, amount=200.0),
            Action(player_name="Hero", action_type=ActionType.CALL, amount=200.0),
        ],
        Street.RIVER: [
            Action(player_name="Hero", action_type=ActionType.CHECK, amount=0.0),
            Action(player_name="Villain", action_type=ActionType.CHECK, amount=0.0),
        ],
    }
    return Hand(
        hand_id="456",
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


class TestStreetNavigation:
    """Test street-by-street replay navigation."""

    def test_has_street_buttons(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        assert Street.PREFLOP in controls.street_buttons
        assert Street.FLOP in controls.street_buttons
        assert Street.TURN in controls.street_buttons
        assert Street.RIVER in controls.street_buttons
        assert Street.SHOWDOWN in controls.street_buttons

    def test_street_buttons_have_correct_labels(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        assert controls.get_street_button(Street.PREFLOP).text() == "Preflop"
        assert controls.get_street_button(Street.FLOP).text() == "Flop"
        assert controls.get_street_button(Street.TURN).text() == "Turn"
        assert controls.get_street_button(Street.RIVER).text() == "River"
        assert controls.get_street_button(Street.SHOWDOWN).text() == "Showdown"

    def test_street_buttons_disabled_without_state(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        for btn in controls.street_buttons.values():
            assert not btn.isEnabled()

    def test_available_streets_enabled(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_multi_street_hand()
        state = ReplayState(hand=hand)
        controls.set_replay_state(state)
        assert controls.get_street_button(Street.PREFLOP).isEnabled()
        assert controls.get_street_button(Street.FLOP).isEnabled()
        assert controls.get_street_button(Street.TURN).isEnabled()
        assert controls.get_street_button(Street.RIVER).isEnabled()

    def test_unavailable_streets_disabled(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_multi_street_hand()
        state = ReplayState(hand=hand)
        controls.set_replay_state(state)
        assert not controls.get_street_button(Street.SHOWDOWN).isEnabled()

    def test_click_flop_jumps_to_flop(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_multi_street_hand()
        state = ReplayState(hand=hand)
        controls.set_replay_state(state)
        controls.get_street_button(Street.FLOP).click()
        assert state.current_street == Street.FLOP

    def test_click_turn_jumps_to_turn(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_multi_street_hand()
        state = ReplayState(hand=hand)
        controls.set_replay_state(state)
        controls.get_street_button(Street.TURN).click()
        assert state.current_street == Street.TURN

    def test_click_river_jumps_to_river(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_multi_street_hand()
        state = ReplayState(hand=hand)
        controls.set_replay_state(state)
        controls.get_street_button(Street.RIVER).click()
        assert state.current_street == Street.RIVER

    def test_click_preflop_jumps_to_preflop(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_multi_street_hand()
        state = ReplayState(hand=hand)
        state.goto_street(Street.RIVER)
        controls.set_replay_state(state)
        controls.get_street_button(Street.PREFLOP).click()
        assert state.current_street == Street.PREFLOP

    def test_street_click_emits_action_changed(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_multi_street_hand()
        state = ReplayState(hand=hand)
        controls.set_replay_state(state)
        with qtbot.waitSignal(controls.action_changed, timeout=1000):
            controls.get_street_button(Street.FLOP).click()

    def test_preflop_only_hand(self, qtbot: Any) -> None:
        controls = ReplayControls()
        qtbot.addWidget(controls)
        hand = make_test_hand()
        state = ReplayState(hand=hand)
        controls.set_replay_state(state)
        assert controls.get_street_button(Street.PREFLOP).isEnabled()
        assert not controls.get_street_button(Street.FLOP).isEnabled()
        assert not controls.get_street_button(Street.TURN).isEnabled()
        assert not controls.get_street_button(Street.RIVER).isEnabled()
        assert not controls.get_street_button(Street.SHOWDOWN).isEnabled()
