# GUI Module Guidelines

## Widget Patterns

### Container Widget with Header
When adding controls (like sort buttons) to a list widget, wrap the `QListWidget` in a `QWidget` container with a `QVBoxLayout`:
- Header row with label and control buttons
- List widget below

Access the internal list via `._list_widget` attribute.

### TournamentListWidget
- Now a `QWidget` container, not `QListWidget`
- Has built-in header with "Tournaments" label and sort button
- Access list methods via `._list_widget` (e.g., `._list_widget.currentItem()`)
- `SortOrder` enum: DEFAULT, ASCENDING, DESCENDING
- Sort resets to DEFAULT when `set_tournaments()` is called

### Replay Context Tuple
The `TableWidget._get_replay_context()` returns a 7-tuple:
`(player_states, visible_hole_cards, winners, showdown_equity, current_street, active_player, street_actions)`

### Player Visual State Flags
Pass boolean flags through the drawing chain:
`_draw_players` → `_draw_single_player` → `_draw_player_box`
Example flags: `is_winner`, `is_active`

### Glow/Highlight Effects
Draw glow effects BEFORE the main element using a larger rounded rect with transparent color.

### Action Badges
Use `street_actions` dict from replay context to show player action badges.
Badge clears when street changes.
