"""Poker table widget for rendering game state."""
import math
from enum import Enum, auto

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QCursor, QFont, QMouseEvent, QPainter, QPen
from PyQt6.QtWidgets import QWidget
from typing_extensions import override

from src.parser.models import Card, Hand, Player, Street
from src.replayer.state import PlayerState, ReplayState, ShowdownEquity


class PlayerZone(Enum):
    """Zone indicating where a player is positioned around the table."""

    TOP = auto()
    BOTTOM = auto()
    LEFT = auto()
    RIGHT = auto()


class TableWidget(QWidget):
    """Widget that displays the poker table with player positions."""
    TABLE_COLOR = QColor("#1a5f2a")
    TABLE_BORDER_COLOR = QColor("#8b4513")
    PLAYER_BG_COLOR = QColor("#2d2d2d")
    PLAYER_BORDER_COLOR = QColor("#5e5e5e")
    HERO_BORDER_COLOR = QColor("#0078d4")
    TEXT_COLOR = QColor("#d4d4d4")
    STACK_COLOR = QColor("#ffd700")
    BUTTON_BG_COLOR = QColor("#ffffff")
    BUTTON_TEXT_COLOR = QColor("#000000")

    CARD_BG_COLOR = QColor("#ffffff")
    CARD_BORDER_COLOR = QColor("#333333")
    CARD_RED_COLOR = QColor("#cc0000")
    CARD_BLACK_COLOR = QColor("#000000")
    CARD_BACK_COLOR = QColor("#1e3a5f")
    CARD_BACK_PATTERN_COLOR = QColor("#2d5a87")
    FOLDED_OVERLAY_COLOR = QColor(0, 0, 0, 128)
    POT_BG_COLOR = QColor("#2d2d2d")
    POT_TEXT_COLOR = QColor("#ffd700")

    CHIP_GREEN = QColor("#2d8b2d")
    CHIP_BLUE = QColor("#2d5ba1")
    CHIP_RED = QColor("#a12d2d")
    CHIP_BORDER_COLOR = QColor("#1a1a1a")
    CHIP_AMOUNT_COLOR = QColor("#ffd700")
    HERO_STACK_HIGHLIGHT_COLOR = QColor(255, 215, 0, 60)
    WINNER_BORDER_COLOR = QColor("#ffd700")
    WINNER_LABEL_BG_COLOR = QColor("#ffd700")
    WINNER_LABEL_TEXT_COLOR = QColor("#000000")
    EQUITY_HIGH_COLOR = QColor("#4caf50")  # Green for >50%
    EQUITY_MID_COLOR = QColor("#ffeb3b")   # Yellow for 25-50%
    EQUITY_LOW_COLOR = QColor("#f44336")   # Red for <25%
    EQUITY_BG_COLOR = QColor(45, 45, 45, 200)

    BASE_PLAYER_BOX_WIDTH = 120
    BASE_PLAYER_BOX_HEIGHT = 50
    BASE_HOLE_CARD_WIDTH = 32
    BASE_HOLE_CARD_HEIGHT = 45
    BASE_HOLE_CARD_SPACING = 4
    BASE_HOLE_CARD_OVERLAP = 4
    BASE_BUTTON_DIAMETER = 24
    BASE_CARD_WIDTH = 40
    BASE_CARD_HEIGHT = 56
    BASE_CARD_SPACING = 4
    BASE_WIDTH = 800
    BASE_HEIGHT = 600
    MIN_SCALE_FACTOR = 0.5
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._replay_state: ReplayState | None = None
        self._hand: Hand | None = None
        self._hero_stack_rect: QRectF | None = None
        self._show_bb: bool = False
        self._bet_opacity: float = 1.0
        self._bet_animation_timer: QTimer = QTimer(self)
        self._bet_animation_timer.timeout.connect(self._animate_bet_opacity)
        self._hero_stack_highlight: bool = False
        self._hero_highlight_timer: QTimer = QTimer(self)
        self._hero_highlight_timer.timeout.connect(self._end_hero_highlight)
        self._hero_highlight_timer.setSingleShot(True)
        self._ui_scale: float = 1.0
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)

    def _get_scale_factor(self) -> float:
        """Calculate scale factor based on widget size relative to base size.
        
        Returns the minimum of width and height scale factors to maintain
        aspect ratio, with a minimum of MIN_SCALE_FACTOR for readability.
        The result is multiplied by the user's ui_scale preference.
        """
        width_scale = self.width() / self.BASE_WIDTH
        height_scale = self.height() / self.BASE_HEIGHT
        scale = min(width_scale, height_scale)
        base_scale = max(scale, self.MIN_SCALE_FACTOR)
        return base_scale * self._ui_scale

    def set_ui_scale(self, ui_scale: float) -> None:
        """Set the UI scale preference and trigger repaint.
        
        Args:
            ui_scale: The scale factor from preferences (e.g., 0.75, 1.0, 1.5, 2.0).
        """
        self._ui_scale = ui_scale
        self.update()

    def _get_player_zone(self, angle: float) -> PlayerZone:
        """Determine which zone a player is in based on their angle.

        The angle is in radians, measured counter-clockwise from positive x-axis.
        In our coordinate system (Y increases downward):
        - BOTTOM: angles near π/2 (90°), roughly 45° to 135° → π/4 to 3π/4
        - LEFT: angles near π (180°), roughly 135° to 225° → 3π/4 to 5π/4
        - TOP: angles near 3π/2 (270°), roughly 225° to 315° → 5π/4 to 7π/4
        - RIGHT: angles near 0°/360°, roughly 315° to 45° → 7π/4 to π/4

        Args:
            angle: The angle in radians (0 to 2π range).

        Returns:
            The PlayerZone indicating the player's position.
        """
        normalized = angle % (2 * math.pi)

        if math.pi / 4 <= normalized < 3 * math.pi / 4:
            return PlayerZone.BOTTOM
        elif 3 * math.pi / 4 <= normalized < 5 * math.pi / 4:
            return PlayerZone.LEFT
        elif 5 * math.pi / 4 <= normalized < 7 * math.pi / 4:
            return PlayerZone.TOP
        else:
            return PlayerZone.RIGHT

    @property
    def PLAYER_BOX_WIDTH(self) -> float:
        return self.BASE_PLAYER_BOX_WIDTH * self._get_scale_factor()

    @property
    def PLAYER_BOX_HEIGHT(self) -> float:
        return self.BASE_PLAYER_BOX_HEIGHT * self._get_scale_factor()

    @property
    def HOLE_CARD_WIDTH(self) -> float:
        return self.BASE_HOLE_CARD_WIDTH * self._get_scale_factor()

    @property
    def HOLE_CARD_HEIGHT(self) -> float:
        return self.BASE_HOLE_CARD_HEIGHT * self._get_scale_factor()

    @property
    def HOLE_CARD_SPACING(self) -> float:
        return self.BASE_HOLE_CARD_SPACING * self._get_scale_factor()

    @property
    def HOLE_CARD_OVERLAP(self) -> float:
        return self.BASE_HOLE_CARD_OVERLAP * self._get_scale_factor()

    @property
    def BUTTON_DIAMETER(self) -> float:
        return self.BASE_BUTTON_DIAMETER * self._get_scale_factor()

    @property
    def CARD_WIDTH(self) -> float:
        return self.BASE_CARD_WIDTH * self._get_scale_factor()

    @property
    def CARD_HEIGHT(self) -> float:
        return self.BASE_CARD_HEIGHT * self._get_scale_factor()

    @property
    def CARD_SPACING(self) -> float:
        return self.BASE_CARD_SPACING * self._get_scale_factor()

    def _scaled_font(
        self, base_size: int, weight: QFont.Weight = QFont.Weight.Normal
    ) -> QFont:
        """Create a font scaled by the current scale factor."""
        scaled_size = max(6, int(base_size * self._get_scale_factor()))
        return QFont("Arial", scaled_size, weight)

    def set_hand(self, hand: Hand) -> None:
        """Set the hand to display and create replay state."""
        self._hand = hand
        self._replay_state = ReplayState(hand=hand)
        self.update()

    def set_replay_state(self, replay_state: ReplayState) -> None:
        """Set the replay state directly."""
        self._replay_state = replay_state
        self._hand = replay_state.hand
        self.update()

    @property
    def replay_state(self) -> ReplayState | None:
        """Get current replay state."""
        return self._replay_state

    @property
    def hand(self) -> Hand | None:
        """Get current hand."""
        return self._hand

    def trigger_bet_animation(self) -> None:
        """Trigger fade-in animation for bet chips.
        
        Call this when a new bet is made (after next_action()).
        """
        self._bet_opacity = 0.0
        self._bet_animation_timer.start(50)
        self.update()

    def _animate_bet_opacity(self) -> None:
        """Animation step: increment bet opacity until fully visible."""
        self._bet_opacity += 0.25
        if self._bet_opacity >= 1.0:
            self._bet_opacity = 1.0
            self._bet_animation_timer.stop()
        self.update()

    def _trigger_hero_highlight(self) -> None:
        """Trigger brief highlight flash on hero stack click."""
        self._hero_stack_highlight = True
        self._hero_highlight_timer.start(150)
        self.update()

    def _end_hero_highlight(self) -> None:
        """End hero stack highlight after timer expires."""
        self._hero_stack_highlight = False
        self.update()

    def clear(self) -> None:
        """Clear the table display."""
        self._hand = None
        self._replay_state = None
        self.update()

    @override
    def paintEvent(self, event: object) -> None:
        """Render the poker table and players."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._draw_table(painter)

        if self._hand:
            self._draw_pot(painter)
            self._draw_board(painter)
            self._draw_players(painter)

        painter.end()

    def _draw_table(self, painter: QPainter) -> None:
        """Draw the oval poker table."""
        width = self.width()
        height = self.height()

        scale = self._get_scale_factor()
        margin = 80 * scale
        table_rect = QRectF(margin, margin, width - 2 * margin, height - 2 * margin)

        painter.setPen(QPen(self.TABLE_BORDER_COLOR, max(2, int(8 * scale))))
        painter.setBrush(QBrush(self.TABLE_COLOR))
        painter.drawEllipse(table_rect)

    def _get_player_positions(self) -> list[tuple[Player, QPointF]]:
        """Calculate positions for all players with hero at bottom center."""
        if not self._hand:
            return []

        players = list(self._hand.players)
        if not players:
            return []

        hero_idx = next(
            (i for i, p in enumerate(players) if p.is_hero),
            0,
        )

        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = (height - 5) / 2

        scale = self._get_scale_factor()
        margin = 80 * scale
        oval_rx = (width - 2 * margin) / 2 - self.PLAYER_BOX_WIDTH / 2
        oval_ry = (height - 2 * margin) / 2 - self.PLAYER_BOX_HEIGHT / 2

        num_players = len(players)
        positions: list[tuple[Player, QPointF]] = []

        for i, player in enumerate(players):
            offset = (i - hero_idx) % num_players

            angle = math.pi / 2 + (2 * math.pi * offset) / num_players
            x = center_x + oval_rx * math.cos(angle) * 1.1
            y = center_y + oval_ry * math.sin(angle) * 1.1

            positions.append((player, QPointF(x, y)))

        return positions

    def _get_bet_position(self, player_center: QPointF) -> QPointF:
        """Calculate position for bet display between player and table center.
        
        Returns a point 40% of the distance from player center toward table center.
        """
        table_center_x = self.width() / 2
        table_center_y = self.height() / 2
        
        dx = table_center_x - player_center.x()
        dy = table_center_y - player_center.y()
        
        bet_x = player_center.x() + dx * 0.4
        bet_y = player_center.y() + dy * 0.4
        
        return QPointF(bet_x, bet_y)

    def _draw_chip_stack(
        self, painter: QPainter, x: float, y: float, chip_count: int, amount: float
    ) -> None:
        """Draw stacked chip sprites with 3D effect.
        
        Args:
            painter: The QPainter to draw with.
            x: X coordinate for the center of the chip stack.
            y: Y coordinate for the base of the chip stack.
            chip_count: Number of chips to stack (1-3).
            amount: The bet amount to display below the chips.
        """
        painter.setOpacity(self._bet_opacity)
        
        scale = self._get_scale_factor()
        chip_width = 24 * scale
        chip_height = 20 * scale
        vertical_offset = 4 * scale
        
        chip_colors = [self.CHIP_GREEN, self.CHIP_BLUE, self.CHIP_RED]
        
        for i in range(chip_count):
            chip_y = y - i * vertical_offset
            chip_color = chip_colors[min(i, len(chip_colors) - 1)]
            
            chip_rect = QRectF(
                x - chip_width / 2,
                chip_y - chip_height / 2,
                chip_width,
                chip_height,
            )
            
            painter.setPen(QPen(self.CHIP_BORDER_COLOR, 1))
            painter.setBrush(QBrush(chip_color))
            painter.drawEllipse(chip_rect)
        
        painter.setFont(self._scaled_font(8, QFont.Weight.Bold))
        painter.setPen(self.CHIP_AMOUNT_COLOR)
        
        amount_text = self._format_stack_or_bb(amount)
        scale = self._get_scale_factor()
        amount_rect = QRectF(
            x - 30 * scale, y + chip_height / 2 + 2, 60 * scale, 14 * scale
        )
        painter.drawText(amount_rect, Qt.AlignmentFlag.AlignCenter, amount_text)
        
        painter.setOpacity(1.0)

    def _get_replay_context(self) -> tuple[
        dict[str, PlayerState],
        dict[str, list[Card]],
        list[str],
        ShowdownEquity | None,
        Street | None,
    ]:
        """Get current replay state context for drawing."""
        if not self._replay_state:
            return {}, {}, [], None, None

        return (
            self._replay_state.get_player_states(),
            self._replay_state.get_visible_hole_cards(),
            self._replay_state.get_winners(),
            self._replay_state.get_cached_equity(),
            self._replay_state.current_street,
        )

    def _calculate_player_angle(self, player_index: int, hero_idx: int, num_players: int) -> float:
        """Calculate the angle for a player's position around the table."""
        if num_players == 0:
            return 0.0
        offset = (player_index - hero_idx) % num_players
        return math.pi / 2 + (2 * math.pi * offset) / num_players

    def _draw_players(self, painter: QPainter) -> None:
        """Draw all players at their positions."""
        positions = self._get_player_positions()
        player_states, visible_hole_cards, winners, showdown_equity, current_street = (
            self._get_replay_context()
        )

        players = self._hand.players if self._hand else []
        hero_idx = next((idx for idx, p in enumerate(players) if p.is_hero), 0)
        num_players = len(players)

        for i, (player, pos) in enumerate(positions):
            angle = self._calculate_player_angle(i, hero_idx, num_players)
            self._draw_single_player(
                painter, player, pos, i, angle, player_states, visible_hole_cards,
                winners, showdown_equity, current_street
            )

    def _draw_single_player(
        self,
        painter: QPainter,
        player: Player,
        pos: QPointF,
        index: int,
        angle: float,
        player_states: dict[str, PlayerState],
        visible_hole_cards: dict[str, list[Card]],
        winners: list[str],
        showdown_equity: ShowdownEquity | None,
        current_street: Street | None,
    ) -> None:
        """Draw a single player with all their elements."""
        is_winner = player.name in winners
        self._draw_player_box(painter, player, pos, player_states, is_winner)
        self._draw_hole_cards(painter, player, pos, player_states, visible_hole_cards, angle)
        
        if self._hand and player.seat == self._hand.button_seat:
            self._draw_button_indicator(painter, pos)
        
        self._draw_player_bet(painter, player, pos, player_states)

        if current_street and self._replay_state and self._replay_state.has_showdown():
            if showdown_equity:
                equity = showdown_equity.get_player_equity(player.name, current_street)
                if equity is not None:
                    self._draw_equity_label(painter, pos, equity, angle)
            else:
                showdown_players = self._replay_state._get_showdown_players()
                if player.name in showdown_players:
                    self._draw_equity_placeholder(painter, pos, angle)

    def _draw_player_bet(
        self,
        painter: QPainter,
        player: Player,
        center: QPointF,
        player_states: dict[str, PlayerState],
    ) -> None:
        """Draw the player's current bet with chip sprites."""
        if player.name not in player_states:
            return
        
        current_bet = player_states[player.name].current_bet
        small_blind = self._hand.small_blind if self._hand and self._hand.small_blind > 0 else 1.0
        if current_bet <= small_blind / 4:
            return

        bet_pos = self._get_bet_position(center)

        big_blind = self._hand.big_blind if self._hand and self._hand.big_blind > 0 else 1.0
        bet_in_bb = current_bet / big_blind

        if bet_in_bb < 3:
            chip_count = 1
        elif bet_in_bb < 10:
            chip_count = 2
        else:
            chip_count = 3

        self._draw_chip_stack(painter, bet_pos.x(), bet_pos.y(), chip_count, current_bet)

    def _draw_player_box(
        self,
        painter: QPainter,
        player: Player,
        center: QPointF,
        player_states: dict[str, PlayerState],
        is_winner: bool = False,
    ) -> None:
        """Draw a single player's info box."""
        box_rect = QRectF(
            center.x() - self.PLAYER_BOX_WIDTH / 2,
            center.y() - self.PLAYER_BOX_HEIGHT / 2,
            self.PLAYER_BOX_WIDTH,
            self.PLAYER_BOX_HEIGHT,
        )

        scale = self._get_scale_factor()
        if is_winner:
            border_color = self.WINNER_BORDER_COLOR
        elif player.is_hero:
            border_color = self.HERO_BORDER_COLOR
        else:
            border_color = self.PLAYER_BORDER_COLOR
        border_width = 3 if is_winner else 2
        painter.setPen(QPen(border_color, border_width))
        painter.setBrush(QBrush(self.PLAYER_BG_COLOR))
        painter.drawRoundedRect(box_rect, 5, 5)

        painter.setFont(self._scaled_font(10, QFont.Weight.Bold))
        painter.setPen(self.TEXT_COLOR)

        name_rect = QRectF(
            box_rect.left() + 5 * scale,
            box_rect.top() + 5 * scale,
            box_rect.width() - 10 * scale,
            20 * scale,
        )
        display_name = player.name[:12] + "..." if len(player.name) > 15 else player.name
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignCenter, display_name)

        painter.setFont(self._scaled_font(9))
        painter.setPen(self.STACK_COLOR)

        if self._replay_state and player.name in player_states:
            stack = player_states[player.name].stack
        else:
            stack = player.stack

        stack_text = self._format_stack_or_bb(stack)
        stack_rect = QRectF(
            box_rect.left() + 5 * scale,
            box_rect.top() + 25 * scale,
            box_rect.width() - 10 * scale,
            20 * scale,
        )

        if player.is_hero and self._hero_stack_highlight:
            painter.setBrush(QBrush(self.HERO_STACK_HIGHLIGHT_COLOR))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(stack_rect, 3, 3)
            painter.setPen(self.STACK_COLOR)

        painter.drawText(stack_rect, Qt.AlignmentFlag.AlignCenter, stack_text)

        if player.is_hero:
            self._hero_stack_rect = stack_rect

        if is_winner:
            self._draw_winner_label(painter, box_rect, scale)

    def _draw_winner_label(
        self, painter: QPainter, box_rect: QRectF, scale: float
    ) -> None:
        """Draw WINNER label above player box."""
        label_width = 50 * scale
        label_height = 16 * scale
        label_rect = QRectF(
            box_rect.center().x() - label_width / 2,
            box_rect.top() - label_height - 2 * scale,
            label_width,
            label_height,
        )

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.WINNER_LABEL_BG_COLOR))
        painter.drawRoundedRect(label_rect, 3, 3)

        painter.setFont(self._scaled_font(8, QFont.Weight.Bold))
        painter.setPen(self.WINNER_LABEL_TEXT_COLOR)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, "WINNER")

    def _get_equity_color(self, equity: float) -> QColor:
        """Get color for equity display based on value."""
        if equity > 0.5:
            return self.EQUITY_HIGH_COLOR
        elif equity >= 0.25:
            return self.EQUITY_MID_COLOR
        else:
            return self.EQUITY_LOW_COLOR

    def _draw_equity_label(
        self,
        painter: QPainter,
        center: QPointF,
        equity: float,
        angle: float,
    ) -> None:
        """Draw equity percentage label near player's cards."""
        scale = self._get_scale_factor()
        label_width = 45 * scale
        label_height = 16 * scale

        zone = self._get_player_zone(angle)
        total_card_width = 2 * self.HOLE_CARD_WIDTH - self.BASE_HOLE_CARD_OVERLAP * scale

        if zone == PlayerZone.RIGHT:
            label_x = (
                center.x() - self.PLAYER_BOX_WIDTH / 2
                - total_card_width - self.HOLE_CARD_SPACING - label_width - 4 * scale
            )
        else:
            label_x = (
                center.x() + self.PLAYER_BOX_WIDTH / 2
                + total_card_width + self.HOLE_CARD_SPACING + 4 * scale
            )

        label_y = center.y() - label_height / 2

        label_rect = QRectF(label_x, label_y, label_width, label_height)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.EQUITY_BG_COLOR))
        painter.drawRoundedRect(label_rect, 3, 3)

        equity_text = f"{equity * 100:.1f}%"
        text_color = self._get_equity_color(equity)
        painter.setFont(self._scaled_font(9, QFont.Weight.Bold))
        painter.setPen(text_color)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, equity_text)

    def _draw_equity_placeholder(
        self,
        painter: QPainter,
        center: QPointF,
        angle: float,
    ) -> None:
        """Draw placeholder '—' when equity hasn't been calculated yet."""
        scale = self._get_scale_factor()
        label_width = 45 * scale
        label_height = 16 * scale

        zone = self._get_player_zone(angle)
        total_card_width = 2 * self.HOLE_CARD_WIDTH - self.BASE_HOLE_CARD_OVERLAP * scale

        if zone == PlayerZone.RIGHT:
            label_x = (
                center.x() - self.PLAYER_BOX_WIDTH / 2
                - total_card_width - self.HOLE_CARD_SPACING - label_width - 4 * scale
            )
        else:
            label_x = (
                center.x() + self.PLAYER_BOX_WIDTH / 2
                + total_card_width + self.HOLE_CARD_SPACING + 4 * scale
            )

        label_y = center.y() - label_height / 2
        label_rect = QRectF(label_x, label_y, label_width, label_height)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(self.EQUITY_BG_COLOR))
        painter.drawRoundedRect(label_rect, 3, 3)

        painter.setFont(self._scaled_font(9, QFont.Weight.Bold))
        painter.setPen(QColor("#888888"))
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, "—")

    def _format_stack(self, stack: float) -> str:
        """Format stack size for display."""
        if stack >= 1_000_000:
            return f"{stack / 1_000_000:.1f}M"
        elif stack >= 1_000:
            return f"{stack / 1_000:.1f}K"
        else:
            return f"{stack:.0f}"

    def _format_stack_or_bb(self, stack: float) -> str:
        """Format stack as chips or BB depending on _show_bb flag.
        
        When _show_bb is True, returns format 'X.X BB' using big_blind.
        When _show_bb is False or big_blind == 0, returns chip format.
        """
        if self._show_bb and self._hand and self._hand.big_blind > 0:
            bb_amount = stack / self._hand.big_blind
            return f"{bb_amount:.1f} BB"
        return self._format_stack(stack)

    def _draw_button_indicator(self, painter: QPainter, player_pos: QPointF) -> None:
        """Draw the dealer button indicator near the player."""
        button_x = player_pos.x() + self.PLAYER_BOX_WIDTH / 2 - self.BUTTON_DIAMETER / 2
        button_y = player_pos.y() - self.BUTTON_DIAMETER / 2

        button_rect = QRectF(
            button_x,
            button_y,
            self.BUTTON_DIAMETER,
            self.BUTTON_DIAMETER,
        )

        painter.setPen(QPen(QColor("#333333"), 2))
        painter.setBrush(QBrush(self.BUTTON_BG_COLOR))
        painter.drawEllipse(button_rect)

        painter.setFont(self._scaled_font(10, QFont.Weight.Bold))
        painter.setPen(self.BUTTON_TEXT_COLOR)
        painter.drawText(button_rect, Qt.AlignmentFlag.AlignCenter, "D")

    def _draw_hole_cards(
        self,
        painter: QPainter,
        player: Player,
        center: QPointF,
        player_states: dict[str, PlayerState],
        visible_hole_cards: dict[str, list[Card]],
        angle: float,
    ) -> None:
        """Draw player's hole cards next to their info box, oriented toward table center.
        
        Cards are positioned based on player zone:
        - TOP/BOTTOM/LEFT players: cards to the right of player box
        - RIGHT players: cards to the left of player box (toward center)
        """
        if player.name in player_states and player_states[player.name].is_folded:
            return

        zone = self._get_player_zone(angle)
        total_width = 2 * self.HOLE_CARD_WIDTH - self.HOLE_CARD_OVERLAP
        card_spacing = self.HOLE_CARD_WIDTH - self.HOLE_CARD_OVERLAP
        
        # Position cards based on zone
        if zone == PlayerZone.RIGHT:
            # Cards to the left of player box (toward center)
            start_x = center.x() - self.PLAYER_BOX_WIDTH / 2 - total_width - self.HOLE_CARD_SPACING
            cards_y = center.y() - self.HOLE_CARD_HEIGHT / 2
        else:
            # TOP/BOTTOM/LEFT: cards to the right of player box
            start_x = center.x() + self.PLAYER_BOX_WIDTH / 2 + self.HOLE_CARD_SPACING
            cards_y = center.y() - self.HOLE_CARD_HEIGHT / 2

        if player.name in visible_hole_cards:
            cards = visible_hole_cards[player.name]
            for i, card in enumerate(cards[:2]):
                x = start_x + i * card_spacing
                self._draw_hole_card(painter, card, x, cards_y)
        else:
            for i in range(2):
                x = start_x + i * card_spacing
                self._draw_card_back(painter, x, cards_y)

    def _draw_hole_card(
        self, painter: QPainter, card: Card, x: float, y: float
    ) -> None:
        """Draw a single hole card (face up)."""
        card_rect = QRectF(x, y, self.HOLE_CARD_WIDTH, self.HOLE_CARD_HEIGHT)

        painter.setPen(QPen(self.CARD_BORDER_COLOR, 1))
        painter.setBrush(QBrush(self.CARD_BG_COLOR))
        painter.drawRoundedRect(card_rect, 3, 3)

        suit_symbols = {"h": "♥", "d": "♦", "c": "♣", "s": "♠"}
        suit_symbol = suit_symbols.get(card.suit.lower(), card.suit)

        is_red = card.suit.lower() in ("h", "d")
        text_color = self.CARD_RED_COLOR if is_red else self.CARD_BLACK_COLOR
        painter.setPen(text_color)

        scale = self._get_scale_factor()
        painter.setFont(self._scaled_font(10, QFont.Weight.Bold))
        rank_rect = QRectF(x, y + 2 * scale, self.HOLE_CARD_WIDTH, 16 * scale)
        painter.drawText(rank_rect, Qt.AlignmentFlag.AlignCenter, card.rank)

        painter.setFont(self._scaled_font(12))
        suit_rect = QRectF(x, y + 16 * scale, self.HOLE_CARD_WIDTH, 20 * scale)
        painter.drawText(suit_rect, Qt.AlignmentFlag.AlignCenter, suit_symbol)

    def _draw_card_back(self, painter: QPainter, x: float, y: float) -> None:
        """Draw a face-down card."""
        card_rect = QRectF(x, y, self.HOLE_CARD_WIDTH, self.HOLE_CARD_HEIGHT)

        painter.setPen(QPen(self.CARD_BORDER_COLOR, 1))
        painter.setBrush(QBrush(self.CARD_BACK_COLOR))
        painter.drawRoundedRect(card_rect, 3, 3)

        painter.setPen(QPen(self.CARD_BACK_PATTERN_COLOR, 1))
        margin = 4 * self._get_scale_factor()
        inner_rect = QRectF(
            x + margin, y + margin,
            self.HOLE_CARD_WIDTH - 2 * margin,
            self.HOLE_CARD_HEIGHT - 2 * margin,
        )
        painter.drawRoundedRect(inner_rect, 2, 2)

    def _draw_pot(self, painter: QPainter) -> None:
        """Draw the current pot amount above the board cards."""
        if not self._replay_state:
            return

        pot = self._replay_state.calculate_pot()
        if pot <= 0:
            return

        center_x = self.width() / 2
        center_y = self.height() / 2

        scale = self._get_scale_factor()
        pot_text = f"Pot: {self._format_stack_or_bb(pot)}"
        pot_rect = QRectF(
            center_x - 60 * scale, center_y - 65 * scale, 120 * scale, 24 * scale
        )

        painter.setPen(QPen(self.PLAYER_BORDER_COLOR, 1))
        painter.setBrush(QBrush(self.POT_BG_COLOR))
        painter.drawRoundedRect(pot_rect, 4, 4)

        painter.setFont(self._scaled_font(11, QFont.Weight.Bold))
        painter.setPen(self.POT_TEXT_COLOR)
        painter.drawText(pot_rect, Qt.AlignmentFlag.AlignCenter, pot_text)

    def _draw_board(self, painter: QPainter) -> None:
        """Draw the community cards in the center of the table."""
        if not self._replay_state:
            return

        visible_cards = self._replay_state.get_visible_board()
        if not visible_cards:
            return

        center_x = self.width() / 2
        center_y = self.height() / 2

        total_width = (
            len(visible_cards) * self.CARD_WIDTH
            + (len(visible_cards) - 1) * self.CARD_SPACING
        )
        start_x = center_x - total_width / 2

        for i, card in enumerate(visible_cards):
            x = start_x + i * (self.CARD_WIDTH + self.CARD_SPACING)
            y = center_y - self.CARD_HEIGHT / 2
            self._draw_card(painter, card, x, y)

    def _draw_card(self, painter: QPainter, card: Card, x: float, y: float) -> None:
        """Draw a single playing card at the specified position."""
        card_rect = QRectF(x, y, self.CARD_WIDTH, self.CARD_HEIGHT)

        painter.setPen(QPen(self.CARD_BORDER_COLOR, 1))
        painter.setBrush(QBrush(self.CARD_BG_COLOR))
        painter.drawRoundedRect(card_rect, 4, 4)

        suit_symbols = {"h": "♥", "d": "♦", "c": "♣", "s": "♠"}
        suit_symbol = suit_symbols.get(card.suit.lower(), card.suit)

        is_red = card.suit.lower() in ("h", "d")
        text_color = self.CARD_RED_COLOR if is_red else self.CARD_BLACK_COLOR
        painter.setPen(text_color)

        scale = self._get_scale_factor()
        painter.setFont(self._scaled_font(14, QFont.Weight.Bold))
        rank_rect = QRectF(x, y + 4 * scale, self.CARD_WIDTH, 20 * scale)
        painter.drawText(rank_rect, Qt.AlignmentFlag.AlignCenter, card.rank)

        painter.setFont(self._scaled_font(16))
        suit_rect = QRectF(x, y + 24 * scale, self.CARD_WIDTH, 24 * scale)
        painter.drawText(suit_rect, Qt.AlignmentFlag.AlignCenter, suit_symbol)

    @override
    def mousePressEvent(self, event: QMouseEvent | None) -> None:
        """Handle mouse press events to toggle hero stack display."""
        if event is None:
            return

        if self._hero_stack_rect and self._hero_stack_rect.contains(event.position()):
            self._show_bb = not self._show_bb
            self._trigger_hero_highlight()
            return

        super().mousePressEvent(event)

    @override
    def mouseMoveEvent(self, event: QMouseEvent | None) -> None:
        """Handle mouse move events to change cursor when hovering hero stack."""
        if event is None:
            return

        if self._hero_stack_rect and self._hero_stack_rect.contains(event.position()):
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        super().mouseMoveEvent(event)
