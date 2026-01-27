from datetime import datetime
from pathlib import Path

import pytest

from src.parser.base import ParseError
from src.parser.models import ActionType, Street
from src.parser.winamax import WinamaxParser

SAMPLE_HAND = '''Winamax Poker - Tournament "ATOM" buyIn: 4.50€ + 0.50€ level: 1 - \
HandId: #4446486702751481892-1-1768934733 - Holdem no limit (25/100/200) - 2026/01/20 18:45:33 UTC
Table: 'ATOM(1035278361)#0035' 6-max (real money) Seat #2 is the button
Seat 1: Win2Win21 (20000, 2.50€ bounty)
Seat 2: jesusito33 (20000, 2.50€ bounty)
Seat 3: Player3 (15000, 2.50€ bounty)
*** ANTE/BLINDS ***
Win2Win21 posts ante 25
jesusito33 posts ante 25
Player3 posts ante 25
Dealt to jesusito33 [7c 4c]
*** PRE-FLOP ***
Win2Win21 folds
jesusito33 folds
Player3 collected 75 from pot
*** SUMMARY ***
Total pot 75 | No rake
'''

SAMPLE_MULTI_HAND = '''Winamax Poker - Tournament "ATOM" buyIn: 4.50€ + 0.50€ level: 1 - \
HandId: #4446486702751481892-1-1768934733 - Holdem no limit (25/100/200) - 2026/01/20 18:45:33 UTC
Table: 'ATOM(1035278361)#0035' 6-max (real money) Seat #2 is the button
Seat 1: Win2Win21 (20000, 2.50€ bounty)
Seat 2: jesusito33 (20000, 2.50€ bounty)
*** ANTE/BLINDS ***
Dealt to jesusito33 [7c 4c]
*** SUMMARY ***

Winamax Poker - Tournament "ATOM" buyIn: 4.50€ + 0.50€ level: 1 - \
HandId: #4446486702751481892-2-1768934782 - Holdem no limit (30/125/250) - 2026/01/20 18:46:22 UTC
Table: 'ATOM(1035278361)#0035' 6-max (real money) Seat #3 is the button
Seat 1: Win2Win21 (19975, 2.50€ bounty)
Seat 2: jesusito33 (19975, 2.50€ bounty)
Seat 3: A.MAKETTE (19875, 2.50€ bounty)
*** ANTE/BLINDS ***
Dealt to jesusito33 [5h 6h]
*** SUMMARY ***
'''

SAMPLE_FULL_HAND = '''Winamax Poker - Tournament "ATOM" buyIn: 4.50€ + 0.50€ level: 1 - \
HandId: #4446486702751481892-1-1768934733 - Holdem no limit (25/100/200) - 2026/01/20 18:45:33 UTC
Table: 'ATOM(1035278361)#0035' 6-max (real money) Seat #2 is the button
Seat 1: Win2Win21 (20000, 2.50€ bounty)
Seat 2: jesusito33 (20000, 2.50€ bounty)
Seat 3: A.MAKETTE (20000, 2.50€ bounty)
Seat 4: tarzakerva17 (20000, 2.50€ bounty)
*** ANTE/BLINDS ***
A.MAKETTE posts ante 25
tarzakerva17 posts ante 25
Win2Win21 posts ante 25
jesusito33 posts ante 25
A.MAKETTE posts small blind 100
tarzakerva17 posts big blind 200
Dealt to jesusito33 [7c 4c]
*** PRE-FLOP *** 
Win2Win21 raises 300 to 500
jesusito33 folds
A.MAKETTE folds
tarzakerva17 calls 300
*** FLOP *** [2c Qh Ks]
tarzakerva17 checks
Win2Win21 bets 438
tarzakerva17 calls 438
*** TURN *** [2c Qh Ks][7d]
tarzakerva17 checks
Win2Win21 checks
*** RIVER *** [2c Qh Ks 7d][Tc]
tarzakerva17 checks
Win2Win21 bets 1382
tarzakerva17 folds
Win2Win21 collected 3508 from pot
*** SUMMARY ***
Total pot 3508 | No rake
Board: [2c Qh Ks 7d Tc]
'''

