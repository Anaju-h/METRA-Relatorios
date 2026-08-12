from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)


class MetricCard(QFrame):
    def __init__(
        self,
        label: str,
        value: str = "0",
        helper_text: str = "",
        accent: str = "blue",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.setObjectName("metricCard")
        self.setProperty("accent", accent)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )
        self.setMinimumHeight(96)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 15, 18, 15)
        layout.setSpacing(3)

        self.label_widget = QLabel(label, self)
        self.label_widget.setObjectName("metricLabel")

        self.value_widget = QLabel(value, self)
        self.value_widget.setObjectName("metricValue")

        self.helper_widget = QLabel(helper_text, self)
        self.helper_widget.setObjectName("metricHelper")
        self.helper_widget.setWordWrap(True)

        layout.addWidget(self.label_widget)
        layout.addWidget(self.value_widget)
        layout.addWidget(self.helper_widget)

        self.helper_widget.setVisible(bool(helper_text))

    def set_value(self, value: str) -> None:
        self.value_widget.setText(str(value))

    def set_helper_text(self, value: str) -> None:
        self.helper_widget.setText(value)
        self.helper_widget.setVisible(bool(value))

    def set_accent(self, value: str) -> None:
        self.setProperty("accent", value)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()