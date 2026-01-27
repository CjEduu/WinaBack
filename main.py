"""WinaBack - Poker Tournament Replayer application entry point."""

import sys

from PyQt6.QtWidgets import QApplication

from src.gui import MainWindow


def main() -> None:
    """Launch the WinaBack application."""
    app = QApplication(sys.argv)
    app.setApplicationName("WinaBack")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