SAMPLE_SHOWDOWN_HAND = '''Winamax Poker - Tournament "ATOM" buyIn: 4.50€ + 0.50€ level: 1 - \
HandId: #4446486702751481892-3-1768934815 - Holdem no limit (25/100/200) - 2026/01/20 18:46:55 UTC
Table: 'ATOM(1035278361)#0035' 6-max (real money) Seat #4 is the button
Seat 4: tarzakerva17 (18512, 2.50€ bounty)
Seat 6: Ziehmax (20800, 2.50€ bounty)
Seat 2: jesusito33 (19950, 2.50€ bounty)
*** ANTE/BLINDS ***
tarzakerva17 posts ante 25
Ziehmax posts ante 25
jesusito33 posts ante 25
tarzakerva17 posts small blind 100
Ziehmax posts big blind 200
Dealt to jesusito33 [8c 2c]
*** PRE-FLOP *** 
jesusito33 folds
tarzakerva17 calls 100
Ziehmax checks
*** FLOP *** [6c Qc Kh]
Ziehmax checks
tarzakerva17 checks
*** TURN *** [6c Qc Kh][5h]
Ziehmax checks
tarzakerva17 checks
*** RIVER *** [6c Qc Kh 5h][Kc]
Ziehmax checks
tarzakerva17 checks
*** SHOW DOWN ***
Ziehmax shows [4s 9d] (One pair : Kings)
tarzakerva17 shows [Ad 4h] (One pair : Kings)
tarzakerva17 collected 650 from pot
*** SUMMARY ***
Total pot 650 | No rake
Board: [6c Qc Kh 5h Kc]
'''

SAMPLE_ALLIN_HAND = '''Winamax Poker - Tournament "ATOM" buyIn: 4.50€ + 0.50€ level: 5 - \
HandId: #4446486702751481892-99-1768999999 - Holdem no limit (50/200/400) - 2026/01/20 20:00:00 UTC
Table: 'ATOM(1035278361)#0035' 6-max (real money) Seat #1 is the button
Seat 1: Hero (5000, 2.50€ bounty)
Seat 2: Villain (10000, 2.50€ bounty)
*** ANTE/BLINDS ***
Hero posts ante 50
Villain posts ante 50
Hero posts small blind 200
Villain posts big blind 400
Dealt to Hero [As Kd]
*** PRE-FLOP *** 
Hero raises 4550 to 4950 and is all-in
Villain calls 4550 and is all-in
*** FLOP *** [Ah 2d 3c]
*** TURN *** [Ah 2d 3c][7s]
*** RIVER *** [Ah 2d 3c 7s][Jh]
*** SHOW DOWN ***
Hero shows [As Kd] (One pair : Aces)
Villain shows [Qc Qd] (One pair : Queens)
Hero collected 10100 from pot
*** SUMMARY ***
'''


@pytest.fixture
def parser() -> WinamaxParser:
    return WinamaxParser()


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    file_path = tmp_path / "test_tournament.txt"
    file_path.write_text(SAMPLE_HAND, encoding="utf-8")
    return file_path


