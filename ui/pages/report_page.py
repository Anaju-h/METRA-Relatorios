from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.project import Project
from services.pdf_service import PDFService
from services.report_extraction_service import ReportExtractionService
from ui.components.page_header import PageHeader
from ui.components.pdf_viewer import PdfViewer


class ReportPage(QWidget):
    """
    Visualizador do documento original do processo.

    Usa o mesmo PdfViewer da pré-visualização do relatório final.
    Assim, zoom, miniaturas, navegação, cache e redimensionamento
    permanecem idênticos nas duas telas.
    """

    back_requested = Signal()
    extraction_requested = Signal()

    def __init__(self):
        super().__init__()

        self.current_project: Project | None = None
        self.current_document = None
        self.current_document_id: int | None = None

        self.pdf_service = PDFService()
        self.extraction_service = ReportExtractionService()

        self.build_ui()

    # INTERFACE

    def build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(
            18,
            14,
            18,
            18,
        )
        root_layout.setSpacing(9)

        self.page_header = PageHeader(
            title="Visualizador do documento",
            subtitle=(
                "Consulte o relatório original e os dados "
                "extraídos deste documento."
            ),
            metadata="-",
            back_text="← Documentos",
        )

        self.page_header.back_button.clicked.connect(
            self.back_requested.emit
        )

        self.analyze_button = QPushButton(
            "Reanalisar documento"
        )
        self.analyze_button.setObjectName(
            "primaryButton"
        )
        self.analyze_button.setMinimumHeight(40)
        self.analyze_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.analyze_button.clicked.connect(
            self.analyze_current_document
        )

        self.page_header.add_action(
            self.analyze_button
        )

        root_layout.addWidget(
            self.page_header
        )

        self.info_card = QFrame()
        self.info_card.setObjectName(
            "dashboardCard"
        )

        info_layout = QHBoxLayout(
            self.info_card
        )
        info_layout.setContentsMargins(
            18,
            10,
            18,
            10,
        )
        info_layout.setSpacing(22)

        file_group = self.create_info_group(
            "Arquivo",
            "-",
        )
        self.file_name_value = (
            file_group.value_label
        )

        pages_group = self.create_info_group(
            "Páginas",
            "-",
        )
        self.pages_value = (
            pages_group.value_label
        )

        source_group = self.create_info_group(
            "Origem",
            "-",
        )
        self.source_value = (
            source_group.value_label
        )

        status_group = self.create_info_group(
            "Status",
            "-",
        )
        self.analysis_status_value = (
            status_group.value_label
        )

        info_layout.addWidget(
            file_group,
            2,
        )
        info_layout.addWidget(
            pages_group
        )
        info_layout.addWidget(
            source_group
        )
        info_layout.addWidget(
            status_group
        )

        root_layout.addWidget(
            self.info_card
        )

        self.extraction_card = QFrame()
        self.extraction_card.setObjectName(
            "dashboardCard"
        )

        extraction_layout = QHBoxLayout(
            self.extraction_card
        )
        extraction_layout.setContentsMargins(
            18,
            10,
            18,
            10,
        )
        extraction_layout.setSpacing(14)

        extraction_text_layout = (
            QVBoxLayout()
        )
        extraction_text_layout.setSpacing(2)

        extraction_title = QLabel(
            "Extração do documento"
        )
        extraction_title.setObjectName(
            "cardTitle"
        )

        self.extraction_status = QLabel(
            "Dados ainda não analisados."
        )
        self.extraction_status.setObjectName(
            "cardDescription"
        )
        self.extraction_status.setWordWrap(
            True
        )

        extraction_text_layout.addWidget(
            extraction_title
        )
        extraction_text_layout.addWidget(
            self.extraction_status
        )

        self.review_button = QPushButton(
            "Revisar dados"
        )
        self.review_button.setObjectName(
            "cardButton"
        )
        self.review_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.review_button.clicked.connect(
            self.extraction_requested.emit
        )

        extraction_layout.addLayout(
            extraction_text_layout,
            1,
        )
        extraction_layout.addWidget(
            self.review_button
        )

        root_layout.addWidget(
            self.extraction_card
        )

        self.pdf_viewer = PdfViewer()

        root_layout.addWidget(
            self.pdf_viewer,
            1,
        )

        self.analyze_button.setEnabled(
            False
        )
        self.review_button.setEnabled(
            False
        )

    # GRUPO DE INFORMAÇÃO

    def create_info_group(
        self,
        label: str,
        value: str,
    ) -> QFrame:
        group = QFrame()

        layout = QVBoxLayout(
            group
        )
        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        layout.setSpacing(2)

        label_widget = QLabel(
            label
        )
        label_widget.setObjectName(
            "dataLabel"
        )

        value_widget = QLabel(
            value
        )
        value_widget.setObjectName(
            "dataValue"
        )
        value_widget.setWordWrap(
            True
        )

        layout.addWidget(
            label_widget
        )
        layout.addWidget(
            value_widget
        )

        group.value_label = (
            value_widget
        )

        return group


    # DEFINIR DOCUMENTO

    def set_document(
        self,
        project: Project,
        document_id: int,
    ) -> None:
        self.current_project = project
        self.current_document_id = (
            document_id
        )

        document = (
            self.pdf_service
            .document_service
            .get_document(
                document_id
            )
        )

        if document is None:
            raise FileNotFoundError(
                (
                    "O documento selecionado "
                    "não foi encontrado."
                )
            )

        self.current_document = document

        self.page_header.set_metadata(
            (
                f"{project.report_id} "
                f"· {project.name}"
            )
        )

        document_name = (
            document.file_name
            or document.stored_name
            or "Documento PDF"
        )

        total_pages = int(
            document.page_count
            or 0
        )

        self.file_name_value.setText(
            document_name
        )
        self.pages_value.setText(
            str(
                total_pages
            )
        )
        self.source_value.setText(
            self.format_source_type(
                document.source_type
            )
        )
        self.analysis_status_value.setText(
            self.format_status(
                document.analysis_status
            )
        )

        self.pdf_viewer.set_document_source(
            document_name=document_name,
            page_count=total_pages,
            render_callback=(
                self._render_document_page
            ),
            source_id=(
                f"document:{document_id}"
            ),
        )

        self.refresh_extraction_summary()

        self.analyze_button.setEnabled(
            True
        )

    def _render_document_page(
        self,
        page_index: int,
        zoom: float,
    ) -> bytes:
        if self.current_document_id is None:
            raise RuntimeError(
                "Nenhum documento foi selecionado."
            )

        return (
            self.pdf_service
            .render_document_page(
                document_id=(
                    self.current_document_id
                ),
                page_index=page_index,
                zoom=zoom,
            )
        )

    # EXTRAÇÃO

    def analyze_current_document(
        self,
    ) -> None:
        if (
            self.current_project is None
            or self.current_project.id is None
            or self.current_document_id is None
        ):
            return

        self.analyze_button.setEnabled(
            False
        )
        self.analyze_button.setText(
            "Analisando..."
        )

        try:
            (
                self.extraction_service
                .analyze_document(
                    project_id=(
                        self.current_project.id
                    ),
                    document_id=(
                        self.current_document_id
                    ),
                )
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro na análise",
                str(
                    error
                ),
            )
            return

        finally:
            self.analyze_button.setEnabled(
                True
            )
            self.analyze_button.setText(
                "Reanalisar documento"
            )

        document = (
            self.pdf_service
            .document_service
            .get_document(
                self.current_document_id
            )
        )

        if document is not None:
            self.current_document = document

            self.source_value.setText(
                self.format_source_type(
                    document.source_type
                )
            )

            self.analysis_status_value.setText(
                self.format_status(
                    document.analysis_status
                )
            )

        self.refresh_extraction_summary()

        QMessageBox.information(
            self,
            "Análise concluída",
            (
                "Os dados deste documento "
                "foram analisados novamente."
            ),
        )

    def refresh_extraction_summary(
        self,
    ) -> None:
        if self.current_document_id is None:
            self.extraction_status.setText(
                "Dados ainda não analisados."
            )
            self.review_button.setEnabled(
                False
            )
            return

        try:
            extraction, characteristics = (
                self.extraction_service
                .get_document_extraction(
                    self.current_document_id
                )
            )

        except Exception as error:
            self.extraction_status.setText(
                (
                    "Não foi possível carregar "
                    f"a extração: {error}"
                )
            )
            self.review_button.setEnabled(
                False
            )
            return

        if extraction is None:
            self.extraction_status.setText(
                "Dados ainda não analisados."
            )
            self.review_button.setEnabled(
                False
            )
            return

        review_status = (
            "Revisado"
            if extraction.reviewed
            else "Aguardando revisão"
        )

        details = [
            extraction.source_type,
            (
                f"{len(characteristics)} "
                "características"
            ),
            review_status,
        ]

        if extraction.part_name:
            details.append(
                (
                    "Peça: "
                    f"{extraction.part_name}"
                )
            )

        if extraction.machine_name:
            details.append(
                (
                    "Equipamento: "
                    f"{extraction.machine_name}"
                )
            )

        self.extraction_status.setText(
            " · ".join(
                details
            )
        )

        self.review_button.setEnabled(
            True
        )

    # FORMATAÇÃO

    def format_source_type(
        self,
        source_type: str | None,
    ) -> str:
        normalized = (
            source_type
            or "UNKNOWN"
        ).upper()

        labels = {
            "CALYPSO":
                "CALYPSO",

            "ZEISS_INSPECT":
                "ZEISS INSPECT",

            "UNKNOWN":
                "Não identificada",
        }

        return labels.get(
            normalized,
            source_type
            or "Não identificada",
        )

    def format_status(
        self,
        status: str | None,
    ) -> str:
        normalized = (
            status
            or "Pendente"
        ).strip().lower()

        labels = {
            "concluído":
                "Analisado",

            "concluido":
                "Analisado",

            "analisando":
                "Analisando",

            "falha":
                "Falha",

            "pendente":
                "Pendente",
        }

        return labels.get(
            normalized,
            status
            or "Pendente",
        )

    # LIMPEZA
    def clear_document(
        self,
    ) -> None:
        self.current_project = None
        self.current_document = None
        self.current_document_id = None

        self.file_name_value.setText(
            "-"
        )
        self.pages_value.setText(
            "-"
        )
        self.source_value.setText(
            "-"
        )
        self.analysis_status_value.setText(
            "-"
        )

        self.extraction_status.setText(
            "Dados ainda não analisados."
        )

        self.review_button.setEnabled(
            False
        )
        self.analyze_button.setEnabled(
            False
        )

        self.pdf_viewer.clear()