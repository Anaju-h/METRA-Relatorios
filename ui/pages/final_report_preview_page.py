from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.components.pdf_viewer import PdfViewer


class FinalReportPreviewPage(QWidget):
    """
    Pré-visualização temporária do relatório técnico.

    O visualizador ocupa praticamente toda a área da página.
    As ações ficam em uma barra compacta própria, sem cabeçalho alto.

    O PDF é explicitamente liberado antes de voltar ou regenerar,
    evitando bloqueio do arquivo temporário no Windows.
    """

    back_requested = Signal()
    regenerate_requested = Signal()
    approve_export_requested = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.pdf_path: Path | None = None

        self.setObjectName(
            "finalReportPreviewPage"
        )

        self.build_ui()

    # =============================================================
    # INTERFACE
    # =============================================================

    def build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        root_layout.setSpacing(
            0
        )

        # ---------------------------------------------------------
        # BARRA SUPERIOR COMPACTA
        # ---------------------------------------------------------

        self.top_bar = QFrame()
        self.top_bar.setObjectName(
            "finalPreviewTopBar"
        )
        self.top_bar.setFixedHeight(
            62
        )

        top_layout = QHBoxLayout(
            self.top_bar
        )
        top_layout.setContentsMargins(
            18,
            10,
            18,
            10,
        )
        top_layout.setSpacing(
            10
        )

        self.back_button = QPushButton(
            "← Voltar e corrigir"
        )
        self.back_button.setObjectName(
            "backButton"
        )
        self.back_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.back_button.clicked.connect(
            self._handle_back_requested
        )

        title_layout = QVBoxLayout()
        title_layout.setSpacing(
            1
        )

        title = QLabel(
            "Pré-visualização do relatório"
        )
        title.setObjectName(
            "finalPreviewTitle"
        )

        self.file_label = QLabel(
            "-"
        )
        self.file_label.setObjectName(
            "finalPreviewFile"
        )
        self.file_label.setWordWrap(
            False
        )

        title_layout.addWidget(
            title
        )
        title_layout.addWidget(
            self.file_label
        )

        self.regenerate_button = QPushButton(
            "Gerar novamente"
        )
        self.regenerate_button.setObjectName(
            "secondaryButton"
        )
        self.regenerate_button.setMinimumHeight(
            40
        )
        self.regenerate_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.regenerate_button.clicked.connect(
            self._handle_regenerate_requested
        )

        self.approve_button = QPushButton(
            "✓  Aprovar e exportar"
        )
        self.approve_button.setObjectName(
            "approveExportButton"
        )
        self.approve_button.setMinimumHeight(
            40
        )
        self.approve_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.approve_button.clicked.connect(
            self.approve_export_requested.emit
        )

        top_layout.addWidget(
            self.back_button
        )
        top_layout.addSpacing(
            6
        )
        top_layout.addLayout(
            title_layout,
            1,
        )
        top_layout.addWidget(
            self.regenerate_button
        )
        top_layout.addWidget(
            self.approve_button
        )

        root_layout.addWidget(
            self.top_bar
        )

        # ---------------------------------------------------------
        # AVISO TEMPORÁRIO
        # ---------------------------------------------------------

        self.notice_bar = QFrame()
        self.notice_bar.setObjectName(
            "previewNoticeBar"
        )
        self.notice_bar.setFixedHeight(
            42
        )

        notice_layout = QHBoxLayout(
            self.notice_bar
        )
        notice_layout.setContentsMargins(
            16,
            7,
            16,
            7,
        )
        notice_layout.setSpacing(
            8
        )

        notice_icon = QLabel(
            "i"
        )
        notice_icon.setObjectName(
            "previewNoticeIcon"
        )
        notice_icon.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        notice_icon.setFixedSize(
            24,
            24,
        )

        notice_text = QLabel(
            "Arquivo temporário para conferência. "
            "O PDF definitivo só será salvo após a aprovação."
        )
        notice_text.setObjectName(
            "previewNoticeText"
        )
        notice_text.setWordWrap(
            False
        )

        notice_layout.addWidget(
            notice_icon
        )
        notice_layout.addWidget(
            notice_text,
            1,
        )

        root_layout.addWidget(
            self.notice_bar
        )

        # ---------------------------------------------------------
        # VISUALIZADOR
        # ---------------------------------------------------------

        self.pdf_viewer = PdfViewer()
        self.pdf_viewer.setObjectName(
            "finalReportPdfViewer"
        )

        root_layout.addWidget(
            self.pdf_viewer,
            1,
        )

        self._update_action_state()

    # =============================================================
    # DEFINIR PDF
    # =============================================================

    def set_pdf(
        self,
        pdf_path: str | Path,
    ) -> None:
        path = Path(
            pdf_path
        )

        if not path.exists():
            raise FileNotFoundError(
                "A pré-visualização gerada não foi encontrada."
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                "O arquivo selecionado não é um PDF."
            )

        self.pdf_path = (
            path
        )

        self.file_label.setText(
            path.name
        )

        self.pdf_viewer.set_pdf(
            path
        )

        self._update_action_state()

    # =============================================================
    # AÇÕES
    # =============================================================

    def _handle_back_requested(
        self,
    ) -> None:
        """
        Libera completamente o arquivo temporário antes de retornar
        para a tela de preparação do relatório.
        """

        self.clear_preview()

        self.back_requested.emit()

    def _handle_regenerate_requested(
        self,
    ) -> None:
        """
        Fecha apenas o handle do PDF atual antes de solicitar a
        regeneração. O caminho permanece armazenado nesta página,
        pois o MainWindow reutiliza o mesmo arquivo temporário.
        """

        self.pdf_viewer.close_document()

        self.regenerate_requested.emit()

    # =============================================================
    # ESTADO
    # =============================================================

    def set_exporting(
        self,
        exporting: bool,
    ) -> None:
        available = (
            self.pdf_path is not None
            and self.pdf_path.exists()
        )

        self.back_button.setEnabled(
            not exporting
        )

        self.regenerate_button.setEnabled(
            available
            and not exporting
        )

        self.approve_button.setEnabled(
            available
            and not exporting
        )

        self.approve_button.setText(
            (
                "Exportando..."
                if exporting
                else "✓  Aprovar e exportar"
            )
        )

    def _update_action_state(
        self,
    ) -> None:
        available = (
            self.pdf_path is not None
            and self.pdf_path.exists()
        )

        self.regenerate_button.setEnabled(
            available
        )

        self.approve_button.setEnabled(
            available
        )

    # =============================================================
    # LIMPEZA
    # =============================================================

    def clear_preview(
        self,
    ) -> None:
        """
        Fecha o documento carregado e limpa o estado visual da prévia.
        """

        self.pdf_viewer.clear()

        self.pdf_path = None

        self.file_label.setText(
            "-"
        )

        self._update_action_state()