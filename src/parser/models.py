from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto


class ActionType(Enum):
    POST = auto()
    CHECK = auto()
    BET = auto()
    CALL = auto()
    RAISE = auto()
    FOLD = auto()
    ALL_IN = auto()


class Street(Enum):
    PREFLOP = auto()
    FLOP = auto()
    TURN = auto()
    RIVER = auto()
    SHOWDOWN = auto()


@dataclass
class Card:
    rank: str
    suit: str

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"


@dataclass
class Action:
    player_name: str
    action_type: ActionType
    amount: float = 0.0
    is_all_in: bool = False


@dataclass
class Player:
    name: str
    seat: int
    stack: float
    bounty: float = 0.0
    hole_cards: list[Card] = field(default_factory=list)
    is_hero: bool = False


@dataclass
class Hand:
    hand_id: str
    timestamp: datetime
    small_blind: float
    big_blind: float
    ante: float
    button_seat: int
    players: list[Player]
    actions: dict[Street, list[Action]] = field(default_factory=dict)
    board: list[Card] = field(default_factory=list)
    showdown_hands: dict[str, list[Card]] = field(default_factory=dict)


@dataclass
class Tournament:
    tournament_id: str
    name: str
    buy_in: float
    start_time: datetime
    hands: list[Hand] = field(default_factory=list)
