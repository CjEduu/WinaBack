import re
from datetime import datetime
from pathlib import Path

from src.parser.base import ParseError, Parser
from src.parser.models import Action, ActionType, Card, Hand, Player, Street, Tournament

HEADER_PATTERN = re.compile(
    r'Winamax Poker - Tournament "(?P<name>[^"]+)" '
    r"buyIn: (?P<buyin>[\d.]+)€ \+ (?P<fee>[\d.]+)€ "
    r"level: (?P<level>\d+) - "
    r"HandId: #(?P<tournament_id>\d+)-(?P<hand_num>\d+)-\d+ - "
    r"Holdem no limit \((?P<ante>\d+)/(?P<sb>\d+)/(?P<bb>\d+)\) - "
    r"(?P<datetime>\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}) UTC"
)

TABLE_PATTERN = re.compile(
    r"Table: '[^']+' \d+-max \(real money\) Seat #(?P<button>\d+) is the button"
)

SEAT_PATTERN = re.compile(
    r"Seat (?P<seat>\d+): (?P<name>[^(]+) \((?P<stack>\d+)(?:, (?P<bounty>[\d.]+)€ bounty)?\)"
)

DEALT_PATTERN = re.compile(r"Dealt to (?P<name>[^\[]+) \[(?P<cards>[^\]]+)\]")

STREET_PATTERNS: dict[Street, re.Pattern[str]] = {
    Street.PREFLOP: re.compile(r"\*\*\* PRE-FLOP \*\*\*"),
    Street.FLOP: re.compile(r"\*\*\* FLOP \*\*\* \[(?P<cards>[^\]]+)\]"),
    Street.TURN: re.compile(r"\*\*\* TURN \*\*\* \[[^\]]+\]\[(?P<card>[^\]]+)\]"),
    Street.RIVER: re.compile(r"\*\*\* RIVER \*\*\* \[[^\]]+\]\[(?P<card>[^\]]+)\]"),
    Street.SHOWDOWN: re.compile(r"\*\*\* SHOW DOWN \*\*\*"),
}

ACTION_PATTERNS: list[tuple[re.Pattern[str], ActionType, bool]] = [
    (re.compile(r"^(?P<name>.+?) posts ante (?P<amount>\d+)$"), ActionType.POST, False),
    (
        re.compile(r"^(?P<name>.+?) posts small blind (?P<amount>\d+)$"),
        ActionType.POST,
        False,
    ),
    (
        re.compile(r"^(?P<name>.+?) posts big blind (?P<amount>\d+)$"),
        ActionType.POST,
        False,
    ),
    (re.compile(r"^(?P<name>.+?) folds$"), ActionType.FOLD, False),
    (re.compile(r"^(?P<name>.+?) checks$"), ActionType.CHECK, False),
    (re.compile(r"^(?P<name>.+?) bets (?P<amount>\d+)$"), ActionType.BET, False),
    (
        re.compile(r"^(?P<name>.+?) bets (?P<amount>\d+) and is all-in$"),
        ActionType.BET,
        True,
    ),
    (re.compile(r"^(?P<name>.+?) calls (?P<amount>\d+)$"), ActionType.CALL, False),
    (
        re.compile(r"^(?P<name>.+?) calls (?P<amount>\d+) and is all-in$"),
        ActionType.CALL,
        True,
    ),
    (
        re.compile(r"^(?P<name>.+?) raises (?P<raise_amount>\d+) to (?P<amount>\d+)$"),
        ActionType.RAISE,
        False,
    ),
    (
        re.compile(
            r"^(?P<name>.+?) raises (?P<raise_amount>\d+) to (?P<amount>\d+) and is all-in$"
        ),
        ActionType.RAISE,
        True,
    ),
]

SHOWDOWN_PATTERN = re.compile(r"^(?P<name>.+?) shows \[(?P<cards>[^\]]+)\]")

WINNER_PATTERN = re.compile(r"^(?P<name>.+?) collected (?P<amount>\d+) from pot$")


