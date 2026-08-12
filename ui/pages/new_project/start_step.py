from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ui.components.page_header import PageHeader
from ui.components.step_indicator import StepIndicator


class ProjectStartStep(QWidget):
    back_requested = Signal()
    import_requested = Signal()
    manual_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("pageBackground")
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(34, 22, 34, 34)

        content = QWidget()
        content.setObjectName("pageContent")
        content.setMaximumWidth(1120)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        self.page_header = PageHeader(
            title="Novo processo",
            subtitle=(
                "Escolha como deseja iniciar. O METRA pode analisar "
                "um ou vários relatórios PDF ou criar o processo manualmente."
            ),
            back_text="← Voltar",
        )
        self.page_header.back_button.clicked.connect(
            self.back_requested.emit
        )
        layout.addWidget(self.page_header)

        self.step_indicator = StepIndicator(
            ["Início", "Documentos", "Revisão", "Criar"],
            current_step=0,
        )
        layout.addWidget(self.step_indicator)

        cards = QHBoxLayout()
        cards.setSpacing(14)

        import_card, import_button = self._create_card(
            icon="PDF",
            title="Importar relatórios",
            description=(
                "Adicione um ou vários PDFs de uma peça única "
                "ou de diferentes unidades pertencentes ao mesmo lote."
            ),
            button_text="Adicionar relatórios PDF",
            button_object_name="primaryButton",
            recommended=True,
        )
        import_button.clicked.connect(self.import_requested.emit)

        manual_card, manual_button = self._create_card(
            icon="✎",
            title="Criar manualmente",
            description=(
                "Use este caminho quando o processo precisar ser criado "
                "antes da medição ou quando ainda não houver relatórios PDF."
            ),
            button_text="Iniciar sem relatórios",
            button_object_name="secondaryButton",
            recommended=False,
        )
        manual_button.clicked.connect(self.manual_requested.emit)

        cards.addWidget(import_card)
        cards.addWidget(manual_card)
        layout.addLayout(cards)
        layout.addStretch()

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(content, 10)
        row.addStretch()
        root_layout.addLayout(row)

    def _create_card(
        self,
        *,
        icon: str,
        title: str,
        description: str,
        button_text: str,
        button_object_name: str,
        recommended: bool,
    ) -> tuple[QFrame, QPushButton]:
        card = QFrame()
        card.setObjectName("startOptionCard")
        card.setProperty("recommended", recommended)
        card.setMinimumHeight(230)
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(10)

        if recommended:
            label = QLabel("RECOMENDADO")
            label.setObjectName("recommendedLabel")
            layout.addWidget(label)

        icon_label = QLabel(icon)
        icon_label.setObjectName("startOptionIcon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(52, 52)

        title_label = QLabel(title)
        title_label.setObjectName("formSectionTitle")

        description_label = QLabel(description)
        description_label.setObjectName("formSectionDescription")
        description_label.setWordWrap(True)

        button = QPushButton(button_text)
        button.setObjectName(button_object_name)
        button.setMinimumHeight(42)
        button.setCursor(Qt.CursorShape.PointingHandCursor)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addStretch()
        layout.addWidget(button)

        return card, button