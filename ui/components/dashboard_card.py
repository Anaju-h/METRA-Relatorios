from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class DashboardCard(QFrame):
    """
    Card reutilizável para módulos, resumos e atalhos.
    """

    def __init__(
        self,
        title: str,
        description: str = "",
        value: str = "",
        action_text: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.setObjectName("dashboardCard")
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("cardTitle")
        self.title_label.setWordWrap(True)

        self.description_label = QLabel(description)
        self.description_label.setObjectName("cardDescription")
        self.description_label.setWordWrap(True)
        self.description_label.setVisible(bool(description))

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.description_label)

        self.value_label = QLabel(value)
        self.value_label.setObjectName("dashboardCardValue")
        self.value_label.setVisible(bool(value))

        top_row.addLayout(text_layout, 1)
        top_row.addWidget(self.value_label)

        layout.addLayout(top_row)
        layout.addStretch(1)

        self.action_button = QPushButton(action_text)
        self.action_button.setObjectName("cardButton")
        self.action_button.setVisible(bool(action_text))

        layout.addWidget(self.action_button)

    def set_title(self, value: str) -> None:
        self.title_label.setText(value)

    def set_description(self, value: str) -> None:
        self.description_label.setText(value)
        self.description_label.setVisible(bool(value))

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)
        self.value_label.setVisible(bool(value))

    def set_action_text(self, value: str) -> None:
        self.action_button.setText(value)
        self.action_button.setVisible(bool(value))