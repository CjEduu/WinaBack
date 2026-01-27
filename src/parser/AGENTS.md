# Parser Module Guidelines

## Adding a New Parser

1. Create a new file `src/parser/<site_name>.py`
2. Implement the `Parser` ABC from `src/parser/base.py`
3. Export the new parser class in `src/parser/__init__.py`

## Required Methods

- `parse_file(file_path: Path) -> Tournament` - Parse a file and return Tournament
- `can_parse(file_path: Path) -> bool` - Check if parser handles this file format

## Data Models

Always use the dataclasses from `src/parser/models.py`:
- `Tournament` - Top-level container with hands list
- `Hand` - Single poker hand with players, actions, board
- `Player` - Player info: name, seat, stack, bounty, hole_cards
- `Action` - Single action: player_name, action_type, amount
- `Card` - rank + suit

## Testing

Add tests in `tests/test_<parser_name>.py` covering:
- File format detection (`can_parse`)
- Tournament metadata parsing
- Hand structure parsing
- Action/card parsing
