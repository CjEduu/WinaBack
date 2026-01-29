"""Tests for equity calculation module."""

import time

import pytest

from src.equity.calculator import calculate_equity
from src.equity.evaluator import HandRank, evaluate_hand
from src.parser.models import Card


class TestHandEvaluator:
    """Tests for hand evaluation."""

    def test_high_card(self) -> None:
        hole = (Card("A", "s"), Card("K", "h"))
        board = [Card("2", "c"), Card("5", "d"), Card("7", "s"), Card("9", "h"), Card("J", "c")]
        rank, tiebreakers = evaluate_hand(hole, board)
        assert rank == HandRank.HIGH_CARD
        assert tiebreakers[0] == 12  # Ace

    def test_pair(self) -> None:
        hole = (Card("A", "s"), Card("A", "h"))
        board = [Card("2", "c"), Card("5", "d"), Card("7", "s"), Card("9", "h"), Card("J", "c")]
        rank, tiebreakers = evaluate_hand(hole, board)
        assert rank == HandRank.PAIR
        assert tiebreakers[0] == 12  # Pair of Aces

    def test_two_pair(self) -> None:
        hole = (Card("A", "s"), Card("K", "h"))
        board = [Card("A", "c"), Card("K", "d"), Card("7", "s"), Card("9", "h"), Card("J", "c")]
        rank, tiebreakers = evaluate_hand(hole, board)
        assert rank == HandRank.TWO_PAIR
        assert tiebreakers[0] == 12  # Aces
        assert tiebreakers[1] == 11  # Kings

    def test_three_of_a_kind(self) -> None:
        hole = (Card("A", "s"), Card("A", "h"))
        board = [Card("A", "c"), Card("5", "d"), Card("7", "s"), Card("9", "h"), Card("J", "c")]
        rank, tiebreakers = evaluate_hand(hole, board)
        assert rank == HandRank.THREE_OF_A_KIND
        assert tiebreakers[0] == 12  # Three Aces

    def test_straight(self) -> None:
        hole = (Card("T", "s"), Card("J", "h"))
        board = [Card("8", "c"), Card("9", "d"), Card("Q", "s"), Card("2", "h"), Card("3", "c")]
        rank, tiebreakers = evaluate_hand(hole, board)
        assert rank == HandRank.STRAIGHT
        assert tiebreakers[0] == 10  # Queen-high straight

    def test_wheel_straight(self) -> None:
        hole = (Card("A", "s"), Card("2", "h"))
        board = [Card("3", "c"), Card("4", "d"), Card("5", "s"), Card("9", "h"), Card("K", "c")]
        rank, tiebreakers = evaluate_hand(hole, board)
        assert rank == HandRank.STRAIGHT
        assert tiebreakers[0] == 3  # 5-high (wheel)

    def test_flush(self) -> None:
        hole = (Card("A", "s"), Card("K", "s"))
        board = [Card("2", "s"), Card("5", "s"), Card("7", "s"), Card("9", "h"), Card("J", "c")]
        rank, tiebreakers = evaluate_hand(hole, board)
        assert rank == HandRank.FLUSH
        assert tiebreakers[0] == 12  # Ace-high flush

    def test_full_house(self) -> None:
        hole = (Card("A", "s"), Card("A", "h"))
        board = [Card("A", "c"), Card("K", "d"), Card("K", "s"), Card("9", "h"), Card("J", "c")]
        rank, tiebreakers = evaluate_hand(hole, board)
        assert rank == HandRank.FULL_HOUSE
        assert tiebreakers[0] == 12  # Aces full
        assert tiebreakers[1] == 11  # of Kings

    def test_four_of_a_kind(self) -> None:
        hole = (Card("A", "s"), Card("A", "h"))
        board = [Card("A", "c"), Card("A", "d"), Card("7", "s"), Card("9", "h"), Card("J", "c")]
        rank, tiebreakers = evaluate_hand(hole, board)
        assert rank == HandRank.FOUR_OF_A_KIND
        assert tiebreakers[0] == 12  # Quad Aces

    def test_straight_flush(self) -> None:
        hole = (Card("T", "s"), Card("J", "s"))
        board = [Card("8", "s"), Card("9", "s"), Card("Q", "s"), Card("2", "h"), Card("3", "c")]
        rank, tiebreakers = evaluate_hand(hole, board)
        assert rank == HandRank.STRAIGHT_FLUSH
        assert tiebreakers[0] == 10  # Queen-high straight flush


class TestEquityCalculator:
    """Tests for equity calculator."""

    def test_empty_players(self) -> None:
        result = calculate_equity([], [])
        assert result == []

    def test_single_player(self) -> None:
        hole = (Card("A", "s"), Card("K", "s"))
        result = calculate_equity([hole], [])
        assert len(result) == 1
        assert result[0] == 1.0

    def test_two_players_preflop(self) -> None:
        aa = (Card("A", "s"), Card("A", "h"))
        kk = (Card("K", "s"), Card("K", "h"))
        result = calculate_equity([aa, kk], [], iterations=5000)
        assert len(result) == 2
        assert result[0] > 0.75  # AA should be ~80% favorite
        assert result[1] < 0.25

    def test_dominated_hand(self) -> None:
        aa = (Card("A", "s"), Card("A", "h"))
        ak = (Card("A", "c"), Card("K", "s"))
        result = calculate_equity([aa, ak], [], iterations=5000)
        assert result[0] > 0.85  # AA dominates AK

    def test_coinflip(self) -> None:
        qq = (Card("Q", "s"), Card("Q", "h"))
        ak = (Card("A", "c"), Card("K", "s"))
        result = calculate_equity([qq, ak], [], iterations=5000)
        assert 0.40 < result[0] < 0.60  # Should be roughly 50/50
        assert 0.40 < result[1] < 0.60

    def test_with_board(self) -> None:
        pair = (Card("A", "s"), Card("A", "h"))
        overcards = (Card("K", "c"), Card("Q", "s"))
        board = [Card("A", "c"), Card("7", "d"), Card("2", "h")]  # AA has set
        result = calculate_equity([pair, overcards], board, iterations=5000)
        assert result[0] > 0.95  # Set is massive favorite

    def test_ties_split_equity(self) -> None:
        hand1 = (Card("A", "s"), Card("K", "h"))
        hand2 = (Card("A", "c"), Card("K", "d"))
        board = [
            Card("2", "s"),
            Card("3", "d"),
            Card("4", "h"),
            Card("5", "c"),
            Card("6", "s"),
        ]  # Board plays straight
        result = calculate_equity([hand1, hand2], board, iterations=1000)
        assert abs(result[0] - 0.5) < 0.05
        assert abs(result[1] - 0.5) < 0.05

    def test_three_players(self) -> None:
        aa = (Card("A", "s"), Card("A", "h"))
        kk = (Card("K", "s"), Card("K", "h"))
        qq = (Card("Q", "s"), Card("Q", "h"))
        result = calculate_equity([aa, kk, qq], [], iterations=5000)
        assert len(result) == 3
        assert sum(result) == pytest.approx(1.0, abs=0.01)
        assert result[0] > result[1] > result[2]  # AA > KK > QQ

    def test_performance(self) -> None:
        aa = (Card("A", "s"), Card("A", "h"))
        kk = (Card("K", "s"), Card("K", "h"))
        start = time.time()
        calculate_equity([aa, kk], [], iterations=10000)
        elapsed = time.time() - start
        assert elapsed < 0.5  # Must complete within 500ms
