from __future__ import annotations

from typing import Any

from PySide6.QtCore import (
    Qt,
    Signal,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
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
from services.final_report_service import (
    FinalReportService,
)
from services.report_templates.template_catalog import (
    get_template_definition,
)
from ui.components.page_header import PageHeader


class FinalReportPage(QWidget):
    """
    Preparação e validação do relatório técnico.

    Esta tela não salva o PDF definitivo. Ela reúne o contexto,
    valida os dados, permite escolher as seções e solicita a geração
    de uma pré-visualização temporária.
    """

    back_requested = Signal()

    documents_requested = Signal()
    characteristics_requested = Signal()
    measurement_requested = Signal()
    images_requested = Signal()
    technical_control_requested = Signal()

    # Mantido para compatibilidade com o MainWindow atual.
    # O MainWindow será refatorado para interpretar este sinal
    # como solicitação de pré-visualização.
    generate_requested = Signal(dict)

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

        self.current_project: Project | None = None
        self.service = FinalReportService()

        self.current_context: dict[str, Any] = {}

        self.section_inputs: dict[str, QCheckBox] = {}
        self.section_frames: dict[str, QFrame] = {}
        self.section_badges: dict[str, QLabel] = {}
        self.section_meta_labels: dict[str, QLabel] = {}

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
        content.setMaximumWidth(1240)
        content.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(18)

        # ---------------------------------------------------------
        # CABEÇALHO
        # ---------------------------------------------------------

        self.page_header = PageHeader(
            title="Relatório final",
            subtitle=(
                "Valide o processo, selecione o conteúdo e gere uma "
                "pré-visualização antes da aprovação e exportação."
            ),
            metadata="-",
            back_text="← Visão geral",
        )
        self.page_header.back_button.clicked.connect(
            self.back_requested.emit
        )

        self.refresh_button = QPushButton(
            "Atualizar conteúdo"
        )
        self.refresh_button.setObjectName("secondaryButton")
        self.refresh_button.setMinimumHeight(40)
        self.refresh_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.refresh_button.clicked.connect(
            self.load_context
        )

        self.page_header.add_action(
            self.refresh_button
        )

        content_layout.addWidget(
            self.page_header
        )

        # ---------------------------------------------------------
        # CONTEXTO DO RELATÓRIO
        # ---------------------------------------------------------

        context_card = QFrame()
        context_card.setObjectName("formCard")

        context_layout = QGridLayout(context_card)
        context_layout.setContentsMargins(20, 16, 20, 16)
        context_layout.setHorizontalSpacing(32)
        context_layout.setVerticalSpacing(7)

        self.template_value = self._add_data_field(
            context_layout,
            "Template",
            0,
            0,
        )
        self.template_version_value = self._add_data_field(
            context_layout,
            "Versão do template",
            0,
            1,
        )
        self.scope_value = self._add_data_field(
            context_layout,
            "Escopo",
            0,
            2,
        )
        self.output_value = self._add_data_field(
            context_layout,
            "Saída desta etapa",
            0,
            3,
        )

        for column in range(4):
            context_layout.setColumnStretch(
                column,
                1,
            )

        content_layout.addWidget(context_card)

        # ---------------------------------------------------------
        # SITUAÇÃO GERAL
        # ---------------------------------------------------------

        self.general_status_card = QFrame()
        self.general_status_card.setObjectName(
            "dashboardCard"
        )

        general_layout = QHBoxLayout(
            self.general_status_card
        )
        general_layout.setContentsMargins(
            24,
            20,
            24,
            20,
        )
        general_layout.setSpacing(18)

        general_text = QVBoxLayout()
        general_text.setSpacing(4)

        self.general_status_title = QLabel(
            "Verificando o processo"
        )
        self.general_status_title.setObjectName(
            "cardTitle"
        )

        self.general_status_description = QLabel(
            "Aguarde enquanto os módulos do processo são validados."
        )
        self.general_status_description.setObjectName(
            "cardDescription"
        )
        self.general_status_description.setWordWrap(True)

        general_text.addWidget(
            self.general_status_title
        )
        general_text.addWidget(
            self.general_status_description
        )

        self.general_status_badge = QLabel(
            "Verificando"
        )
        self.general_status_badge.setObjectName(
            "statusBadge"
        )

        general_layout.addLayout(
            general_text,
            1,
        )
        general_layout.addWidget(
            self.general_status_badge,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        content_layout.addWidget(
            self.general_status_card
        )

        # ---------------------------------------------------------
        # INDICADORES
        # ---------------------------------------------------------

        indicators_layout = QGridLayout()
        indicators_layout.setHorizontalSpacing(12)
        indicators_layout.setVerticalSpacing(12)

        (
            documents_card,
            self.documents_value,
        ) = self.create_summary_card("Documentos")

        (
            units_card,
            self.units_value,
        ) = self.create_summary_card("Unidades")

        (
            characteristics_card,
            self.characteristics_value,
        ) = self.create_summary_card("Características")

        (
            approved_card,
            self.approved_value,
        ) = self.create_summary_card("Conformes")

        (
            rejected_card,
            self.rejected_value,
        ) = self.create_summary_card("Não conformes")

        (
            images_card,
            self.images_value,
        ) = self.create_summary_card("Imagens")

        indicator_cards = [
            documents_card,
            units_card,
            characteristics_card,
            approved_card,
            rejected_card,
            images_card,
        ]

        for column, card in enumerate(indicator_cards):
            indicators_layout.addWidget(
                card,
                0,
                column,
            )
            indicators_layout.setColumnStretch(
                column,
                1,
            )

        content_layout.addLayout(
            indicators_layout
        )

        # ---------------------------------------------------------
        # VALIDAÇÃO
        # ---------------------------------------------------------

        validation_card = QFrame()
        validation_card.setObjectName("formCard")

        validation_layout = QVBoxLayout(
            validation_card
        )
        validation_layout.setContentsMargins(
            20,
            17,
            20,
            17,
        )
        validation_layout.setSpacing(14)

        validation_title = QLabel(
            "Conteúdo disponível"
        )
        validation_title.setObjectName(
            "formSectionTitle"
        )

        validation_description = QLabel(
            "Os módulos disponíveis podem compor a pré-visualização. "
            "Apenas a emissão oficial depende da aprovação do Controle Técnico."
        )
        validation_description.setObjectName(
            "formSectionDescription"
        )
        validation_description.setWordWrap(True)

        self.validation_container = QWidget()

        self.validation_items_layout = QVBoxLayout(
            self.validation_container
        )
        self.validation_items_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self.validation_items_layout.setSpacing(10)

        validation_layout.addWidget(validation_title)
        validation_layout.addWidget(
            validation_description
        )
        validation_layout.addWidget(
            self.validation_container
        )

        content_layout.addWidget(
            validation_card
        )

        # ---------------------------------------------------------
        # SELEÇÃO DE CONTEÚDO
        # ---------------------------------------------------------

        sections_card = QFrame()
        sections_card.setObjectName("finalReportContentCard")

        sections_layout = QVBoxLayout(sections_card)
        sections_layout.setContentsMargins(20, 18, 20, 18)
        sections_layout.setSpacing(12)

        sections_title = QLabel(
            "Conteúdo disponível no processo"
        )
        sections_title.setObjectName(
            "formSectionTitle"
        )

        sections_description = QLabel(
            "Selecione as seções que deseja incluir no relatório. "
            "Itens sem informações continuam visíveis, mas ficam "
            "indisponíveis até que exista conteúdo."
        )
        sections_description.setObjectName(
            "formSectionDescription"
        )
        sections_description.setWordWrap(True)

        sections_layout.addWidget(sections_title)
        sections_layout.addWidget(sections_description)

        self.sections_container = QWidget()
        self.sections_container.setObjectName(
            "finalReportSectionsContainer"
        )

        self.sections_list_layout = QVBoxLayout(
            self.sections_container
        )
        self.sections_list_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self.sections_list_layout.setSpacing(0)

        section_definitions = [
            (
                "process_summary",
                "▤",
                "Resumo executivo",
                (
                    "Identificação do processo, template, equipamento "
                    "e indicadores gerais."
                ),
                None,
            ),
            (
                "documents",
                "▧",
                "Documentos e unidades",
                (
                    "Arquivos de origem, páginas e identificações "
                    "das unidades analisadas."
                ),
                "documents",
            ),
            (
                "measurement",
                "⌁",
                "Informações da medição",
                (
                    "Responsável, equipamento, sensores, alinhamento, "
                    "fixação e instruções."
                ),
                "measurement",
            ),
            (
                "characteristics",
                "≡",
                "Resultados metrológicos",
                (
                    "Resultados, tolerâncias, estatísticas, gráficos "
                    "e interpretação por característica."
                ),
                "characteristics",
            ),
            (
                "images",
                "▣",
                "Imagens técnicas",
                (
                    "Fotografias, CAD, renders, setup, fixação "
                    "e evidências anotadas."
                ),
                "images",
            ),
            (
                "observations",
                "✎",
                "Observações técnicas",
                (
                    "Condições especiais, ressalvas e notas "
                    "da elaboração ou revisão."
                ),
                None,
            ),
            (
                "technical_control",
                "◇",
                "Elaboração e aprovação",
                (
                    "Responsáveis, datas, situação da revisão "
                    "e Controle Técnico."
                ),
                "technical_control",
            ),
        ]

        for (
            key,
            icon,
            title,
            description,
            action_key,
        ) in section_definitions:
            self.sections_list_layout.addWidget(
                self.create_section_option(
                    key=key,
                    icon=icon,
                    title=title,
                    description=description,
                    action_key=action_key,
                )
            )

        sections_layout.addWidget(
            self.sections_container
        )

        info_bar = QFrame()
        info_bar.setObjectName(
            "finalReportInfoBar"
        )

        info_layout = QHBoxLayout(
            info_bar
        )
        info_layout.setContentsMargins(
            12,
            8,
            12,
            8,
        )
        info_layout.setSpacing(8)

        info_icon = QLabel("i")
        info_icon.setObjectName(
            "finalReportInfoIcon"
        )
        info_icon.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        info_icon.setFixedSize(22, 22)

        info_text = QLabel(
            "Seções marcadas serão incluídas na pré-visualização. "
            "Itens indisponíveis permanecem desabilitados até que "
            "existam informações."
        )
        info_text.setObjectName(
            "finalReportInfoText"
        )
        info_text.setWordWrap(True)

        info_layout.addWidget(info_icon)
        info_layout.addWidget(info_text, 1)

        sections_layout.addWidget(info_bar)

        content_layout.addWidget(sections_card)

        # ---------------------------------------------------------
        # RESUMO DA PRÉ-VISUALIZAÇÃO
        # ---------------------------------------------------------

        preview_card = QFrame()
        preview_card.setObjectName("formCard")

        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(
            20,
            17,
            20,
            17,
        )
        preview_layout.setSpacing(10)

        preview_title = QLabel(
            "Resumo da pré-visualização"
        )
        preview_title.setObjectName(
            "formSectionTitle"
        )

        self.preview_description = QLabel(
            "O resumo será atualizado após a validação do processo."
        )
        self.preview_description.setObjectName(
            "cardDescription"
        )
        self.preview_description.setWordWrap(True)

        preview_layout.addWidget(preview_title)
        preview_layout.addWidget(
            self.preview_description
        )

        content_layout.addWidget(
            preview_card
        )

        # ---------------------------------------------------------
        # AÇÕES
        # ---------------------------------------------------------

        actions = QHBoxLayout()
        actions.setSpacing(12)

        self.back_action_button = QPushButton(
            "Voltar"
        )
        self.back_action_button.setObjectName(
            "secondaryButton"
        )
        self.back_action_button.setMinimumHeight(44)
        self.back_action_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.back_action_button.clicked.connect(
            self.back_requested.emit
        )

        self.generate_button = QPushButton(
            "Gerar pré-visualização"
        )
        self.generate_button.setObjectName(
            "primaryButton"
        )
        self.generate_button.setMinimumHeight(44)
        self.generate_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.generate_button.clicked.connect(
            self.request_generation
        )

        actions.addStretch()
        actions.addWidget(
            self.back_action_button
        )
        actions.addWidget(
            self.generate_button
        )

        content_layout.addLayout(actions)

        # ---------------------------------------------------------
        # CENTRALIZAÇÃO
        # ---------------------------------------------------------

        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(content, 10)
        row.addStretch(1)

        scroll_layout.addLayout(row)
        scroll_layout.addSpacing(20)

        self.scroll_area.setWidget(scroll_content)
        root_layout.addWidget(self.scroll_area)

    # =============================================================
    # COMPONENTES
    # =============================================================

    def _add_data_field(
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

    def create_summary_card(
        self,
        title: str,
    ) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setObjectName("dashboardCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(
            18,
            15,
            18,
            15,
        )
        layout.setSpacing(4)

        label = QLabel(title)
        label.setObjectName("dataLabel")
        label.setWordWrap(True)

        value = QLabel("0")
        value.setObjectName("summaryValue")

        layout.addWidget(label)
        layout.addWidget(value)

        return card, value

    def create_section_option(
        self,
        *,
        key: str,
        icon: str,
        title: str,
        description: str,
        action_key: str | None,
    ) -> QFrame:
        frame = QFrame()
        frame.setObjectName(
            "finalReportSectionRow"
        )
        frame.setProperty(
            "available",
            False,
        )

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(
            14,
            10,
            14,
            10,
        )
        layout.setSpacing(12)

        checkbox = QCheckBox()
        checkbox.setObjectName(
            "finalReportSectionCheck"
        )
        checkbox.setFixedSize(22, 22)
        checkbox.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        checkbox.stateChanged.connect(
            self.update_preview_from_selection
        )

        icon_label = QLabel(icon)
        icon_label.setObjectName(
            "finalReportSectionIcon"
        )
        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        icon_label.setFixedSize(38, 38)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setObjectName(
            "finalReportSectionTitle"
        )

        description_label = QLabel(
            description
        )
        description_label.setObjectName(
            "finalReportSectionDescription"
        )
        description_label.setWordWrap(True)

        text_layout.addWidget(title_label)
        text_layout.addWidget(description_label)

        badge = QLabel(
            "Não disponível"
        )
        badge.setObjectName(
            "finalReportUnavailableBadge"
        )

        meta_label = QLabel("-")
        meta_label.setObjectName(
            "finalReportSectionMeta"
        )
        meta_label.setMinimumWidth(125)

        action_button = None
        if action_key:
            action_button = (
                self.create_section_action(
                    action_key
                )
            )

        layout.addWidget(
            checkbox,
            alignment=Qt.AlignmentFlag.AlignVCenter,
        )
        layout.addWidget(
            icon_label,
            alignment=Qt.AlignmentFlag.AlignVCenter,
        )
        layout.addLayout(text_layout, 1)
        layout.addWidget(
            badge,
            alignment=Qt.AlignmentFlag.AlignVCenter,
        )
        layout.addWidget(
            meta_label,
            alignment=Qt.AlignmentFlag.AlignVCenter,
        )

        if action_button is not None:
            layout.addWidget(
                action_button,
                alignment=Qt.AlignmentFlag.AlignVCenter,
            )

        self.section_inputs[key] = checkbox
        self.section_frames[key] = frame
        self.section_badges[key] = badge
        self.section_meta_labels[key] = meta_label

        return frame

    def create_section_action(
        self,
        key: str,
    ) -> QPushButton | None:
        actions = {
            "documents": (
                "Abrir documentos",
                self.documents_requested.emit,
            ),
            "characteristics": (
                "Ver características",
                self.characteristics_requested.emit,
            ),
            "measurement": (
                "Completar medição",
                self.measurement_requested.emit,
            ),
            "images": (
                "Abrir imagens",
                self.images_requested.emit,
            ),
            "technical_control": (
                "Abrir controle",
                self.technical_control_requested.emit,
            ),
        }

        action = actions.get(key)

        if action is None:
            return None

        text, callback = action

        button = QPushButton(text)
        button.setObjectName(
            "finalReportSectionAction"
        )
        button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        button.clicked.connect(callback)

        return button

    def create_validation_row(
        self,
        item: dict[str, Any],
    ) -> QFrame:
        row = QFrame()
        row.setObjectName("documentListItem")

        layout = QHBoxLayout(row)
        layout.setContentsMargins(
            16,
            13,
            16,
            13,
        )
        layout.setSpacing(14)

        status = item["status"]
        required = bool(
            item.get("required", False)
        )

        if status == "complete":
            symbol = "✓"
            status_text = "Concluído"
            badge_name = "statusBadgeSuccess"
        else:
            symbol = "!"
            status_text = (
                "Obrigatório"
                if required
                else "Opcional"
            )
            badge_name = "statusBadgeWarning"

        symbol_label = QLabel(symbol)
        symbol_label.setObjectName("documentOrder")
        symbol_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        symbol_label.setFixedSize(40, 40)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        title = QLabel(item["title"])
        title.setObjectName("cardTitle")

        description = QLabel(item["message"])
        description.setObjectName(
            "cardDescription"
        )
        description.setWordWrap(True)

        text_layout.addWidget(title)
        text_layout.addWidget(description)

        status_label = QLabel(status_text)
        status_label.setObjectName(badge_name)

        action_button = self.create_validation_action(
            item["key"]
        )

        layout.addWidget(symbol_label)
        layout.addLayout(text_layout, 1)
        layout.addWidget(
            status_label,
            alignment=Qt.AlignmentFlag.AlignTop,
        )

        if action_button is not None:
            layout.addWidget(
                action_button,
                alignment=Qt.AlignmentFlag.AlignTop,
            )

        return row

    def create_validation_action(
        self,
        key: str,
    ) -> QPushButton | None:
        actions = {
            "documents": (
                "Abrir documentos",
                self.documents_requested.emit,
            ),
            "characteristics": (
                "Ver características",
                self.characteristics_requested.emit,
            ),
            "measurement": (
                "Completar medição",
                self.measurement_requested.emit,
            ),
            "images": (
                "Abrir imagens",
                self.images_requested.emit,
            ),
            "primary_image": (
                "Selecionar imagem",
                self.images_requested.emit,
            ),
            "technical_control": (
                "Abrir controle",
                self.technical_control_requested.emit,
            ),
        }

        action = actions.get(key)

        if action is None:
            return None

        text, callback = action

        button = QPushButton(text)
        button.setObjectName("cardButton")
        button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        button.clicked.connect(callback)

        return button

    # =============================================================
    # PROJETO E CONTEXTO
    # =============================================================

    def set_project(
        self,
        project: Project,
    ) -> None:
        self.current_project = project

        self.page_header.set_metadata(
            f"{project.report_id} · {project.name}"
        )

        self.template_value.setText(
            self._get_template_name(
                project.template
            )
        )
        self.template_version_value.setText(
            project.template_version
            or "1.0"
        )
        self.output_value.setText(
            "PDF temporário para conferência"
        )

        self.load_context()

        self.scroll_area.verticalScrollBar().setValue(
            0
        )

    def load_context(self) -> None:
        if (
            self.current_project is None
            or self.current_project.id is None
        ):
            return

        try:
            context = (
                self.service.get_report_context(
                    self.current_project
                )
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Erro ao validar relatório",
                (
                    "Não foi possível preparar o contexto "
                    f"do relatório.\n\nDetalhes: {error}"
                ),
            )
            return

        self.current_context = context

        self.populate_scope(context)
        self.populate_summary(context)
        self.populate_validation(context)
        self.populate_sections(context)
        self.populate_general_status(context)
        self.populate_preview_summary(context)

    # =============================================================
    # PREENCHIMENTO
    # =============================================================

    def populate_scope(
        self,
        context: dict[str, Any],
    ) -> None:
        is_batch = bool(
            context.get("is_batch", False)
        )

        document_summary = context.get(
            "document_summary",
            {},
        )

        unit_count = int(
            document_summary.get(
                "unit_count",
                0,
            )
            or 0
        )

        if is_batch:
            scope = (
                "Relatório consolidado de lote"
                f" · {unit_count} unidade(s)"
            )
        else:
            scope = "Relatório de peça única"

        self.scope_value.setText(scope)

    def populate_summary(
        self,
        context: dict[str, Any],
    ) -> None:
        documents = context["document_summary"]
        characteristics = context[
            "characteristic_summary"
        ]
        images = context["image_summary"]

        self.documents_value.setText(
            str(documents["total"])
        )
        self.units_value.setText(
            str(
                documents.get(
                    "unit_count",
                    documents["total"],
                )
            )
        )
        self.characteristics_value.setText(
            str(characteristics["total"])
        )
        self.approved_value.setText(
            str(characteristics["ok"])
        )
        self.rejected_value.setText(
            str(characteristics["nok"])
        )
        self.images_value.setText(
            str(images["total"])
        )

    def populate_validation(
        self,
        context: dict[str, Any],
    ) -> None:
        self.clear_layout(
            self.validation_items_layout
        )

        for item in context["validation_items"]:
            self.validation_items_layout.addWidget(
                self.create_validation_row(item)
            )

    def populate_sections(
        self,
        context: dict[str, Any],
    ) -> None:
        available_sections = context[
            "available_sections"
        ]
        default_sections = context[
            "default_sections"
        ]

        for key, checkbox in self.section_inputs.items():
            checkbox.blockSignals(True)

            available = bool(
                available_sections.get(
                    key,
                    False,
                )
            )
            checked = bool(
                default_sections.get(
                    key,
                    False,
                )
            )

            checkbox.setEnabled(
                available
            )
            checkbox.setChecked(
                available and checked
            )

            frame = self.section_frames[key]
            frame.setProperty(
                "available",
                available,
            )
            frame.style().unpolish(frame)
            frame.style().polish(frame)

            badge = self.section_badges[key]

            if available:
                badge.setText(
                    self._get_available_badge_text(
                        key,
                        context,
                    )
                )
                badge.setObjectName(
                    "finalReportAvailableBadge"
                )
            else:
                badge.setText(
                    "Não disponível"
                )
                badge.setObjectName(
                    "finalReportUnavailableBadge"
                )

            badge.style().unpolish(badge)
            badge.style().polish(badge)

            self.section_meta_labels[
                key
            ].setText(
                self._get_section_meta(
                    key,
                    context,
                )
            )

            checkbox.setToolTip(
                (
                    "Seção disponível para inclusão no relatório."
                    if available
                    else (
                        "Seção indisponível porque não há "
                        "informações preenchidas."
                    )
                )
            )

            checkbox.blockSignals(False)

    def populate_general_status(
        self,
        context: dict[str, Any],
    ) -> None:
        can_export = bool(
            context.get(
                "can_export",
                False,
            )
        )

        available_count = sum(
            1
            for item in context.get(
                "validation_items",
                [],
            )
            if item.get("available")
        )

        if can_export:
            self.general_status_title.setText(
                "Pré-visualização e emissão disponíveis"
            )
            self.general_status_description.setText(
                (
                    f"{available_count} módulo(s) possuem conteúdo disponível. "
                    "O Controle Técnico está aprovado e o relatório poderá "
                    "ser exportado oficialmente após a conferência."
                )
            )
            self.general_status_badge.setText(
                "Aprovado"
            )
            self.general_status_badge.setObjectName(
                "statusBadgeSuccess"
            )
        else:
            self.general_status_title.setText(
                "Pré-visualização disponível"
            )
            self.general_status_description.setText(
                (
                    f"{available_count} módulo(s) possuem conteúdo disponível. "
                    "A pré-visualização pode ser gerada normalmente. "
                    "A exportação oficial permanecerá bloqueada até a "
                    "aprovação do Controle Técnico."
                )
            )
            self.general_status_badge.setText(
                "Em elaboração"
            )
            self.general_status_badge.setObjectName(
                "statusBadgeWarning"
            )

        self.general_status_badge.style().unpolish(
            self.general_status_badge
        )
        self.general_status_badge.style().polish(
            self.general_status_badge
        )

        self.generate_button.setEnabled(
            bool(
                context.get(
                    "can_preview",
                    True,
                )
            )
        )

    def populate_preview_summary(
        self,
        context: dict[str, Any],
    ) -> None:
        project = context["project"]
        documents = context["document_summary"]
        characteristics = context[
            "characteristic_summary"
        ]
        images = context["image_summary"]
        control = context["control_summary"]

        selected_count = sum(
            1
            for checkbox in self.section_inputs.values()
            if checkbox.isEnabled()
            and checkbox.isChecked()
        )

        scope_text = (
            (
                "Um PDF consolidado será montado "
                f"para {documents.get('unit_count', 0)} unidade(s)."
            )
            if context.get("is_batch", False)
            else "Um PDF técnico será montado para a peça única."
        )

        primary_text = (
            "Imagem principal definida."
            if images.get("has_primary", False)
            else "Imagem principal não definida."
        )

        parts = [
            (
                f"Processo {project.report_id}: "
                f"{project.name}."
            ),
            scope_text,
            (
                f"{documents['total']} documento(s) de origem "
                f"e {documents['pages']} página(s)."
            ),
            (
                f"{characteristics['total']} característica(s): "
                f"{characteristics['ok']} conforme(s) e "
                f"{characteristics['nok']} não conforme(s)."
            ),
            (
                f"{images['total']} imagem(ns). "
                f"{primary_text}"
            ),
            (
                f"Controle técnico: {control['status']}."
            ),
            (
                f"{selected_count} seção(ões) será(ão) incluída(s)."
            ),
            (
                "Nenhum local de salvamento será solicitado nesta etapa."
            ),
        ]

        self.preview_description.setText(
            "\n".join(parts)
        )

    def update_preview_from_selection(
        self,
    ) -> None:
        if self.current_context:
            self.populate_preview_summary(
                self.current_context
            )

    # =============================================================
    # METADADOS DAS SEÇÕES
    # =============================================================

    def _get_available_badge_text(
        self,
        key: str,
        context: dict[str, Any],
    ) -> str:
        if (
            key == "technical_control"
            and context.get(
                "can_export",
                False,
            )
        ):
            return "Aprovado"

        return "Disponível"

    def _get_section_meta(
        self,
        key: str,
        context: dict[str, Any],
    ) -> str:
        documents = context.get(
            "document_summary",
            {},
        )
        characteristics = context.get(
            "characteristic_summary",
            {},
        )
        images = context.get(
            "image_summary",
            {},
        )
        measurement = context.get(
            "measurement_summary",
            {},
        )
        control = context.get(
            "control_summary",
            {},
        )

        if key == "process_summary":
            return "Dados gerais"

        if key == "documents":
            total = int(
                documents.get(
                    "total",
                    0,
                )
                or 0
            )
            return f"{total} documento(s)"

        if key == "measurement":
            return (
                "Informações preenchidas"
                if measurement.get(
                    "complete",
                    False,
                )
                else "Sem informações"
            )

        if key == "characteristics":
            total = int(
                characteristics.get(
                    "total",
                    0,
                )
                or 0
            )
            return (
                f"{total} característica(s)"
            )

        if key == "images":
            total = int(
                images.get(
                    "total",
                    0,
                )
                or 0
            )
            return f"{total} imagem(ns)"

        if key == "observations":
            return (
                "Conteúdo preenchido"
                if context.get(
                    "available_sections",
                    {},
                ).get(
                    "observations",
                    False,
                )
                else "Sem observações"
            )

        if key == "technical_control":
            return str(
                control.get(
                    "status",
                    "Não iniciado",
                )
            )

        return "-"

    # =============================================================
    # SOLICITAÇÃO
    # =============================================================

    def request_generation(self) -> None:
        if not self.current_context:
            return

        selected_sections = {
            key: checkbox.isChecked()
            for key, checkbox in self.section_inputs.items()
            if checkbox.isEnabled()
        }

        if not any(selected_sections.values()):
            QMessageBox.warning(
                self,
                "Nenhuma seção selecionada",
                (
                    "Selecione pelo menos uma seção "
                    "para gerar a pré-visualização."
                ),
            )
            return

        payload = {
            "project": self.current_project,
            "context": self.current_context,
            "sections": selected_sections,
        }

        self.generate_requested.emit(payload)

    def set_generating(
        self,
        generating: bool,
    ) -> None:
        self.generate_button.setEnabled(
            not generating
            and bool(
                self.current_context.get(
                    "can_preview",
                    True,
                )
            )
        )
        self.refresh_button.setEnabled(
            not generating
        )
        self.back_action_button.setEnabled(
            not generating
        )
        self.generate_button.setText(
            (
                "Gerando pré-visualização..."
                if generating
                else "Gerar pré-visualização"
            )
        )

    # =============================================================
    # UTILITÁRIOS
    # =============================================================

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

    def clear_layout(
        self,
        layout,
    ) -> None:
        while layout.count():
            item = layout.takeAt(0)

            widget = item.widget()
            child_layout = item.layout()

            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                self.clear_layout(child_layout)