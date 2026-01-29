# Equity Module Guidelines

## Architecture

- `evaluator.py` - Hand evaluation (ranks 5-7 card hands)
- `calculator.py` - Monte Carlo equity calculation

## Hand Evaluation Pattern

```python
from src.equity.evaluator import evaluate_hand, HandRank

rank, tiebreakers = evaluate_hand(hole_cards, board)
# rank: int (HandRank.HIGH_CARD to HandRank.STRAIGHT_FLUSH)
# tiebreakers: list[int] for comparing same-rank hands
```

## Equity Calculation Pattern

```python
from src.equity.calculator import calculate_equity

equities = calculate_equity(
    players_cards=[(card1, card2), (card3, card4)],
    board=[flop1, flop2, flop3],  # 0-5 cards
    iterations=10000
)
# Returns list[float] with probabilities summing to 1.0
```

## Performance Notes

- 10000 iterations takes ~300ms for 2-3 players
- For UI responsiveness, consider running in background thread
- Reduce iterations (e.g., 5000) for faster but less accurate results
