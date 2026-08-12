from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget,
)


class PageHeader(QWidget):
    def __init__(
        self,
        title: str,
        subtitle: str = "",
        metadata: str = "",
        back_text: str = "",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.setObjectName("pageHeader")
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(8)

        if back_text:
            self.back_button = QPushButton(back_text, self)
            self.back_button.setObjectName("backButton")
            self.back_button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )
            root_layout.addWidget(
                self.back_button,
                0,
                Qt.AlignmentFlag.AlignLeft,
            )
        else:
            self.back_button = None

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(24)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(5)

        self.title_label = QLabel(title, self)
        self.title_label.setObjectName("pageTitle")
        self.title_label.setWordWrap(True)

        self.subtitle_label = QLabel(subtitle, self)
        self.subtitle_label.setObjectName("pageSubtitle")
        self.subtitle_label.setWordWrap(True)

        self.metadata_label = QLabel(metadata, self)
        self.metadata_label.setObjectName("projectMeta")
        self.metadata_label.setWordWrap(True)

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.subtitle_label)
        text_layout.addWidget(self.metadata_label)

        self.subtitle_label.setVisible(bool(subtitle))
        self.metadata_label.setVisible(bool(metadata))

        self.actions_widget = QWidget(self)
        self.actions_widget.setObjectName("pageHeaderActions")

        self.actions_layout = QHBoxLayout(self.actions_widget)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(10)
        self.actions_layout.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignTop
        )

        content_row.addLayout(text_layout, 1)
        content_row.addWidget(
            self.actions_widget,
            0,
            Qt.AlignmentFlag.AlignTop,
        )

        root_layout.addLayout(content_row)

    def add_action(self, widget: QWidget) -> None:
        self.actions_layout.addWidget(widget)

    def set_title(self, value: str) -> None:
        self.title_label.setText(value)

    def set_subtitle(self, value: str) -> None:
        self.subtitle_label.setText(value)
        self.subtitle_label.setVisible(bool(value))

    def set_metadata(self, value: str) -> None:
        self.metadata_label.setText(value)
        self.metadata_label.setVisible(bool(value))