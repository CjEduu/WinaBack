from src.parser import Parser
from src.parser.winamax import WinamaxParser


def test_winamax_parser_implements_parser_interface() -> None:
    """Verify WinamaxParser implements the Parser ABC."""
    parser = WinamaxParser()
    assert isinstance(parser, Parser)


def test_parser_interface_has_required_methods() -> None:
    """Verify the Parser interface defines required methods."""
    assert hasattr(Parser, "parse_file")
    assert hasattr(Parser, "can_parse")


def test_winamax_parser_has_parse_file_method() -> None:
    """WinamaxParser has parse_file method."""
    parser = WinamaxParser()
    assert callable(getattr(parser, "parse_file", None))


def test_winamax_parser_has_can_parse_method() -> None:
    """WinamaxParser has can_parse method."""
    parser = WinamaxParser()
    assert callable(getattr(parser, "can_parse", None))
