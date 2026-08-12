from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout, QWidget


class PDFDropArea(QFrame):
    files_dropped = Signal(list)
    select_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("pdfDropArea")
        self.setAcceptDrops(True)
        self.setMinimumHeight(165)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel("PDF")
        icon.setObjectName("dropPdfIcon")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Arraste um ou mais relatórios PDF")
        title.setObjectName("uploadTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        description = QLabel(
            "Solte os arquivos nesta área ou selecione-os manualmente."
        )
        description.setObjectName("uploadDescription")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)

        button = QPushButton("Selecionar arquivos")
        button.setObjectName("primaryButton")
        button.setMinimumHeight(44)
        button.setMinimumWidth(180)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(self.select_requested.emit)

        layout.addStretch()
        layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addSpacing(8)
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._extract_pdf_paths(event):
            event.acceptProposedAction()
            self._set_drag_active(True)
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        self._set_drag_active(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        self._set_drag_active(False)
        file_paths = self._extract_pdf_paths(event)

        if not file_paths:
            event.ignore()
            return

        self.files_dropped.emit(file_paths)
        event.acceptProposedAction()

    def _extract_pdf_paths(self, event) -> list[str]:
        mime_data = event.mimeData()

        if not mime_data.hasUrls():
            return []

        result: list[str] = []

        for url in mime_data.urls():
            path = Path(url.toLocalFile())

            if path.is_file() and path.suffix.lower() == ".pdf":
                result.append(str(path))

        return result

    def _set_drag_active(self, active: bool) -> None:
        self.setProperty("dragActive", active)
        self.style().unpolish(self)
        self.style().polish(self)