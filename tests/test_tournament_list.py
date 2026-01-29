"""Tests for TournamentListWidget."""

from datetime import datetime
from typing import Any

import pytest

from src.gui.tournament_list import TournamentListWidget
from src.parser.models import Tournament


@pytest.fixture
def sample_tournaments() -> list[Tournament]:
    """Create sample tournaments for testing."""
    return [
        Tournament(
            tournament_id="123",
            name="Sunday Million",
            buy_in=10.0,
            start_time=datetime(2024, 1, 15, 14, 30),
        ),
        Tournament(
            tournament_id="456",
            name="Daily Challenge",
            buy_in=5.0,
            start_time=datetime(2024, 1, 16, 18, 0),
        ),
        Tournament(
            tournament_id="789",
            name="Freeroll",
            buy_in=0.0,
            start_time=datetime(2024, 1, 17, 20, 0),
        ),
    ]


class TestTournamentListWidget:
    """Tests for TournamentListWidget."""

    def test_widget_is_created(self, qtbot: Any) -> None:
        """Test widget can be created."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)
        assert isinstance(widget, TournamentListWidget)

    def test_set_tournaments_populates_list(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test setting tournaments populates the list."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)

        widget.set_tournaments(sample_tournaments)

        assert widget.count() == 3

    def test_tournament_entry_shows_name(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test each entry shows tournament name."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)

        widget.set_tournaments(sample_tournaments)

        item = widget.item(0)
        assert item is not None
        assert "Sunday Million" in item.text()

    def test_tournament_entry_shows_date(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test each entry shows tournament date."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)

        widget.set_tournaments(sample_tournaments)

        item = widget.item(0)
        assert item is not None
        assert "2024-01-15" in item.text()

    def test_clicking_tournament_emits_signal(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test clicking a tournament emits tournament_selected signal."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)
        widget.set_tournaments(sample_tournaments)

        with qtbot.waitSignal(widget.tournament_selected, timeout=1000) as blocker:
            item = widget.item(1)
            assert item is not None
            widget.itemClicked.emit(item)

        assert blocker.args[0].name == "Daily Challenge"

    def test_selected_tournament_is_highlighted(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test clicking a tournament highlights it (sets current item)."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)
        widget.set_tournaments(sample_tournaments)

        item = widget.item(1)
        assert item is not None
        widget.setCurrentItem(item)

        assert widget.currentItem() == item
        assert widget.currentRow() == 1

    def test_get_selected_tournament(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test get_selected_tournament returns the correct tournament."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)
        widget.set_tournaments(sample_tournaments)

        item = widget.item(2)
        assert item is not None
        widget.setCurrentItem(item)

        selected = widget.get_selected_tournament()
        assert selected is not None
        assert selected.name == "Freeroll"

    def test_get_selected_tournament_returns_none_when_empty(
        self, qtbot: Any
    ) -> None:
        """Test get_selected_tournament returns None when nothing selected."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)

        assert widget.get_selected_tournament() is None

    def test_tournaments_property(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test tournaments property returns the list."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)
        widget.set_tournaments(sample_tournaments)

        assert widget.tournaments == sample_tournaments

    def test_clear_and_repopulate(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test setting tournaments twice clears and repopulates."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)

        widget.set_tournaments(sample_tournaments)
        assert widget.count() == 3

        new_tournaments = [sample_tournaments[0]]
        widget.set_tournaments(new_tournaments)
        assert widget.count() == 1

    def test_scrollable_list(self, qtbot: Any) -> None:
        """Test list widget is scrollable with many tournaments."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)

        tournaments = [
            Tournament(
                tournament_id=str(i),
                name=f"Tournament {i}",
                buy_in=float(i),
                start_time=datetime(2024, 1, i % 28 + 1, 12, 0),
            )
            for i in range(50)
        ]
        widget.set_tournaments(tournaments)

        assert widget.count() == 50
        assert widget.verticalScrollBar() is not None
