from abc import ABC, abstractmethod
from pathlib import Path

from src.parser.models import Tournament


class Parser(ABC):
    """Abstract base class for poker hand history parsers.

    Implement this interface to add support for new poker sites.
    """

    @abstractmethod
    def parse_file(self, file_path: Path) -> Tournament:
        """Parse a hand history file and return a Tournament object.

        Args:
            file_path: Path to the hand history file.

        Returns:
            Tournament object containing all parsed hands.

        Raises:
            ParseError: If the file cannot be parsed.
        """
        ...

    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if this parser can handle the given file.

        Args:
            file_path: Path to the hand history file.

        Returns:
            True if this parser can handle the file format.
        """
        ...


class ParseError(Exception):
    """Raised when a hand history file cannot be parsed."""
