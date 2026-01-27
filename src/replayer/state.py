from dataclasses import dataclass, field
from typing import NamedTuple

from src.parser.models import Action, ActionType, Card, Hand, Street


class ActionIndex(NamedTuple):
    street: Street
    action_idx: int


@dataclass
class PlayerState:
    name: str
    stack: float
    is_folded: bool = False
    current_bet: float = 0.0


@dataclass
class ReplayState:
    hand: Hand
    _action_sequence: list[tuple[Street, int, Action]] = field(
        default_factory=list, init=False
    )
    _current_position: int = field(default=0, init=False)
    _initial_stacks: dict[str, float] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._build_action_sequence()
        self._initial_stacks = {p.name: p.stack for p in self.hand.players}

    def _build_action_sequence(self) -> None:
        self._action_sequence = []
        street_order = [
            Street.PREFLOP,
            Street.FLOP,
            Street.TURN,
            Street.RIVER,
            Street.SHOWDOWN,
        ]
        for street in street_order:
            actions = self.hand.actions.get(street, [])
            for i, action in enumerate(actions):
                self._action_sequence.append((street, i, action))

    @property
    def total_actions(self) -> int:
        return len(self._action_sequence)

    @property
    def current_position(self) -> int:
        return self._current_position

    @property
    def current_street(self) -> Street:
        if not self._action_sequence:
            return Street.PREFLOP
        if self._current_position == 0:
            return self._action_sequence[0][0]
        if self._current_position >= len(self._action_sequence):
            return Street.SHOWDOWN
        pos = self._current_position - 1
        return self._action_sequence[pos][0]

    @property
    def current_action(self) -> Action | None:
        if self._current_position == 0 or not self._action_sequence:
            return None
        pos = min(self._current_position - 1, len(self._action_sequence) - 1)
        return self._action_sequence[pos][2]

    def next_action(self) -> bool:
        if self._current_position >= self.total_actions:
            return False
        self._current_position += 1
        return True

    def prev_action(self) -> bool:
        if self._current_position <= 0:
            return False
        self._current_position -= 1
        return True

    def goto_street(self, street: Street) -> bool:
        if street not in self.hand.actions or not self.hand.actions[street]:
            return False

        for i, (s, _, _) in enumerate(self._action_sequence):
            if s == street:
                self._current_position = i + 1
                return True
        return False

    def goto_position(self, position: int) -> bool:
        if position < 0 or position > self.total_actions:
            return False
        self._current_position = position
        return True

    def calculate_pot(self) -> float:
        pot = 0.0
        for i in range(self._current_position):
            _, _, action = self._action_sequence[i]
            if action.action_type in (
                ActionType.POST,
                ActionType.BET,
                ActionType.CALL,
                ActionType.RAISE,
                ActionType.ALL_IN,
            ):
                pot += action.amount
        return pot

    def calculate_player_stacks(self) -> dict[str, float]:
        stacks = dict(self._initial_stacks)

        for i in range(self._current_position):
            _, _, action = self._action_sequence[i]
            if action.action_type in (
                ActionType.POST,
                ActionType.BET,
                ActionType.CALL,
                ActionType.RAISE,
                ActionType.ALL_IN,
            ):
                stacks[action.player_name] -= action.amount

        return stacks

    def get_player_states(self) -> dict[str, PlayerState]:
        stacks = self.calculate_player_stacks()
        states: dict[str, PlayerState] = {}

        for player in self.hand.players:
            states[player.name] = PlayerState(
                name=player.name,
                stack=stacks.get(player.name, player.stack),
            )

        current_street_bets: dict[str, float] = {}
        last_street: Street | None = None

        for i in range(self._current_position):
            street, _, action = self._action_sequence[i]

            if last_street is not None and street != last_street:
                current_street_bets = {}
            last_street = street

            if action.action_type == ActionType.FOLD:
                states[action.player_name].is_folded = True
            elif action.action_type in (
                ActionType.POST,
                ActionType.BET,
                ActionType.CALL,
                ActionType.RAISE,
                ActionType.ALL_IN,
            ):
                current_street_bets[action.player_name] = (
                    current_street_bets.get(action.player_name, 0.0) + action.amount
                )

        # Determine if current street differs from last processed action's street
        # If so, bets should be reset (we're at the start of a new street)
        current = self.current_street
        if last_street is not None and current != last_street:
            current_street_bets = {}

        # Apply current street bets to player states
        for player_name, bet_amount in current_street_bets.items():
            if player_name in states:
                states[player_name].current_bet = bet_amount

        return states

    def get_visible_board(self) -> list[Card]:
        current = self.current_street
        board = self.hand.board

        if current == Street.PREFLOP:
            return []
        elif current == Street.FLOP:
            return board[:3] if len(board) >= 3 else board
        elif current == Street.TURN:
            return board[:4] if len(board) >= 4 else board
        elif current in (Street.RIVER, Street.SHOWDOWN):
            return board

        return []

    def get_visible_hole_cards(self) -> dict[str, list[Card]]:
        visible: dict[str, list[Card]] = {}
        player_states = self.get_player_states()
        at_showdown = (
            self.current_street == Street.SHOWDOWN
            or self._current_position == self.total_actions
        )

        for player in self.hand.players:
            if player.is_hero and player.hole_cards:
                visible[player.name] = player.hole_cards
            elif (
                at_showdown
                and player.name in self.hand.showdown_hands
                and not player_states[player.name].is_folded
            ):
                visible[player.name] = self.hand.showdown_hands[player.name]

        return visible

    def get_actions_up_to_current(self) -> list[tuple[Street, Action]]:
        return [
            (street, action)
            for street, _, action in self._action_sequence[: self._current_position]
        ]

    def get_available_streets(self) -> list[Street]:
        return [s for s in Street if s in self.hand.actions and self.hand.actions[s]]
