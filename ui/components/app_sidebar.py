from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class AppSidebar(QFrame):
    """
    Navegação global do METRA.

    Início e Processos ficam sempre disponíveis. Os módulos técnicos
    dependem de um processo aberto.
    """

    home_requested = Signal()
    processes_requested = Signal()
    overview_requested = Signal()
    documents_requested = Signal()
    characteristics_requested = Signal()
    measurement_requested = Signal()
    images_requested = Signal()
    technical_control_requested = Signal()
    final_report_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self.setObjectName("appSidebar")
        self.setFixedWidth(168)
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Expanding,
        )

        self.buttons: dict[str, QPushButton] = {}

        self._build_ui()
        self.set_project_available(False)
        self.set_active("home")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 18, 10, 14)
        layout.setSpacing(6)

        navigation_label = QLabel("NAVEGAÇÃO")
        navigation_label.setObjectName("sidebarSectionLabel")
        layout.addWidget(navigation_label)

        self._add_button(
            layout,
            key="home",
            text="⌂  Início",
            callback=self.home_requested.emit,
        )

        self._add_button(
            layout,
            key="processes",
            text="▤  Processos",
            callback=self.processes_requested.emit,
        )

        layout.addSpacing(10)

        project_label = QLabel("PROCESSO ABERTO")
        project_label.setObjectName("sidebarSectionLabel")
        layout.addWidget(project_label)

        self._add_button(
            layout,
            key="overview",
            text="▦  Visão geral",
            callback=self.overview_requested.emit,
        )
        self._add_button(
            layout,
            key="documents",
            text="▤  Documentos",
            callback=self.documents_requested.emit,
        )
        self._add_button(
            layout,
            key="characteristics",
            text="☷  Características",
            callback=self.characteristics_requested.emit,
        )
        self._add_button(
            layout,
            key="measurement",
            text="⌁  Medição",
            callback=self.measurement_requested.emit,
        )
        self._add_button(
            layout,
            key="images",
            text="▧  Imagens",
            callback=self.images_requested.emit,
        )
        self._add_button(
            layout,
            key="technical",
            text="◉  Controle técnico",
            callback=self.technical_control_requested.emit,
        )
        self._add_button(
            layout,
            key="final_report",
            text="▥  Relatório final",
            callback=self.final_report_requested.emit,
        )

        layout.addStretch(1)

        footer = QLabel("METRA  •  v1.0")
        footer.setObjectName("sidebarFooter")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(footer)

    def _add_button(
        self,
        layout: QVBoxLayout,
        *,
        key: str,
        text: str,
        callback,
    ) -> None:
        button = QPushButton(text)
        button.setObjectName("sidebarButton")
        button.setProperty("active", False)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setMinimumHeight(44)
        button.clicked.connect(callback)

        self.buttons[key] = button
        layout.addWidget(button)

    def set_project_available(
        self,
        available: bool,
    ) -> None:
        always_available = {
            "home",
            "processes",
        }

        for key, button in self.buttons.items():
            if key in always_available:
                button.setEnabled(True)
                continue

            button.setEnabled(available)

    def set_active(
        self,
        key: str,
    ) -> None:
        for button_key, button in self.buttons.items():
            is_active = button_key == key
            button.setProperty("active", is_active)

            button.style().unpolish(button)
            button.style().polish(button)
            button.update()