from dataclasses import dataclass, field
from typing import NamedTuple

from src.equity.calculator import calculate_equity
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
class ShowdownEquity:
    """Stores pre-calculated equity percentages for each street at showdown."""

    player_names: list[str]
    preflop: list[float] = field(default_factory=list)
    flop: list[float] = field(default_factory=list)
    turn: list[float] = field(default_factory=list)
    river: list[float] = field(default_factory=list)

    def get_equity_for_street(self, street: Street) -> list[float]:
        """Get equity list for the given street."""
        if street == Street.PREFLOP:
            return self.preflop
        elif street == Street.FLOP:
            return self.flop
        elif street == Street.TURN:
            return self.turn
        elif street in (Street.RIVER, Street.SHOWDOWN):
            return self.river
        return []

    def get_player_equity(self, player_name: str, street: Street) -> float | None:
        """Get equity for a specific player at a specific street."""
        if player_name not in self.player_names:
            return None
        idx = self.player_names.index(player_name)
        equities = self.get_equity_for_street(street)
        if idx < len(equities):
            return equities[idx]
        return None


@dataclass
class ReplayState:
    hand: Hand
    _action_sequence: list[tuple[Street, int, Action]] = field(
        default_factory=list, init=False
    )
    _current_position: int = field(default=0, init=False)
    _initial_stacks: dict[str, float] = field(default_factory=dict, init=False)
    _showdown_equity: ShowdownEquity | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self._build_action_sequence()
        self._initial_stacks = {p.name: p.stack for p in self.hand.players}
        self._skip_to_first_non_post()

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

    def _skip_to_first_non_post(self) -> None:
        """Skip past initial POST actions (antes/blinds) to start at first real action."""
        for i, (_, _, action) in enumerate(self._action_sequence):
            if action.action_type != ActionType.POST:
                self._current_position = i
                return
        self._current_position = len(self._action_sequence)

    def _is_blind_post(self, action: Action) -> bool:
        """Check if a POST action is a blind (SB or BB) rather than an ante."""
        if action.action_type != ActionType.POST:
            return False
        return action.amount in (self.hand.small_blind, self.hand.big_blind)

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

    def get_active_player(self) -> str | None:
        """Get the name of the player who just acted (current action's player).
        
        Returns None if no actions have been executed yet or at end of hand.
        """
        action = self.current_action
        if action is None:
            return None
        return action.player_name

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
        states = self._init_player_states(stacks)
        current_street_bets, last_street = self._process_actions_for_states(states)
        current_street_bets = self._reset_bets_if_street_changed(
            current_street_bets, last_street
        )
        self._apply_current_bets(states, current_street_bets)
        return states

    def _init_player_states(self, stacks: dict[str, float]) -> dict[str, PlayerState]:
        """Initialize player states with stack values."""
        return {
            player.name: PlayerState(
                name=player.name,
                stack=stacks.get(player.name, player.stack),
            )
            for player in self.hand.players
        }

    def _process_actions_for_states(
        self, states: dict[str, PlayerState]
    ) -> tuple[dict[str, float], Street | None]:
        """Process actions to update fold status and track bets."""
        current_street_bets: dict[str, float] = {}
        last_street: Street | None = None

        for i in range(self._current_position):
            street, _, action = self._action_sequence[i]

            if last_street is not None and street != last_street:
                current_street_bets = {}
            last_street = street

            self._apply_action_to_states(action, states, current_street_bets)

        return current_street_bets, last_street

    def _apply_action_to_states(
        self,
        action: Action,
        states: dict[str, PlayerState],
        current_street_bets: dict[str, float],
    ) -> None:
        """Apply a single action to update states and bets."""
        if action.action_type == ActionType.FOLD:
            states[action.player_name].is_folded = True
        elif action.action_type == ActionType.POST:
            if self._is_blind_post(action):
                current_street_bets[action.player_name] = (
                    current_street_bets.get(action.player_name, 0.0) + action.amount
                )
        elif action.action_type in (
            ActionType.BET,
            ActionType.CALL,
            ActionType.RAISE,
            ActionType.ALL_IN,
        ):
            current_street_bets[action.player_name] = (
                current_street_bets.get(action.player_name, 0.0) + action.amount
            )

    def _reset_bets_if_street_changed(
        self, current_street_bets: dict[str, float], last_street: Street | None
    ) -> dict[str, float]:
        """Reset bets if we've moved to a new street."""
        if last_street is not None and self.current_street != last_street:
            return {}
        return current_street_bets

    def _apply_current_bets(
        self, states: dict[str, PlayerState], current_street_bets: dict[str, float]
    ) -> None:
        """Apply current street bets to player states."""
        for player_name, bet_amount in current_street_bets.items():
            if player_name in states:
                states[player_name].current_bet = bet_amount

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

    def is_at_end(self) -> bool:
        """Check if replay is at the end of the hand (winners should be displayed)."""
        return self._current_position >= self.total_actions

    def get_winners(self) -> list[str]:
        """Get the list of winners when at end of hand."""
        if self.is_at_end():
            return self.hand.winners
        return []

    def _get_showdown_players(self) -> list[str]:
        """Get list of player names who reached showdown (not folded, have cards)."""
        player_states = self.get_player_states()
        showdown_players: list[str] = []
        for player in self.hand.players:
            if player_states[player.name].is_folded:
                continue
            if player.name in self.hand.showdown_hands:
                showdown_players.append(player.name)
        return showdown_players

    def _calculate_showdown_equity(self) -> ShowdownEquity | None:
        """Calculate equity for all streets for players who reached showdown."""
        showdown_players = self._get_showdown_players()
        if len(showdown_players) < 2:
            return None

        players_cards: list[tuple[Card, Card]] = []
        for name in showdown_players:
            cards = self.hand.showdown_hands[name]
            if len(cards) >= 2:
                players_cards.append((cards[0], cards[1]))
            else:
                return None

        board = self.hand.board

        iters = 10000
        preflop_eq = calculate_equity(players_cards, [], iterations=iters)
        flop_eq = (
            calculate_equity(players_cards, board[:3], iterations=iters)
            if len(board) >= 3 else []
        )
        turn_eq = (
            calculate_equity(players_cards, board[:4], iterations=iters)
            if len(board) >= 4 else []
        )
        river_eq = (
            calculate_equity(players_cards, board[:5], iterations=iters)
            if len(board) >= 5 else []
        )

        return ShowdownEquity(
            player_names=showdown_players,
            preflop=preflop_eq,
            flop=flop_eq,
            turn=turn_eq,
            river=river_eq,
        )

    def get_showdown_equity(self) -> ShowdownEquity | None:
        """Get showdown equity, calculating and caching if needed."""
        if not self.hand.showdown_hands:
            return None
        if self._showdown_equity is None:
            self._showdown_equity = self._calculate_showdown_equity()
        return self._showdown_equity

    def get_cached_equity(self) -> ShowdownEquity | None:
        """Get cached equity without triggering calculation."""
        return self._showdown_equity

    def has_showdown(self) -> bool:
        """Check if this hand has a showdown."""
        return bool(self.hand.showdown_hands)