class WinamaxParser(Parser):
    """Parser for Winamax hand history files."""

    def parse_file(self, file_path: Path) -> Tournament:
        """Parse a Winamax hand history file.

        Args:
            file_path: Path to the hand history file.

        Returns:
            Tournament object with metadata.

        Raises:
            ParseError: If the file cannot be parsed.
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="cp1252")
        except FileNotFoundError as e:
            raise ParseError(f"File not found: {file_path}") from e

        return self._parse_content(content)

    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file.

        Checks for Winamax header signature in first line.
        """
        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError):
            try:
                content = file_path.read_text(encoding="cp1252")
            except FileNotFoundError:
                return False

        first_line = content.split("\n")[0] if content else ""
        return first_line.startswith("Winamax Poker - Tournament")

    def _parse_content(self, content: str) -> Tournament:
        """Parse file content into Tournament object."""
        hands_text = self._split_hands(content)

        if not hands_text:
            raise ParseError("No hands found in file")

        first_hand = hands_text[0]
        match = HEADER_PATTERN.search(first_hand)
        if not match:
            raise ParseError("Could not parse tournament header")

        tournament_name = match.group("name")
        buy_in = float(match.group("buyin")) + float(match.group("fee"))
        tournament_id = match.group("tournament_id")
        start_time = datetime.strptime(match.group("datetime"), "%Y/%m/%d %H:%M:%S")

        hands = [self._parse_hand(hand_text) for hand_text in hands_text]

        return Tournament(
            tournament_id=tournament_id,
            name=tournament_name,
            buy_in=buy_in,
            start_time=start_time,
            hands=hands,
        )

    def _split_hands(self, content: str) -> list[str]:
        """Split file content into individual hand texts."""
        hands: list[str] = []
        current_hand: list[str] = []

        for line in content.split("\n"):
            if line.startswith("Winamax Poker - Tournament"):
                if current_hand:
                    hands.append("\n".join(current_hand))
                current_hand = [line]
            elif current_hand:
                current_hand.append(line)

        if current_hand:
            hands.append("\n".join(current_hand))

        return hands

    def _parse_hand(self, hand_text: str) -> Hand:
        """Parse a single hand from its text block."""
        lines = hand_text.split("\n")

        header_match = HEADER_PATTERN.search(lines[0])
        if not header_match:
            raise ParseError(f"Could not parse hand header: {lines[0][:50]}")

        hand_id = f"{header_match.group('tournament_id')}-{header_match.group('hand_num')}"
        timestamp = datetime.strptime(
            header_match.group("datetime"), "%Y/%m/%d %H:%M:%S"
        )
        ante = float(header_match.group("ante"))
        small_blind = float(header_match.group("sb"))
        big_blind = float(header_match.group("bb"))

        button_seat = 1
        table_match = TABLE_PATTERN.search(hand_text)
        if table_match:
            button_seat = int(table_match.group("button"))

        players = self._parse_players(hand_text)
        actions = self._parse_actions(hand_text)
        board = self._parse_board(hand_text)
        showdown_hands = self._parse_showdown_hands(hand_text)
        winners = self._parse_winners(hand_text)

        return Hand(
            hand_id=hand_id,
            timestamp=timestamp,
            small_blind=small_blind,
            big_blind=big_blind,
            ante=ante,
            button_seat=button_seat,
            players=players,
            actions=actions,
            board=board,
            showdown_hands=showdown_hands,
            winners=winners,
        )

    def _parse_players(self, hand_text: str) -> list[Player]:
        """Parse all players from a hand text block."""
        players: list[Player] = []

        dealt_match = DEALT_PATTERN.search(hand_text)
        hero_name = dealt_match.group("name").strip() if dealt_match else None
        hero_cards = (
            self._parse_cards(dealt_match.group("cards")) if dealt_match else []
        )

        for match in SEAT_PATTERN.finditer(hand_text):
            seat = int(match.group("seat"))
            name = match.group("name").strip()
            stack = float(match.group("stack"))
            bounty = float(match.group("bounty")) if match.group("bounty") else 0.0
            is_hero = name == hero_name
            hole_cards = hero_cards if is_hero else []

            players.append(
                Player(
                    name=name,
                    seat=seat,
                    stack=stack,
                    bounty=bounty,
                    hole_cards=hole_cards,
                    is_hero=is_hero,
                )
            )

        return players

    def _parse_cards(self, cards_str: str) -> list[Card]:
        """Parse card string like '7c 4c' into list of Card objects."""
        cards: list[Card] = []
        for card_str in cards_str.split():
            if len(card_str) >= 2:
                rank = card_str[:-1]
                suit = card_str[-1]
                cards.append(Card(rank=rank, suit=suit))
        return cards

    def _parse_actions(self, hand_text: str) -> dict[Street, list[Action]]:
        """Parse all actions from a hand, organized by street."""
        actions: dict[Street, list[Action]] = {}
        current_street: Street | None = None

        for line in hand_text.split("\n"):
            line = line.strip()
            if not line:
                continue

            for street, pattern in STREET_PATTERNS.items():
                if pattern.match(line):
                    current_street = street
                    if street not in actions:
                        actions[street] = []
                    break

            if current_street is None:
                if "*** ANTE/BLINDS ***" in line:
                    current_street = Street.PREFLOP
                    actions[Street.PREFLOP] = []
                continue

            if line.startswith("***"):
                continue

            action = self._parse_action_line(line)
            if action and current_street in actions:
                actions[current_street].append(action)

        return actions

    def _parse_action_line(self, line: str) -> Action | None:
        """Parse a single action line into an Action object."""
        for pattern, action_type, is_all_in in ACTION_PATTERNS:
            match = pattern.match(line)
            if match:
                name = match.group("name")
                amount = float(match.group("amount")) if "amount" in match.groupdict() else 0.0
                return Action(
                    player_name=name,
                    action_type=action_type,
                    amount=amount,
                    is_all_in=is_all_in,
                )
        return None

    def _parse_board(self, hand_text: str) -> list[Card]:
        """Parse board cards from a hand."""
        board: list[Card] = []

        flop_match = STREET_PATTERNS[Street.FLOP].search(hand_text)
        if flop_match:
            board.extend(self._parse_cards(flop_match.group("cards")))

        turn_match = STREET_PATTERNS[Street.TURN].search(hand_text)
        if turn_match:
            board.extend(self._parse_cards(turn_match.group("card")))

        river_match = STREET_PATTERNS[Street.RIVER].search(hand_text)
        if river_match:
            board.extend(self._parse_cards(river_match.group("card")))

        return board

    def _parse_showdown_hands(self, hand_text: str) -> dict[str, list[Card]]:
        """Parse revealed hands from showdown."""
        showdown_hands: dict[str, list[Card]] = {}

        in_showdown = False
        for line in hand_text.split("\n"):
            if "*** SHOW DOWN ***" in line:
                in_showdown = True
                continue
            if in_showdown and line.startswith("***"):
                break
            if in_showdown:
                match = SHOWDOWN_PATTERN.match(line)
                if match:
                    name = match.group("name")
                    cards = self._parse_cards(match.group("cards"))
                    showdown_hands[name] = cards

        return showdown_hands

    def _parse_winners(self, hand_text: str) -> list[str]:
        """Parse winner(s) from collected pot lines."""
        winners: list[str] = []

        for line in hand_text.split("\n"):
            match = WINNER_PATTERN.match(line.strip())
            if match:
                name = match.group("name")
                if name not in winners:
                    winners.append(name)

        return winners
