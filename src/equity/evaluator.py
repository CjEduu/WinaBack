"""Hand evaluation module for determining poker hand rankings."""

from src.parser.models import Card

RANK_ORDER = "23456789TJQKA"
RANK_VALUES: dict[str, int] = {r: i for i, r in enumerate(RANK_ORDER)}


class HandRank:
    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8


def _get_rank_counts(cards: list[Card]) -> dict[str, int]:
    """Count occurrences of each rank."""
    counts: dict[str, int] = {}
    for card in cards:
        counts[card.rank] = counts.get(card.rank, 0) + 1
    return counts


def _get_suit_counts(cards: list[Card]) -> dict[str, int]:
    """Count occurrences of each suit."""
    counts: dict[str, int] = {}
    for card in cards:
        counts[card.suit] = counts.get(card.suit, 0) + 1
    return counts


def _is_straight(ranks: list[int]) -> tuple[bool, int]:
    """Check if ranks form a straight. Returns (is_straight, high_card)."""
    unique = sorted(set(ranks), reverse=True)
    if len(unique) < 5:
        return False, 0

    for i in range(len(unique) - 4):
        if unique[i] - unique[i + 4] == 4:
            return True, unique[i]

    if set([12, 0, 1, 2, 3]).issubset(set(ranks)):
        return True, 3

    return False, 0


def _get_flush_suit(cards: list[Card]) -> str | None:
    """Return suit with 5+ cards, or None."""
    suit_counts = _get_suit_counts(cards)
    for suit, count in suit_counts.items():
        if count >= 5:
            return suit
    return None


def evaluate_hand(hole_cards: tuple[Card, Card], board: list[Card]) -> tuple[int, list[int]]:
    """
    Evaluate a poker hand and return (hand_rank, tiebreakers).

    Higher hand_rank is better. Tiebreakers are compared left-to-right.
    """
    all_cards = list(hole_cards) + board
    rank_counts = _get_rank_counts(all_cards)
    flush_suit = _get_flush_suit(all_cards)

    counts_list = sorted(rank_counts.items(), key=lambda x: (x[1], RANK_VALUES[x[0]]), reverse=True)

    quads = [r for r, c in counts_list if c == 4]
    trips = [r for r, c in counts_list if c == 3]
    pairs = [r for r, c in counts_list if c == 2]

    all_rank_values = [RANK_VALUES[c.rank] for c in all_cards]

    if flush_suit:
        flush_cards = [c for c in all_cards if c.suit == flush_suit]
        flush_ranks = sorted([RANK_VALUES[c.rank] for c in flush_cards], reverse=True)
        is_str, high = _is_straight(flush_ranks)
        if is_str:
            return (HandRank.STRAIGHT_FLUSH, [high])
        return (HandRank.FLUSH, flush_ranks[:5])

    if quads:
        quad_rank = RANK_VALUES[quads[0]]
        kickers = sorted([v for v in all_rank_values if v != quad_rank], reverse=True)
        return (HandRank.FOUR_OF_A_KIND, [quad_rank, kickers[0]])

    if trips and (len(trips) > 1 or pairs):
        trip_rank = RANK_VALUES[trips[0]]
        if len(trips) > 1:
            pair_rank = RANK_VALUES[trips[1]]
        else:
            pair_rank = RANK_VALUES[pairs[0]]
        return (HandRank.FULL_HOUSE, [trip_rank, pair_rank])

    is_str, high = _is_straight(all_rank_values)
    if is_str:
        return (HandRank.STRAIGHT, [high])

    if trips:
        trip_rank = RANK_VALUES[trips[0]]
        kickers = sorted([v for v in all_rank_values if v != trip_rank], reverse=True)
        return (HandRank.THREE_OF_A_KIND, [trip_rank] + kickers[:2])

    if len(pairs) >= 2:
        pair_ranks = sorted([RANK_VALUES[p] for p in pairs], reverse=True)[:2]
        kickers = sorted([v for v in all_rank_values if v not in pair_ranks], reverse=True)
        return (HandRank.TWO_PAIR, pair_ranks + [kickers[0]])

    if pairs:
        pair_rank = RANK_VALUES[pairs[0]]
        kickers = sorted([v for v in all_rank_values if v != pair_rank], reverse=True)
        return (HandRank.PAIR, [pair_rank] + kickers[:3])

    kickers = sorted(all_rank_values, reverse=True)[:5]
    return (HandRank.HIGH_CARD, kickers)
