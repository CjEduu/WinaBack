"""Monte Carlo equity calculator for poker hands."""

import random
from collections.abc import Sequence

from src.equity.evaluator import evaluate_hand
from src.parser.models import Card

RANKS = "23456789TJQKA"
SUITS = "cdhs"


def _build_deck() -> list[Card]:
    """Build a standard 52-card deck."""
    return [Card(rank=r, suit=s) for r in RANKS for s in SUITS]


def _remove_cards(deck: list[Card], cards: Sequence[Card]) -> list[Card]:
    """Remove cards from deck (by rank+suit matching)."""
    used = {(c.rank, c.suit) for c in cards}
    return [c for c in deck if (c.rank, c.suit) not in used]


def calculate_equity(
    players_cards: list[tuple[Card, Card]],
    board: list[Card],
    iterations: int = 10000,
) -> list[float]:
    """
    Calculate win probability for each player using Monte Carlo simulation.

    Args:
        players_cards: List of (hole_card1, hole_card2) tuples for each player
        board: Current community cards (0-5 cards)
        iterations: Number of simulations to run (default 10000)

    Returns:
        List of win probabilities (0.0 to 1.0) for each player.
        Ties split equity equally among tied players.
    """
    if not players_cards:
        return []

    num_players = len(players_cards)
    wins = [0.0] * num_players

    all_known = list(board)
    for hole in players_cards:
        all_known.extend(hole)

    base_deck = _remove_cards(_build_deck(), all_known)
    cards_needed = 5 - len(board)

    for _ in range(iterations):
        if cards_needed > 0:
            sampled = random.sample(base_deck, cards_needed)
            full_board = list(board) + sampled
        else:
            full_board = list(board)

        hands = [evaluate_hand(hole, full_board) for hole in players_cards]

        best_hand = max(hands)
        winners_idx = [i for i, h in enumerate(hands) if h == best_hand]
        share = 1.0 / len(winners_idx)

        for idx in winners_idx:
            wins[idx] += share

    return [w / iterations for w in wins]
