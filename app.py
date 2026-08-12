import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from database.setup import initialize_database
from ui.main_window import MainWindow


def load_stylesheet(app: QApplication) -> None:
    base_dir = Path(__file__).resolve().parent
    stylesheet_path = (
        base_dir
        / "assets"
        / "styles"
        / "app.qss"
    )

    if stylesheet_path.exists():
        with open(
            stylesheet_path,
            "r",
            encoding="utf-8",
        ) as file:
            app.setStyleSheet(
                file.read()
            )


def main() -> None:
    app = QApplication(sys.argv)

    app.setApplicationName("MetroReport")
    app.setOrganizationName("SENAI")

    load_stylesheet(app)

    initialize_database()

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()