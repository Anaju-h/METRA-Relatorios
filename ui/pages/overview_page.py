from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from models.project import Project
from services.image_service import ImageService
from services.measurement_service import MeasurementService
from services.pdf_service import PDFService
from services.report_extraction_service import (
    ReportExtractionService,
)
from services.report_templates.template_catalog import (
    get_template_definition,
)
from services.technical_control_service import (
    TechnicalControlService,
)
from ui.components.metric_card import MetricCard
from ui.components.section_header import SectionHeader


class OverviewPage(QWidget):
    """
    Visão geral do processo.

    Consolida a identidade técnica do processo, o template,
    o andamento dos módulos e os principais indicadores.
    """

    home_requested = Signal()
    report_requested = Signal()
    characteristics_requested = Signal()
    measurement_requested = Signal()
    images_requested = Signal()
    technical_control_requested = Signal()
    final_report_requested = Signal()

    def __init__(self):
        super().__init__()

        self.current_project: Project | None = None

        self.pdf_service = PDFService()
        self.extraction_service = ReportExtractionService()
        self.measurement_service = MeasurementService()
        self.image_service = ImageService()
        self.technical_control_service = TechnicalControlService()

        self.build_ui()

    # INTERFACE

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
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        scroll_content = QWidget()
        scroll_content.setObjectName("pageBackground")

        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(34, 22, 34, 34)
        scroll_layout.setSpacing(0)

        central_content = QWidget()
        central_content.setObjectName("pageContent")
        central_content.setMaximumWidth(1320)
        central_content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        central_layout = QVBoxLayout(central_content)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(18)

        # TOPO

        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        self.home_button = QPushButton("← Processos")
        self.home_button.setObjectName("backButton")
        self.home_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.home_button.clicked.connect(
            self.home_requested.emit
        )

        self.status_label = QLabel("Em edição")
        self.status_label.setObjectName("statusBadge")

        self.version_label = QLabel("V1.0")
        self.version_label.setObjectName("versionBadge")

        top_row.addWidget(self.home_button)
        top_row.addStretch()
        top_row.addWidget(self.status_label)
        top_row.addWidget(self.version_label)

        central_layout.addLayout(top_row)

        # IDENTIDADE

        identity_card = QFrame()
        identity_card.setObjectName("overviewIdentityCard")

        identity_layout = QVBoxLayout(identity_card)
        identity_layout.setContentsMargins(24, 18, 24, 18)
        identity_layout.setSpacing(6)

        self.report_id_label = QLabel("MET-0000-0000")
        self.report_id_label.setObjectName("projectId")

        self.project_name_label = QLabel("Processo")
        self.project_name_label.setObjectName(
            "overviewProjectTitle"
        )
        self.project_name_label.setWordWrap(True)

        identity_meta = QHBoxLayout()
        identity_meta.setSpacing(12)

        self.template_label = QLabel("-")
        self.template_label.setObjectName("projectMeta")

        self.equipment_inline_label = QLabel("-")
        self.equipment_inline_label.setObjectName(
            "overviewEquipmentBadge"
        )

        identity_meta.addWidget(self.template_label)
        identity_meta.addStretch()
        identity_meta.addWidget(
            self.equipment_inline_label
        )

        dates_row = QHBoxLayout()
        dates_row.setSpacing(18)

        self.created_label = QLabel("Criado em: -")
        self.created_label.setObjectName("projectMeta")

        self.updated_label = QLabel("Atualizado em: -")
        self.updated_label.setObjectName("projectMeta")

        dates_row.addWidget(self.created_label)
        dates_row.addWidget(self.updated_label)
        dates_row.addStretch()

        identity_layout.addWidget(self.report_id_label)
        identity_layout.addWidget(self.project_name_label)
        identity_layout.addLayout(identity_meta)
        identity_layout.addLayout(dates_row)

        central_layout.addWidget(identity_card)

        # MÉTRICAS

        metrics_layout = QGridLayout()
        metrics_layout.setHorizontalSpacing(12)
        metrics_layout.setVerticalSpacing(12)

        self.documents_metric = MetricCard(
            "Documentos",
            "0",
            "PDFs do processo",
            "blue",
        )
        self.characteristics_metric = MetricCard(
            "Características",
            "0",
            "Resultados identificados",
            "navy",
        )
        self.images_metric = MetricCard(
            "Imagens",
            "0",
            "Registros adicionados",
            "blue",
        )
        self.pending_metric = MetricCard(
            "Pendências",
            "0",
            "Etapas para revisar",
            "orange",
        )

        metrics_layout.addWidget(
            self.documents_metric,
            0,
            0,
        )
        metrics_layout.addWidget(
            self.characteristics_metric,
            0,
            1,
        )
        metrics_layout.addWidget(
            self.images_metric,
            0,
            2,
        )
        metrics_layout.addWidget(
            self.pending_metric,
            0,
            3,
        )

        for column in range(4):
            metrics_layout.setColumnStretch(
                column,
                1,
            )

        central_layout.addLayout(metrics_layout)

        # RESUMO TÉCNICO

        technical_card = QFrame()
        technical_card.setObjectName("overviewDetailsCard")

        technical_layout = QVBoxLayout(technical_card)
        technical_layout.setContentsMargins(
            20,
            16,
            20,
            16,
        )
        technical_layout.setSpacing(12)

        technical_title = QLabel("Resumo técnico")
        technical_title.setObjectName("formSectionTitle")

        technical_grid = QGridLayout()
        technical_grid.setHorizontalSpacing(36)
        technical_grid.setVerticalSpacing(8)

        self.inspection_type_value = self.add_data_field(
            technical_grid,
            "Tipo de inspeção",
            0,
            0,
        )
        self.analysis_mode_value = self.add_data_field(
            technical_grid,
            "Modo da análise",
            0,
            1,
        )
        self.template_value = self.add_data_field(
            technical_grid,
            "Template",
            0,
            2,
        )
        self.template_version_value = self.add_data_field(
            technical_grid,
            "Versão do template",
            0,
            3,
        )

        self.quantity_value = self.add_data_field(
            technical_grid,
            "Quantidade",
            2,
            0,
        )
        self.technology_value = self.add_data_field(
            technical_grid,
            "Tecnologia",
            2,
            1,
        )
        self.equipment_value = self.add_data_field(
            technical_grid,
            "Equipamento principal",
            2,
            2,
        )
        self.status_value = self.add_data_field(
            technical_grid,
            "Situação",
            2,
            3,
        )

        for column in range(4):
            technical_grid.setColumnStretch(
                column,
                1,
            )

        technical_layout.addWidget(technical_title)
        technical_layout.addLayout(technical_grid)

        central_layout.addWidget(technical_card)

        # IDENTIFICAÇÃO DA PEÇA

        piece_card = QFrame()
        piece_card.setObjectName("overviewDetailsCard")

        piece_layout = QVBoxLayout(piece_card)
        piece_layout.setContentsMargins(
            20,
            16,
            20,
            16,
        )
        piece_layout.setSpacing(12)

        piece_title = QLabel("Identificação da peça")
        piece_title.setObjectName("formSectionTitle")

        piece_grid = QGridLayout()
        piece_grid.setHorizontalSpacing(36)
        piece_grid.setVerticalSpacing(8)

        self.part_value = self.add_data_field(
            piece_grid,
            "Peça ou modelo",
            0,
            0,
        )
        self.code_value = self.add_data_field(
            piece_grid,
            "Código da peça",
            0,
            1,
        )
        self.client_value = self.add_data_field(
            piece_grid,
            "Cliente",
            0,
            2,
        )
        self.description_value = self.add_data_field(
            piece_grid,
            "Descrição",
            0,
            3,
        )

        for column in range(4):
            piece_grid.setColumnStretch(
                column,
                1,
            )

        piece_layout.addWidget(piece_title)
        piece_layout.addLayout(piece_grid)

        central_layout.addWidget(piece_card)

        # ANDAMENTO

        progress_card = QFrame()
        progress_card.setObjectName("overviewDetailsCard")

        progress_layout = QVBoxLayout(progress_card)
        progress_layout.setContentsMargins(
            20,
            16,
            20,
            16,
        )
        progress_layout.setSpacing(10)

        progress_top = QHBoxLayout()

        progress_title = QLabel("Andamento do processo")
        progress_title.setObjectName("formSectionTitle")

        self.progress_value_label = QLabel("0%")
        self.progress_value_label.setObjectName("dataValue")

        progress_top.addWidget(progress_title)
        progress_top.addStretch()
        progress_top.addWidget(self.progress_value_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimumHeight(12)

        self.progress_description = QLabel(
            "Preencha os módulos para concluir o processo."
        )
        self.progress_description.setObjectName(
            "formSectionDescription"
        )
        self.progress_description.setWordWrap(True)

        progress_layout.addLayout(progress_top)
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(
            self.progress_description
        )

        central_layout.addWidget(progress_card)

        # ETAPAS

        self.refresh_button = QPushButton(
            "Atualizar resumo"
        )
        self.refresh_button.setObjectName(
            "secondaryButton"
        )
        self.refresh_button.setMinimumHeight(38)
        self.refresh_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.refresh_button.clicked.connect(
            self.refresh_process_summary
        )

        section_header = SectionHeader(
            "Preparação do relatório",
            (
                "Acompanhe o andamento dos módulos e acesse "
                "diretamente a etapa que precisa de atenção."
            ),
        )
        section_header.add_action(
            self.refresh_button
        )

        central_layout.addWidget(section_header)

        cards_layout = QGridLayout()
        cards_layout.setHorizontalSpacing(12)
        cards_layout.setVerticalSpacing(12)

        (
            documents_card,
            self.documents_description,
            self.documents_button,
        ) = self.create_stage_card(
            "Documentos",
            "Nenhum documento adicionado",
            "Abrir documentos",
            self.report_requested.emit,
        )

        (
            characteristics_card,
            self.characteristics_description,
            self.characteristics_button,
        ) = self.create_stage_card(
            "Características",
            "Nenhuma característica identificada",
            "Consultar características",
            self.characteristics_requested.emit,
        )

        (
            measurement_card,
            self.measurement_description,
            self.measurement_button,
        ) = self.create_stage_card(
            "Medição",
            "Informações não preenchidas",
            "Completar medição",
            self.measurement_requested.emit,
        )

        (
            images_card,
            self.images_description,
            self.images_button,
        ) = self.create_stage_card(
            "Imagens",
            "Nenhuma imagem adicionada",
            "Adicionar imagens",
            self.images_requested.emit,
        )

        (
            technical_control_card,
            self.technical_description,
            self.technical_button,
        ) = self.create_stage_card(
            "Controle técnico",
            "Responsáveis não definidos",
            "Configurar",
            self.technical_control_requested.emit,
        )

        (
            report_card,
            self.report_description,
            self.report_button,
        ) = self.create_stage_card(
            "Relatório final",
            "Valide o processo e prepare a emissão",
            "Preparar relatório",
            self.final_report_requested.emit,
        )

        cards_layout.addWidget(
            documents_card,
            0,
            0,
        )
        cards_layout.addWidget(
            characteristics_card,
            0,
            1,
        )
        cards_layout.addWidget(
            measurement_card,
            0,
            2,
        )
        cards_layout.addWidget(
            images_card,
            1,
            0,
        )
        cards_layout.addWidget(
            technical_control_card,
            1,
            1,
        )
        cards_layout.addWidget(
            report_card,
            1,
            2,
        )

        for column in range(3):
            cards_layout.setColumnStretch(
                column,
                1,
            )

        central_layout.addLayout(cards_layout)
        central_layout.addSpacing(14)

        central_row = QHBoxLayout()
        central_row.addStretch(1)
        central_row.addWidget(
            central_content,
            12,
        )
        central_row.addStretch(1)

        scroll_layout.addLayout(central_row)
        scroll_layout.addStretch(1)

        self.scroll_area.setWidget(
            scroll_content
        )
        root_layout.addWidget(
            self.scroll_area
        )

    # CAMPOS DE DADOS

    def add_data_field(
        self,
        layout: QGridLayout,
        title: str,
        row: int,
        column: int,
    ) -> QLabel:
        title_label = QLabel(title)
        title_label.setObjectName("dataLabel")

        value_label = QLabel("-")
        value_label.setObjectName("dataValue")
        value_label.setWordWrap(True)

        layout.addWidget(
            title_label,
            row,
            column,
        )
        layout.addWidget(
            value_label,
            row + 1,
            column,
        )

        return value_label

    # CARD DE ETAPA

    def create_stage_card(
        self,
        title: str,
        description: str,
        button_text: str,
        callback,
    ) -> tuple[QFrame, QLabel, QPushButton]:
        card = QFrame()
        card.setObjectName("overviewStageCard")
        card.setMinimumHeight(124)
        card.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(
            18,
            15,
            18,
            15,
        )
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")

        description_label = QLabel(description)
        description_label.setObjectName(
            "cardDescription"
        )
        description_label.setWordWrap(True)

        button = QPushButton(button_text)
        button.setObjectName("cardButton")
        button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        button.clicked.connect(callback)

        layout.addWidget(title_label)
        layout.addWidget(description_label)
        layout.addStretch(1)
        layout.addWidget(
            button,
            0,
            Qt.AlignmentFlag.AlignLeft,
        )

        return card, description_label, button

    # DEFINIR PROJETO

    def set_project(
        self,
        project: Project,
    ) -> None:
        self.current_project = project

        self.report_id_label.setText(
            project.report_id
        )
        self.project_name_label.setText(
            project.name
        )
        self.status_label.setText(
            project.status
        )
        self.version_label.setText(
            project.version
        )

        template_name = self._get_template_name(
            project.template
        )

        self.template_label.setText(
            (
                f"{template_name} · "
                f"Template v{project.template_version}"
            )
        )

        self.equipment_inline_label.setText(
            project.equipment
            or "Equipamento não informado"
        )

        self.inspection_type_value.setText(
            project.inspection_type
            or "-"
        )
        self.analysis_mode_value.setText(
            project.analysis_mode
            or "-"
        )
        self.template_value.setText(
            template_name
        )
        self.template_version_value.setText(
            project.template_version
            or "1.0"
        )
        self.quantity_value.setText(
            (
                f"{project.quantity} unidade"
                if project.quantity == 1
                else f"{project.quantity} unidades"
            )
        )
        self.technology_value.setText(
            project.technology
            or "-"
        )
        self.equipment_value.setText(
            project.equipment
            or "-"
        )
        self.status_value.setText(
            project.status
            or "-"
        )

        self.part_value.setText(
            project.part_name
            or "-"
        )
        self.code_value.setText(
            project.part_code
            or "-"
        )
        self.client_value.setText(
            project.client
            or "-"
        )
        self.description_value.setText(
            project.description
            or "-"
        )

        self.created_label.setText(
            "Criado em: "
            + self._format_datetime(
                project.created_at
            )
        )
        self.updated_label.setText(
            "Atualizado em: "
            + self._format_datetime(
                project.updated_at
            )
        )

        self.refresh_process_summary()

        self.scroll_area.verticalScrollBar().setValue(
            0
        )

    # ATUALIZAR RESUMO

    def refresh_process_summary(
        self,
    ) -> None:
        if (
            self.current_project is None
            or self.current_project.id is None
        ):
            return

        project_id = self.current_project.id

        try:
            documents = (
                self.pdf_service
                .get_project_documents(
                    project_id
                )
            )

            extractions = (
                self.extraction_service
                .get_project_extractions(
                    project_id
                )
            )

            measurement = (
                self.measurement_service
                .get_measurement(
                    project_id
                )
            )

            images = (
                self.image_service
                .get_project_images(
                    project_id
                )
            )

            technical_control = (
                self.technical_control_service
                .get_control(
                    project_id
                )
            )

        except Exception as error:
            QMessageBox.warning(
                self,
                "Resumo indisponível",
                (
                    "Não foi possível atualizar o resumo "
                    f"do processo.\n\n{error}"
                ),
            )
            return

        characteristics = [
            characteristic
            for _, extraction_characteristics
            in extractions
            for characteristic
            in extraction_characteristics
        ]

        self.update_documents_card(documents)
        self.update_characteristics_card(
            characteristics
        )
        self.update_measurement_card(
            measurement
        )
        self.update_images_card(images)
        self.update_technical_control_card(
            technical_control
        )
        self.update_final_report_card(
            documents=documents,
            characteristics=characteristics,
            measurement=measurement,
            images=images,
            technical_control=technical_control,
        )

    # DOCUMENTOS

    def update_documents_card(
        self,
        documents,
    ) -> None:
        total = len(documents)

        self.documents_metric.set_value(
            str(total)
        )

        analyzed = sum(
            1
            for document in documents
            if str(
                getattr(
                    document,
                    "analysis_status",
                    "",
                )
                or ""
            ).strip().lower()
            in {
                "concluído",
                "concluido",
                "analisado",
            }
        )

        failed = sum(
            1
            for document in documents
            if str(
                getattr(
                    document,
                    "analysis_status",
                    "",
                )
                or ""
            ).strip().lower()
            == "falha"
        )

        if total == 0:
            self.documents_description.setText(
                "Nenhum documento adicionado"
            )
            self.documents_button.setText(
                "Adicionar documentos"
            )
            return

        parts = [
            (
                f"{total} documento"
                if total == 1
                else f"{total} documentos"
            ),
            (
                f"{analyzed} analisado"
                if analyzed == 1
                else f"{analyzed} analisados"
            ),
        ]

        if failed:
            parts.append(
                f"{failed} com falha"
            )

        self.documents_description.setText(
            " · ".join(parts)
        )
        self.documents_button.setText(
            "Abrir documentos"
        )

    # CARACTERÍSTICAS

    def update_characteristics_card(
        self,
        characteristics,
    ) -> None:
        total = len(characteristics)

        self.characteristics_metric.set_value(
            str(total)
        )

        nok_count = sum(
            1
            for characteristic in characteristics
            if self.normalize_characteristic_status(
                characteristic.status
            )
            == "NOK"
        )

        unknown_count = sum(
            1
            for characteristic in characteristics
            if self.normalize_characteristic_status(
                characteristic.status
            )
            == "UNKNOWN"
        )

        if total == 0:
            self.characteristics_description.setText(
                "Nenhuma característica identificada"
            )
            return

        text = (
            f"{total} característica"
            if total == 1
            else f"{total} características"
        )

        details = []

        if nok_count:
            details.append(
                f"{nok_count} fora da tolerância"
            )

        if unknown_count:
            details.append(
                f"{unknown_count} não avaliadas"
            )

        if details:
            text += " · " + " · ".join(details)

        self.characteristics_description.setText(
            text
        )

    # MEDIÇÃO

    def update_measurement_card(
        self,
        measurement,
    ) -> None:
        if measurement is None:
            self.measurement_description.setText(
                "Informações não preenchidas"
            )
            self.measurement_button.setText(
                "Completar medição"
            )
            return

        responsible = str(
            measurement.responsible
            or ""
        ).strip()

        machine_details = str(
            measurement.machine_details
            or ""
        ).strip()

        filled_fields = sum(
            1
            for value in [
                measurement.responsible,
                measurement.measurement_datetime,
                measurement.drawing_reference,
                measurement.alignment,
                measurement.fixture,
                measurement.machine_details,
                measurement.accessories,
                measurement.sensors,
                measurement.special_instructions,
            ]
            if str(value or "").strip()
        )

        if responsible and machine_details:
            self.measurement_description.setText(
                (
                    "Dados essenciais preenchidos"
                    f" · {filled_fields} campos informados"
                )
            )
        else:
            pending = []

            if not responsible:
                pending.append("responsável")

            if not machine_details:
                pending.append("equipamento")

            self.measurement_description.setText(
                "Revisar: " + ", ".join(pending)
            )

        self.measurement_button.setText(
            "Abrir medição"
        )

    # IMAGENS

    def update_images_card(
        self,
        images,
    ) -> None:
        total = len(images)

        self.images_metric.set_value(
            str(total)
        )

        with_caption = sum(
            1
            for image in images
            if str(
                image.caption
                or ""
            ).strip()
        )

        if total == 0:
            self.images_description.setText(
                "Nenhuma imagem adicionada"
            )
            self.images_button.setText(
                "Adicionar imagens"
            )
            return

        text = (
            "1 imagem"
            if total == 1
            else f"{total} imagens"
        )

        if with_caption:
            text += (
                f" · {with_caption} com legenda"
            )

        self.images_description.setText(text)
        self.images_button.setText(
            "Abrir imagens"
        )

    # CONTROLE TÉCNICO

    def update_technical_control_card(
        self,
        control,
    ) -> None:
        if control is None:
            self.technical_description.setText(
                "Controle técnico não iniciado"
            )
            self.technical_button.setText(
                "Configurar"
            )
            return

        status = (
            control.status
            or "Em elaboração"
        )

        details = [status]

        if control.prepared_by:
            details.append(
                (
                    "Elaboração: "
                    f"{control.prepared_by}"
                )
            )

        if control.reviewed_by:
            details.append(
                (
                    "Revisão: "
                    f"{control.reviewed_by}"
                )
            )

        self.technical_description.setText(
            " · ".join(details)
        )
        self.technical_button.setText(
            "Abrir controle"
        )

    # RELATÓRIO FINAL E PROGRESSO

    def update_final_report_card(
        self,
        documents,
        characteristics,
        measurement,
        images,
        technical_control,
    ) -> None:
        completed_steps = 0
        total_steps = 5
        pending = []

        if documents:
            completed_steps += 1
        else:
            pending.append("documentos")

        if characteristics:
            completed_steps += 1
        else:
            pending.append("características")

        if measurement is not None:
            completed_steps += 1
        else:
            pending.append("medição")

        if images:
            completed_steps += 1
        else:
            pending.append("imagens")

        if (
            technical_control is not None
            and technical_control.status == "Aprovado"
        ):
            completed_steps += 1
        elif technical_control is None:
            pending.append("controle técnico")
        else:
            pending.append("aprovação")

        progress = round(
            completed_steps
            / total_steps
            * 100
        )

        self.progress_bar.setValue(progress)
        self.progress_value_label.setText(
            f"{progress}%"
        )

        self.pending_metric.set_value(
            str(len(pending))
        )
        self.pending_metric.set_helper_text(
            (
                "Processo pronto para emissão"
                if not pending
                else "Etapas que precisam de revisão"
            )
        )

        if pending:
            self.progress_description.setText(
                (
                    "Ainda faltam: "
                    + ", ".join(pending)
                    + "."
                )
            )
            self.report_description.setText(
                (
                    f"{len(pending)} etapa(s) "
                    "ainda precisam de revisão"
                )
            )
        else:
            self.progress_description.setText(
                "Todas as etapas obrigatórias foram concluídas."
            )
            self.report_description.setText(
                "Processo pronto para preparação do relatório"
            )

        self.report_button.setText(
            "Preparar relatório"
        )

    # UTILITÁRIOS

    def normalize_characteristic_status(
        self,
        value,
    ) -> str:
        normalized = str(
            value
            or ""
        ).strip().upper()

        if normalized in {
            "OK",
            "PASS",
            "APPROVED",
            "CONFORME",
        }:
            return "OK"

        if normalized in {
            "NOK",
            "FAIL",
            "FAILED",
            "REJECTED",
            "NÃO CONFORME",
            "NAO CONFORME",
        }:
            return "NOK"

        return "UNKNOWN"

    def _get_template_name(
        self,
        template_code: str,
    ) -> str:
        try:
            return get_template_definition(
                template_code
            ).name
        except ValueError:
            return (
                template_code
                or "Template não informado"
            )

    def _format_datetime(
        self,
        value: str | None,
    ) -> str:
        if not value:
            return "-"

        try:
            parsed = datetime.fromisoformat(value)
            return parsed.strftime(
                "%d/%m/%Y %H:%M"
            )
        except ValueError:
            return value