class TestCanParse:
    def test_can_parse_winamax_file(self, parser: WinamaxParser, sample_file: Path) -> None:
        assert parser.can_parse(sample_file) is True

    def test_cannot_parse_non_winamax_file(
        self, parser: WinamaxParser, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "pokerstars.txt"
        file_path.write_text("PokerStars Hand #123456", encoding="utf-8")
        assert parser.can_parse(file_path) is False

    def test_cannot_parse_missing_file(self, parser: WinamaxParser, tmp_path: Path) -> None:
        missing_file = tmp_path / "nonexistent.txt"
        assert parser.can_parse(missing_file) is False


class TestTournamentMetadata:
    def test_parse_tournament_name(self, parser: WinamaxParser, sample_file: Path) -> None:
        tournament = parser.parse_file(sample_file)
        assert tournament.name == "ATOM"

    def test_parse_tournament_id(self, parser: WinamaxParser, sample_file: Path) -> None:
        tournament = parser.parse_file(sample_file)
        assert tournament.tournament_id == "4446486702751481892"

    def test_parse_buy_in(self, parser: WinamaxParser, sample_file: Path) -> None:
        tournament = parser.parse_file(sample_file)
        assert tournament.buy_in == pytest.approx(5.0)

    def test_parse_start_time(self, parser: WinamaxParser, sample_file: Path) -> None:
        tournament = parser.parse_file(sample_file)
        expected = datetime(2026, 1, 20, 18, 45, 33)
        assert tournament.start_time == expected


class TestFileEncoding:
    def test_handles_utf8_encoding(self, parser: WinamaxParser, tmp_path: Path) -> None:
        file_path = tmp_path / "utf8.txt"
        file_path.write_text(SAMPLE_HAND, encoding="utf-8")
        tournament = parser.parse_file(file_path)
        assert tournament.name == "ATOM"

    def test_handles_cp1252_encoding(self, parser: WinamaxParser, tmp_path: Path) -> None:
        file_path = tmp_path / "cp1252.txt"
        file_path.write_text(SAMPLE_HAND, encoding="cp1252")
        tournament = parser.parse_file(file_path)
        assert tournament.name == "ATOM"


class TestErrorHandling:
    def test_raises_on_missing_file(self, parser: WinamaxParser, tmp_path: Path) -> None:
        missing = tmp_path / "missing.txt"
        with pytest.raises(ParseError, match="File not found"):
            parser.parse_file(missing)

    def test_raises_on_empty_file(self, parser: WinamaxParser, tmp_path: Path) -> None:
        empty = tmp_path / "empty.txt"
        empty.write_text("", encoding="utf-8")
        with pytest.raises(ParseError, match="No hands found"):
            parser.parse_file(empty)

    def test_raises_on_invalid_format(self, parser: WinamaxParser, tmp_path: Path) -> None:
        invalid = tmp_path / "invalid.txt"
        invalid.write_text("Some random text", encoding="utf-8")
        with pytest.raises(ParseError, match="No hands found"):
            parser.parse_file(invalid)


class TestHandStructure:
    """Tests for US-003: Parse hand structure (players, seats, stacks, bounties)."""

    def test_parses_hands_list(self, parser: WinamaxParser, sample_file: Path) -> None:
        tournament = parser.parse_file(sample_file)
        assert len(tournament.hands) == 1

    def test_parses_multiple_hands(self, parser: WinamaxParser, tmp_path: Path) -> None:
        file_path = tmp_path / "multi.txt"
        file_path.write_text(SAMPLE_MULTI_HAND, encoding="utf-8")
        tournament = parser.parse_file(file_path)
        assert len(tournament.hands) == 2

    def test_parses_hand_id(self, parser: WinamaxParser, sample_file: Path) -> None:
        tournament = parser.parse_file(sample_file)
        hand = tournament.hands[0]
        assert hand.hand_id == "4446486702751481892-1"

    def test_parses_hand_timestamp(self, parser: WinamaxParser, sample_file: Path) -> None:
        tournament = parser.parse_file(sample_file)
        hand = tournament.hands[0]
        expected = datetime(2026, 1, 20, 18, 45, 33)
        assert hand.timestamp == expected

    def test_parses_blind_structure(self, parser: WinamaxParser, sample_file: Path) -> None:
        tournament = parser.parse_file(sample_file)
        hand = tournament.hands[0]
        assert hand.ante == 25.0
        assert hand.small_blind == 100.0
        assert hand.big_blind == 200.0

    def test_parses_button_seat(self, parser: WinamaxParser, sample_file: Path) -> None:
        tournament = parser.parse_file(sample_file)
        hand = tournament.hands[0]
        assert hand.button_seat == 2

    def test_parses_players_count(self, parser: WinamaxParser, sample_file: Path) -> None:
        tournament = parser.parse_file(sample_file)
        hand = tournament.hands[0]
        assert len(hand.players) == 3

    def test_parses_player_seats(self, parser: WinamaxParser, sample_file: Path) -> None:
        tournament = parser.parse_file(sample_file)
        players = tournament.hands[0].players
        seats = [p.seat for p in players]
        assert seats == [1, 2, 3]

    def test_parses_player_names(self, parser: WinamaxParser, sample_file: Path) -> None:
        tournament = parser.parse_file(sample_file)
        players = tournament.hands[0].players
        names = [p.name for p in players]
        assert names == ["Win2Win21", "jesusito33", "Player3"]

    def test_parses_player_stacks(self, parser: WinamaxParser, sample_file: Path) -> None:
        tournament = parser.parse_file(sample_file)
        players = tournament.hands[0].players
        stacks = [p.stack for p in players]
        assert stacks == [20000.0, 20000.0, 15000.0]

    def test_parses_player_bounties(self, parser: WinamaxParser, sample_file: Path) -> None:
        tournament = parser.parse_file(sample_file)
        players = tournament.hands[0].players
        bounties = [p.bounty for p in players]
        assert bounties == [2.5, 2.5, 2.5]

    def test_identifies_hero(self, parser: WinamaxParser, sample_file: Path) -> None:
        tournament = parser.parse_file(sample_file)
        players = tournament.hands[0].players
        hero = next(p for p in players if p.is_hero)
        assert hero.name == "jesusito33"

    def test_handles_variable_player_counts(
        self, parser: WinamaxParser, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "multi.txt"
        file_path.write_text(SAMPLE_MULTI_HAND, encoding="utf-8")
        tournament = parser.parse_file(file_path)
        assert len(tournament.hands[0].players) == 2
        assert len(tournament.hands[1].players) == 3

    def test_second_hand_different_blind_structure(
        self, parser: WinamaxParser, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "multi.txt"
        file_path.write_text(SAMPLE_MULTI_HAND, encoding="utf-8")
        tournament = parser.parse_file(file_path)
        hand2 = tournament.hands[1]
        assert hand2.ante == 30.0
        assert hand2.small_blind == 125.0
        assert hand2.big_blind == 250.0
        assert hand2.button_seat == 3


class TestActionsAndCards:
    """Tests for US-004: Parse actions and cards."""

    def test_parses_preflop_actions(self, parser: WinamaxParser, tmp_path: Path) -> None:
        file_path = tmp_path / "full.txt"
        file_path.write_text(SAMPLE_FULL_HAND, encoding="utf-8")
        tournament = parser.parse_file(file_path)
        hand = tournament.hands[0]
        preflop = hand.actions[Street.PREFLOP]
        action_types = [a.action_type for a in preflop]
        assert ActionType.POST in action_types
        assert ActionType.RAISE in action_types
        assert ActionType.FOLD in action_types
        assert ActionType.CALL in action_types

    def test_parses_ante_actions(self, parser: WinamaxParser, tmp_path: Path) -> None:
        file_path = tmp_path / "full.txt"
        file_path.write_text(SAMPLE_FULL_HAND, encoding="utf-8")
        tournament = parser.parse_file(file_path)
        hand = tournament.hands[0]
        preflop = hand.actions[Street.PREFLOP]
        ante_actions = [a for a in preflop if a.amount == 25.0]
        assert len(ante_actions) == 4

    def test_parses_flop_actions(self, parser: WinamaxParser, tmp_path: Path) -> None:
        file_path = tmp_path / "full.txt"
        file_path.write_text(SAMPLE_FULL_HAND, encoding="utf-8")
        tournament = parser.parse_file(file_path)
        hand = tournament.hands[0]
        flop = hand.actions[Street.FLOP]
        assert len(flop) == 3
        assert flop[0].action_type == ActionType.CHECK
        assert flop[1].action_type == ActionType.BET
        assert flop[1].amount == 438.0
        assert flop[2].action_type == ActionType.CALL

    def test_parses_turn_actions(self, parser: WinamaxParser, tmp_path: Path) -> None:
        file_path = tmp_path / "full.txt"
        file_path.write_text(SAMPLE_FULL_HAND, encoding="utf-8")
        tournament = parser.parse_file(file_path)
        hand = tournament.hands[0]
        turn = hand.actions[Street.TURN]
        assert len(turn) == 2
        assert all(a.action_type == ActionType.CHECK for a in turn)

    def test_parses_river_actions(self, parser: WinamaxParser, tmp_path: Path) -> None:
        file_path = tmp_path / "full.txt"
        file_path.write_text(SAMPLE_FULL_HAND, encoding="utf-8")
        tournament = parser.parse_file(file_path)
        hand = tournament.hands[0]
        river = hand.actions[Street.RIVER]
        assert len(river) == 3
        assert river[1].action_type == ActionType.BET
        assert river[1].amount == 1382.0

    def test_parses_flop_cards(self, parser: WinamaxParser, tmp_path: Path) -> None:
        file_path = tmp_path / "full.txt"
        file_path.write_text(SAMPLE_FULL_HAND, encoding="utf-8")
        tournament = parser.parse_file(file_path)
        hand = tournament.hands[0]
        assert len(hand.board) == 5
        board_str = [str(c) for c in hand.board]
        assert board_str[:3] == ["2c", "Qh", "Ks"]

    def test_parses_turn_card(self, parser: WinamaxParser, tmp_path: Path) -> None:
        file_path = tmp_path / "full.txt"
        file_path.write_text(SAMPLE_FULL_HAND, encoding="utf-8")
        tournament = parser.parse_file(file_path)
        hand = tournament.hands[0]
        assert str(hand.board[3]) == "7d"

    def test_parses_river_card(self, parser: WinamaxParser, tmp_path: Path) -> None:
        file_path = tmp_path / "full.txt"
        file_path.write_text(SAMPLE_FULL_HAND, encoding="utf-8")
        tournament = parser.parse_file(file_path)
        hand = tournament.hands[0]
        assert str(hand.board[4]) == "Tc"

    def test_parses_hero_hole_cards(self, parser: WinamaxParser, tmp_path: Path) -> None:
        file_path = tmp_path / "full.txt"
        file_path.write_text(SAMPLE_FULL_HAND, encoding="utf-8")
        tournament = parser.parse_file(file_path)
        hand = tournament.hands[0]
        hero = next(p for p in hand.players if p.is_hero)
        assert len(hero.hole_cards) == 2
        cards_str = [str(c) for c in hero.hole_cards]
        assert cards_str == ["7c", "4c"]

    def test_non_hero_no_hole_cards_before_showdown(
        self, parser: WinamaxParser, tmp_path: Path
    ) -> None:
        file_path = tmp_path / "full.txt"
        file_path.write_text(SAMPLE_FULL_HAND, encoding="utf-8")
        tournament = parser.parse_file(file_path)
        hand = tournament.hands[0]
        non_heroes = [p for p in hand.players if not p.is_hero]
        assert all(len(p.hole_cards) == 0 for p in non_heroes)

    def test_parses_showdown_hands(self, parser: WinamaxParser, tmp_path: Path) -> None:
        file_path = tmp_path / "showdown.txt"
        file_path.write_text(SAMPLE_SHOWDOWN_HAND, encoding="utf-8")
        tournament = parser.parse_file(file_path)
        hand = tournament.hands[0]
        assert "Ziehmax" in hand.showdown_hands
        assert "tarzakerva17" in hand.showdown_hands
        ziehmax_cards = [str(c) for c in hand.showdown_hands["Ziehmax"]]
        assert ziehmax_cards == ["4s", "9d"]

    def test_parses_all_in_actions(self, parser: WinamaxParser, tmp_path: Path) -> None:
        file_path = tmp_path / "allin.txt"
        file_path.write_text(SAMPLE_ALLIN_HAND, encoding="utf-8")
        tournament = parser.parse_file(file_path)
        hand = tournament.hands[0]
        preflop = hand.actions[Street.PREFLOP]
        all_in_actions = [a for a in preflop if a.is_all_in]
        assert len(all_in_actions) == 2
        assert all_in_actions[0].action_type == ActionType.RAISE
        assert all_in_actions[1].action_type == ActionType.CALL

    def test_raise_amount_is_total(self, parser: WinamaxParser, tmp_path: Path) -> None:
        file_path = tmp_path / "full.txt"
        file_path.write_text(SAMPLE_FULL_HAND, encoding="utf-8")
        tournament = parser.parse_file(file_path)
        hand = tournament.hands[0]
        preflop = hand.actions[Street.PREFLOP]
        raise_action = next(a for a in preflop if a.action_type == ActionType.RAISE)
        assert raise_action.amount == 500.0

    def test_board_only_flop_if_no_turn(
        self, parser: WinamaxParser, tmp_path: Path
    ) -> None:
        hand_text = '''Winamax Poker - Tournament "TEST" buyIn: 1.00€ + 0.00€ level: 1 - \
HandId: #123-1-999 - Holdem no limit (0/50/100) - 2026/01/20 18:00:00 UTC
Table: 'TEST' 6-max (real money) Seat #1 is the button
Seat 1: Hero (1000, 1.00€ bounty)
Seat 2: Villain (1000, 1.00€ bounty)
*** ANTE/BLINDS ***
Dealt to Hero [Ah Kh]
*** PRE-FLOP ***
Hero raises 100 to 200
Villain folds
*** SUMMARY ***
'''
        file_path = tmp_path / "noboard.txt"
        file_path.write_text(hand_text, encoding="utf-8")
        tournament = parser.parse_file(file_path)
        hand = tournament.hands[0]
        assert len(hand.board) == 0

    def test_parses_check_action(self, parser: WinamaxParser, tmp_path: Path) -> None:
        file_path = tmp_path / "full.txt"
        file_path.write_text(SAMPLE_FULL_HAND, encoding="utf-8")
        tournament = parser.parse_file(file_path)
        hand = tournament.hands[0]
        flop = hand.actions[Street.FLOP]
        check_actions = [a for a in flop if a.action_type == ActionType.CHECK]
        assert len(check_actions) == 1
        assert check_actions[0].player_name == "tarzakerva17"
