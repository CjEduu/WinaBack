"""Tests for TournamentListWidget."""

from datetime import datetime
from typing import Any

import pytest

from src.gui.tournament_list import SortOrder, TournamentListWidget
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

        assert widget._list_widget.count() == 3

    def test_tournament_entry_shows_name(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test each entry shows tournament name."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)

        widget.set_tournaments(sample_tournaments)

        item = widget._list_widget.item(0)
        assert item is not None
        assert "Sunday Million" in item.text()

    def test_tournament_entry_shows_date(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test each entry shows tournament date."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)

        widget.set_tournaments(sample_tournaments)

        item = widget._list_widget.item(0)
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
            item = widget._list_widget.item(1)
            assert item is not None
            widget._list_widget.itemClicked.emit(item)

        assert blocker.args[0].name == "Daily Challenge"

    def test_selected_tournament_is_highlighted(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test clicking a tournament highlights it (sets current item)."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)
        widget.set_tournaments(sample_tournaments)

        item = widget._list_widget.item(1)
        assert item is not None
        widget._list_widget.setCurrentItem(item)

        assert widget._list_widget.currentItem() == item
        assert widget._list_widget.currentRow() == 1

    def test_get_selected_tournament(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test get_selected_tournament returns the correct tournament."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)
        widget.set_tournaments(sample_tournaments)

        item = widget._list_widget.item(2)
        assert item is not None
        widget._list_widget.setCurrentItem(item)

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
        assert widget._list_widget.count() == 3

        new_tournaments = [sample_tournaments[0]]
        widget.set_tournaments(new_tournaments)
        assert widget._list_widget.count() == 1

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

        assert widget._list_widget.count() == 50
        assert widget._list_widget.verticalScrollBar() is not None


class TestTournamentListSorting:
    """Tests for tournament list sorting functionality."""

    def test_initial_sort_order_is_default(self, qtbot: Any) -> None:
        """Test initial sort order is DEFAULT."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)

        assert widget.sort_order == SortOrder.DEFAULT

    def test_sort_button_exists(self, qtbot: Any) -> None:
        """Test sort button is present."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)

        assert widget._sort_button is not None
        assert "Sort" in widget._sort_button.text()

    def test_sort_button_shows_default_state(self, qtbot: Any) -> None:
        """Test sort button shows default state initially."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)

        assert widget._sort_button.text() == "Sort: —"

    def test_cycle_to_ascending(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test clicking sort button cycles to ascending order."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)
        widget.set_tournaments(sample_tournaments)

        widget._sort_button.click()

        assert widget.sort_order == SortOrder.ASCENDING
        assert widget._sort_button.text() == "Sort: ↑"

    def test_cycle_to_descending(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test clicking sort button twice cycles to descending order."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)
        widget.set_tournaments(sample_tournaments)

        widget._sort_button.click()
        widget._sort_button.click()

        assert widget.sort_order == SortOrder.DESCENDING
        assert widget._sort_button.text() == "Sort: ↓"

    def test_cycle_back_to_default(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test clicking sort button three times cycles back to default."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)
        widget.set_tournaments(sample_tournaments)

        widget._sort_button.click()
        widget._sort_button.click()
        widget._sort_button.click()

        assert widget.sort_order == SortOrder.DEFAULT
        assert widget._sort_button.text() == "Sort: —"

    def test_ascending_sorts_oldest_first(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test ascending order sorts oldest first."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)
        widget.set_tournaments(sample_tournaments)

        widget._sort_button.click()

        first_item = widget._list_widget.item(0)
        assert first_item is not None
        assert "Sunday Million" in first_item.text()

    def test_descending_sorts_newest_first(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test descending order sorts newest first."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)
        widget.set_tournaments(sample_tournaments)

        widget._sort_button.click()
        widget._sort_button.click()

        first_item = widget._list_widget.item(0)
        assert first_item is not None
        assert "Freeroll" in first_item.text()

    def test_default_restores_original_order(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test default order restores original parse order."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)
        widget.set_tournaments(sample_tournaments)

        widget._sort_button.click()
        widget._sort_button.click()
        widget._sort_button.click()

        first_item = widget._list_widget.item(0)
        assert first_item is not None
        assert "Sunday Million" in first_item.text()

    def test_set_tournaments_resets_sort_order(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test setting new tournaments resets sort order to default."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)
        widget.set_tournaments(sample_tournaments)

        widget._sort_button.click()
        assert widget.sort_order == SortOrder.ASCENDING

        widget.set_tournaments(sample_tournaments)
        assert widget.sort_order == SortOrder.DEFAULT
        assert widget._sort_button.text() == "Sort: —"

    def test_tournaments_property_reflects_sorted_order(
        self, qtbot: Any, sample_tournaments: list[Tournament]
    ) -> None:
        """Test tournaments property returns sorted order after sort."""
        widget = TournamentListWidget()
        qtbot.addWidget(widget)
        widget.set_tournaments(sample_tournaments)

        widget._sort_button.click()
        widget._sort_button.click()

        assert widget.tournaments[0].name == "Freeroll"
        assert widget.tournaments[2].name == "Sunday Million"
