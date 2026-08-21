from __future__ import annotations

from collections import Counter

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from models.project import Project
from ui.components.metric_card import MetricCard
from ui.components.page_header import PageHeader
from ui.components.section_header import SectionHeader
from services.pdf_service import PDFService
from services.report_extraction_service import (
    ReportExtractionService,
)


class DocumentsPage(QWidget):
    """
    Central de documentos do processo.

    Responsabilidades:

    - listar todos os PDFs do projeto;
    - exibir o status individual de cada documento;
    - mostrar origem, páginas e resultados extraídos;
    - solicitar a abertura de um documento no visualizador;
    - adicionar, abrir e remover documentos do processo.
    """

    back_requested = Signal()

    # Envia o ID do ProjectDocument selecionado.
    open_document_requested = Signal(int)

    # Solicita inclusão de novos documentos no processo.
    add_documents_requested = Signal()

    def __init__(self):
        super().__init__()

        self.current_project: Project | None = None

        self.pdf_service = PDFService()

        self.extraction_service = (
            ReportExtractionService()
        )

        self.build_ui()

    # =============================================================
    # INTERFACE
    # =============================================================

    def build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        scroll_content = QWidget()
        scroll_content.setObjectName("pageBackground")

        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(34, 22, 34, 34)
        scroll_layout.setSpacing(0)

        content = QWidget()
        content.setObjectName("pageContent")
        content.setMaximumWidth(1320)
        content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(18)

        self.page_header = PageHeader(
            title="Documentos do processo",
            subtitle=(
                "Consulte os relatórios originais, os resultados "
                "extraídos e o status de processamento."
            ),
            metadata="-",
            back_text="← Visão geral",
        )

        self.back_button = self.page_header.back_button
        self.back_button.clicked.connect(
            self.back_requested.emit
        )

        self.project_label = self.page_header.metadata_label

        self.add_button = QPushButton(
            "+ Adicionar documentos"
        )
        self.add_button.setObjectName("primaryButton")
        self.add_button.setMinimumHeight(40)
        self.add_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.add_button.clicked.connect(
            self.add_documents_requested.emit
        )

        self.page_header.add_action(
            self.add_button
        )

        content_layout.addWidget(
            self.page_header
        )

        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(12)

        self.total_documents_group = MetricCard(
            label="Documentos",
            value="0",
            helper_text="PDFs vinculados",
            accent="blue",
        )

        self.analyzed_documents_group = MetricCard(
            label="Analisados",
            value="0",
            helper_text="Processamento concluído",
            accent="navy",
        )

        self.total_pages_group = MetricCard(
            label="Páginas",
            value="0",
            helper_text="Total do processo",
            accent="blue",
        )

        self.characteristics_group = MetricCard(
            label="Características",
            value="0",
            helper_text="Resultados extraídos",
            accent="orange",
        )

        metrics_layout.addWidget(
            self.total_documents_group
        )
        metrics_layout.addWidget(
            self.analyzed_documents_group
        )
        metrics_layout.addWidget(
            self.total_pages_group
        )
        metrics_layout.addWidget(
            self.characteristics_group
        )

        content_layout.addLayout(
            metrics_layout
        )

        self.sources_label = QLabel("")
        self.sources_label.setObjectName(
            "documentSources"
        )
        self.sources_label.setWordWrap(True)
        self.sources_label.hide()

        content_layout.addWidget(
            self.sources_label
        )

        section_header = SectionHeader(
            title="Relatórios originais",
            description=(
                "Cada documento mantém seu próprio PDF, sua extração "
                "e as características identificadas."
            ),
        )

        content_layout.addWidget(
            section_header
        )

        self.documents_container = QWidget()
        self.documents_container.setObjectName(
            "documentsListContainer"
        )

        self.documents_layout = QVBoxLayout(
            self.documents_container
        )
        self.documents_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self.documents_layout.setSpacing(9)

        content_layout.addWidget(
            self.documents_container
        )

        content_row = QHBoxLayout()
        content_row.addStretch(1)
        content_row.addWidget(content, 12)
        content_row.addStretch(1)

        scroll_layout.addLayout(
            content_row
        )
        scroll_layout.addStretch(1)

        self.scroll_area.setWidget(
            scroll_content
        )

        root_layout.addWidget(
            self.scroll_area
        )

    # =============================================================
    # RESUMO
    # =============================================================

    # =============================================================
    # PROJETO
    # =============================================================

    def set_project(
        self,
        project: Project,
    ) -> None:
        self.current_project = project

        self.project_label.setText(
            f"{project.report_id}  ·  {project.name}"
        )

        self.refresh_documents()

    # =============================================================
    # CARREGAMENTO
    # =============================================================

    def refresh_documents(
        self,
    ) -> None:
        self.clear_layout(
            self.documents_layout
        )

        if (
            self.current_project is None
            or self.current_project.id is None
        ):
            self.show_empty_state(
                "O processo não possui um identificador válido."
            )

            self.update_summary(
                documents=[],
                extraction_by_document={},
            )

            return

        try:
            documents = (
                self.pdf_service
                .get_project_documents(
                    self.current_project.id
                )
            )

            extraction_results = (
                self.extraction_service
                .get_project_extractions(
                    self.current_project.id
                )
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao carregar documentos",
                str(error),
            )

            self.show_empty_state(
                "Não foi possível carregar os documentos."
            )

            return

        extraction_by_document = {}

        for (
            extraction,
            characteristics,
        ) in extraction_results:
            if extraction.document_id is None:
                continue

            extraction_by_document[
                extraction.document_id
            ] = (
                extraction,
                characteristics,
            )

        self.update_summary(
            documents=documents,
            extraction_by_document=(
                extraction_by_document
            ),
        )

        if not documents:
            self.show_empty_state(
                "Nenhum documento foi adicionado ao processo."
            )

            return

        for index, document in enumerate(
            documents,
            start=1,
        ):
            extraction_data = None

            if document.id is not None:
                extraction_data = (
                    extraction_by_document.get(
                        document.id
                    )
                )

            card = (
                self.create_document_card(
                    index=index,
                    document=document,
                    extraction_data=(
                        extraction_data
                    ),
                )
            )

            self.documents_layout.addWidget(
                card
            )

    # =============================================================
    # CARD DO DOCUMENTO
    # =============================================================

    def create_document_card(
        self,
        index: int,
        document,
        extraction_data,
    ) -> QFrame:
        card = QFrame()
        card.setObjectName("processDocumentCard")
        card.setMinimumHeight(88)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 13, 16, 13)
        layout.setSpacing(14)

        order_label = QLabel(f"{index:02d}")
        order_label.setObjectName("documentOrder")
        order_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        order_label.setFixedSize(36, 36)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(3)

        file_name = QLabel(
            getattr(
                document,
                "file_name",
                "Documento PDF",
            )
        )
        file_name.setObjectName("cardTitle")
        file_name.setWordWrap(True)

        metadata_parts = []

        source_type = getattr(
            document,
            "source_type",
            None,
        )

        if source_type:
            metadata_parts.append(
                self.format_source_type(
                    source_type
                )
            )

        page_count = int(
            getattr(
                document,
                "page_count",
                0,
            )
            or 0
        )

        metadata_parts.append(
            (
                f"{page_count} página"
                if page_count == 1
                else f"{page_count} páginas"
            )
        )

        specimen = getattr(
            document,
            "specimen_identifier",
            None,
        )

        if specimen:
            metadata_parts.append(
                f"Identificação: {specimen}"
            )

        metadata_label = QLabel(
            " · ".join(metadata_parts)
        )
        metadata_label.setObjectName(
            "cardDescription"
        )
        metadata_label.setWordWrap(True)

        extraction_parts = []

        if extraction_data is not None:
            extraction, characteristics = (
                extraction_data
            )

            if extraction.part_name:
                extraction_parts.append(
                    f"Peça: {extraction.part_name}"
                )

            if extraction.machine_name:
                extraction_parts.append(
                    f"Equipamento: {extraction.machine_name}"
                )

            extraction_parts.append(
                (
                    f"{len(characteristics)} "
                    "características"
                )
            )
        else:
            extraction_parts.append(
                "Extração ainda não disponível"
            )

        extraction_label = QLabel(
            " · ".join(extraction_parts)
        )
        extraction_label.setObjectName(
            "documentExtractionInfo"
        )
        extraction_label.setWordWrap(True)

        info_layout.addWidget(file_name)
        info_layout.addWidget(metadata_label)
        info_layout.addWidget(extraction_label)

        status = getattr(
            document,
            "analysis_status",
            "Pendente",
        )

        status_label = QLabel(
            self.format_status(status)
        )
        status_label.setObjectName(
            self.get_status_object_name(status)
        )

        open_button = QPushButton(
            "Abrir documento"
        )
        open_button.setObjectName("primaryButton")
        open_button.setFixedSize(148, 38)
        open_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        document_id = getattr(
            document,
            "id",
            None,
        )

        open_button.setEnabled(
            document_id is not None
        )

        if document_id is not None:
            open_button.clicked.connect(
                lambda checked=False,
                selected_id=document_id:
                self.open_document_requested.emit(
                    selected_id
                )
            )

        delete_button = QPushButton(
            "Excluir documento"
        )
        delete_button.setObjectName(
            "deleteDocumentButton"
        )
        delete_button.setFixedSize(148, 38)
        delete_button.setStyleSheet(
            """
            QPushButton#deleteDocumentButton {
                background: #FFFFFF;
                border: 1px solid #D9A3A3;
                border-radius: 7px;
                color: #A51D1D;
                padding: 6px 12px;
                font-weight: 600;
            }

            QPushButton#deleteDocumentButton:hover {
                background: #FFF4F4;
                border-color: #C94C4C;
            }

            QPushButton#deleteDocumentButton:pressed {
                background: #FDE7E7;
            }

            QPushButton#deleteDocumentButton:disabled {
                background: #F7F8F9;
                border-color: #D9DEE4;
                color: #A7ADB4;
            }
            """
        )
        delete_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        delete_button.setEnabled(
            document_id is not None
        )

        if document_id is not None:
            delete_button.clicked.connect(
                lambda checked=False,
                selected_id=document_id,
                selected_name=getattr(
                    document,
                    "file_name",
                    "Documento PDF",
                ):
                self.confirm_remove_document(
                    document_id=selected_id,
                    file_name=selected_name,
                )
            )

        action_layout = QVBoxLayout()
        action_layout.setSpacing(8)
        action_layout.setAlignment(
            Qt.AlignmentFlag.AlignRight
            | Qt.AlignmentFlag.AlignVCenter
        )

        action_layout.addWidget(
            status_label,
            0,
            Qt.AlignmentFlag.AlignRight,
        )
        action_layout.addWidget(
            open_button,
            0,
            Qt.AlignmentFlag.AlignRight,
        )
        action_layout.addWidget(
            delete_button,
            0,
            Qt.AlignmentFlag.AlignRight,
        )

        layout.addWidget(
            order_label,
            0,
            Qt.AlignmentFlag.AlignTop,
        )
        layout.addLayout(info_layout, 1)
        layout.addLayout(action_layout)

        return card

    # =============================================================
    # EXCLUSÃO
    # =============================================================

    def confirm_remove_document(
        self,
        *,
        document_id: int,
        file_name: str,
    ) -> None:
        """
        Confirma e executa a remoção lógica do documento.

        O arquivo físico e o histórico permanecem preservados;
        o documento apenas deixa de participar do processo ativo.
        """

        dialog = QMessageBox(
            self
        )
        dialog.setWindowTitle(
            "Excluir documento"
        )
        dialog.setIcon(
            QMessageBox.Icon.Warning
        )
        dialog.setText(
            (
                f'Deseja remover o documento '
                f'"{file_name}" deste processo?'
            )
        )
        dialog.setInformativeText(
            (
                "O registro será preservado para rastreabilidade, "
                "mas o documento deixará de participar do relatório "
                "e dos cálculos ativos."
            )
        )

        cancel_button = dialog.addButton(
            "Cancelar",
            QMessageBox.ButtonRole.RejectRole,
        )

        remove_button = dialog.addButton(
            "Excluir documento",
            QMessageBox.ButtonRole.DestructiveRole,
        )

        remove_button.setStyleSheet(
            """
            QPushButton {
                min-width: 128px;
                min-height: 32px;
                background: #B3261E;
                border: 1px solid #B3261E;
                border-radius: 6px;
                color: white;
                padding: 5px 14px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #982018;
                border-color: #982018;
            }
            """
        )

        cancel_button.setStyleSheet(
            """
            QPushButton {
                min-width: 92px;
                min-height: 32px;
                background: white;
                border: 1px solid #B8C5D1;
                border-radius: 6px;
                color: #17324D;
                padding: 5px 14px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #F4F7FA;
            }
            """
        )

        dialog.setDefaultButton(
            cancel_button
        )

        dialog.exec()

        if (
            dialog.clickedButton()
            is not remove_button
        ):
            return

        try:
            self.pdf_service.document_service.remove_document(
                document_id
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao excluir documento",
                (
                    "Não foi possível remover o documento.\n\n"
                    f"Detalhes: {error}"
                ),
            )
            return

        self.refresh_documents()

        confirmation = QMessageBox(
            self
        )
        confirmation.setWindowTitle(
            "Documento removido"
        )
        confirmation.setIcon(
            QMessageBox.Icon.Information
        )
        confirmation.setText(
            "O documento foi removido do processo."
        )
        confirmation.setInformativeText(
            (
                "O registro permanece preservado para rastreabilidade. "
                "Se havia uma aprovação técnica anterior, ela foi "
                "invalidada e o processo deverá ser revisado novamente."
            )
        )

        ok_button = confirmation.addButton(
            "Entendi",
            QMessageBox.ButtonRole.AcceptRole,
        )
        ok_button.setStyleSheet(
            """
            QPushButton {
                min-width: 92px;
                min-height: 32px;
                background: #0B78C4;
                border: 1px solid #0B78C4;
                border-radius: 6px;
                color: white;
                padding: 5px 14px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #0869AC;
            }
            """
        )

        confirmation.exec()

    # =============================================================
    # RESUMO
    # =============================================================

    def update_summary(
        self,
        documents,
        extraction_by_document: dict,
    ) -> None:
        total_documents = len(
            documents
        )

        analyzed_documents = sum(
            1
            for document in documents
            if (
                str(
                    getattr(
                        document,
                        "analysis_status",
                        "",
                    )
                ).lower()
                in {
                    "concluído",
                    "concluido",
                }
            )
        )

        total_pages = sum(
            int(
                getattr(
                    document,
                    "page_count",
                    0,
                )
                or 0
            )
            for document in documents
        )

        total_characteristics = sum(
            len(
                extraction_data[1]
            )
            for extraction_data
            in extraction_by_document.values()
        )

        self.total_documents_group.set_value(
            str(total_documents)
        )

        self.analyzed_documents_group.set_value(
            str(analyzed_documents)
        )

        self.total_pages_group.set_value(
            str(total_pages)
        )

        self.characteristics_group.set_value(
            str(total_characteristics)
        )

        sources = []

        for document in documents:
            source_type = getattr(
                document,
                "source_type",
                None,
            )

            if not source_type:
                continue

            sources.append(
                self.format_source_type(
                    source_type
                )
            )

        source_counts = Counter(
            sources
        )

        if source_counts:
            source_text = "  ·  ".join(
                (
                    f"{count} {source}"
                    if count > 1
                    else source
                )
                for source, count
                in source_counts.items()
            )

            self.sources_label.setText(
                f"Origens identificadas: {source_text}"
            )

            self.sources_label.show()

        else:
            self.sources_label.clear()

            self.sources_label.hide()

    # =============================================================
    # ESTADO VAZIO
    # =============================================================

    def show_empty_state(
        self,
        message: str,
    ) -> None:
        empty_label = QLabel(
            message
        )

        empty_label.setObjectName(
            "emptyState"
        )

        empty_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        empty_label.setWordWrap(
            True
        )

        self.documents_layout.addWidget(
            empty_label
        )

    # =============================================================
    # FORMATAÇÃO
    # =============================================================

    def format_source_type(
        self,
        source_type: str,
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
                "Origem não identificada",
        }

        return labels.get(
            normalized,
            source_type,
        )

    def format_status(
        self,
        status: str,
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
            status,
        )

    def get_status_object_name(
        self,
        status: str,
    ) -> str:
        normalized = (
            status
            or ""
        ).strip().lower()

        if normalized in {
            "concluído",
            "concluido",
        }:
            return (
                "documentSuccessBadge"
            )

        if normalized == "falha":
            return (
                "documentFailureBadge"
            )

        if normalized == "analisando":
            return (
                "documentProcessingBadge"
            )

        return (
            "documentPendingBadge"
        )

    # =============================================================
    # LIMPEZA
    # =============================================================

    def clear_layout(
        self,
        layout,
    ) -> None:
        while layout.count():
            item = layout.takeAt(
                0
            )

            widget = item.widget()

            child_layout = item.layout()

            if widget is not None:
                widget.setParent(
                    None
                )

                widget.deleteLater()

            elif child_layout is not None:
                self.clear_layout(
                    child_layout
                )