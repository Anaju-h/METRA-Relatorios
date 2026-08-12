from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class SectionHeader(QWidget):
    """
    Cabeçalho de seção reutilizável.

    Mantém títulos, descrições e ações com a mesma
    hierarquia visual em todas as páginas.
    """

    def __init__(
        self,
        title: str,
        description: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.setObjectName("sectionHeader")
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("sectionTitle")
        self.title_label.setWordWrap(True)

        self.description_label = QLabel(description)
        self.description_label.setObjectName(
            "sectionDescription"
        )
        self.description_label.setWordWrap(True)
        self.description_label.setVisible(
            bool(description)
        )

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(
            self.description_label
        )

        self.actions_widget = QWidget()
        self.actions_widget.setObjectName(
            "sectionHeaderActions"
        )

        self.actions_layout = QHBoxLayout(
            self.actions_widget
        )
        self.actions_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self.actions_layout.setSpacing(8)
        self.actions_layout.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        layout.addLayout(text_layout, 1)
        layout.addWidget(
            self.actions_widget,
            0,
            Qt.AlignmentFlag.AlignVCenter,
        )

    def add_action(self, widget: QWidget) -> None:
        self.actions_layout.addWidget(widget)

    def set_title(self, value: str) -> None:
        self.title_label.setText(value)

    def set_description(self, value: str) -> None:
        self.description_label.setText(value)
        self.description_label.setVisible(
            bool(value)
        )